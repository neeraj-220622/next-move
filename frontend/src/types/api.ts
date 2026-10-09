/** API response types — kept in sync with backend/app/schemas/common.py */

export type ServiceStatus = 'ok' | 'unavailable' | 'unknown' | 'disabled'

export interface DependencyInfo {
  name: string
  status: ServiceStatus
  message: string
  latency_ms: number | null
}

export interface HealthResponse {
  status: string
  app_name: string
  timestamp: string
}

export interface StatusResponse {
  status: string
  app_name: string
  app_env: string
  version: string
  timestamp: string
  dependencies: DependencyInfo[]
}

export type ConnectionState = 'connecting' | 'connected' | 'error'

export interface BackendStatus {
  connectionState: ConnectionState
  health: HealthResponse | null
  status: StatusResponse | null
  errorMessage: string | null
  lastChecked: Date | null
}
