export function TimeMachinePage() {
  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-slate-900">Strategic Time Machine</h1>
        <p className="mt-1 text-sm text-slate-500">
          Reconstruct historical signals and evaluate what could have been predicted before a competitor move.
        </p>
      </div>

      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-12 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-slate-200">
          <svg className="h-6 w-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="mb-2 text-base font-semibold text-slate-900">Historical Replay Not Implemented</h2>
        <p className="mx-auto max-w-md text-sm text-slate-500">
          Historical reconstruction depends on the Phase 4 orchestration layer and Phase 5 Hindsight integration. Data cutoff controls and retrodictive forecasts will be built out then.
        </p>
        <span className="mt-6 inline-flex items-center gap-1.5 rounded-full bg-slate-200 px-3 py-1 text-xs font-medium text-slate-600">
          <span className="h-1.5 w-1.5 rounded-full bg-slate-400"></span>
          Pending Integration
        </span>
      </div>
    </div>
  )
}
