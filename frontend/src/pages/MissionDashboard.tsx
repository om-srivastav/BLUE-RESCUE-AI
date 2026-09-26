import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Database, Radar, Satellite } from 'lucide-react'
import { Badge } from '../components/common/Badge'
import { ErrorState, Loading } from '../components/common/State'
import { api, errorMessage } from '../services/api'
import type { Mission } from '../types/mission'
import { DemoPlanner } from '../components/mission/DemoPlanner'
import { DataSourcesPanel } from '../components/mission/DataSourcesPanel'
import type { SystemStatus } from '../types/report'

const modules = [
  { title: 'Satellite analysis', icon: Satellite, detail: 'Before/after imagery and change regions', path: 'satellite' },
  { title: 'Sonar survey', icon: Radar, detail: 'Recorded frame replay and annotations', path: 'sonar' },
]

export function MissionDashboard() {
  const { id } = useParams()
  const [mission, setMission] = useState<Mission | null>(null)
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [statusError, setStatusError] = useState('')
  const [error, setError] = useState('')
  useEffect(() => { api.mission(Number(id)).then(setMission).catch(e => setError(errorMessage(e))) }, [id])
  useEffect(() => { api.systemStatus(Number(id)).then(setSystemStatus).catch(e => setStatusError(errorMessage(e))) }, [id])
  if (error) return <ErrorState message={error} />
  if (!mission) return <Loading label="Loading mission…" />
  return <div>
    <Link to="/missions" className="inline-flex items-center gap-2 text-sm text-aqua hover:underline"><ArrowLeft size={16} /> All missions</Link>
    <div className="mt-6 rounded-2xl border border-aqua/20 bg-panel p-8"><div className="flex flex-wrap items-start justify-between gap-6"><div><p className="text-sm uppercase tracking-widest text-aqua">Mission dashboard</p><h1 className="mt-2 text-3xl font-bold">{mission.name}</h1><p className="mt-3 max-w-2xl text-slate-300">{mission.description}</p></div><Badge tone="slate">{mission.status}</Badge></div><div className="mt-6 flex flex-wrap gap-2"><Badge>{mission.mode.replaceAll('_', ' ')}</Badge><Badge tone="amber">{mission.source_type === 'SIMULATED' ? 'SIMULATED DEMONSTRATION MISSION' : mission.source_type}</Badge></div></div>
    {mission.name === 'Mission Cyclone Varuna' && mission.mode === 'DEMO' && mission.source_type === 'SIMULATED' && <DemoPlanner missionId={mission.id} />}
    <div className="mt-8 grid gap-4 md:grid-cols-2">{modules.map(({ title, icon: Icon, detail, path }) => <Link to={`/missions/${mission.id}/${path}`} key={title} className="rounded-xl border border-white/10 bg-panel p-6 hover:border-aqua/40"><Icon className="text-aqua" size={26} /><h2 className="mt-4 text-lg font-bold">{title}</h2><p className="mt-1 text-sm text-slate-400">{detail}</p><p className="mt-5 text-xs text-aqua">Open module →</p></Link>)}</div>
    <section className="mt-8 rounded-xl border border-white/10 bg-panel p-6"><div className="flex items-center gap-2"><Database size={20} className="text-aqua" /><h2 className="font-bold">Data provenance</h2></div><p className="mt-3 text-sm text-slate-300">Mission metadata source: <strong>{mission.source_type}</strong>. {mission.source_type === 'SIMULATED' ? 'Cyclone Varuna is fictional. Its grid, hazards, routes, satellite images, and sonar replay are bundled simulated demonstration data.' : 'No external datasets have been connected to this mission.'}</p><p className="mt-3 text-sm text-slate-400">Areas of interest: {mission.aois.length}.</p></section>
    <div className="mt-8">{systemStatus ? <DataSourcesPanel status={systemStatus} /> : statusError ? <ErrorState message={statusError} /> : <Loading label="Loading data source status…" />}</div>
  </div>
}
