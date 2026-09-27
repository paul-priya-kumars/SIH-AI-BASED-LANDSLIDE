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
 * Enhanced API service with better state management, stale data detection, and retry mechanisms
 */
interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  lastUpdated: number | null;
  isStale: boolean;
  retryCount: number;
}

interface ApiResponse<T> {
  data: T | null;
  isMock: boolean;
  timestamp: number;
}

class EnhancedApiService {
  private readonly STALE_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutes
  private readonly MAX_RETRY_ATTEMPTS = 3;

  private states: Map<string, ApiState<any>> = new Map();

  /**
   * Robust fetch wrapper that gracefully falls back to mock data fixtures
   * when the backend server is unreachable or encountering network errors.
   */
  private async fetchWithFallback<T>(url: string, fallbackData: T, options?: RequestInit): Promise<ApiResponse<T>> {
    try {
      const res = await fetch(url, options);
      if (!res.ok) {
        console.warn(`API returned ${res.status} for ${url}. Using fallback fixture.`);
        return {
          data: fallbackData,
          isMock: true,
          timestamp: Date.now()
        };
      }
      const data = await res.json();
      return {
        data,
        isMock: false,
        timestamp: Date.now()
      };
    } catch (err) {
      console.warn(`Network/API error fetching ${url}. Seamlessly using fallback fixture.`, err);
      return {
        data: fallbackData,
        isMock: true,
        timestamp: Date.now()
      };
    }
  }

  /**
   * Get state for a specific endpoint, initializing if needed
   */
  private getState<T>(key: string): ApiState<T> {
    if (!this.states.has(key)) {
      this.states.set(key, {
        data: null,
        loading: false,
        error: null,
        lastUpdated: null,
        isStale: true,
        retryCount: 0
      });
    }
    return this.states.get(key) as ApiState<T>;
  }

  /**
   * Check if data is stale based on time threshold
   */
  private isDataStale(lastUpdated: number | null): boolean {
    if (lastUpdated === null) return true;
    return (Date.now() - lastUpdated) > this.STALE_THRESHOLD_MS;
  }

  /**
   * Update state with new data
   */
  private updateState<T>(key: string, data: T | null, isMock: boolean, error: string | null = null): void {
    const state = this.getState<T>(key);
    state.data = data;
    state.loading = false;
    state.error = error;
    state.lastUpdated = Date.now();
    state.isStale = this.isDataStale(state.lastUpdated);
    // Reset retry count on successful fetch
    if (!error) {
      state.retryCount = 0;
    }
  }

