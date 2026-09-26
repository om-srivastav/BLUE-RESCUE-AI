export function Loading({ label = 'Loading…' }: { label?: string }) {
  return <div className="rounded-xl border border-white/10 bg-panel p-6 text-slate-300" role="status">{label}</div>
}

export function ErrorState({ message }: { message: string }) {
  return <div className="rounded-xl border border-red-400/40 bg-red-950/30 p-6 text-red-200" role="alert">{message}</div>
}
