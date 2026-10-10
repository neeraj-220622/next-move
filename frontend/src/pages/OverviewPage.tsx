import { useSharedBackendStatus } from '../components/layout/AppShell'
import { StatusPanel } from '../components/dashboard/StatusPanel'

export function OverviewPage() {
  useSharedBackendStatus()

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-slate-900">Overview</h1>
        <p className="mt-1 text-sm text-slate-500">
          NextMove Architecture Phase 2 implementation.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="space-y-6">
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-400">
              Project Status
            </h2>
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="mb-4 text-sm text-slate-600 leading-relaxed">
                This environment is currently running <strong>Architecture Phase 2</strong>.
                The frontend and backend are integrated, and the core routing is in place.
              </p>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-center gap-2">
                  <span className="text-emerald-500">✓</span> Phase 1: Repository Foundation
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-emerald-500">✓</span> Phase 2: UI & FastAPI connection
                </li>
                <li className="flex items-center gap-2 text-slate-400">
                  <span>○</span> Phase 3: Shared schemas & contracts
                </li>
                <li className="flex items-center gap-2 text-slate-400">
                  <span>○</span> Phase 4: Agent layer
                </li>
              </ul>
            </div>
          </section>
        </div>

        <div>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-400">
            System Health
          </h2>
          <StatusPanel />
        </div>
      </div>
    </div>
  )
}
