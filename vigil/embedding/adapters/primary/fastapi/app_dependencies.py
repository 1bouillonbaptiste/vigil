from fastapi import Depends
from starlette.requests import Request

from vigil.embedding.business_logic.gateways.embedded_track_repository import EmbeddedTrackRepository
from vigil.embedding.business_logic.gateways.embedding_model import EmbeddingModel
from vigil.embedding.business_logic.use_cases.find_similar_tracks import FindSimilarTracksUseCase


def _get_embedded_track_repository(request: Request) -> EmbeddedTrackRepository:
    return request.app.state.embedded_track_repository


def _get_embedding_model(request: Request) -> EmbeddingModel:
    return request.app.state.embedding_model


def get_find_similar_tracks_use_case(
    repository=Depends(_get_embedded_track_repository), model=Depends(_get_embedding_model)
) -> FindSimilarTracksUseCase:
    """Build the find similar tracks use case."""
    return FindSimilarTracksUseCase(repository=repository, model=model)
