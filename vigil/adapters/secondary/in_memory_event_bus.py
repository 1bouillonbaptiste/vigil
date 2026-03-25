from collections.abc import Callable
from dataclasses import dataclass, field

from vigil.business_logic.models.domain_event import DomainEvent


@dataclass
class InMemoryEventBus:
    """Dispatch domain events synchronously to in-process subscribers."""

    _handlers: list[Callable[[DomainEvent], None]] = field(default_factory=list, init=False)

    def subscribe(self, handler: Callable[[DomainEvent], None]) -> None:
        """Register a handler to be called on every published event."""
        self._handlers.append(handler)

    def publish(self, event: DomainEvent) -> None:
        """Call all registered handlers with the event."""
        for handler in self._handlers:
            handler(event)
