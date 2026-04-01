from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class TrackMatch:
    """A track that matched a description query, with its similarity score."""

    id: UUID
    score: float
