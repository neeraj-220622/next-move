import type { StrategicCluster } from './cluster'
import type { Provenance } from './evidence'

export type MemoryCategory =
  | "historical_evidence"
  | "behavioral_pattern"
  | "prediction"
  | "outcome"
  | "lesson"

export interface MemoryReference {
  memory_id: string
  competitor_id: string | null
  cluster: StrategicCluster | null
  category: MemoryCategory
  content: string
  evidence_ids: string[]
  observation_time: string | null
  provenance: Provenance
  metadata: Record<string, any>
}
