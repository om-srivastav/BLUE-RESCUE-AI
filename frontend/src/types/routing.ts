export interface GridPoint { row: number; col: number }

export interface RiskCell extends GridPoint {
  depth_m: number
  wave_height_m: number
  u_current_mps: number
  v_current_mps: number
  hazard_risk: number
  depth_risk: number
  wave_risk: number
  current_risk: number
  uncertainty_risk: number
  total_risk: number
  navigable: boolean
}

export interface DemoHazard extends GridPoint {
  id: string
  label: string
  hazard_type: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  severity_factor: number
  confidence: number
  anomaly_score?: number | null
  radius_cells: number
  source_type: string
  status: 'ACTIVE' | 'RESOLVED'
  created_at: string | null
}

export interface RiskMap {
  rows: number
  cols: number
  cell_size_m: number
  coordinate_system: string
  source_type: string
  depth_threshold_label: string
  minimum_operational_depth_m: number
  cells: RiskCell[][]
  hazards: DemoHazard[]
  start: GridPoint
  destination: GridPoint
  start_name: string
  destination_name: string
  provenance: Record<string, string>
}

export interface RouteData {
  route_type: string
  coordinates: GridPoint[]
  distance_m: number
  average_risk: number
  accumulated_risk: number
  minimum_depth_m: number
  hazards_approached: string[]
  average_wave_height_m: number
  accumulated_wave_exposure_m: number
  average_directional_current_risk: number
  computation_time_ms: number
  distance_basis: string
}

export interface RouteResult {
  shortest_route: RouteData
  lower_risk_route: RouteData
  comparison: {
    distance_difference_m: number
    average_risk_difference: number
    hazards_avoided: string[]
    minimum_depth_difference_m: number
    explanation: string
  }
  start?: GridPoint | null
  destination?: GridPoint | null
  calculated_at?: string | null
}

export interface HazardCreateInput extends GridPoint {
  hazard_type: string
  severity: string
  confidence: number
  notes: string
  source_type: 'MANUAL'
  client_request_id: string
}

export interface HazardImpact {
  risk_recalculated: boolean
  route_recalculated: boolean
  reason: string | null
  previous_route_affected: boolean | null
  route_changed: boolean | null
  previous_route: { distance_m: number; average_risk: number; accumulated_risk: number } | null
  updated_route: { distance_m: number; average_risk: number; accumulated_risk: number } | null
  retained_path_average_risk: number | null
  explanation: string
}

export interface HazardMutationResult {
  hazard: DemoHazard
  impact: HazardImpact
  risk_map: RiskMap
  routes: RouteResult | null
}
