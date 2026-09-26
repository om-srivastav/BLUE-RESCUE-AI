import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Plus } from 'lucide-react'
import { Badge } from '../components/common/Badge'
import { ErrorState, Loading } from '../components/common/State'
import { api, errorMessage } from '../services/api'
import type { Mission, MissionMode } from '../types/mission'

export function MissionsPage() {
  const [missions, setMissions] = useState<Mission[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [mode, setMode] = useState<MissionMode>('DEMO')
  const [saving, setSaving] = useState(false)

  useEffect(() => { api.missions().then(setMissions).catch(e => setError(errorMessage(e))).finally(() => setLoading(false)) }, [])

  async function create(event: FormEvent) {
    event.preventDefault()
    setError('')
    setSaving(true)
    try {
      const mission = await api.createMission({ name: name.trim(), description, mode })
      setMissions(current => [mission, ...current])
      setName('')
      setDescription('')
    } catch (e) { setError(errorMessage(e)) }
    finally { setSaving(false) }
  }

  return <div>
    <div className="mb-8"><p className="text-sm font-semibold uppercase tracking-widest text-aqua">Mission registry</p><h1 className="mt-2 text-3xl font-bold">Missions</h1><p className="mt-2 text-slate-400">Create a mission or open the bundled fictional scenario.</p></div>
    <div className="grid gap-8 xl:grid-cols-[1fr_340px]">
      <section><h2 className="mb-4 text-lg font-semibold">Available missions</h2>{loading ? <Loading /> : error && missions.length === 0 ? <ErrorState message={error} /> : <div className="space-y-4">{missions.map(mission => <Link key={mission.id} to={`/missions/${mission.id}`} className="block rounded-xl border border-white/10 bg-panel p-6 transition hover:border-aqua/50"><div className="flex flex-wrap items-center justify-between gap-3"><h3 className="text-lg font-bold">{mission.name}</h3><ArrowRight className="text-aqua" size={18} /></div><p className="mt-2 text-sm text-slate-400">{mission.description || 'No description provided.'}</p><div className="mt-4 flex flex-wrap gap-2"><Badge>{mission.mode.replaceAll('_', ' ')}</Badge><Badge tone="amber">{mission.source_type === 'SIMULATED' ? 'SIMULATED DEMONSTRATION MISSION' : mission.source_type}</Badge><Badge tone="slate">{mission.status}</Badge></div></Link>)}{missions.length === 0 && <p className="text-slate-400">No missions yet.</p>}</div>}</section>
      <form onSubmit={create} className="h-fit rounded-xl border border-white/10 bg-panel p-6"><div className="mb-5 flex items-center gap-2"><Plus className="text-aqua" size={20} /><h2 className="text-lg font-semibold">New mission</h2></div><label className="mb-4 block text-sm">Name<input required maxLength={120} value={name} onChange={e => setName(e.target.value)} className="mt-2 w-full rounded-lg border border-white/10 bg-navy px-3 py-2 outline-none focus:border-aqua" placeholder="Harbor survey" /></label><label className="mb-4 block text-sm">Description<textarea value={description} onChange={e => setDescription(e.target.value)} className="mt-2 min-h-24 w-full rounded-lg border border-white/10 bg-navy px-3 py-2 outline-none focus:border-aqua" /></label><label className="mb-5 block text-sm">Mode<select value={mode} onChange={e => setMode(e.target.value as MissionMode)} className="mt-2 w-full rounded-lg border border-white/10 bg-navy px-3 py-2"><option value="DEMO">Demo</option><option value="REAL_DATA">Real data (foundation only)</option><option value="OFFLINE_CACHED">Offline/cached (foundation only)</option></select></label><button disabled={saving || !name.trim()} className="w-full rounded-lg bg-aqua px-4 py-3 font-bold text-navy disabled:opacity-50">{saving ? 'Creating…' : 'Create mission'}</button>{error && missions.length > 0 && <p role="alert" className="mt-3 text-sm text-red-300">{error}</p>}</form>
    </div>
  </div>
}
