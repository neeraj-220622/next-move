export type EvaluationStatus = "pending" | "evaluated"
export type EventOccurrence = "occurred" | "not_occurred" | "unknown"

export interface PredictionOutcomeBase {
  prediction_id: string
  occurrence: EventOccurrence
  window_start: string
  window_end: string
  evidence_ids: string[]
  metrics: Record<string, any>
  lesson_ids: string[]
}

export interface PredictionOutcomeCreate extends PredictionOutcomeBase {}

export interface PredictionOutcomeResponse extends PredictionOutcomeBase {
  outcome_id: string
  status: EvaluationStatus
  evaluation_time: string | null
}
