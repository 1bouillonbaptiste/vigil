from collections.abc import Callable
from typing import Protocol

from vigil.business_logic.models.domain_event import DomainEvent


class DomainEventBus(Protocol):
    """Publish domain events to registered handlers."""

    def publish(self, event: DomainEvent) -> None:
        """Dispatch an event to all registered handlers."""
        ...

    def subscribe(self, handler: Callable[[DomainEvent], None]) -> None:
        """Register a handler to receive future events."""
        ...
