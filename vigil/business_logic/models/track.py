from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Track:
    """Represent a track."""

    id: UUID
