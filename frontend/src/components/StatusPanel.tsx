import type { ConnectionState, DependencyInfo, StatusResponse } from '../types/api'

interface StatusBadgeProps {
  state: ConnectionState
}

const stateConfig: Record<
  ConnectionState,
  { label: string; dot: string; ring: string; text: string }
> = {
  connecting: {
    label: 'Connecting…',
    dot: 'bg-amber-400 animate-pulse',
    ring: 'ring-amber-400/30',
    text: 'text-amber-300',
  },
  connected: {
    label: 'Backend online',
    dot: 'bg-emerald-400',
    ring: 'ring-emerald-400/30',
    text: 'text-emerald-300',
  },
  error: {
    label: 'Backend unreachable',
    dot: 'bg-rose-500',
    ring: 'ring-rose-500/30',
    text: 'text-rose-300',
  },
}

export function StatusBadge({ state }: StatusBadgeProps) {
  const cfg = stateConfig[state]
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ring-1 ${cfg.ring} ${cfg.text} bg-white/5`}
    >
      <span className={`h-2 w-2 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  )
}

// ── Dependency row inside the status panel ────────────────────────────────────

interface DepRowProps {
  dep: DependencyInfo
}

const depStatusStyle: Record<string, string> = {
  ok: 'text-emerald-400',
  unavailable: 'text-rose-400',
  disabled: 'text-slate-400',
  unknown: 'text-amber-400',
}

export function DependencyRow({ dep }: DepRowProps) {
  const colour = depStatusStyle[dep.status] ?? 'text-slate-400'
  return (
    <div className="flex items-start justify-between gap-4 py-2 text-sm border-b border-white/5 last:border-0">
      <div>
        <span className="font-medium text-slate-200 capitalize">{dep.name}</span>
        {dep.message && (
          <p className="text-xs text-slate-500 mt-0.5">{dep.message}</p>
        )}
      </div>
      <span className={`shrink-0 font-semibold uppercase text-xs ${colour}`}>
        {dep.status}
      </span>
    </div>
  )
}

// ── Status panel card ─────────────────────────────────────────────────────────

interface StatusPanelProps {
  state: ConnectionState
  statusData: StatusResponse | null
  errorMessage: string | null
  lastChecked: Date | null
  onRefresh: () => void
}

export function StatusPanel({
  state,
  statusData,
  errorMessage,
  lastChecked,
  onRefresh,
}: StatusPanelProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Backend Status
        </h2>
        <button
          onClick={onRefresh}
          disabled={state === 'connecting'}
          className="text-xs text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-40"
        >
          ↻ Refresh
        </button>
      </div>

      {state === 'connecting' && (
        <p className="text-sm text-slate-400 animate-pulse">
          Probing backend…
        </p>
      )}

      {state === 'error' && (
        <div className="rounded-xl bg-rose-950/40 border border-rose-500/20 p-3 text-sm text-rose-300">
          <p className="font-medium mb-1">Cannot reach the backend</p>
          <p className="text-xs text-rose-400">{errorMessage}</p>
          <p className="text-xs text-slate-500 mt-2">
            Make sure FastAPI is running:{' '}
            <code className="font-mono text-slate-400">
              uvicorn app.main:app --reload
            </code>
          </p>
        </div>
      )}

      {state === 'connected' && statusData && (
        <>
          <div className="flex items-center gap-3 mb-4">
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-semibold uppercase ${
                statusData.status === 'ok'
                  ? 'bg-emerald-900/60 text-emerald-300'
                  : statusData.status === 'degraded'
                  ? 'bg-amber-900/60 text-amber-300'
                  : 'bg-rose-900/60 text-rose-300'
              }`}
            >
              {statusData.status}
            </span>
            <span className="text-xs text-slate-500">
              v{statusData.version} · {statusData.app_env}
            </span>
          </div>

          <div>
            {statusData.dependencies.map((dep) => (
              <DependencyRow key={dep.name} dep={dep} />
            ))}
          </div>
        </>
      )}

      {lastChecked && (
        <p className="mt-3 text-xs text-slate-600">
          Last checked: {lastChecked.toLocaleTimeString()}
        </p>
      )}
    </div>
  )
}
