import { NavLink, useLocation } from 'react-router-dom'
import type { ConnectionState } from '../../types/api'

interface NavItem {
  to: string
  label: string
  icon: React.ReactNode
  description: string
}

const NAV_ITEMS: NavItem[] = [
  {
    to: '/',
    label: 'Overview',
    description: 'Dashboard & status',
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    to: '/behavioral-dna',
    label: 'Behavioral DNA',
    description: 'Competitor patterns',
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
      </svg>
    ),
  },
  {
    to: '/time-machine',
    label: 'Time Machine',
    description: 'Historical analysis',
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    to: '/prediction-autopsy',
    label: 'Prediction Autopsy',
    description: 'Forecast outcomes',
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
]

const connectionDot: Record<ConnectionState, string> = {
  connecting: 'bg-amber-400 animate-pulse',
  connected: 'bg-emerald-400',
  degraded: 'bg-amber-400',
  disconnected: 'bg-slate-400',
  error: 'bg-rose-500',
}

const connectionLabel: Record<ConnectionState, string> = {
  connecting: 'Connecting…',
  connected: 'Backend online',
  degraded: 'Degraded',
  disconnected: 'Disconnected',
  error: 'Error',
}

interface SidebarProps {
  connectionState: ConnectionState
  appName: string
  appEnv?: string
}

export function Sidebar({ connectionState, appName, appEnv }: SidebarProps) {
  const location = useLocation()

  return (
    <aside className="flex h-screen w-56 shrink-0 flex-col border-r border-slate-200 bg-white">
      {/* ── Brand ── */}
      <div className="flex items-center gap-2.5 border-b border-slate-100 px-5 py-4">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-slate-900">
          <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.5l7.5-7.5 4.5 4.5 6-7.5" />
          </svg>
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-slate-900">{appName}</p>
          {appEnv && (
            <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
              {appEnv}
            </p>
          )}
        </div>
      </div>

      {/* ── Navigation ── */}
      <nav className="flex-1 overflow-y-auto px-3 py-3" aria-label="Primary navigation">
        <p className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
          Navigation
        </p>
        <ul className="space-y-0.5">
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.to === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(item.to)

            return (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.to === '/'}
                  className={[
                    'group flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:ring-offset-1',
                    isActive
                      ? 'bg-slate-900 text-white'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
                  ].join(' ')}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <span className={isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-600'}>
                    {item.icon}
                  </span>
                  {item.label}
                </NavLink>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* ── Connection indicator ── */}
      <div className="border-t border-slate-100 px-5 py-3">
        <div className="flex items-center gap-2">
          <span className={`h-2 w-2 shrink-0 rounded-full ${connectionDot[connectionState]}`} />
          <span className="text-xs text-slate-500">{connectionLabel[connectionState]}</span>
        </div>
      </div>
    </aside>
  )
}
