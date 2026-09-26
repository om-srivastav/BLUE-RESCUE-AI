// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { api } from '../services/api'
import { ReportPage } from './ReportPage'
import { DataSourcesPanel } from '../components/mission/DataSourcesPanel'
import type { MissionReport, SystemStatus } from '../types/report'

vi.mock('../services/api', () => ({ api: { report: vi.fn() }, errorMessage: (e: unknown) => String(e) }))

const source = (source: string, status = 'AVAILABLE') => ({ provider: 'LOCAL', source, status })
const status: SystemStatus = { mission_id: 7, satellite: source('SIMULATED_DEMO_DATA'), sonar: { ...source('MISSION_REPLAY'), model_status: 'MODEL_NOT_CONFIGURED' }, bathymetry: source('SIMULATED_DEMO_DATA'), ocean: source('SIMULATED_DEMO_DATA'), routing: source('LOCAL_COMPUTATION'), external_providers: { provider: 'EXTERNAL', source: 'NONE', status: 'NOT_CONFIGURED' } }
const report: MissionReport = {
  generated_at: '2026-09-26T12:00:00Z',
  mission: { id: 7, name: 'Mission Cyclone Varuna', description: '', mode: 'DEMO', status: 'PLANNING', source_type: 'SIMULATED', created_at: '2026-09-26T09:00:00Z', updated_at: '2026-09-26T09:00:00Z', aois: [] },
  coordinate_status: 'SCHEMATIC_GRID_NOT_GEOGRAPHIC', system_status: status,
  satellite: { source: 'SIMULATED_DEMO_DATA', method: 'CLASSICAL_CV_BASELINE', analysis_status: 'COMPUTED_ON_DEMAND', percent_changed: 2.06, changed_pixels: 100, region_count: 2 },
  sonar: { source: 'MISSION_REPLAY', replay_frames: 5, uploaded_frame: false, detection_method: 'DEMO_ANNOTATIONS', anomaly_count: null, ml_model_status: 'MODEL_NOT_CONFIGURED' },
  hazards: { total: 3, active: 2, resolved: 1, manual: 1, demo: 2 },
  environment: { available: true, coordinate_system: 'SCHEMATIC_GRID_NOT_GEOGRAPHIC', bathymetry_source: 'SIMULATED_DEMO_DATA', ocean_source: 'SIMULATED_DEMO_DATA', rows: 24, cols: 36, cell_size_m: 50, parameters: { minimum_operational_depth_m: 4.5, depth_comfort_m: 9.5, wave_low_m: 0.4, wave_high_m: 2, current_reference_mps: 1, routing_risk_aggressiveness: 4 } },
  risk: { available: true, navigable_cells: 700, average_total_risk: 0.15, minimum_total_risk: 0.01, maximum_total_risk: 0.7, weights: { hazard: 0.4, depth: 0.2 } },
  routing: null, limitations: ['No external provider is configured.'], disclaimer: 'BLUE-RESCUE AI is an academic decision-support prototype. It is not a certified maritime navigation or emergency-response system.',
}

beforeEach(() => { vi.clearAllMocks(); vi.mocked(api.report).mockResolvedValue(report) })
afterEach(cleanup)

it('shows honest source and model status cards', () => {
  render(<DataSourcesPanel status={status} />)
  expect(screen.getByText('Data sources / system status')).toBeTruthy()
  expect(screen.getByText(/Source: MISSION REPLAY/)).toBeTruthy()
  expect(screen.getByText(/ML model: MODEL NOT CONFIGURED/)).toBeTruthy()
  expect(screen.getByText('NOT CONFIGURED')).toBeTruthy()
})

it('renders current report sections and prints on request', async () => {
  const print = vi.fn()
  vi.stubGlobal('print', print)
  render(<MemoryRouter initialEntries={['/missions/7/report']}><Routes><Route path="/missions/:id/report" element={<ReportPage />} /></Routes></MemoryRouter>)
  expect(await screen.findByText('Mission Cyclone Varuna')).toBeTruthy()
  expect(screen.getByText('2.06%')).toBeTruthy()
  expect(screen.getByText('No route has been calculated for this mission.')).toBeTruthy()
  expect(screen.getByText(/It is not a certified maritime navigation/)).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Print report' }))
  expect(print).toHaveBeenCalledOnce()
  expect(api.report).toHaveBeenCalledWith(7)
  vi.unstubAllGlobals()
})
