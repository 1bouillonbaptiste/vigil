from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from vigil.embedding.adapters.primary.fastapi.app_dependencies import get_find_similar_tracks_use_case

router = APIRouter()


class QueryByDescriptionRequest(BaseModel):
    """Model for query by description request."""

    description: str
    """Description of the tracks to query from the database."""


class TrackMatchResponse(BaseModel):
    """A track ID with its similarity score."""

    id: UUID
    score: float


class QueryByDescriptionContent(BaseModel):
    """Model for query by description content."""

    tracks: list[TrackMatchResponse]
    """Tracks matching the description, with their similarity scores."""


class QueryByDescriptionResponse(BaseModel):
    """Model for query by description response."""

    status: str
    content: QueryByDescriptionContent | None = None
    error: str | None = None


@router.get("/tracks/by-description")
def query_by_description(
    description: str,
    use_case=Depends(get_find_similar_tracks_use_case),
) -> QueryByDescriptionResponse:
    """Return tracks matching the given description with similarity scores."""
    matches = use_case.execute(description=description)
    return QueryByDescriptionResponse(
        status="success",
        content=QueryByDescriptionContent(
            tracks=[TrackMatchResponse(id=match.id, score=match.score) for match in matches]
        ),
    )
