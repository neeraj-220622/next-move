/**
 * useBackendStatus — shared hook for polling FastAPI health + status.
 *
 * Features
 * ─────────
 * • Fetches on mount
 * • Refreshes every POLL_INTERVAL_MS (15 s)
 * • Manual refresh via returned `refresh()` function
 * • Cancels in-flight requests on unmount / re-trigger (AbortController)
 * • Derives ConnectionState from the actual backend response — a backend
 *   that is reachable but has unavailable optional deps is "degraded",
 *   not "disconnected"
 * • Never overlaps two simultaneous polls
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { api, NetworkError } from '../services/api'
import type { BackendStatus, ConnectionState } from '../types/api'

const POLL_INTERVAL_MS = 15_000

const INITIAL_STATE: BackendStatus = {
  connectionState: 'connecting',
  health: null,
  status: null,
  errorMessage: null,
  lastChecked: null,
}

function deriveConnectionState(backendStatus: string): ConnectionState {
  switch (backendStatus) {
    case 'ok':
      return 'connected'
    case 'degraded':
      return 'degraded'
    default:
      return 'error'
  }
}

export function useBackendStatus() {
  const [state, setState] = useState<BackendStatus>(INITIAL_STATE)
  const inFlight = useRef(false)
  const abortRef = useRef<AbortController | null>(null)

  const fetchStatus = useCallback(async (manual = false) => {
    if (inFlight.current && !manual) return   // skip if already polling

    // Cancel any previous request
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    inFlight.current = true

    setState((prev) => ({ ...prev, connectionState: 'connecting' }))

    try {
      const health = await api.health(controller.signal)

      // Health passed — now attempt full status (best-effort)
      let statusData = null
      try {
        statusData = await api.status(controller.signal)
      } catch {
        // Status probe failed but health passed → still connected, no dep info
      }

      if (controller.signal.aborted) return

      const connectionState = statusData
        ? deriveConnectionState(statusData.status)
        : 'connected'

      setState({
        connectionState,
        health,
        status: statusData,
        errorMessage: null,
        lastChecked: new Date(),
      })
    } catch (err) {
      if (controller.signal.aborted) return

      const isNetwork = err instanceof NetworkError
      setState({
        connectionState: isNetwork ? 'disconnected' : 'error',
        health: null,
        status: null,
        errorMessage: err instanceof Error ? err.message : 'Unknown error',
        lastChecked: new Date(),
      })
    } finally {
      inFlight.current = false
    }
  }, [])

  // Fetch on mount + set up polling interval
  useEffect(() => {
    fetchStatus()
    const interval = setInterval(() => fetchStatus(), POLL_INTERVAL_MS)
    return () => {
      clearInterval(interval)
      abortRef.current?.abort()
    }
  }, [fetchStatus])

  const refresh = useCallback(() => fetchStatus(true), [fetchStatus])

  return { ...state, refresh }
}
