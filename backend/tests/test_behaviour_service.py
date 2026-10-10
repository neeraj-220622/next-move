import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.schemas.evidence import EvidenceResponse, Provenance, ValidationStatus
from app.schemas.cluster import StrategicCluster
from app.services.behaviour_service import BehaviourService


@pytest.fixture
def service():
    return BehaviourService()


@pytest.fixture
def competitor_id():
    return uuid4()


def create_evidence(
    competitor_id,
    cluster: StrategicCluster,
    obs_time: datetime,
    provenance: Provenance = Provenance.VERIFIED,
) -> EvidenceResponse:
    return EvidenceResponse(
        evidence_id=uuid4(),
        competitor_id=competitor_id,
        cluster=cluster,
        description=f"Observed action in {cluster.value}",
        observation_time=obs_time,
        provenance=provenance,
        validation_status=ValidationStatus.VALIDATED,
    )


def test_empty_evidence(service, competitor_id):
    profile = service.analyze_evidence(competitor_id, [])
    assert profile.competitor_id == competitor_id
    assert profile.sample_size == 0
    assert profile.low_sample_warning is True
    assert profile.entropy_score == 0.0
    assert len(profile.cluster_frequencies) == 0
    assert len(profile.transition_matrix) == 0
    assert len(profile.recurring_patterns) == 0
    assert len(profile.backing_evidence_ids) == 0


def test_single_evidence(service, competitor_id):
    now = datetime.now(timezone.utc)
    ev = create_evidence(competitor_id, StrategicCluster.PRICING_PROMOTIONS, now)
    profile = service.analyze_evidence(competitor_id, [ev])

    assert profile.sample_size == 1
    assert profile.low_sample_warning is True
    assert profile.provenance_breakdown.verified == 1
    assert profile.provenance_breakdown.synthetic == 0
    assert len(profile.cluster_frequencies) == 1
    assert profile.cluster_frequencies[0].cluster == StrategicCluster.PRICING_PROMOTIONS
    assert profile.cluster_frequencies[0].percentage == 100.0
    assert len(profile.transition_matrix) == 0
    assert profile.temporal_stats.time_span_days == 0.0
    assert len(profile.backing_evidence_ids) == 1


def test_multiple_evidence_and_transitions(service, competitor_id):
    base_time = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    t1 = base_time
    t2 = base_time + timedelta(days=2)
    t3 = base_time + timedelta(days=5)
    t4 = base_time + timedelta(days=7)

    e1 = create_evidence(competitor_id, StrategicCluster.PRICING_PROMOTIONS, t1, Provenance.VERIFIED)
    e2 = create_evidence(competitor_id, StrategicCluster.LOGISTICS_FULFILLMENT, t2, Provenance.UNVERIFIED)
    e3 = create_evidence(competitor_id, StrategicCluster.PRICING_PROMOTIONS, t3, Provenance.SYNTHETIC)
    e4 = create_evidence(competitor_id, StrategicCluster.LOGISTICS_FULFILLMENT, t4, Provenance.VERIFIED)

    profile = service.analyze_evidence(competitor_id, [e1, e2, e3, e4])

    assert profile.sample_size == 4
    assert profile.low_sample_warning is True  # sample_size < 5
    assert profile.provenance_breakdown.verified == 2
    assert profile.provenance_breakdown.unverified == 1
    assert profile.provenance_breakdown.synthetic == 1

    # Frequency check: 2 Pricing, 2 Logistics (50% each)
    assert len(profile.cluster_frequencies) == 2
    for cf in profile.cluster_frequencies:
        assert cf.percentage == 50.0

    # Temporal stats check: total span 7 days
    assert profile.temporal_stats.time_span_days == 7.0
    assert profile.temporal_stats.first_observed == t1
    assert profile.temporal_stats.last_observed == t4

    # Transition matrix check:
    # Transitions: Pricing -> Logistics (2 times), Logistics -> Pricing (1 time)
    assert len(profile.transition_matrix) == 2
    pricing_to_logistics = next(
        t for t in profile.transition_matrix
        if t.from_cluster == StrategicCluster.PRICING_PROMOTIONS and t.to_cluster == StrategicCluster.LOGISTICS_FULFILLMENT
    )
    assert pricing_to_logistics.count == 2
    assert pricing_to_logistics.probability == 1.0  # 100% of transitions from Pricing went to Logistics

    logistics_to_pricing = next(
        t for t in profile.transition_matrix
        if t.from_cluster == StrategicCluster.LOGISTICS_FULFILLMENT and t.to_cluster == StrategicCluster.PRICING_PROMOTIONS
    )
    assert logistics_to_pricing.count == 1
    assert logistics_to_pricing.probability == 1.0


