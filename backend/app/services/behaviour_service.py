from datetime import datetime
import math
from typing import List, Optional, Dict, Tuple
from uuid import UUID

from app.schemas.evidence import EvidenceResponse, Provenance
from app.schemas.cluster import StrategicCluster
from app.schemas.behaviour import (
    CompetitorBehaviourProfile,
    ActionFrequency,
    TransitionProbability,
    TemporalStats,
    RecurringPattern,
    ProvenanceBreakdown,
    ClusterConfidenceInterval,
)


class BehaviourService:
    """
    Core backend domain engine for competitor behavior analysis.
    Purely statistical, deterministic, and LLM-independent.
    """

    def analyze_evidence(
        self,
        competitor_id: UUID,
        evidence_list: List[EvidenceResponse],
        competitor_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        cutoff_date: Optional[datetime] = None,
    ) -> CompetitorBehaviourProfile:
        """
        Analyze a list of evidence items for a given competitor and return a complete Behaviour Profile.

        Parameters
        ----------
        competitor_id : UUID
            The target competitor ID.
        evidence_list : List[EvidenceResponse]
            List of evidence items.
        competitor_name : Optional[str]
            Optional competitor display name.
        start_date : Optional[datetime]
            Optional timestamp filter lower bound.
        cutoff_date : Optional[datetime]
            Optional timestamp filter upper bound (historical cutoff).
        """
        # Filter evidence items chronologically and by date constraints
        filtered: List[EvidenceResponse] = []
        for e in evidence_list:
            if e.competitor_id != competitor_id:
                continue
            if start_date and e.observation_time < start_date:
                continue
            if cutoff_date and e.observation_time > cutoff_date:
                continue
            filtered.append(e)

        # Sort chronologically by observation_time
        sorted_evidence = sorted(filtered, key=lambda x: x.observation_time)
        sample_size = len(sorted_evidence)

        # Handle empty dataset cleanly
        if sample_size == 0:
            return CompetitorBehaviourProfile(
                competitor_id=competitor_id,
                competitor_name=competitor_name,
                sample_size=0,
                provenance_breakdown=ProvenanceBreakdown(verified=0, unverified=0, synthetic=0),
                cluster_frequencies=[],
                transition_matrix=[],
                temporal_stats=TemporalStats(
                    total_observations=0,
                    first_observed=None,
                    last_observed=None,
                    time_span_days=0.0,
                    avg_days_between_events=0.0,
                    event_velocity_per_day=0.0,
                ),
                recurring_patterns=[],
                entropy_score=0.0,
                confidence_intervals=[],
                low_sample_warning=True,
                backing_evidence_ids=[],
            )

        backing_ids = [e.evidence_id for e in sorted_evidence]
        low_sample = sample_size < 5

        # 1. Provenance Breakdown
        verified = sum(1 for e in sorted_evidence if e.provenance == Provenance.VERIFIED)
        unverified = sum(1 for e in sorted_evidence if e.provenance == Provenance.UNVERIFIED)
        synthetic = sum(1 for e in sorted_evidence if e.provenance == Provenance.SYNTHETIC)
        prov_breakdown = ProvenanceBreakdown(
            verified=verified,
            unverified=unverified,
            synthetic=synthetic,
        )

        # 2. Cluster Frequencies
        cluster_counts: Dict[StrategicCluster, int] = {}
        for e in sorted_evidence:
            cluster_counts[e.cluster] = cluster_counts.get(e.cluster, 0) + 1

        cluster_frequencies: List[ActionFrequency] = []
        for cluster, count in sorted(cluster_counts.items(), key=lambda x: x[1], reverse=True):
            pct = round((count / sample_size) * 100.0, 2)
            cluster_frequencies.append(ActionFrequency(cluster=cluster, count=count, percentage=pct))

        # 3. Temporal Statistics
        first_obs = sorted_evidence[0].observation_time
        last_obs = sorted_evidence[-1].observation_time
        time_span_sec = (last_obs - first_obs).total_seconds()
        time_span_days = max(0.0, time_span_sec / 86400.0)

        if sample_size > 1:
            gaps = [
                (sorted_evidence[i].observation_time - sorted_evidence[i - 1].observation_time).total_seconds() / 86400.0
                for i in range(1, sample_size)
            ]
            avg_gap = sum(gaps) / len(gaps)
        else:
            avg_gap = 0.0

        event_velocity = sample_size / time_span_days if time_span_days > 0 else float(sample_size)

        temp_stats = TemporalStats(
            total_observations=sample_size,
            first_observed=first_obs,
            last_observed=last_obs,
            time_span_days=round(time_span_days, 2),
            avg_days_between_events=round(avg_gap, 2),
            event_velocity_per_day=round(event_velocity, 4),
        )

        # 4. Action Transition Matrix (1st-Order Markov)
        transition_counts: Dict[StrategicCluster, Dict[StrategicCluster, int]] = {}
        for i in range(1, sample_size):
            from_c = sorted_evidence[i - 1].cluster
            to_c = sorted_evidence[i].cluster
            if from_c not in transition_counts:
                transition_counts[from_c] = {}
            transition_counts[from_c][to_c] = transition_counts[from_c].get(to_c, 0) + 1

        transition_matrix: List[TransitionProbability] = []
        for from_c, to_dict in transition_counts.items():
            total_from = sum(to_dict.values())
            for to_c, count in to_dict.items():
                prob = round(count / total_from, 4)
                transition_matrix.append(
                    TransitionProbability(
                        from_cluster=from_c,
                        to_cluster=to_c,
                        count=count,
                        probability=prob,
                    )
                )
        # Sort transition matrix by probability descending
        transition_matrix.sort(key=lambda x: (x.from_cluster.value, -x.probability))

        # 5. Recurring Pattern Detection (N-grams of length 2 and 3)
        recurring_patterns = self._extract_recurring_patterns(sorted_evidence)

        # 6. Statistical Metrics: Shannon Entropy
        entropy = 0.0
        for count in cluster_counts.values():
            p = count / sample_size
            if p > 0:
                entropy -= p * math.log2(p)
        entropy_score = round(entropy, 4)

        # 7. Wilson Score 95% Confidence Intervals for Cluster Proportions
        confidence_intervals = self._compute_confidence_intervals(cluster_counts, sample_size)

        return CompetitorBehaviourProfile(
            competitor_id=competitor_id,
            competitor_name=competitor_name,
            sample_size=sample_size,
            provenance_breakdown=prov_breakdown,
            cluster_frequencies=cluster_frequencies,
            transition_matrix=transition_matrix,
            temporal_stats=temp_stats,
            recurring_patterns=recurring_patterns,
            entropy_score=entropy_score,
            confidence_intervals=confidence_intervals,
            low_sample_warning=low_sample,
            backing_evidence_ids=backing_ids,
        )

    def _extract_recurring_patterns(self, evidence: List[EvidenceResponse]) -> List[RecurringPattern]:
        """Detect recurring sequence patterns (2-grams and 3-grams) in chronological evidence."""
        n = len(evidence)
        if n < 2:
            return []

        patterns_found: Dict[Tuple[StrategicCluster, ...], List[List[EvidenceResponse]]] = {}

        # Search for n-grams of size 2 and 3
        for k in (2, 3):
            if n < k:
                continue
            for i in range(n - k + 1):
                sub = evidence[i : i + k]
                key = tuple(e.cluster for e in sub)
                if key not in patterns_found:
                    patterns_found[key] = []
                patterns_found[key].append(sub)

        result: List[RecurringPattern] = []
        pattern_counter = 1

        for seq, occurrences in patterns_found.items():
            if len(occurrences) < 2:
                continue  # Only report recurring patterns (occurred at least twice)

            # Collect all backing evidence IDs for these occurrences
            evidence_ids = []
            occurrence_start_times = []
            for occ in occurrences:
                for item in occ:
                    if item.evidence_id not in evidence_ids:
                        evidence_ids.append(item.evidence_id)
                occurrence_start_times.append(occ[0].observation_time)

            # Calculate average interval between pattern occurrences
            occurrence_start_times.sort()
            if len(occurrence_start_times) > 1:
                intervals = [
                    (occurrence_start_times[j] - occurrence_start_times[j - 1]).total_seconds() / 86400.0
                    for j in range(1, len(occurrence_start_times))
                ]
                avg_interval = sum(intervals) / len(intervals)
            else:
                avg_interval = 0.0

            seq_names = " -> ".join([c.name for c in seq])
            pattern_id = f"PAT_{pattern_counter:03d}_{seq[0].name}_TO_{seq[-1].name}"

            result.append(
                RecurringPattern(
                    pattern_id=pattern_id,
                    sequence=list(seq),
                    occurrences=len(occurrences),
                    avg_interval_days=round(avg_interval, 2),
                    evidence_ids=evidence_ids,
                )
            )
            pattern_counter += 1

        # Sort patterns by occurrences descending
        result.sort(key=lambda x: x.occurrences, reverse=True)
        return result

    def _compute_confidence_intervals(
        self, cluster_counts: Dict[StrategicCluster, int], total_n: int
    ) -> List[ClusterConfidenceInterval]:
        """Compute Wilson Score 95% Confidence Intervals for cluster proportions."""
        z = 1.96  # 95% CI
        intervals: List[ClusterConfidenceInterval] = []

        for cluster, count in cluster_counts.items():
            p_hat = count / total_n
            denom = 1 + (z**2) / total_n
            center = (p_hat + (z**2) / (2 * total_n)) / denom
            spread = (z * math.sqrt((p_hat * (1 - p_hat) / total_n) + ((z**2) / (4 * (total_n**2))))) / denom

            ci_lower = max(0.0, center - spread)
            ci_upper = min(1.0, center + spread)

            intervals.append(
                ClusterConfidenceInterval(
                    cluster=cluster,
                    proportion=round(p_hat, 4),
                    ci_lower=round(ci_lower, 4),
                    ci_upper=round(ci_upper, 4),
                )
            )

        intervals.sort(key=lambda x: x.proportion, reverse=True)
        return intervals
