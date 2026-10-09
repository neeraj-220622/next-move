interface HeaderProps {
  appName: string
}

export function Header({ appName }: HeaderProps) {
  return (
    <header className="border-b border-white/10 bg-black/30 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        {/* Logo / wordmark */}
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 shadow-lg shadow-violet-900/40">
            <svg
              className="h-4 w-4 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 13.5l7.5-7.5 4.5 4.5 6-7.5"
              />
            </svg>
          </div>
          <span className="text-lg font-bold tracking-tight text-white">
            {appName}
          </span>
        </div>

        {/* Nav links */}
        <nav className="hidden sm:flex items-center gap-6 text-sm text-slate-400">
          <a href="#features" className="hover:text-white transition-colors">
            Features
          </a>
          <a href="#status" className="hover:text-white transition-colors">
            Status
          </a>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-white transition-colors"
          >
            API Docs ↗
          </a>
        </nav>
      </div>
    </header>
  )
}
