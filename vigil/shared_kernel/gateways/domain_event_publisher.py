from collections.abc import Callable
from typing import Protocol

from vigil.shared_kernel.models.domain_event import DomainEvent


class DomainEventPublisher(Protocol):
    """Publish domain events to registered handlers."""

    def publish(self, event: DomainEvent) -> None:
        """Dispatch an event to all registered handlers."""
        ...

    def subscribe(self, handler: Callable[[DomainEvent], None]) -> None:
        """Register a handler (event type inferred from annotation)."""
        ...
