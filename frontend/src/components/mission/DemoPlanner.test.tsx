// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { DemoPlanner } from './DemoPlanner'
import { api } from '../../services/api'
import type { DemoHazard, HazardMutationResult, RiskMap, RouteData, RouteResult } from '../../types/routing'

vi.mock('../../services/api', () => ({
  api: { riskMap: vi.fn(), latestRoutes: vi.fn(), calculateRoutes: vi.fn(), recalculateRiskMap: vi.fn(), createHazard: vi.fn(), resolveHazard: vi.fn() },
  errorMessage: (error: unknown) => String(error),
}))

const cells = Array.from({ length: 2 }, (_, row) => Array.from({ length: 3 }, (_, col) => ({
  row, col, depth_m: 8, wave_height_m: 0.7, u_current_mps: 0.2, v_current_mps: 0.1,
  hazard_risk: 0, depth_risk: 0.1, wave_risk: 0.2, current_risk: 0.1,
  uncertainty_risk: 0, total_risk: 0.1, navigable: true,
})))

const map: RiskMap = {
  rows: 2, cols: 3, cell_size_m: 50, coordinate_system: 'SCHEMATIC_GRID_NOT_GEOGRAPHIC',
  source_type: 'SIMULATED', depth_threshold_label: 'SIMULATED_OPERATIONAL_DEPTH_THRESHOLD',
  minimum_operational_depth_m: 4.5, cells, hazards: [],
  start: { row: 0, col: 0 }, destination: { row: 0, col: 2 },
  start_name: 'Survey Base', destination_name: 'Harbor Entrance', provenance: {},
}

function route(route_type: string, row: number): RouteData {
  return {
    route_type, coordinates: [{ row: 0, col: 0 }, { row, col: 1 }, { row: 0, col: 2 }],
    distance_m: row ? 141.42 : 100, average_risk: row ? 0.1 : 0.3,
    accumulated_risk: row ? 0.2 : 0.6, minimum_depth_m: 8,
    hazards_approached: [], average_wave_height_m: 0.7, accumulated_wave_exposure_m: 2.1,
    average_directional_current_risk: 0.1, computation_time_ms: 2,
    distance_basis: 'SIMULATED_50_METER_GRID_CELLS',
  }
}

const routes: RouteResult = {
  shortest_route: route('SHORTEST', 0), lower_risk_route: route('LOWER_MODELED_RISK', 1),
  comparison: {
    distance_difference_m: 41.42, average_risk_difference: -0.2,
    hazards_avoided: [], minimum_depth_difference_m: 0,
    explanation: 'Modeled distance increases by 41 m while average modeled risk decreases.',
  },
}

const manualHazard: DemoHazard = {
  id: 'manual-1', row: 0, col: 1, hazard_type: 'SUBMERGED_OBSTRUCTION',
  label: 'Submerged obstruction', severity: 'HIGH', severity_factor: 0.82,
  confidence: 0.95, anomaly_score: null, radius_cells: 5, source_type: 'MANUAL',
  status: 'ACTIVE', created_at: '2026-09-26T12:00:00Z',
}

function mutation(hazard: DemoHazard, routeChanged = true): HazardMutationResult {
  const changedCells = map.cells.map(line => line.map(cell => cell.row === hazard.row && cell.col === hazard.col ? { ...cell, total_risk: hazard.status === 'ACTIVE' ? 0.7 : 0.1 } : cell))
  return {
    hazard,
    impact: {
      risk_recalculated: true, route_recalculated: true, reason: null,
      previous_route_affected: true, route_changed: routeChanged,
      previous_route: { distance_m: 100, average_risk: 0.3, accumulated_risk: 0.6 },
      updated_route: { distance_m: 141.42, average_risk: 0.1, accumulated_risk: 0.2 },
      retained_path_average_risk: 0.4,
      explanation: 'The previous path crossed the hazard influence radius.',
    },
    risk_map: { ...map, cells: changedCells, hazards: [hazard] }, routes: { ...routes, start: map.start, destination: map.destination },
  }
}

