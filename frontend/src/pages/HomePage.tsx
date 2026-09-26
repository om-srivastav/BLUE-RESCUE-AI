import { ArrowRight, Radar, Route, Satellite, Waves } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Badge } from '../components/common/Badge'

const stages = [
  { title: 'WHERE', subtitle: 'Satellite change', icon: Satellite },
  { title: 'WHAT', subtitle: 'Sonar observations', icon: Radar },
  { title: 'RISK', subtitle: 'Environment + hazards', icon: Waves },
  { title: 'ROUTE', subtitle: 'Route comparison', icon: Route },
]

export function HomePage() {
  return <div>
    <div className="rounded-2xl border border-aqua/20 bg-gradient-to-br from-panel to-[#0a3a48] p-8 md:p-12">
      <Badge>ACADEMIC DECISION-SUPPORT PROTOTYPE</Badge>
      <h1 className="mt-6 max-w-3xl text-4xl font-black tracking-tight text-white md:text-6xl">See Above. <span className="text-aqua">Detect Below.</span> Navigate Smarter.</h1>
      <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-300">BLUE-RESCUE AI brings coastal observations, underwater detections, environmental risk, and route planning into one research workflow.</p>
      <Link to="/missions" className="mt-8 inline-flex items-center gap-2 rounded-lg bg-aqua px-5 py-3 font-bold text-navy hover:bg-teal-200">Explore missions <ArrowRight size={18} /></Link>
    </div>
    <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{stages.map(({ title, subtitle, icon: Icon }) => <div key={title} className="rounded-xl border border-white/10 bg-panel p-6"><Icon size={28} className="text-aqua" /><h2 className="mt-5 text-xl font-bold">{title}</h2><p className="mt-1 text-sm text-slate-400">{subtitle}</p><p className="mt-5 text-xs text-amber-300">Planned analysis module</p></div>)}</div>
  </div>
}