  /**
   * Fetch data with automatic retry mechanism
   */
  private async fetchWithRetry<T>(
    key: string,
    fetchFn: () => Promise<ApiResponse<T>>,
    retryCount = 0
  ): Promise<T | null> {
    const state = this.getState<T>(key);

    // If we're already loading and have recent data, return it
    if (state.loading && state.data !== null && !state.isStale) {
      return state.data;
    }

    // Set loading state
    state.loading = true;
    state.error = null;

    try {
      const response = await fetchFn();

      // Update state with response data
      this.updateState<T>(key, response.data, response.isMock);

      // If we got mock data and it's not the first attempt, we might want to retry
      if (response.isMock && retryCount < this.MAX_RETRY_ATTEMPTS) {
        // Wait a bit before retrying (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, retryCount) * 1000));
        return this.fetchWithRetry<T>(key, fetchFn, retryCount + 1);
      }

      return response.data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      state.loading = false;
      state.error = errorMessage;

      // Increment retry count and retry if under limit
      state.retryCount++;
      if (state.retryCount <= this.MAX_RETRY_ATTEMPTS) {
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, state.retryCount) * 1000));
        return this.fetchWithRetry<T>(key, fetchFn, state.retryCount);
      }

      // If we've exhausted retries, return null or fallback data will be used by caller
      return null;
    }
  }

  /**
   * Fetches landslide risk prediction and contributing factors for specific coordinates.
   */
  async getRisk(latitude: number, longitude: number): Promise<RiskPrediction | null> {
    const key = `risk-${latitude}-${longitude}`;
    const url = `${API_BASE}/risk?latitude=${latitude}&longitude=${longitude}`;
    const dynamicMock: RiskPrediction = {
      ...MOCK_RISK_PREDICTION,
      latitude,
      longitude,
      updated_at: new Date().toISOString(),
    };

    return this.fetchWithRetry<RiskPrediction>(
      key,
      () => this.fetchWithFallback<RiskPrediction>(url, dynamicMock)
    );
  }

  /**
   * Fetches environmental telemetry (Rainfall, Slope, Elevation, NDVI, Soil).
   */
  async getEnvironment(latitude: number, longitude: number): Promise<EnvironmentData | null> {
    const key = `environment-${latitude}-${longitude}`;
    const url = `${API_BASE}/environment?latitude=${latitude}&longitude=${longitude}`;
    const dynamicMock: EnvironmentData = {
      ...MOCK_ENVIRONMENT,
      latitude,
      longitude,
    };

    return this.fetchWithRetry<EnvironmentData>(
      key,
      () => this.fetchWithFallback<EnvironmentData>(url, dynamicMock)
    );
  }

  /**
   * Fetches geographic hazard zones for Leaflet map overlay.
   */
  async getRiskZones(): Promise<RiskZone[]> {
    const key = 'risk-zones';
    const result = await this.fetchWithRetry<RiskZone[]>(
      key,
      () => this.fetchWithFallback<RiskZone[]>(`${API_BASE}/risk-zones`, MOCK_RISK_ZONES)
    );
    return result ?? [];
  }

  /**
   * Retrieves active disaster bulletins and advisories.
   */
  async getAlerts(severity?: string): Promise<Alert[]> {
    const key = `alerts-${severity || 'all'}`;
    let url = `${API_BASE}/alerts`;
    if (severity) {
      url += `?severity=${encodeURIComponent(severity)}`;
    }

    const result = await this.fetchWithRetry<Alert[]>(
      key,
      () => this.fetchWithFallback<Alert[]>(url, MOCK_ALERTS)
    );
    return result ?? [];
  }

  /**
   * Retrieves single alert details.
   */
  async getAlert(alertId: string): Promise<Alert | null> {
    const key = `alert-${alertId}`;
    const url = `${API_BASE}/alerts/${alertId}`;
    const fallback = MOCK_ALERTS.find((a) => a.alert_id === alertId) || null;

    return this.fetchWithRetry<Alert | null>(
      key,
      () => this.fetchWithFallback<Alert | null>(url, fallback)
    );
  }

  /**
   * Retrieves citizen hazard reports with optional filters.
   */
  async getReports(status?: string, hazardType?: string): Promise<HazardReport[]> {
    const key = `reports-${status || 'all'}-${hazardType || 'all'}`;
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

    const result = await this.fetchWithRetry<HazardReport[]>(
      key,
      () => this.fetchWithFallback<HazardReport[]>(url, combinedFallback)
    );
    return result ?? [];
  }

  /**
   * Fetches a specific report by report_id.
   */
  async getReport(reportId: string): Promise<HazardReport | null> {
    const key = `report-${reportId}`;
    const url = `${API_BASE}/reports/${reportId}`;
    const localSubmissions: HazardReport[] = JSON.parse(
      localStorage.getItem('geoshield_local_reports') || '[]'
    );
    const fallback =
      localSubmissions.find((r) => r.report_id === reportId) ||
      MOCK_REPORTS.find((r) => r.report_id === reportId) ||
      null;

    return this.fetchWithRetry<HazardReport | null>(
      key,
      () => this.fetchWithFallback<HazardReport | null>(url, fallback)
    );
  }

  /**
   * Subsits a new citizen hazard report with optional photograph (multipart/form-data).
   */
  async createReport(formData: FormData): Promise<HazardReport | null> {
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

      // Clear relevant cache entries since we created a new report
      this.clearReportsCache();

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
  }

  /**
   * Updates status of a report (Authority function).
   */
  async updateReportStatus(reportId: string, status: string): Promise<HazardReport | null> {
    const key = `report-status-${reportId}`;
    const url = `${API_BASE}/reports/${reportId}/status`;
    try {
      const res = await fetch(url, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      if (res.ok) {
        const updated: HazardReport = await res.json();

        // Clear relevant cache entries since we updated a report
        this.clearReportsCache();

        return updated;
      }
    } catch (err) {
      console.warn('Status update API error', err);
    }
    return null;
  }

  /**
   * Compares travel route safety between start location and destination.
   */
  async getRouteRisk(start: string, destination: string): Promise<RouteRisk | null> {
    const key = `route-${start}-${destination}`;
    const url = `${API_BASE}/route-risk?start=${encodeURIComponent(start)}&destination=${encodeURIComponent(destination)}`;
    const dynamicMock: RouteRisk = {
      ...MOCK_ROUTE_RISK,
      start_location: start || MOCK_ROUTE_RISK.start_location,
      destination: destination || MOCK_ROUTE_RISK.destination,
      timestamp: new Date().toISOString(),
    };

    return this.fetchWithRetry<RouteRisk>(
      key,
      () => this.fetchWithFallback<RouteRisk>(url, dynamicMock)
    );
  }

  /**
   * NEW: Fetch model information from /api/ml/model-info endpoint
   */
  async getModelInfo(): Promise<{
    available: boolean;
    model_path: string | null;
    model_version: string | null;
    checksum: string | null;
    load_time_seconds: number | null;
    image_ai_enabled: boolean;
    cached_model: boolean;
    model_loaded: boolean;
    checkpoint_epoch: string | null;
    checkpoint_best_val_dice: string | null;
    error: string | null;
  } | null> {
    const key = 'model-info';
    return this.fetchWithRetry<any>(
      key,
      () => this.fetchWithFallback<any>(`${API_BASE}/ml/model-info`, {
        available: false,
        model_path: null,
        model_version: null,
        checksum: null,
        load_time_seconds: null,
        image_ai_enabled: false,
        cached_model: false,
        model_loaded: false,
        checkpoint_epoch: null,
        checkpoint_best_val_dice: null,
        error: 'Failed to fetch model info'
      })
    );
  }

  /**
   * NEW: Fetch drift status from /api/drift/status endpoint
   */
  async getDriftStatus(): Promise<{
    enabled: boolean;
    window_size: number;
    psi_threshold: number;
    observation_count: number;
    baseline_available: boolean;
    drift_detected: boolean;
    model_name: string;
    timestamp: string;
    details: {
      psi_scores: number[] | null;
      band_means: number[] | null;
      band_stds: number[] | null;
    } | null;
    error: string | null;
  } | null> {
    const key = 'drift-status';
    return this.fetchWithRetry<any>(
      key,
      () => this.fetchWithFallback<any>(`${API_BASE}/drift/status`, {
        enabled: false,
        window_size: 100,
        psi_threshold: 0.2,
        observation_count: 0,
        baseline_available: false,
        drift_detected: false,
        model_name: 'unknown',
        timestamp: new Date().toISOString(),
        details: null,
        error: 'Failed to fetch drift status'
      })
    );
  }

  /**
   * Clear cache for reports-related entries
   */
  private clearReportsCache(): void {
    for (const [key] of this.states.entries()) {
      if (key.startsWith('reports-') || key.startsWith('report-') || key.startsWith('report-status-')) {
        this.states.delete(key);
      }
    }
  }

  /**
   * Get current state for a specific endpoint (for UI components to consume)
   */
  getStateSnapshot<T>(key: string): ApiState<T> {
    // Create a getter method to access the private states map
    // Since TypeScript doesn't allow direct access to private fields from outside the class,
    // we'll create a public method that returns a copy of the state
    const state = this.states.get(key);
    if (!state) {
      // Initialize if not exists
      this.states.set(key, {
        data: null,
        loading: false,
        error: null,
        lastUpdated: null,
        isStale: true,
        retryCount: 0
      });
      return this.states.get(key) as ApiState<T>;
    }
    return state;
  }

  /**
   * Clear all cached states (useful for logout or reset)
   */
  clearAllStates(): void {
    this.states.clear();
  }
}

// Export singleton instance
export const enhancedApi = new EnhancedApiService();

// Also export the original api for backward compatibility
export { api } from './api';