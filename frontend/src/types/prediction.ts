import type { StrategicCluster } from './cluster'

export type PredictionStatus = "pending" | "completed" | "unavailable"

export interface PredictionRequest {
  competitor_id: string
  cluster: StrategicCluster
  cutoff_date: string
  horizon_days: number
  evidence_ids: string[]
  metadata: Record<string, any>
}

export interface PredictionResponse {
  prediction_id: string
  competitor_id: string
  cluster: StrategicCluster
  cutoff_date: string
  horizon_days: number
  probability: number | null
  model_version: string | null
  evidence_ids: string[]
  created_at: string
  status: PredictionStatus
}
