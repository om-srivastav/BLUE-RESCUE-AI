import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, errorMessage } from '../services/api'
import type { SonarReplay, SonarResult } from '../types/imagery'

export function SonarPage() {
  const id = Number(useParams().id)
  const [replay, setReplay] = useState<SonarReplay | null>(null)
  const [index, setIndex] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [uploaded, setUploaded] = useState(false)
  const [result, setResult] = useState<SonarResult | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [revision, setRevision] = useState(0)
  useEffect(() => { api.sonarReplay(id).then(setReplay).catch(e => setError(errorMessage(e))) }, [id])
  useEffect(() => { api.sonarStatus(id).then(status => setUploaded(status.uploaded_frame)).catch(e => setError(errorMessage(e))) }, [id])
  useEffect(() => { if (!playing || !replay) return; const timer = window.setInterval(() => setIndex(i => (i + 1) % replay.frames.length), 1100); return () => window.clearInterval(timer) }, [playing, replay])
  const frame = replay?.frames[index]
  async function upload(file?: File) { if (!file) return; setBusy(true); setError(''); try { await api.sonarUpload(id, file); setUploaded(true); setResult(null); setRevision(n => n + 1) } catch (e) { setError(errorMessage(e)) } finally { setBusy(false) } }
  async function analyze() { setBusy(true); setError(''); try { setResult(await api.sonarAnalyze(id)) } catch (e) { setError(errorMessage(e)) } finally { setBusy(false) } }
  return <div className="space-y-6"><Link to={`/missions/${id}`} className="text-aqua">← Mission dashboard</Link><div><p className="text-xs tracking-widest text-aqua">SONAR SURVEY</p><h1 className="text-3xl font-bold">Recorded frame replay</h1><p className="mt-2 text-slate-400">Fictional synthetic frames with bundled annotations. Playback is a replay, not a live feed.</p></div>
    <section className="rounded-xl border border-white/10 bg-panel p-5"><p className="text-xs text-amber-300">SIMULATED DEMO DATA · DEMO ANNOTATIONS</p>{frame && <><div className="relative mx-auto mt-4 max-w-2xl"><img className="w-full rounded" src={frame.image_url} alt={`Synthetic sonar frame ${frame.frame_number}`} />{frame.annotations.map((a, i) => <div key={i} title={`${a.label} · ${a.source_type}`} className="absolute border-2 border-amber-400" style={{ left: `${a.x / frame.width * 100}%`, top: `${a.y / frame.height * 100}%`, width: `${a.width / frame.width * 100}%`, height: `${a.height / frame.height * 100}%` }} />)}</div><p className="mt-3 text-sm">Frame {frame.frame_number} of {replay.frames.length} · {frame.metadata.scenario}</p><p className="text-xs text-slate-400">Annotation: {frame.annotations.map(a => a.label).join(', ')}</p></>}<div className="mt-4 flex gap-2">{['Previous', playing ? 'Pause' : 'Play', 'Next'].map(label => <button key={label} className="rounded bg-white/10 px-4 py-2" onClick={() => label === 'Previous' ? setIndex(i => Math.max(0, i - 1)) : label === 'Next' ? setIndex(i => Math.min((replay?.frames.length || 1) - 1, i + 1)) : setPlaying(p => !p)}>{label}</button>)}</div></section>
    <section className="rounded-xl border border-white/10 bg-panel p-5"><h2 className="font-bold">Analyze an uploaded sonar image</h2><p className="mt-1 text-sm text-slate-400">Heuristic bright-region anomaly detection only. Results do not classify objects.</p><input aria-label="Upload sonar image" className="mt-3 block" type="file" accept="image/png,image/jpeg" onChange={e => upload(e.target.files?.[0])} />{uploaded && <div className="relative mt-4 max-w-lg"><img className="w-full rounded" src={`${api.sonarAsset(id)}?v=${revision}`} alt="Uploaded sonar frame" />{result?.regions.map((r, i) => <div key={i} title={`${r.label} · score ${r.score}`} className="absolute border-2 border-aqua" style={{ left: `${r.x / result.width * 100}%`, top: `${r.y / result.height * 100}%`, width: `${r.width / result.width * 100}%`, height: `${r.height / result.height * 100}%` }} />)}</div>}<button className="mt-4 rounded bg-aqua px-5 py-2 font-bold text-navy disabled:opacity-40" disabled={!uploaded || busy} onClick={analyze}>Run heuristic analysis</button>{result && <div className="mt-4"><p>{result.anomaly_count} unknown anomaly regions · {result.detector.replaceAll('_', ' ')}</p><p className="text-sm text-slate-400">Highest heuristic score: {result.anomaly_score.toFixed(2)} (not a probability)</p><ul>{result.regions.map((r, i) => <li key={i} className="text-sm text-slate-300">Region {i + 1}: x {r.x}, y {r.y}, {r.width} × {r.height} px · score {r.score}</li>)}</ul></div>}</section>{error && <p role="alert" className="text-red-300">{error}</p>}
  </div>
}
