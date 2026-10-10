/**
 * API response types — single source of truth.
 * Kept in sync with backend/app/schemas/common.py
 */

// ── Dependency / service status ─────────────────────────────────────────────

export type ServiceStatus = 'ok' | 'unavailable' | 'unknown' | 'disabled'

export interface DependencyInfo {
  name: string
  status: ServiceStatus
  message: string
  latency_ms: number | null
}

// ── Backend response schemas ─────────────────────────────────────────────────

export interface HealthResponse {
  status: string
  app_name: string
  timestamp: string
}

export interface StatusResponse {
  status: string          // 'ok' | 'degraded' | 'error'
  app_name: string
  app_env: string
  version: string
  timestamp: string
  dependencies: DependencyInfo[]
}

// ── UI-level connection state ────────────────────────────────────────────────

/**
 * Five connection states the UI must distinguish:
 *  connecting   – first request in flight
 *  connected    – backend healthy (all deps ok)
 *  degraded     – backend responds but ≥1 optional dep unavailable/disabled
 *  disconnected – network or fetch error (backend not reachable)
 *  error        – unexpected response (non-2xx, malformed JSON, etc.)
 */
export type ConnectionState =
  | 'connecting'
  | 'connected'
  | 'degraded'
  | 'disconnected'
  | 'error'

export interface BackendStatus {
  connectionState: ConnectionState
  health: HealthResponse | null
  status: StatusResponse | null
  errorMessage: string | null
  lastChecked: Date | null
}
