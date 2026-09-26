import type { SystemStatus } from '../../types/report'

const labels = [
  ['satellite', 'Satellite'], ['sonar', 'Sonar'], ['bathymetry', 'Bathymetry'],
  ['ocean', 'Ocean'], ['routing', 'Routing'], ['external_providers', 'External providers'],
] as const

export function DataSourcesPanel({ status }: { status: SystemStatus }) {
  return <section className="rounded-xl border border-white/10 bg-panel p-6" aria-label="Data sources and system status">
    <h2 className="text-lg font-bold">Data sources / system status</h2>
    <p className="mt-1 text-sm text-slate-400">Sources and methods currently available to this mission.</p>
    <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{labels.map(([key, label]) => {
      const item = status[key]
      return <div key={key} className="rounded-lg border border-white/10 bg-navy/60 p-4"><div className="flex items-center justify-between gap-2"><h3 className="font-semibold">{label}</h3><span className={`text-xs font-semibold ${item.status === 'AVAILABLE' ? 'text-aqua' : 'text-amber-300'}`}>{item.status.replaceAll('_', ' ')}</span></div><p className="mt-2 text-xs text-slate-300">Source: {item.source.replaceAll('_', ' ')}</p><p className="text-xs text-slate-400">Provider: {item.provider}</p>{item.method && <p className="text-xs text-slate-400">Method: {item.method.replaceAll('_', ' ')}</p>}{item.model_status && <p className="text-xs text-amber-300">ML model: {item.model_status.replaceAll('_', ' ')}</p>}</div>
    })}</div>
  </section>
}
