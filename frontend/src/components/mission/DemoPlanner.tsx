import { useEffect, useState } from 'react'
import { RefreshCw, Route as RouteIcon } from 'lucide-react'
import { Badge } from '../common/Badge'
import { ErrorState, Loading } from '../common/State'
import { HazardPanel } from './HazardPanel'
import { api, errorMessage } from '../../services/api'
import type { GridPoint, HazardCreateInput, HazardImpact, HazardMutationResult, RiskCell, RiskMap, RouteData, RouteResult } from '../../types/routing'

type BaseLayer = 'risk' | 'bathymetry' | 'waves'
type PickMode = 'IDLE' | 'SELECT_START' | 'SELECT_DESTINATION' | 'ADD_HAZARD'

function markerColor(severity: string, status: string): string {
  if (status === 'RESOLVED') return '#94a3b8'
  return severity === 'CRITICAL' ? '#ef4444' : severity === 'HIGH' ? '#fb7185' : severity === 'MEDIUM' ? '#fbbf24' : '#43d8d1'
}

function impactMessage(impact: HazardImpact, resolved: boolean): string {
  const action = resolved ? 'Hazard resolved.' : 'New hazard added.'
  if (!impact.route_recalculated) return `${action} Risk map updated. No active route plan was available to recalculate.`
  const overlap = impact.previous_route_affected ? 'Previous lower modeled-risk route affected.' : 'Previous route not materially affected.'
  const geometry = impact.route_changed ? 'A new lower modeled-risk path has been calculated.' : 'Route recalculated; path unchanged.'
  return `${action} Risk map updated. ${overlap} ${geometry}`
}

function cellColor(cell: RiskCell, layer: BaseLayer): string {
  if (!cell.navigable) return '#263440'
  if (layer === 'bathymetry') {
    const intensity = Math.max(0, Math.min(1, (cell.depth_m - 4.5) / 6))
    return `hsl(${192 + 18 * intensity} 62% ${22 + 23 * intensity}%)`
  }
  if (layer === 'waves') {
    const intensity = Math.max(0, Math.min(1, cell.wave_height_m / 2))
    return `hsl(${195 - 165 * intensity} 72% ${24 + 18 * intensity}%)`
  }
  const risk = cell.total_risk
  return `hsl(${170 - 155 * Math.min(1, risk / 0.65)} 75% ${23 + 17 * Math.min(1, risk / 0.65)}%)`
}

function polyline(route?: RouteData): string {
  return route?.coordinates.map(point => `${point.col + 0.5},${point.row + 0.5}`).join(' ') ?? ''
}

function MetricCard({ title, route, tone }: { title: string; route: RouteData; tone: 'amber' | 'aqua' }) {
  return <div className={`rounded-xl border bg-panel p-5 ${tone === 'amber' ? 'border-amber-400/40' : 'border-aqua/40'}`}>
    <h3 className={`font-bold ${tone === 'amber' ? 'text-amber-300' : 'text-aqua'}`}>{title}</h3>
    <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
      <div><dt className="text-slate-400">Modeled distance</dt><dd className="font-semibold">{(route.distance_m / 1000).toFixed(2)} km</dd></div>
      <div><dt className="text-slate-400">Average risk</dt><dd className="font-semibold">{route.average_risk.toFixed(3)}</dd></div>
      <div><dt className="text-slate-400">Accumulated risk</dt><dd className="font-semibold">{route.accumulated_risk.toFixed(2)}</dd></div>
      <div><dt className="text-slate-400">Minimum depth</dt><dd className="font-semibold">{route.minimum_depth_m.toFixed(1)} m</dd></div>
      <div><dt className="text-slate-400">Hazards approached</dt><dd className="font-semibold">{route.hazards_approached.length}</dd></div>
      <div><dt className="text-slate-400">Mean wave height</dt><dd className="font-semibold">{route.average_wave_height_m.toFixed(2)} m</dd></div>
      <div><dt className="text-slate-400">Accumulated wave exposure</dt><dd className="font-semibold">{route.accumulated_wave_exposure_m.toFixed(1)} m</dd></div>
      <div><dt className="text-slate-400">Mean current penalty</dt><dd className="font-semibold">{route.average_directional_current_risk.toFixed(3)}</dd></div>
    </dl>
    {route.hazards_approached.length > 0 && <p className="mt-3 text-xs text-slate-400">Within fictional hazard radius: {route.hazards_approached.join(', ')}</p>}
  </div>
}

