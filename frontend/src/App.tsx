import { Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { OverviewPage } from './pages/OverviewPage'
import { BehavioralDNAPage } from './pages/BehavioralDNAPage'
import { TimeMachinePage } from './pages/TimeMachinePage'
import { PredictionAutopsyPage } from './pages/PredictionAutopsyPage'

function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/behavioral-dna" element={<BehavioralDNAPage />} />
        <Route path="/time-machine" element={<TimeMachinePage />} />
        <Route path="/prediction-autopsy" element={<PredictionAutopsyPage />} />
        {/* Catch-all route -> redirect to overview */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  )
}

export default App
