import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, errorMessage } from '../services/api'
import type { SatelliteResult, SatelliteStatus } from '../types/imagery'

export function SatellitePage() {
  const id = Number(useParams().id)
  const [status, setStatus] = useState<SatelliteStatus | null>(null)
  const [source, setSource] = useState<'demo' | 'uploaded'>('demo')
  const [result, setResult] = useState<SatelliteResult | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [revision, setRevision] = useState(0)
  useEffect(() => { api.satelliteStatus(id).then(setStatus).catch(e => setError(errorMessage(e))) }, [id, revision])
  async function upload(role: 'before' | 'after', file?: File) {
    if (!file) return
    setError(''); setBusy(true)
    try { await api.satelliteUpload(id, role, file); setSource('uploaded'); setResult(null); setRevision(n => n + 1) }
    catch (e) { setError(errorMessage(e)) }
    finally { setBusy(false) }
  }
  async function analyze() {
    setError(''); setBusy(true)
    try { setResult(await api.satelliteAnalyze(id, source)) }
    catch (e) { setError(errorMessage(e)) }
    finally { setBusy(false) }
  }
  return <div className="space-y-6">
    <Link to={`/missions/${id}`} className="text-aqua">← Mission dashboard</Link>
    <div><p className="text-xs tracking-widest text-aqua">SATELLITE ANALYSIS</p><h1 className="text-3xl font-bold">Before / after change detection</h1><p className="mt-2 text-slate-400">Offline image comparison. Changes are visual differences, not identified objects or verified damage.</p></div>
    <div className="rounded-xl border border-white/10 bg-panel p-5"><p className="text-sm font-semibold">Image source</p><div className="mt-3 flex gap-4"><label><input type="radio" checked={source === 'demo'} onChange={() => { setSource('demo'); setResult(null) }} /> Bundled demo</label><label><input type="radio" checked={source === 'uploaded'} onChange={() => { setSource('uploaded'); setResult(null) }} /> My uploads</label></div><p className="mt-2 text-xs text-amber-300">{source === 'demo' ? 'SIMULATED DEMO DATA' : 'USER UPLOAD'} · CLASSICAL CV BASELINE</p></div>
    <div className="grid gap-4 md:grid-cols-2">{(['before', 'after'] as const).map(role => <div key={role} className="rounded-xl border border-white/10 bg-panel p-4"><h2 className="mb-3 font-bold capitalize">{role}</h2>{(source === 'demo' ? status?.demo_available : role === 'before' ? status?.uploaded_before : status?.uploaded_after) ? <img className="w-full rounded object-contain" src={`${api.satelliteAsset(id, source, role)}?v=${revision}`} alt={`${role} satellite sample`} /> : <div className="flex h-40 items-center justify-center bg-navy text-slate-400">No {role} image</div>}<label className="mt-3 block text-sm">Upload {role} PNG/JPEG <input aria-label={`Upload ${role}`} className="mt-2 block w-full" type="file" accept="image/png,image/jpeg" onChange={e => upload(role, e.target.files?.[0])} /></label></div>)}</div>
    <button className="rounded-lg bg-aqua px-5 py-3 font-bold text-navy disabled:opacity-40" disabled={busy || (source === 'uploaded' && !(status?.uploaded_before && status?.uploaded_after))} onClick={analyze}>{busy ? 'Working…' : 'Run Analysis'}</button>
    {error && <p role="alert" className="text-red-300">{error}</p>}
    {result && <section className="rounded-xl border border-aqua/20 bg-panel p-5"><h2 className="text-xl font-bold">Change result</h2><p className="mt-2 text-sm text-amber-300">{result.source_type} · {result.detector.replaceAll('_', ' ')}</p><div className="mt-4 grid gap-4 md:grid-cols-2"><div><p className="text-2xl font-bold">{result.percent_changed}%</p><p className="text-sm text-slate-400">Pixels changed ({result.changed_pixels.toLocaleString()})</p><p className="mt-2 text-sm">{result.regions.length} change regions</p></div><img src={result.mask_data_url} alt="Binary change mask" className="w-full rounded" /></div><ul className="mt-4 space-y-1 text-sm">{result.regions.map((r, i) => <li key={i}>Region {i + 1}: x {r.x}, y {r.y}, {r.width} × {r.height} px</li>)}</ul></section>}
  </div>
}
