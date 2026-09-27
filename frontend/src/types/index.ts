export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH' | 'CRITICAL';

export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type ReportStatus = 'PENDING' | 'UNDER_REVIEW' | 'VERIFIED' | 'REJECTED' | 'RESOLVED';

export type HazardType =
  | 'Road crack'
  | 'Ground crack'
  | 'Rockfall'
  | 'Soil movement'
  | 'Landslide'
  | 'Water seepage'
  | 'Fallen debris'
  | 'Other';

export interface UserLocation {
  latitude: number;
  longitude: number;
  name?: string;
  isCustom?: boolean;
  accuracy?: number;
}

export interface RiskPrediction {
  latitude: number;
  longitude: number;
  location_name?: string;
  risk_probability: number;
  risk_level: RiskLevel;
  confidence: number;
  factors: string[];
  updated_at: string;
  is_mock: boolean;
}

export interface EnvironmentData {
  latitude: number;
  longitude: number;
  location_name?: string;
  rainfall: number;
  temperature: number;
  humidity: number;
  slope: number;
  elevation: number;
  ndvi: number;
  soil_saturation_pct?: number;
  is_mock: boolean;
}

export interface Alert {
  id: number;
  alert_id: string;
  title: string;
  message: string;
  severity: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  location: string;
  latitude: number;
  longitude: number;
  issued_at: string;
  recommended_action: string;
  is_active: boolean;
}

export interface HazardReport {
  id: number;
  report_id: string;
  user_id?: string;
  latitude: number;
  longitude: number;
  location_name?: string;
  hazard_type: HazardType | string;
  description: string;
  severity: SeverityLevel;
  image_path?: string | null;
  image_url?: string | null;
  contact_name?: string | null;
  contact_phone?: string | null;
  status: ReportStatus;
  created_at: string;
  updated_at: string;
}

export interface RiskZone {
  id: number;
  zone_id: string;
  name: string;
  risk_level: RiskLevel;
  risk_probability: number;
  latitude: number;
  longitude: number;
  radius_meters: number;
  polygon_geojson?: string | null;
  rainfall_mm: number;
  slope_deg: number;
  elevation_m: number;
  soil_type?: string | null;
  updated_at: string;
}

export interface RouteSegment {
  name: string;
  risk_level: RiskLevel;
  distance_km: number;
  travel_time_mins: number;
  hazard_zones_crossed: string[];
  is_recommended: boolean;
  summary_advisory: string;
  waypoints?: [number, number][];
}

export interface RouteRisk {
  start_location: string;
  destination: string;
  recommended_route: RouteSegment;
  alternative_route: RouteSegment;
  overall_advisory: string;
  timestamp: string;
  is_mock: boolean;
}
