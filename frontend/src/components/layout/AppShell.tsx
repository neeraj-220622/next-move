import type { ReactNode } from 'react'
import { useBackendStatus } from '../../hooks/useBackendStatus'
import { Sidebar } from './Sidebar'

interface AppShellProps {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const status = useBackendStatus()
  const appName = status.health?.app_name ?? status.status?.app_name ?? 'NextMove'
  const appEnv = status.status?.app_env

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 font-sans antialiased">
      <Sidebar
        connectionState={status.connectionState}
        appName={appName}
        appEnv={appEnv}
      />

      {/* ── Main content area ── */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* ── Top bar ── */}
        <header className="flex shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
          <p className="text-xs text-slate-500">
            Competitive intelligence powered by historical evidence and predictive analysis
          </p>
          <div className="flex items-center gap-3">
            <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
              Local Development
            </span>
            {status.status && (
              <a
                href={`${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}/docs`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-slate-500 hover:text-slate-800 transition-colors underline underline-offset-2"
              >
                API Docs ↗
              </a>
            )}
          </div>
        </header>

        {/* ── Scrollable page content ── */}
        <main className="flex-1 overflow-y-auto px-8 py-6" id="main-content">
          {/* Pass backend status down via context — avoids re-fetching in each page */}
          <BackendStatusContext.Provider value={status}>
            {children}
          </BackendStatusContext.Provider>
        </main>
      </div>
    </div>
  )
}

// ── Context so pages can read backend status without re-fetching ─────────────

import { createContext, useContext } from 'react'
import type { BackendStatus } from '../../types/api'

const BackendStatusContext = createContext<BackendStatus & { refresh: () => void }>({
  connectionState: 'connecting',
  health: null,
  status: null,
  errorMessage: null,
  lastChecked: null,
  refresh: () => {},
})

export function useSharedBackendStatus() {
  return useContext(BackendStatusContext)
}