export function DemoPlanner({ missionId }: { missionId: number }) {
  const [map, setMap] = useState<RiskMap | null>(null)
  const [routes, setRoutes] = useState<RouteResult | null>(null)
  const [start, setStart] = useState<GridPoint | null>(null)
  const [destination, setDestination] = useState<GridPoint | null>(null)
  const [pick, setPick] = useState<PickMode>('IDLE')
  const [hazardLocation, setHazardLocation] = useState<GridPoint | null>(null)
  const [hazardRequestId, setHazardRequestId] = useState<string | null>(null)
  const [highlightedHazardId, setHighlightedHazardId] = useState<string | null>(null)
  const [notification, setNotification] = useState('')
  const [impact, setImpact] = useState<HazardImpact | null>(null)
  const [previousPath, setPreviousPath] = useState<RouteData | null>(null)
  const [layer, setLayer] = useState<BaseLayer>('risk')
  const [showHazards, setShowHazards] = useState(true)
  const [showCurrents, setShowCurrents] = useState(false)
  const [showRoutes, setShowRoutes] = useState(true)
  const [selected, setSelected] = useState<RiskCell | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let cancelled = false
    api.riskMap(missionId).then(async value => {
      if (cancelled) return
      setMap(value); setStart(value.start); setDestination(value.destination)
      try {
        const latest = await api.latestRoutes(missionId)
        if (!cancelled) { setRoutes(latest); if (latest.start) setStart(latest.start); if (latest.destination) setDestination(latest.destination) }
      } catch { /* No route plan has been calculated yet. */ }
    }).catch(e => { if (!cancelled) setError(errorMessage(e)) })
    return () => { cancelled = true }
  }, [missionId])

  function chooseCell(cell: RiskCell) {
    setSelected(cell)
    if (pick === 'IDLE' || !cell.navigable) return
    if (pick === 'ADD_HAZARD') { setHazardLocation({ row: cell.row, col: cell.col }); return }
    if (pick === 'SELECT_START') setStart({ row: cell.row, col: cell.col })
    else setDestination({ row: cell.row, col: cell.col })
    setRoutes(null)
    setPreviousPath(null)
    setPick('IDLE')
  }

  async function calculate() {
    if (!start || !destination) return
    setBusy(true); setError('')
    try { setRoutes(await api.calculateRoutes(missionId, start, destination)); setPreviousPath(null); setNotification(''); setImpact(null) }
    catch (e) { setError(errorMessage(e)) }
    finally { setBusy(false) }
  }

  async function refresh() {
    setBusy(true); setError('')
    try { setMap(await api.recalculateRiskMap(missionId)); setRoutes(await api.latestRoutes(missionId).catch(() => null)); setPreviousPath(null) }
    catch (e) { setError(errorMessage(e)) }
    finally { setBusy(false) }
  }

  function startAddingHazard() {
    setPick('ADD_HAZARD')
    setHazardLocation(null)
    setHazardRequestId(crypto.randomUUID())
    setNotification('')
    setError('')
  }

  function cancelHazard() {
    setPick('IDLE')
    setHazardLocation(null)
    setHazardRequestId(null)
  }

  function applyMutation(result: HazardMutationResult, resolved: boolean) {
    if (result.impact.route_changed && routes) setPreviousPath(routes.lower_risk_route)
    else setPreviousPath(null)
    setMap(result.risk_map)
    setRoutes(result.routes)
    if (result.routes) {
      if (result.routes.start) setStart(result.routes.start)
      if (result.routes.destination) setDestination(result.routes.destination)
    }
    setSelected(current => current ? result.risk_map.cells[current.row][current.col] : null)
    setImpact(result.impact)
    setNotification(impactMessage(result.impact, resolved))
    setHighlightedHazardId(result.hazard.id)
    cancelHazard()
  }

  async function saveHazard(details: Omit<HazardCreateInput, 'row' | 'col' | 'client_request_id'>) {
    if (!hazardLocation || !hazardRequestId) return
    setBusy(true); setError('')
    try { applyMutation(await api.createHazard(missionId, { ...hazardLocation, ...details, client_request_id: hazardRequestId }), false) }
    catch (e) { setError(errorMessage(e)) }
    finally { setBusy(false) }
  }

  async function resolveHazard(id: string) {
    setBusy(true); setError('')
    try { applyMutation(await api.resolveHazard(missionId, id), true) }
    catch (e) { setError(errorMessage(e)) }
    finally { setBusy(false) }
  }

  if (error && !map) return <ErrorState message={error} />
  if (!map) return <Loading label="Loading simulated risk grid…" />

  return <section className="mt-8" id="demo-planner">
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-widest text-aqua">Demo geographic / risk / routing core</p><h2 className="mt-1 text-2xl font-bold">Harbor risk map</h2></div><button onClick={refresh} disabled={busy} className="inline-flex items-center gap-2 rounded-lg border border-white/20 px-4 py-2 text-sm hover:bg-white/5 disabled:opacity-50"><RefreshCw size={16} /> Recalculate grid</button></div>
    <div className="mb-5 flex flex-wrap gap-2"><Badge tone="amber">SIMULATED DEMONSTRATION MISSION</Badge><Badge tone="slate">SCHEMATIC GRID — NO GPS COORDINATES</Badge><Badge tone="slate">50 m modeled cells</Badge></div>
    {notification && <div role="status" className="mb-5 rounded-xl border border-aqua/40 bg-aqua/10 p-4 text-sm text-aqua"><p className="font-semibold">{notification}</p>{impact && <p className="mt-2 text-xs leading-5 text-slate-200">{impact.explanation}</p>}{impact?.previous_route && impact.updated_route && <p className="mt-2 text-xs text-slate-200">Previous: {impact.previous_route.distance_m.toFixed(0)} m, risk {impact.previous_route.average_risk.toFixed(3)} → Updated: {impact.updated_route.distance_m.toFixed(0)} m, risk {impact.updated_route.average_risk.toFixed(3)}</p>}</div>}
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_300px]">
      <div className="min-w-0 rounded-xl border border-white/10 bg-panel p-4">
        <div className="mb-4 flex flex-wrap items-center gap-2 text-xs">{(['risk', 'bathymetry', 'waves'] as BaseLayer[]).map(value => <button key={value} onClick={() => setLayer(value)} className={`rounded-lg px-3 py-2 capitalize ${layer === value ? 'bg-aqua text-navy' : 'bg-white/10 text-slate-300'}`}>{value}</button>)}<label className="ml-2 flex items-center gap-1"><input type="checkbox" checked={showCurrents} onChange={e => setShowCurrents(e.target.checked)} /> Currents</label><label className="ml-2 flex items-center gap-1"><input type="checkbox" checked={showHazards} onChange={e => setShowHazards(e.target.checked)} /> Hazards</label><label className="ml-2 flex items-center gap-1"><input type="checkbox" checked={showRoutes} onChange={e => setShowRoutes(e.target.checked)} /> Routes</label></div>
        <div className="overflow-x-auto"><div className="relative" style={{ width: map.cols * 20, height: map.rows * 20 }}>
          <div className="grid" style={{ gridTemplateColumns: `repeat(${map.cols}, 20px)` }}>{map.cells.flat().map(cell => <button key={`${cell.row}-${cell.col}`} onClick={() => chooseCell(cell)} title={`Cell ${cell.row},${cell.col} · risk ${cell.total_risk.toFixed(2)} · depth ${cell.depth_m} m · waves ${cell.wave_height_m} m${cell.navigable ? '' : ' · blocked'}`} aria-label={`Grid cell ${cell.row}, ${cell.col}`} className={`h-5 w-5 border border-[#071524]/30 hover:outline hover:outline-1 hover:outline-white ${hazardLocation?.row === cell.row && hazardLocation.col === cell.col ? 'outline outline-2 outline-rose-300' : ''}`} style={{ backgroundColor: cellColor(cell, layer) }} />)}</div>
          <svg className="pointer-events-none absolute inset-0" width={map.cols * 20} height={map.rows * 20} viewBox={`0 0 ${map.cols} ${map.rows}`} aria-hidden="true">
            {showRoutes && previousPath && <polyline points={polyline(previousPath)} fill="none" stroke="#cbd5e1" strokeWidth="0.15" strokeDasharray="0.25 0.18" opacity="0.7" />}
            {showRoutes && routes && <><polyline points={polyline(routes.shortest_route)} fill="none" stroke="#fbbf24" strokeWidth="0.28" strokeLinejoin="round" strokeLinecap="round" opacity="0.85" /><polyline points={polyline(routes.lower_risk_route)} fill="none" stroke="#42e6e0" strokeWidth="0.18" strokeLinejoin="round" strokeLinecap="round" /></>}
            {showCurrents && map.cells.flat().filter(cell => cell.row % 4 === 2 && cell.col % 4 === 2).map(cell => { const magnitude = Math.hypot(cell.u_current_mps, cell.v_current_mps); const scale = magnitude ? 0.35 / magnitude : 0; return <line key={`current-${cell.row}-${cell.col}`} x1={cell.col + 0.5} y1={cell.row + 0.5} x2={cell.col + 0.5 + cell.u_current_mps * scale} y2={cell.row + 0.5 - cell.v_current_mps * scale} stroke="white" strokeWidth="0.08" markerEnd="url(#arrow)" /> })}
            <defs><marker id="arrow" markerWidth="4" markerHeight="4" refX="3" refY="2" orient="auto"><path d="M0 0 L4 2 L0 4 Z" fill="white" /></marker></defs>
            {showHazards && map.hazards.map(hazard => <g key={hazard.id}><title>{hazard.label} · {hazard.severity} · {Math.round(hazard.confidence * 100)}% · {hazard.source_type} · {hazard.status}</title><circle cx={hazard.col + 0.5} cy={hazard.row + 0.5} r={highlightedHazardId === hazard.id ? '0.45' : '0.34'} fill={markerColor(hazard.severity, hazard.status)} stroke="#fff" strokeWidth={highlightedHazardId === hazard.id ? '0.13' : '0.08'} /><text x={hazard.col + 0.5} y={hazard.row + 0.68} fontSize="0.48" textAnchor="middle" fill="#071524">{hazard.status === 'ACTIVE' ? '!' : '×'}</text></g>)}
            {start && <circle cx={start.col + 0.5} cy={start.row + 0.5} r="0.38" fill="#86efac" stroke="#071524" strokeWidth="0.1" />}
            {destination && <circle cx={destination.col + 0.5} cy={destination.row + 0.5} r="0.38" fill="#c4b5fd" stroke="#071524" strokeWidth="0.1" />}
            {hazardLocation && <circle cx={hazardLocation.col + 0.5} cy={hazardLocation.row + 0.5} r="0.46" fill="none" stroke="#fff" strokeWidth="0.12" />}
          </svg>
        </div></div>
        <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-300"><span>■ Risk: 0–0.30 lower, 0.31–0.60 moderate, 0.61–1 high</span><span>■ Gray: below simulated depth threshold</span><span className="text-amber-300">━ Shortest</span><span className="text-aqua">━ Lower modeled-risk</span>{previousPath && <span>┄ Previous path</span>}</div>
      </div>
      <div className="space-y-4"><div className="rounded-xl border border-white/10 bg-panel p-5"><h3 className="font-bold">Route planner</h3><p className="mt-2 text-xs text-slate-400">Select an endpoint, then click a navigable grid cell. Defaults are Survey Base and Harbor Entrance.</p><div className="mt-5 space-y-3 text-sm"><div className="flex items-center justify-between gap-2"><span>{start?.row === map.start.row && start.col === map.start.col ? map.start_name : 'Start'}: {start ? `${start.row}, ${start.col}` : '—'}</span><button disabled={busy} onClick={() => { setPick('SELECT_START'); setHazardLocation(null) }} className={`rounded px-2 py-1 ${pick === 'SELECT_START' ? 'bg-aqua text-navy' : 'bg-white/10'}`}>Select start</button></div><div className="flex items-center justify-between gap-2"><span>{destination?.row === map.destination.row && destination.col === map.destination.col ? map.destination_name : 'Destination'}: {destination ? `${destination.row}, ${destination.col}` : '—'}</span><button disabled={busy} onClick={() => { setPick('SELECT_DESTINATION'); setHazardLocation(null) }} className={`rounded px-2 py-1 ${pick === 'SELECT_DESTINATION' ? 'bg-aqua text-navy' : 'bg-white/10'}`}>Select destination</button></div></div>{(pick === 'SELECT_START' || pick === 'SELECT_DESTINATION') && <p className="mt-3 text-xs text-aqua">Click a navigable cell for {pick === 'SELECT_START' ? 'start' : 'destination'}.</p>}<button disabled={busy || !start || !destination} onClick={calculate} className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg bg-aqua px-4 py-3 font-bold text-navy disabled:opacity-50"><RouteIcon size={17} /> {busy ? 'Calculating…' : 'Calculate routes'}</button></div>
        <div className="rounded-xl border border-white/10 bg-panel p-5"><h3 className="font-bold">Selected cell</h3>{selected ? <dl className="mt-3 space-y-1 text-sm text-slate-300"><div>Grid position: {selected.row}, {selected.col}</div><div>Modeled depth: {selected.depth_m} m</div><div>Wave height: {selected.wave_height_m} m</div><div>Current: u {selected.u_current_mps}, v {selected.v_current_mps} m/s</div><div>Risk: {selected.total_risk.toFixed(3)}</div><div>{selected.navigable ? 'Navigable under simulated threshold' : 'Blocked under simulated threshold'}</div></dl> : <p className="mt-2 text-sm text-slate-400">Click a cell to inspect its values.</p>}</div>
        <HazardPanel hazards={map.hazards} picking={pick === 'ADD_HAZARD'} location={hazardLocation} busy={busy} highlightedId={highlightedHazardId} onStart={startAddingHazard} onCancel={cancelHazard} onSave={saveHazard} onResolve={resolveHazard} onHighlight={setHighlightedHazardId} />
      </div>
    </div>
    {error && <div className="mt-4"><ErrorState message={error} /></div>}
    {routes && <div className="mt-6"><div className="grid gap-4 md:grid-cols-2"><MetricCard title="Shortest route" route={routes.shortest_route} tone="amber" /><MetricCard title="Lower modeled-risk route" route={routes.lower_risk_route} tone="aqua" /></div><div className="mt-4 rounded-xl border border-aqua/30 bg-panel p-6"><h3 className="font-bold">Why this route?</h3><p className="mt-2 text-sm leading-6 text-slate-300">{routes.comparison.explanation}</p><div className="mt-4 flex flex-wrap gap-4 text-sm text-slate-400"><span>Distance difference: {routes.comparison.distance_difference_m.toFixed(0)} m</span><span>Average risk difference: {routes.comparison.average_risk_difference.toFixed(3)}</span><span>Minimum depth difference: {routes.comparison.minimum_depth_difference_m.toFixed(1)} m</span><span>Hazards avoided: {routes.comparison.hazards_avoided.join(', ') || 'none'}</span></div></div></div>}
    <p className="mt-5 text-xs leading-5 text-slate-400">Bathymetry, waves, currents, hazards and distances are bundled simulated values. Current arrows show sampled u/v vectors (east/north). The operational depth threshold is a simulated academic parameter, not a vessel draft. This is simplified academic routing logic, not a vessel hydrodynamics model.</p>
  </section>
}
