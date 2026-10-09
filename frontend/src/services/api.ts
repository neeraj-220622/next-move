/**
 * API service — all FastAPI communication lives here.
 *
 * The base URL is read from the VITE_API_BASE_URL env variable (default: '').
 * When empty the Vite dev-server proxy forwards /health and /api/* to FastAPI,
 * so no hard-coded port is needed in development.
 */

import type { HealthResponse, StatusResponse } from '../types/api'

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? ''

async function fetchJson<T>(path: string, timeoutMs = 8000): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      signal: controller.signal,
    })
    if (!response.ok) {
      throw new Error(`HTTP ${response.status} — ${response.statusText}`)
    }
    return (await response.json()) as T
  } finally {
    clearTimeout(timer)
  }
}

export const api = {
  /** Lightweight liveness probe — fastest check. */
  health: (): Promise<HealthResponse> => fetchJson<HealthResponse>('/health'),

  /** Full dependency status — may be slower due to external probes. */
  status: (): Promise<StatusResponse> =>
    fetchJson<StatusResponse>('/api/v1/status', 15_000),
}
