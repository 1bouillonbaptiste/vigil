from vigil.adapters.secondary.in_memory_domain_event_publisher import InMemoryDomainEventPublisher
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
    publisher: InMemoryDomainEventPublisher[FrameAnalyzed] = InMemoryDomainEventPublisher()
    received: list[FrameAnalyzed] = []
    publisher.subscribe(received.append)

    publisher.publish(_make_event())

    assert len(received) == 1


def test_handler_receives_the_published_event() -> None:
    publisher: InMemoryDomainEventPublisher[FrameAnalyzed] = InMemoryDomainEventPublisher()
    received: list[FrameAnalyzed] = []
    publisher.subscribe(received.append)
    event = _make_event(position=3)

    publisher.publish(event)

    assert received[0] is event


def test_multiple_handlers_all_receive_the_event() -> None:
    publisher: InMemoryDomainEventPublisher[FrameAnalyzed] = InMemoryDomainEventPublisher()
    first: list[FrameAnalyzed] = []
    second: list[FrameAnalyzed] = []
    publisher.subscribe(first.append)
    publisher.subscribe(second.append)

    publisher.publish(_make_event())

    assert len(first) == 1
    assert len(second) == 1


def test_no_handler_subscribed_publish_does_nothing() -> None:
    publisher: InMemoryDomainEventPublisher[FrameAnalyzed] = InMemoryDomainEventPublisher()

    publisher.publish(_make_event())  # must not raise
