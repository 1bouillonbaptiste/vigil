from collections.abc import Callable
from typing import Protocol, TypeVar

from vigil.shared_kernel.models.domain_event import DomainEvent

T = TypeVar("T", bound=DomainEvent)


class DomainEventPublisher(Protocol):
    """Publish domain events to registered handlers."""

    def publish(self, event: T) -> None:
        """Dispatch an event to all registered handlers."""
        ...

    def subscribe(self, handler: Callable[[T], None]) -> None:
        """Register a handler (event type inferred from annotation)."""
        ...
