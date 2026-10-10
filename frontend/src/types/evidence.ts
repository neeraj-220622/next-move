import type { StrategicCluster } from './cluster'

export type Provenance = "verified" | "unverified" | "synthetic"
export type ValidationStatus = "pending" | "validated" | "rejected"

export interface EvidenceBase {
  competitor_id: string
  cluster: StrategicCluster
  description: string
  source_url: string | null
  observation_time: string
  provenance: Provenance
  confidence: number | null
}

export interface EvidenceCreate extends EvidenceBase {}

export interface EvidenceResponse extends EvidenceBase {
  evidence_id: string
  ingestion_time: string
  validation_status: ValidationStatus
}
