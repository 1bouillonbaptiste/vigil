from vigil.embedding.business_logic.gateways.embedded_track_repository import EmbeddedTrackRepository
from vigil.embedding.business_logic.gateways.embedding_model import EmbeddingModel
from vigil.embedding.business_logic.models.embedded_track import EmbeddedTrack
from vigil.embedding.business_logic.services.embedding_matcher import EmbeddingMatcher


class FindSimilarTracksUseCase:
    """Retrieves similar tracks from the database."""

    def __init__(
        self,
        repository: EmbeddedTrackRepository,
        model: EmbeddingModel,
        matcher: EmbeddingMatcher,
    ) -> None:
        self._repository = repository
        self._model = model
        self._matcher = matcher

    def execute(self, description: str, min_probability: float = 0.6) -> list[EmbeddedTrack]:
        """Return tracks exceeding min_probability for the given description."""
        if not description:
            return self._repository.list_tracks()
        text_embedding = self._model.embed(description)

        result: list[EmbeddedTrack] = []
        for track in self._repository.list_tracks():
            if not track.detections:
                continue
            probs = [self._matcher.probability(det, text_embedding) for det in track.detections]
            if sum(probs) / len(probs) >= min_probability:
                result.append(track)
        return result
