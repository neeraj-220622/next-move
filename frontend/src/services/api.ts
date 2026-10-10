/**
 * Centralised API client.
 *
 * All HTTP calls to the FastAPI backend go through this module.
 * Page components and hooks must never construct fetch() calls directly.
 *
 * Base URL resolution order:
 *  1. VITE_API_BASE_URL env variable (set in .env.local for production-like dev)
 *  2. Empty string → Vite dev-server proxy forwards /health and /api/* to :8000
 */

import type { HealthResponse, StatusResponse } from '../types/api'
import type { CompetitorCreate, CompetitorResponse } from '../types/competitor'
import type { PredictionRequest, PredictionResponse } from '../types/prediction'
import type { EvidenceCreate, EvidenceResponse } from '../types/evidence'

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? ''

// ── Core fetch wrapper ───────────────────────────────────────────────────────

class ApiError extends Error {
  public readonly status: number
  
  constructor(
    status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

class NetworkError extends Error {
  constructor(cause?: unknown) {
    super(cause instanceof Error ? cause.message : 'Network request failed')
    this.name = 'NetworkError'
  }
}

async function fetchJson<T>(
  path: string,
  options: { timeoutMs?: number; signal?: AbortSignal; method?: string; headers?: Record<string, string>; body?: string } = {},
): Promise<T> {
  const { timeoutMs = 8_000, signal: externalSignal } = options

  // Combine caller's signal with a local timeout signal
  const timeoutController = new AbortController()
  const timer = setTimeout(() => timeoutController.abort(), timeoutMs)

  // Merge signals if an external one is provided
  const signal = externalSignal
    ? AbortSignal.any
      ? AbortSignal.any([externalSignal, timeoutController.signal])
      : timeoutController.signal           // fallback: timeout wins
    : timeoutController.signal

  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      ...options,
      signal,
    })

    if (!response.ok) {
      throw new ApiError(
        response.status,
        `HTTP ${response.status} — ${response.statusText}`,
      )
    }

    return (await response.json()) as T
  } catch (err) {
    if (err instanceof ApiError) throw err
    // AbortError = timeout OR caller cancelled
    throw new NetworkError(err)
  } finally {
    clearTimeout(timer)
  }
}

// ── Public API surface ───────────────────────────────────────────────────────

export const api = {
  /**
   * Lightweight liveness probe.
   * Use this to confirm the server process is up before calling /status.
   */
  health: (signal?: AbortSignal): Promise<HealthResponse> =>
    fetchJson<HealthResponse>('/health', { timeoutMs: 6_000, signal }),

  /**
   * Full dependency status.
   * Probes Hindsight, LLM, and forecasting — may take up to 15 s.
   */
  status: (signal?: AbortSignal): Promise<StatusResponse> =>
    fetchJson<StatusResponse>('/api/v1/status', { timeoutMs: 15_000, signal }),

  // ── Phase 3: Competitors, Predictions, Evidence (Development Stubs) ─────────

  getCompetitors: (signal?: AbortSignal): Promise<CompetitorResponse[]> =>
    fetchJson<CompetitorResponse[]>('/api/v1/competitors', { signal }),

  getCompetitor: (id: string, signal?: AbortSignal): Promise<CompetitorResponse> =>
    fetchJson<CompetitorResponse>(`/api/v1/competitors/${id}`, { signal }),

  registerCompetitor: (data: CompetitorCreate): Promise<CompetitorResponse> =>
    fetchJson<CompetitorResponse>('/api/v1/competitors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  requestPrediction: (data: PredictionRequest): Promise<PredictionResponse> =>
    fetchJson<PredictionResponse>('/api/v1/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  getPrediction: (id: string, signal?: AbortSignal): Promise<PredictionResponse> =>
    fetchJson<PredictionResponse>(`/api/v1/predict/${id}`, { signal }),

  getEvidence: (signal?: AbortSignal): Promise<EvidenceResponse[]> =>
    fetchJson<EvidenceResponse[]>('/api/v1/evidence', { signal }),

  registerEvidence: (data: EvidenceCreate): Promise<EvidenceResponse> =>
    fetchJson<EvidenceResponse>('/api/v1/evidence', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),
}

export { ApiError, NetworkError }
