import type { StrategicCluster } from './cluster'

export interface CompetitorBase {
  name: string
  website: string | null
  description: string | null
  tracked_clusters: StrategicCluster[]
}

export interface CompetitorCreate extends CompetitorBase {}

export interface CompetitorResponse extends CompetitorBase {
  competitor_id: string
  created_at: string
  updated_at: string
}
