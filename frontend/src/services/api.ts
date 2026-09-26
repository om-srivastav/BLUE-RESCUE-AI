import axios from 'axios'
import type { Health, Mission, MissionMode } from '../types/mission'
import type { DemoHazard, GridPoint, HazardCreateInput, HazardMutationResult, RiskMap, RouteResult } from '../types/routing'
import type { MissionReport, SystemStatus } from '../types/report'

const client = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || '/api', timeout: 10000 })

export const api = {
  health: async () => (await client.get<Health>('/health')).data,
  missions: async () => (await client.get<Mission[]>('/missions')).data,
  mission: async (id: number) => (await client.get<Mission>(`/missions/${id}`)).data,
  createMission: async (payload: { name: string; description: string; mode: MissionMode }) =>
    (await client.post<Mission>('/missions', payload)).data,
  riskMap: async (id: number) => (await client.get<RiskMap>(`/missions/${id}/risk-map`)).data,
  recalculateRiskMap: async (id: number) => (await client.post<RiskMap>(`/missions/${id}/risk-map/recalculate`, {})).data,
  calculateRoutes: async (id: number, start: GridPoint, destination: GridPoint) =>
    (await client.post<RouteResult>(`/missions/${id}/routes/calculate`, { start, destination })).data,
  latestRoutes: async (id: number) => (await client.get<RouteResult>(`/missions/${id}/routes`)).data,
  hazards: async (id: number) => (await client.get<DemoHazard[]>(`/missions/${id}/hazards`)).data,
  createHazard: async (id: number, payload: HazardCreateInput) =>
    (await client.post<HazardMutationResult>(`/missions/${id}/hazards`, payload)).data,
  resolveHazard: async (id: number, hazardId: string) =>
    (await client.patch<HazardMutationResult>(`/missions/${id}/hazards/${encodeURIComponent(hazardId)}`, { status: 'RESOLVED' })).data,
  satelliteStatus: async (id: number) => (await client.get<import('../types/imagery').SatelliteStatus>(`/missions/${id}/satellite/status`)).data,
  satelliteUpload: async (id: number, role: 'before' | 'after', file: File) => {
    const data = new FormData(); data.append('file', file)
    return (await client.post(`/missions/${id}/satellite/upload?role=${role}`, data)).data
  },
  satelliteAnalyze: async (id: number, source: 'demo' | 'uploaded') =>
    (await client.post<import('../types/imagery').SatelliteResult>(`/missions/${id}/satellite/analyze`, { source, detector: 'classical' })).data,
  satelliteAsset: (id: number, source: string, role: string) => `${client.defaults.baseURL}/missions/${id}/satellite/assets/${source}/${role}`,
  sonarReplay: async (id: number) => (await client.get<import('../types/imagery').SonarReplay>(`/missions/${id}/sonar/replay`)).data,
  sonarStatus: async (id: number) => (await client.get<{ uploaded_frame: boolean; ml_model_configured: boolean }>(`/missions/${id}/sonar/model/status`)).data,
  sonarUpload: async (id: number, file: File) => {
    const data = new FormData(); data.append('file', file)
    return (await client.post(`/missions/${id}/sonar/upload`, data)).data
  },
  sonarAnalyze: async (id: number) => (await client.post<import('../types/imagery').SonarResult>(`/missions/${id}/sonar/analyze`, { source: 'uploaded', detector: 'heuristic' })).data,
  sonarAsset: (id: number) => `${client.defaults.baseURL}/missions/${id}/sonar/assets/uploaded/frame`,
  systemStatus: async (id: number) => (await client.get<SystemStatus>(`/missions/${id}/system-status`)).data,
  report: async (id: number) => (await client.get<MissionReport>(`/missions/${id}/report`)).data,
}

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    return typeof detail === 'string' ? detail : detail?.message || error.message
  }
  return error instanceof Error ? error.message : 'Unexpected error'
}
