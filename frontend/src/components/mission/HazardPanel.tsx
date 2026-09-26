import { FormEvent, useState } from 'react'
import { Badge } from '../common/Badge'
import type { DemoHazard, GridPoint, HazardCreateInput } from '../../types/routing'

const TYPES = [
  ['WRECKAGE', 'Possible wreckage'], ['DEBRIS', 'Marine debris'],
  ['SUBMERGED_OBSTRUCTION', 'Submerged obstruction'],
  ['KNOWN_INFRASTRUCTURE', 'Known infrastructure'],
  ['UNKNOWN_ANOMALY', 'Unknown anomaly'], ['OTHER', 'Other'],
] as const

export function HazardPanel({ hazards, picking, location, busy, highlightedId, onStart, onCancel, onSave, onResolve, onHighlight }: {
  hazards: DemoHazard[]
  picking: boolean
  location: GridPoint | null
  busy: boolean
  highlightedId: string | null
  onStart: () => void
  onCancel: () => void
  onSave: (payload: Omit<HazardCreateInput, 'row' | 'col' | 'client_request_id'>) => Promise<void>
  onResolve: (id: string) => Promise<void>
  onHighlight: (id: string) => void
}) {
  const [hazardType, setHazardType] = useState('SUBMERGED_OBSTRUCTION')
  const [severity, setSeverity] = useState('MEDIUM')
  const [confidencePercent, setConfidencePercent] = useState(80)
  const [notes, setNotes] = useState('')
  const active = hazards.filter(h => h.status === 'ACTIVE')
  const resolved = hazards.filter(h => h.status === 'RESOLVED')

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!location || busy) return
    await onSave({ hazard_type: hazardType, severity, confidence: confidencePercent / 100, notes, source_type: 'MANUAL' })
  }

  function card(hazard: DemoHazard) {
    const color = hazard.status === 'RESOLVED' ? 'text-slate-400' : hazard.severity === 'CRITICAL' ? 'text-red-300' : hazard.severity === 'HIGH' ? 'text-orange-300' : hazard.severity === 'MEDIUM' ? 'text-amber-300' : 'text-aqua'
    return <li key={hazard.id} className={`rounded-lg border p-3 text-xs ${highlightedId === hazard.id ? 'border-aqua' : 'border-white/10'} ${hazard.status === 'RESOLVED' ? 'opacity-70' : ''}`}>
      <button type="button" onClick={() => onHighlight(hazard.id)} className="w-full text-left"><span className={`font-bold ${color}`}>{hazard.label}</span><span className="ml-2 text-slate-400">{hazard.severity}</span><span className="mt-1 block text-slate-300">Cell {hazard.row}, {hazard.col} · operator certainty {(hazard.confidence * 100).toFixed(0)}%</span><span className="mt-1 block text-slate-400">{hazard.source_type === 'MANUAL' ? 'MANUAL · operator-entered' : 'DEMO annotation'} · {hazard.status}</span></button>
      {hazard.status === 'ACTIVE' && <button type="button" disabled={busy} onClick={() => onResolve(hazard.id)} className="mt-2 text-aqua underline disabled:opacity-50">Mark Resolved</button>}
    </li>
  }

  return <div className="rounded-xl border border-white/10 bg-panel p-5">
    <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-bold">Hazards</h3><button type="button" disabled={busy} onClick={onStart} className="rounded-lg bg-rose-400 px-3 py-2 text-xs font-bold text-navy disabled:opacity-50">ADD HAZARD</button></div>
    {picking && <div className="mt-4 rounded-lg border border-rose-400/40 bg-rose-400/10 p-3 text-sm"><p className="font-semibold text-rose-200">Adding manual hazard</p>{location ? <p className="mt-1 text-xs text-slate-200">Grid Cell: row {location.row}, col {location.col} · SIMULATED GRID LOCATION</p> : <p className="mt-1 text-xs text-slate-200">Select a navigable cell on the grid.</p>}<button type="button" onClick={onCancel} className="mt-2 text-xs text-aqua underline">Cancel</button></div>}
    {picking && location && <form onSubmit={submit} className="mt-4 space-y-3 text-sm">
      <label className="block">Hazard type<select aria-label="Hazard type" value={hazardType} onChange={e => setHazardType(e.target.value)} className="mt-1 w-full rounded-lg border border-white/20 bg-navy p-2">{TYPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label className="block">Severity<select aria-label="Severity" value={severity} onChange={e => setSeverity(e.target.value)} className="mt-1 w-full rounded-lg border border-white/20 bg-navy p-2">{['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(value => <option key={value}>{value}</option>)}</select></label>
      <label className="block">Operator-entered certainty (%)<input aria-label="Operator-entered certainty (%)" type="number" min="0" max="100" step="1" required value={confidencePercent} onChange={e => setConfidencePercent(Number(e.target.value))} className="mt-1 w-full rounded-lg border border-white/20 bg-navy p-2" /></label>
      <label className="block">Notes (optional)<textarea aria-label="Notes" maxLength={1000} value={notes} onChange={e => setNotes(e.target.value)} className="mt-1 w-full rounded-lg border border-white/20 bg-navy p-2" /></label>
      <p className="text-xs text-slate-400">Manual certainty is an operator estimate, not ML confidence.</p>
      <button type="submit" disabled={busy} className="w-full rounded-lg bg-aqua px-4 py-2 font-bold text-navy disabled:opacity-50">{busy ? 'Saving…' : 'Save hazard and update routes'}</button>
    </form>}
    <div className="mt-5 flex items-center gap-2"><Badge tone="amber">{active.length} ACTIVE</Badge><span className="text-xs text-slate-400">Seeded and manual records</span></div>
    <ul className="mt-3 max-h-72 space-y-2 overflow-y-auto">{active.map(card)}</ul>
    {resolved.length > 0 && <><h4 className="mt-5 text-xs font-semibold uppercase tracking-wider text-slate-400">Resolved · retained for review</h4><ul className="mt-2 space-y-2">{resolved.map(card)}</ul></>}
  </div>
}
