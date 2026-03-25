from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""

    event_id: UUID = field(default_factory=uuid4, kw_only=True)
    occurred_on: datetime = field(default_factory=lambda: datetime.now(UTC), kw_only=True)