describe('demo planner interaction', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('crypto', { randomUUID: () => '11111111-1111-4111-8111-111111111111' })
    vi.mocked(api.riskMap).mockResolvedValue(map)
    vi.mocked(api.latestRoutes).mockRejectedValue(new Error('No route plan'))
    vi.mocked(api.calculateRoutes).mockResolvedValue(routes)
  })
  afterEach(() => { cleanup(); vi.unstubAllGlobals() })

  it('loads the grid, switches a layer, and shows both calculated routes', async () => {
    render(<DemoPlanner missionId={7} />)
    expect(await screen.findByText('Harbor risk map')).toBeTruthy()
    expect(screen.getAllByRole('button', { name: /Grid cell/ })).toHaveLength(6)
    fireEvent.click(screen.getByRole('button', { name: 'bathymetry' }))
    fireEvent.click(screen.getByRole('button', { name: /Calculate routes/ }))
    expect(await screen.findByText('Why this route?')).toBeTruthy()
    expect(screen.getByText('Shortest route')).toBeTruthy()
    expect(screen.getByText('Lower modeled-risk route')).toBeTruthy()
    expect(screen.getByText(routes.comparison.explanation)).toBeTruthy()
    expect(api.calculateRoutes).toHaveBeenCalledWith(7, map.start, map.destination)
  })

  it('adds a manual hazard from a selected cell and displays the computed reroute', async () => {
    vi.mocked(api.createHazard).mockResolvedValue(mutation(manualHazard))
    render(<DemoPlanner missionId={7} />)
    await screen.findByText('Harbor risk map')
    fireEvent.click(screen.getByRole('button', { name: /Calculate routes/ }))
    await screen.findByText('Why this route?')
    fireEvent.click(screen.getByRole('button', { name: 'ADD HAZARD' }))
    expect(screen.getByText('Select a navigable cell on the grid.')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Grid cell 0, 1' }))
    expect(screen.getByText(/Grid Cell: row 0, col 1/)).toBeTruthy()
    fireEvent.change(screen.getByRole('combobox', { name: 'Severity' }), { target: { value: 'HIGH' } })
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Operator-entered certainty (%)' }), { target: { value: '95' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save hazard and update routes' }))
    expect(await screen.findByText(/Previous lower modeled-risk route affected/)).toBeTruthy()
    expect(screen.getByText(/A new lower modeled-risk path has been calculated/)).toBeTruthy()
    expect(screen.getByText(/MANUAL · operator-entered/)).toBeTruthy()
    expect(screen.getByText('Submerged obstruction')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Grid cell 0, 1' }).getAttribute('title')).toContain('risk 0.70')
    expect(api.createHazard).toHaveBeenCalledWith(7, expect.objectContaining({ row: 0, col: 1, hazard_type: 'SUBMERGED_OBSTRUCTION', severity: 'HIGH', confidence: 0.95, source_type: 'MANUAL', client_request_id: '11111111-1111-4111-8111-111111111111' }))
  })

  it('cancels add mode and allows normal endpoint selection', async () => {
    render(<DemoPlanner missionId={7} />)
    await screen.findByText('Harbor risk map')
    fireEvent.click(screen.getByRole('button', { name: 'ADD HAZARD' }))
    fireEvent.click(screen.getByRole('button', { name: 'Grid cell 0, 1' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(screen.queryByRole('button', { name: 'Save hazard and update routes' })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Select start' }))
    fireEvent.click(screen.getByRole('button', { name: 'Grid cell 1, 0' }))
    expect(screen.getByText('Start: 1, 0')).toBeTruthy()
    expect(api.createHazard).not.toHaveBeenCalled()
  })

  it('marks an active hazard resolved and shows the retained record', async () => {
    const withHazard = { ...map, hazards: [manualHazard] }
    vi.mocked(api.riskMap).mockResolvedValue(withHazard)
    vi.mocked(api.resolveHazard).mockResolvedValue(mutation({ ...manualHazard, status: 'RESOLVED' }, false))
    render(<DemoPlanner missionId={7} />)
    await screen.findByText('Submerged obstruction')
    fireEvent.click(screen.getByRole('button', { name: 'Mark Resolved' }))
    await waitFor(() => expect(screen.getByText(/Hazard resolved/)).toBeTruthy())
    expect(screen.getAllByText(/RESOLVED/).length).toBeGreaterThan(0)
    expect(screen.queryByRole('button', { name: 'Mark Resolved' })).toBeNull()
    expect(api.resolveHazard).toHaveBeenCalledWith(7, 'manual-1')
  })

  it('loads a persisted manual hazard and route plan after remount', async () => {
    vi.mocked(api.riskMap).mockResolvedValue({ ...map, hazards: [manualHazard] })
    vi.mocked(api.latestRoutes).mockResolvedValue({ ...routes, start: map.start, destination: map.destination })
    render(<DemoPlanner missionId={7} />)
    expect(await screen.findByText('Submerged obstruction')).toBeTruthy()
    expect(await screen.findByText('Why this route?')).toBeTruthy()
    expect(screen.getByText(/MANUAL · operator-entered/)).toBeTruthy()
  })
})
