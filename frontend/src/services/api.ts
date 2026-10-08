import {
  Alert,
  EnvironmentData,
  HazardReport,
  RiskPrediction,
  RiskZone,
  RouteRisk,
} from '../types';
import {
  MOCK_ALERTS,
  MOCK_ENVIRONMENT,
  MOCK_REPORTS,
  MOCK_RISK_PREDICTION,
  MOCK_RISK_ZONES,
  MOCK_ROUTE_RISK,
} from '../data/mockData';

const API_BASE = '/api';

/**
 * Robust fetch wrapper that gracefully falls back to mock data fixtures
 * when the backend server is unreachable or encountering network errors.
 */
async function fetchWithFallback<T>(url: string, fallbackData: T, options?: RequestInit): Promise<T> {
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      console.warn(`API returned ${res.status} for ${url}. Using fallback fixture.`);
      return fallbackData;
    }
    return await res.json();
  } catch (err) {
    console.warn(`Network/API error fetching ${url}. Seamlessly using fallback fixture.`, err);
    return fallbackData;
  }
}

export const api = {
  /**
   * Fetches landslide risk prediction and contributing factors for specific coordinates.
   * Connects to M1 ML model contract in Phase 2.
   */
  async getRisk(latitude: number, longitude: number): Promise<RiskPrediction> {
    const url = `${API_BASE}/risk?latitude=${latitude}&longitude=${longitude}`;
    const dynamicMock: RiskPrediction = {
      ...MOCK_RISK_PREDICTION,
      latitude,
      longitude,
      updated_at: new Date().toISOString(),
    };
    return fetchWithFallback<RiskPrediction>(url, dynamicMock);
  },

  /**
   * Fetches environmental telemetry (Rainfall, Slope, Elevation, NDVI, Soil).
   * Connects to M2 GIS data pipelines in Phase 2.
   */
  async getEnvironment(latitude: number, longitude: number): Promise<EnvironmentData> {
    const url = `${API_BASE}/environment?latitude=${latitude}&longitude=${longitude}`;
    const dynamicMock: EnvironmentData = {
      ...MOCK_ENVIRONMENT,
      latitude,
      longitude,
    };
    return fetchWithFallback<EnvironmentData>(url, dynamicMock);
  },

  /**
   * Fetches geographic hazard zones for Leaflet map overlay.
   */
  async getRiskZones(): Promise<RiskZone[]> {
    const url = `${API_BASE}/risk-zones`;
    return fetchWithFallback<RiskZone[]>(url, MOCK_RISK_ZONES);
  },

  /**
   * Retrieves active disaster bulletins and advisories.
   */
  async getAlerts(severity?: string): Promise<Alert[]> {
    let url = `${API_BASE}/alerts`;
    if (severity) {
      url += `?severity=${encodeURIComponent(severity)}`;
    }
    return fetchWithFallback<Alert[]>(url, MOCK_ALERTS);
  },

  /**
   * Retrieves single alert details.
   */
  async getAlert(alertId: string): Promise<Alert | null> {
    const url = `${API_BASE}/alerts/${alertId}`;
    const fallback = MOCK_ALERTS.find((a) => a.alert_id === alertId) || null;
    return fetchWithFallback<Alert | null>(url, fallback);
  },

  /**
   * Retrieves citizen hazard reports with optional filters.
   */
  async getReports(status?: string, hazardType?: string): Promise<HazardReport[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (hazardType) params.append('hazard_type', hazardType);
    const queryString = params.toString() ? `?${params.toString()}` : '';
    const url = `${API_BASE}/reports${queryString}`;

    // Read any locally submitted reports stored in browser session/localStorage
    const localSubmissions: HazardReport[] = JSON.parse(
      localStorage.getItem('geoshield_local_reports') || '[]'
    );
    const combinedFallback = [...localSubmissions, ...MOCK_REPORTS];

    return fetchWithFallback<HazardReport[]>(url, combinedFallback);
  },

  /**
   * Fetches a specific report by report_id.
   */
  async getReport(reportId: string): Promise<HazardReport | null> {
    const url = `${API_BASE}/reports/${reportId}`;
    const localSubmissions: HazardReport[] = JSON.parse(
      localStorage.getItem('geoshield_local_reports') || '[]'
    );
    const fallback =
      localSubmissions.find((r) => r.report_id === reportId) ||
      MOCK_REPORTS.find((r) => r.report_id === reportId) ||
      null;
    return fetchWithFallback<HazardReport | null>(url, fallback);
  },

  /**
   * Submits a new citizen hazard report with optional photograph (multipart/form-data).
   */
  async createReport(formData: FormData): Promise<HazardReport> {
    try {
      const res = await fetch(`${API_BASE}/reports`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server returned error ${res.status}`);
      }

      const created: HazardReport = await res.json();
      return created;
    } catch (err) {
      console.warn('Backend unavailable, saving locally as fallback.', err);
      // Generate client-side report fallback
      const currentYear = new Date().getFullYear();
      const randomSeq = Math.floor(1000 + Math.random() * 9000);
      const generatedId = `LSR-${currentYear}-${randomSeq}`;

      const localReport: HazardReport = {
        id: Date.now(),
        report_id: generatedId,
        latitude: parseFloat(formData.get('latitude') as string) || 11.41,
        longitude: parseFloat(formData.get('longitude') as string) || 76.69,
        location_name: (formData.get('location_name') as string) || 'Reported Location',
        hazard_type: (formData.get('hazard_type') as string) || 'Other',
        description: (formData.get('description') as string) || '',
        severity: (formData.get('severity') as any) || 'MEDIUM',
        contact_name: (formData.get('contact_name') as string) || null,
        contact_phone: (formData.get('contact_phone') as string) || null,
        image_path: null,
        image_url: null,
        status: 'PENDING',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      const existing: HazardReport[] = JSON.parse(
        localStorage.getItem('geoshield_local_reports') || '[]'
      );
      localStorage.setItem(
        'geoshield_local_reports',
        JSON.stringify([localReport, ...existing])
      );

      return localReport;
    }
  },

  /**
   * Updates status of a report (Authority function).
   */
  async updateReportStatus(reportId: string, status: string): Promise<HazardReport | null> {
    const url = `${API_BASE}/reports/${reportId}/status`;
    try {
      const res = await fetch(url, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      if (res.ok) {
        return await res.json();
      }
    } catch (err) {
      console.warn('Status update API error', err);
    }
    return null;
  },

  /**
   * Compares travel route safety between start location and destination.
   */
  async getRouteRisk(start: string, destination: string): Promise<RouteRisk> {
    const url = `${API_BASE}/route-risk?start=${encodeURIComponent(start)}&destination=${encodeURIComponent(destination)}`;
    const dynamicMock: RouteRisk = {
      ...MOCK_ROUTE_RISK,
      start_location: start || MOCK_ROUTE_RISK.start_location,
      destination: destination || MOCK_ROUTE_RISK.destination,
      timestamp: new Date().toISOString(),
    };
    return fetchWithFallback<RouteRisk>(url, dynamicMock);
  },
};
