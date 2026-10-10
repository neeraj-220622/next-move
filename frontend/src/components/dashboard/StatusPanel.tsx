import { useSharedBackendStatus } from '../layout/AppShell'
import type { ConnectionState, DependencyInfo } from '../../types/api'

const connectionDot: Record<ConnectionState, string> = {
  connecting: 'bg-amber-400 animate-pulse',
  connected: 'bg-emerald-500',
  degraded: 'bg-amber-400',
  disconnected: 'bg-slate-400',
  error: 'bg-rose-500',
}

const connectionLabel: Record<ConnectionState, string> = {
  connecting: 'Connecting to backend…',
  connected: 'All services online',
  degraded: 'Some services unavailable',
  disconnected: 'Backend offline',
  error: 'Backend error',
}

function DependencyRow({ dep }: { dep: DependencyInfo }) {
  const isOk = dep.status === 'ok'
  const isDisabled = dep.status === 'disabled'
  
  return (
    <div className="flex items-start justify-between gap-4 border-b border-slate-100 py-3 last:border-0">
      <div>
        <p className="text-sm font-medium text-slate-900 capitalize">{dep.name}</p>
        {dep.message && (
          <p className="mt-0.5 text-xs text-slate-500">{dep.message}</p>
        )}
      </div>
      <span
        className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
          isOk
            ? 'bg-emerald-50 text-emerald-600'
            : isDisabled
            ? 'bg-slate-100 text-slate-500'
            : 'bg-rose-50 text-rose-600'
        }`}
      >
        {dep.status}
      </span>
    </div>
  )
}

export function StatusPanel() {
  const { connectionState, status, errorMessage, lastChecked, refresh } =
    useSharedBackendStatus()

  return (
    <div className="flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-5 py-4">
        <div className="flex items-center gap-2.5">
          <span className={`h-2.5 w-2.5 rounded-full ${connectionDot[connectionState]}`} />
          <h3 className="text-sm font-medium text-slate-900">
            {connectionLabel[connectionState]}
          </h3>
        </div>
        <button
          onClick={refresh}
          disabled={connectionState === 'connecting'}
          className="text-xs font-medium text-indigo-600 hover:text-indigo-700 disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      <div className="p-5">
        {connectionState === 'disconnected' || connectionState === 'error' ? (
          <div className="rounded-lg border border-rose-100 bg-rose-50 p-4">
            <p className="text-sm font-medium text-rose-800">Connection Failed</p>
            <p className="mt-1 text-xs text-rose-600">{errorMessage}</p>
            <p className="mt-3 text-xs text-rose-700">
              Ensure the FastAPI backend is running:
              <br />
              <code className="mt-1 block rounded bg-white/60 px-2 py-1 font-mono">
                uvicorn app.main:app --reload
              </code>
            </p>
          </div>
        ) : status ? (
          <div className="space-y-1">
            {status.dependencies.map((dep) => (
              <DependencyRow key={dep.name} dep={dep} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-500">Loading service details…</p>
        )}
      </div>

      {lastChecked && (
        <div className="bg-slate-50 px-5 py-2 text-right">
          <p className="text-[10px] uppercase tracking-wider text-slate-400">
            Last checked: {lastChecked.toLocaleTimeString()}
          </p>
        </div>
      )}
    </div>
  )
}
