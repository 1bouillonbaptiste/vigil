from vigil.adapters.secondary.in_memory_event_bus import InMemoryEventBus
from vigil.business_logic.models.domain_event import DomainEvent
from vigil.business_logic.models.frame_analyzed import FrameAnalyzed
from vigil.business_logic.models.video_source import VideoSource
from vigil.business_logic.services.id_factory import IdFactory

VIDEO_ID = IdFactory.new_video_id(VideoSource(uri="test-video"))


def _make_event(position: int = 0) -> FrameAnalyzed:
    return FrameAnalyzed(
        video_id=VIDEO_ID,
        frame_id=IdFactory.new_frame_id(video_id=VIDEO_ID, position=position),
        position=position,
    )


def test_subscribed_handler_is_called_on_publish() -> None:
    bus = InMemoryEventBus()
    received: list[DomainEvent] = []
    bus.subscribe(received.append)

    bus.publish(_make_event())

    assert len(received) == 1


def test_handler_receives_the_published_event() -> None:
    bus = InMemoryEventBus()
    received: list[DomainEvent] = []
    bus.subscribe(received.append)
    event = _make_event(position=3)

    bus.publish(event)

    assert received[0] is event


def test_multiple_handlers_all_receive_the_event() -> None:
    bus = InMemoryEventBus()
    first: list[DomainEvent] = []
    second: list[DomainEvent] = []
    bus.subscribe(first.append)
    bus.subscribe(second.append)

    bus.publish(_make_event())

    assert len(first) == 1
    assert len(second) == 1


def test_no_handler_subscribed_publish_does_nothing() -> None:
    bus = InMemoryEventBus()

    bus.publish(_make_event())  # must not raise
