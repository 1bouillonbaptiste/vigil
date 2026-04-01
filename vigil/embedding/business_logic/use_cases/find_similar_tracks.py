from vigil.embedding.business_logic.gateways.embedded_track_repository import EmbeddedTrackRepository
from vigil.embedding.business_logic.gateways.embedding_model import EmbeddingModel
from vigil.embedding.business_logic.models.track_match import TrackMatch
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

    def execute(self, description: str, min_probability: float = 0.6) -> list[TrackMatch]:
        """Return tracks exceeding min_probability for the given description."""
        if not description:
            return [TrackMatch(id=track.id, score=1.0) for track in self._repository.list_tracks()]

        query = f"This photo shows {description}"
        text_embedding = self._model.embed(query)

        result: list[TrackMatch] = []
        for track in self._repository.list_tracks():
            if not track.detections:
                continue
            probs = [self._matcher.probability(det, text_embedding) for det in track.detections]
            score = sum(probs) / len(probs)
            if score >= min_probability:
                result.append(TrackMatch(id=track.id, score=score))
        return result
