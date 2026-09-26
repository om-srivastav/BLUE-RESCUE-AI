export type MissionMode = 'DEMO' | 'REAL_DATA' | 'OFFLINE_CACHED'

export interface AOI {
  id: number
  mission_id: number
  name: string
  min_latitude: number
  max_latitude: number
  min_longitude: number
  max_longitude: number
  crs: 'EPSG:4326'
}

export interface Mission {
  id: number
  name: string
  description: string
  mode: MissionMode
  status: string
  source_type: string
  created_at: string
  updated_at: string
  aois: AOI[]
}

export interface Health { status: string; database: string; data_mode: string }
