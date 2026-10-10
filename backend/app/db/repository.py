from uuid import UUID
from typing import TypeVar, Generic, Optional

T = TypeVar('T')

class InMemoryRepository(Generic[T]):
    """
    In-memory development storage for testing contracts without a database.
    WARNING: Data is lost on server restart. Do not use for persistence.
    """
    def __init__(self):
        self._store: dict[UUID, T] = {}

    def get(self, item_id: UUID) -> Optional[T]:
        return self._store.get(item_id)

    def add(self, item_id: UUID, item: T) -> bool:
        if item_id in self._store:
            return False
        self._store[item_id] = item
        return True

    def update(self, item_id: UUID, item: T) -> bool:
        if item_id not in self._store:
            return False
        self._store[item_id] = item
        return True

    def list_all(self) -> list[T]:
        return list(self._store.values())

    def clear(self):
        """Used to isolate tests"""
        self._store.clear()

# Global instances for development stub
from app.schemas.competitor import CompetitorResponse
from app.schemas.prediction import PredictionResponse
from app.schemas.evidence import EvidenceResponse

competitor_repo: InMemoryRepository[CompetitorResponse] = InMemoryRepository()
prediction_repo: InMemoryRepository[PredictionResponse] = InMemoryRepository()
evidence_repo: InMemoryRepository[EvidenceResponse] = InMemoryRepository()
