import inspect
from collections import defaultdict
from collections.abc import Callable
from typing import TypeVar, get_type_hints

from vigil.shared_kernel.gateways.domain_event_bus import DomainEventBus
from vigil.shared_kernel.models.domain_event import DomainEvent

T = TypeVar("T", bound=DomainEvent)
"""A concrete domain event."""

Handler = Callable[[T], None]
"""An interactor that processes domain events."""


def _event_type_of(handler: Callable[[T], None]) -> type[DomainEvent]:
    first_param = next(iter(inspect.signature(handler).parameters))
    return get_type_hints(handler)[first_param]


class InMemoryEventBus(DomainEventBus):
    """Dispatch domain events synchronously to in-process subscribers."""

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[Handler]] = defaultdict(list)

    def subscribe(self, handler: Handler) -> None:
        """Register a handler (event type inferred from annotation)."""
        self._handlers[_event_type_of(handler)].append(handler)  # type: ignore[arg-type]

    def publish(self, event: T) -> None:
        """Call all registered handlers for the event's type."""
        for handler in self._handlers[type(event)]:
            handler(event)
