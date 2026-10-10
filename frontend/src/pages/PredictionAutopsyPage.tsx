export function PredictionAutopsyPage() {
  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-slate-900">Prediction Autopsy</h1>
        <p className="mt-1 text-sm text-slate-500">
          Compare past predictions with actual outcomes to improve forecasting accuracy.
        </p>
      </div>

      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-12 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-slate-200">
          <svg className="h-6 w-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <h2 className="mb-2 text-base font-semibold text-slate-900">No Predictions Available</h2>
        <p className="mx-auto max-w-md text-sm text-slate-500">
          Prediction recording and outcome evaluation rely on the Phase 4/5 integration of the forecasting engine and Hindsight memory. Evaluation metrics will appear here once real outcomes are recorded.
        </p>
        <span className="mt-6 inline-flex items-center gap-1.5 rounded-full bg-slate-200 px-3 py-1 text-xs font-medium text-slate-600">
          <span className="h-1.5 w-1.5 rounded-full bg-slate-400"></span>
          Pending Integration
        </span>
      </div>
    </div>
  )
}
