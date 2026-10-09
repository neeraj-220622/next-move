import { useCallback, useEffect, useState } from 'react'
import { Header } from './components/Header'
import { FeatureCard } from './components/FeatureCard'
import { StatusBadge, StatusPanel } from './components/StatusPanel'
import type { BackendStatus, StatusResponse } from './types/api'
import { api } from './services/api'

const FEATURES = [
  {
    icon: '🧬',
    title: 'Competitor Behavioral DNA',
    description:
      'Identify and remember recurring competitor behaviours. Build a persistent profile of patterns across time — product launches, pricing moves, hiring surges, and market expansions.',
    phase: 'Phase 2+',
    gradient: 'bg-violet-500',
  },
  {
    icon: '⏳',
    title: 'Strategic Time Machine',
    description:
      'Reconstruct historical market signals and evaluate what could have been predicted before a competitor made their move. Learn from hindsight to sharpen foresight.',
    phase: 'Phase 3+',
    gradient: 'bg-indigo-500',
  },
  {
    icon: '🔬',
    title: 'Prediction Autopsy',
    description:
      'Compare past predictions with actual outcomes. Extract lessons and feed them back into the forecasting model to improve future accuracy over time.',
    phase: 'Phase 4+',
    gradient: 'bg-sky-500',
  },
]

function App() {
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({
    connectionState: 'connecting',
    health: null,
    status: null,
    errorMessage: null,
    lastChecked: null,
  })

  const checkBackend = useCallback(async () => {
    setBackendStatus((prev) => ({ ...prev, connectionState: 'connecting' }))
    try {
      const health = await api.health()
      // If health passes, fetch full status (best-effort — don't crash if slow)
      let statusData: StatusResponse | null = null
      try {
        statusData = await api.status()
      } catch {
        // status probe failed — still mark as connected (health passed)
      }
      setBackendStatus({
        connectionState: 'connected',
        health,
        status: statusData,
        errorMessage: null,
        lastChecked: new Date(),
      })
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Unknown connection error'
      setBackendStatus({
        connectionState: 'error',
        health: null,
        status: null,
        errorMessage: message,
        lastChecked: new Date(),
      })
    }
  }, [])

  useEffect(() => {
    checkBackend()
  }, [checkBackend])

  const appName =
    backendStatus.health?.app_name ?? backendStatus.status?.app_name ?? 'NextMove'

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-slate-100 font-sans antialiased">
      {/* ── Background glow ── */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 h-96 w-[700px] rounded-full bg-violet-600/10 blur-3xl" />
        <div className="absolute top-1/3 -left-20 h-64 w-64 rounded-full bg-indigo-700/8 blur-3xl" />
        <div className="absolute bottom-0 right-0 h-64 w-64 rounded-full bg-sky-700/8 blur-3xl" />
      </div>

      <Header appName={appName} />

      <main className="relative mx-auto max-w-6xl px-6 py-12">
        {/* ── Hero ── */}
        <section className="mb-16 text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-4 py-1.5 text-xs text-violet-300">
            <span className="h-1.5 w-1.5 rounded-full bg-violet-400" />
            Architecture Phase 1 — Foundation
          </div>

          <h1 className="mb-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
            AI-Powered{' '}
            <span className="bg-gradient-to-r from-violet-400 to-indigo-400 bg-clip-text text-transparent">
              Competitive Intelligence
            </span>
          </h1>

          <p className="mx-auto max-w-2xl text-base text-slate-400 leading-relaxed">
            NextMove analyses competitor behaviour, reconstructs historical market
            signals, predicts potential competitor actions, and learns from
            previous prediction outcomes.
          </p>

          <div className="mt-6 flex justify-center">
            <StatusBadge state={backendStatus.connectionState} />
          </div>
        </section>

        {/* ── Main grid ── */}
        <div className="grid gap-8 lg:grid-cols-3">
          {/* ── Feature cards column ── */}
          <div id="features" className="lg:col-span-2 space-y-4">
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-widest text-slate-500">
              Core Features
            </h2>
            {FEATURES.map((f) => (
              <FeatureCard key={f.title} {...f} />
            ))}
          </div>

          {/* ── Right sidebar ── */}
          <div id="status" className="space-y-4">
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-widest text-slate-500">
              System Status
            </h2>
            <StatusPanel
              state={backendStatus.connectionState}
              statusData={backendStatus.status}
              errorMessage={backendStatus.errorMessage}
              lastChecked={backendStatus.lastChecked}
              onRefresh={checkBackend}
            />

            {/* Phase roadmap */}
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <h3 className="mb-3 text-sm font-semibold text-slate-300">
                Phase Roadmap
              </h3>
              <ol className="space-y-2 text-xs text-slate-500">
                {[
                  ['Phase 1', 'Repository foundation', true],
                  ['Phase 2', 'UI & FastAPI connection', false],
                  ['Phase 3', 'Shared schemas & contracts', false],
                  ['Phase 4', 'Agent / orchestration layer', false],
                  ['Phase 5', 'Hindsight & Qwen integration', false],
                  ['Phase 6', 'Config, logging & resilience', false],
                  ['Phase 7', 'Integration & handoff', false],
                ].map(([phase, label, done]) => (
                  <li key={phase as string} className="flex items-center gap-2">
                    <span
                      className={`h-4 w-4 rounded-full flex items-center justify-center text-[9px] shrink-0 ${
                        done
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : 'bg-white/5 text-slate-600'
                      }`}
                    >
                      {done ? '✓' : '·'}
                    </span>
                    <span className={done ? 'text-slate-300' : ''}>
                      <strong>{phase as string}</strong> — {label as string}
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </div>
      </main>

      <footer className="relative mt-16 border-t border-white/5 py-8 text-center text-xs text-slate-600">
        NextMove · Architecture Phase 1 · No fake data · No hardcoded status
      </footer>
    </div>
  )
}

export default App