def test_recurring_patterns(service, competitor_id):
    base_time = datetime(2025, 2, 1, 0, 0, tzinfo=timezone.utc)
    # Sequence: (Pricing -> Logistics -> Product) repeated twice
    clusters = [
        StrategicCluster.PRICING_PROMOTIONS,
        StrategicCluster.LOGISTICS_FULFILLMENT,
        StrategicCluster.PRODUCT_ECOSYSTEM,
        StrategicCluster.PRICING_PROMOTIONS,
        StrategicCluster.LOGISTICS_FULFILLMENT,
        StrategicCluster.PRODUCT_ECOSYSTEM,
    ]
    ev_list = [
        create_evidence(competitor_id, c, base_time + timedelta(days=i * 3))
        for i, c in enumerate(clusters)
    ]

    profile = service.analyze_evidence(competitor_id, ev_list)

    assert profile.sample_size == 6
    assert profile.low_sample_warning is False  # 6 >= 5

    # Should detect recurring patterns (e.g. Pricing -> Logistics)
    assert len(profile.recurring_patterns) > 0
    pattern_seqs = [p.sequence for p in profile.recurring_patterns]
    assert [StrategicCluster.PRICING_PROMOTIONS, StrategicCluster.LOGISTICS_FULFILLMENT] in pattern_seqs
    assert [StrategicCluster.PRICING_PROMOTIONS, StrategicCluster.LOGISTICS_FULFILLMENT, StrategicCluster.PRODUCT_ECOSYSTEM] in pattern_seqs


def test_date_filtering(service, competitor_id):
    t1 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t2 = datetime(2025, 2, 1, tzinfo=timezone.utc)
    t3 = datetime(2025, 3, 1, tzinfo=timezone.utc)

    e1 = create_evidence(competitor_id, StrategicCluster.PRICING_PROMOTIONS, t1)
    e2 = create_evidence(competitor_id, StrategicCluster.LOGISTICS_FULFILLMENT, t2)
    e3 = create_evidence(competitor_id, StrategicCluster.PRODUCT_ECOSYSTEM, t3)

    # Filter with cutoff_date = t2
    profile = service.analyze_evidence(competitor_id, [e1, e2, e3], cutoff_date=t2)
    assert profile.sample_size == 2
    assert profile.backing_evidence_ids == [e1.evidence_id, e2.evidence_id]

    # Filter with start_date = t2
    profile_start = service.analyze_evidence(competitor_id, [e1, e2, e3], start_date=t2)
    assert profile_start.sample_size == 2
    assert profile_start.backing_evidence_ids == [e2.evidence_id, e3.evidence_id]


def test_entropy(service, competitor_id):
    now = datetime.now(timezone.utc)
    # All same cluster -> entropy 0
    evs_same = [create_evidence(competitor_id, StrategicCluster.PRICING_PROMOTIONS, now + timedelta(days=i)) for i in range(4)]
    profile_same = service.analyze_evidence(competitor_id, evs_same)
    assert profile_same.entropy_score == 0.0

    # Equal split between 2 clusters -> entropy = 1.0 bit
    evs_mixed = [
        create_evidence(competitor_id, StrategicCluster.PRICING_PROMOTIONS, now),
        create_evidence(competitor_id, StrategicCluster.LOGISTICS_FULFILLMENT, now + timedelta(days=1)),
    ]
    profile_mixed = service.analyze_evidence(competitor_id, evs_mixed)
    assert profile_mixed.entropy_score == 1.0
