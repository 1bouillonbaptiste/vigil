from dataclasses import dataclass

import pytest

from vigil.shared_kernel.gateways.in_memory_event_publisher import InMemoryEventPublisher
from vigil.shared_kernel.models.domain_event import DomainEvent


@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    """Dummy domain event."""

    order_id: str


@dataclass(frozen=True)
class OrderCancelled(DomainEvent):
    """Dummy domain event."""

    order_id: str


@dataclass
class ThisContext:
    """Context for testing the in memory event bus."""

    bus: InMemoryEventPublisher
    received: list[DomainEvent]


@pytest.fixture
def this_context() -> ThisContext:
    return ThisContext(bus=InMemoryEventPublisher(), received=[])


def test_should_call_handler_when_matching_event_is_published(this_context: ThisContext):
    # Given
    def _on_order_placed(event: OrderPlaced) -> None:
        this_context.received.append(event)

    this_context.bus.subscribe(_on_order_placed)

    # When
    event = OrderPlaced(order_id="123")
    this_context.bus.publish(event)

    # Then
    assert this_context.received == [event]


def test_should_not_call_handler_for_different_event_type(this_context: ThisContext):
    # Given
    def _on_order_placed(event: OrderPlaced) -> None:
        this_context.received.append(event)

    this_context.bus.subscribe(_on_order_placed)

    # When
    this_context.bus.publish(OrderCancelled(order_id="123"))

    # Then
    assert this_context.received == []


def test_should_call_multiple_handlers_for_same_event_type(this_context: ThisContext):
    # Given
    calls: list[str] = []

    def _first_handler(event: OrderPlaced) -> None:
        calls.append("first")

    def _second_handler(event: OrderPlaced) -> None:
        calls.append("second")

    this_context.bus.subscribe(_first_handler)
    this_context.bus.subscribe(_second_handler)

    # When
    this_context.bus.publish(OrderPlaced(order_id="123"))

    # Then
    assert calls == ["first", "second"]
