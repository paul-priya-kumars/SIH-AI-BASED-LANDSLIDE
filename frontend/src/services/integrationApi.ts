/**
 * Integration API client (M1 environmental + M2 spatial + M3 satellite).
 *
 * Mirrors the backend `backend/app/routes/integration.py` contract. Every
 * component carries its own availability/provenance, so the UI can show honest
 * "not available" states instead of inventing values.
 */
const API_BASE = '/api';

export interface RiskComponent {
  available: boolean;
  is_real?: boolean;
  probability: number | null;
  level?: string | null;
  confidence?: number;
  reason?: string;
  error?: string;
  provider?: string;
  data_source?: string;
  zone_id?: string | null;
  name?: string | null;
  inside_zone?: boolean;
  distance_m?: number | null;
}

export interface CompositeRisk {
  latitude: number;
  longitude: number;
  location_name?: string | null;
  components: {
    environmental_m1: RiskComponent;
    spatial_m2: RiskComponent;
    satellite_m3: RiskComponent;
  };
  components_used: string[];
  final_risk: {
    available: boolean;
    probability: number | null;
    risk_level: string | null;
    method: string;
  };
  environment_is_mock: boolean;
  is_mock: boolean;
}

export interface M1Status {
  available: boolean;
  model_version?: string;
  artifact_path?: string;
  classes?: string[];
  error?: string | null;
}

export interface M3Status {
  available: boolean;
  artifact_present?: boolean;
  model_architecture?: string;
  coordinate_mapping?: { available: boolean; reason: string };
  error?: string | null;
}

export interface ModelsStatus {
  environmental_m1: M1Status;
  satellite_m3: M3Status;
}

export async function fetchCompositeRisk(
  latitude: number,
  longitude: number,
  signal?: AbortSignal,
): Promise<CompositeRisk> {
  const response = await fetch(
    `${API_BASE}/risk/composite?latitude=${latitude}&longitude=${longitude}`,
    { signal },
  );
  if (!response.ok) {
    throw new Error(`Composite risk request failed (${response.status})`);
  }
  return response.json();
}

export async function fetchModelsStatus(signal?: AbortSignal): Promise<ModelsStatus> {
  const response = await fetch(`${API_BASE}/ml/models/status`, { signal });
  if (!response.ok) {
    throw new Error(`Model status request failed (${response.status})`);
  }
  return response.json();
}
