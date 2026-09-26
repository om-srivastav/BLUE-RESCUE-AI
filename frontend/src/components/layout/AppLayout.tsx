import { Activity, Anchor, Compass, LayoutDashboard, List, Waves, Satellite, Radar, Route, FileText } from 'lucide-react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { api } from '../../services/api'
import { Badge } from '../common/Badge'

const links = [
  { to: '/', label: 'Overview', icon: Compass, end: true },
  { to: '/missions', label: 'Missions', icon: List, end: false },
]

export function AppLayout() {
  const [online, setOnline] = useState<boolean | null>(null)
  const location = useLocation()
  const missionId = location.pathname.match(/^\/missions\/(\d+)/)?.[1]
  useEffect(() => { api.health().then(() => setOnline(true)).catch(() => setOnline(false)) }, [])

  return <div className="min-h-screen bg-navy lg:flex">
    <aside className="border-b border-white/10 bg-[#0b1d2d] p-5 lg:min-h-screen lg:w-64 lg:border-b-0 lg:border-r">
      <NavLink to="/" className="flex items-center gap-3 text-lg font-black tracking-tight text-white"><span className="rounded-lg bg-aqua p-2 text-navy"><Anchor size={22} /></span> BLUE-RESCUE <span className="text-aqua">AI</span></NavLink>
      <p className="mt-2 text-xs tracking-widest text-slate-400">MARITIME DECISION SUPPORT</p>
      <nav className="mt-8 flex gap-2 lg:flex-col">
        {links.map(({ to, label, icon: Icon, end }) => <NavLink key={to} to={to} end={end} className={({ isActive }) => `flex items-center gap-3 rounded-lg px-4 py-3 text-sm ${isActive ? 'bg-aqua/10 text-aqua' : 'text-slate-300 hover:bg-white/5'}`}><Icon size={18} />{label}</NavLink>)}
        {missionId && [
          { to: `/missions/${missionId}`, label: 'Dashboard', icon: LayoutDashboard },
          { to: `/missions/${missionId}/satellite`, label: 'Satellite', icon: Satellite },
          { to: `/missions/${missionId}/sonar`, label: 'Sonar', icon: Radar },
          { to: `/missions/${missionId}/risk`, label: 'Risk / Routing', icon: Route },
          { to: `/missions/${missionId}/report`, label: 'Report', icon: FileText },
        ].map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} end className={({ isActive }) => `flex items-center gap-3 rounded-lg px-4 py-3 text-sm ${isActive ? 'bg-aqua/10 text-aqua' : 'text-slate-300 hover:bg-white/5'}`}><Icon size={18} />{label}</NavLink>)}
      </nav>
      <div className="mt-10 hidden rounded-xl border border-white/10 bg-white/5 p-4 lg:block"><Waves className="mb-3 text-aqua" size={22} /><p className="text-sm font-semibold">WHERE → WHAT → RISK → ROUTE</p><p className="mt-2 text-xs leading-5 text-slate-400">Offline research prototype with simulated imagery.</p></div>
    </aside>
    <div className="min-w-0 flex-1">
      <header className="app-header flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-5 py-4 md:px-10"><div className="flex items-center gap-3"><LayoutDashboard size={20} className="text-aqua" /><span className="font-semibold">Command center</span></div><Badge tone={online === true ? 'aqua' : online === false ? 'amber' : 'slate'}><Activity size={12} className="mr-1" /> API {online === true ? 'ONLINE' : online === false ? 'UNAVAILABLE' : 'CHECKING'}</Badge></header>
      <main className="mx-auto max-w-7xl p-5 md:p-10"><Outlet /></main>
      <footer className="mx-auto max-w-7xl px-5 pb-8 text-xs leading-5 text-slate-500 md:px-10">BLUE-RESCUE AI is an academic decision-support prototype. It is not a certified maritime navigation or emergency-response system. Operational deployment would require hydrographic validation, calibrated sensors, validated models and qualified maritime authorities.</footer>
    </div>
  </div>
}
