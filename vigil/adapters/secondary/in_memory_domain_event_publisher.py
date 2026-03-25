from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from vigil.business_logic.models.domain_event import DomainEvent

T = TypeVar("T", bound=DomainEvent)


@dataclass
class InMemoryDomainEventPublisher(Generic[T]):
    """Dispatch domain events synchronously to in-process subscribers."""

    _handlers: list[Callable[[T], None]] = field(default_factory=list, init=False)

    def subscribe(self, handler: Callable[[T], None]) -> None:
        """Register a handler to be called on every published event."""
        self._handlers.append(handler)

    def publish(self, event: T) -> None:
        """Call all registered handlers with the event."""
        for handler in self._handlers:
            handler(event)
