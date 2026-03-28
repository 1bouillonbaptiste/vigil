from vigil.embedding.business_logic.gateways.embedded_track_repository import EmbeddedTrackRepository
from vigil.embedding.business_logic.gateways.embedding_model import EmbeddingModel
from vigil.embedding.business_logic.models.embedded_track import EmbeddedTrack


class FindSimilarTracksUseCase:
    """Retrieves similar tracks from the database."""

    def __init__(self, repository: EmbeddedTrackRepository, model: EmbeddingModel) -> None:
        self._repository = repository
        self._model = model

    def execute(self, description: str, min_similarity: float = 0.9) -> list[EmbeddedTrack]:
        """Execute the use case given an embedding."""
        embedding = self._model.embed(description)

        result: list[EmbeddedTrack] = []
        for track in self._repository.list_tracks():
            if track.similarity(embedding) > min_similarity:
                result.append(track)
        return result
