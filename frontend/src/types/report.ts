import type { Mission } from './mission'
import type { RouteResult } from './routing'

export interface SourceStatus { provider: string; source: string; status: string; method?: string | null; model_status?: string | null }
export interface SystemStatus {
  mission_id: number
  satellite: SourceStatus
  sonar: SourceStatus
  bathymetry: SourceStatus
  ocean: SourceStatus
  routing: SourceStatus
  external_providers: SourceStatus
}
export interface MissionReport {
  generated_at: string
  mission: Mission
  coordinate_status: string
  system_status: SystemStatus
  satellite: { source: string; method: string; analysis_status: string; percent_changed: number | null; changed_pixels: number | null; region_count: number | null }
  sonar: { source: string; replay_frames: number; uploaded_frame: boolean; detection_method: string; anomaly_count: number | null; ml_model_status: string }
  hazards: { total: number; active: number; resolved: number; manual: number; demo: number }
  environment: { available: boolean; coordinate_system: string; bathymetry_source: string; ocean_source: string; rows: number | null; cols: number | null; cell_size_m: number | null; parameters: { minimum_operational_depth_m: number; depth_comfort_m: number; wave_low_m: number; wave_high_m: number; current_reference_mps: number; routing_risk_aggressiveness: number } | null }
  risk: { available: boolean; navigable_cells: number | null; average_total_risk: number | null; minimum_total_risk: number | null; maximum_total_risk: number | null; weights: Record<string, number> | null }
  routing: RouteResult | null
  limitations: string[]
  disclaimer: string
}
