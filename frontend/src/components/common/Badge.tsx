export function Badge({ children, tone = 'aqua' }: { children: React.ReactNode; tone?: 'aqua' | 'amber' | 'slate' }) {
  const colors = { aqua: 'border-aqua/40 bg-aqua/10 text-aqua', amber: 'border-amber-400/40 bg-amber-400/10 text-amber-300', slate: 'border-slate-500/40 bg-slate-500/10 text-slate-300' }
  return <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold tracking-wide ${colors[tone]}`}>{children}</span>
}
