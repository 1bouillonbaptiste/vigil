from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from vigil.embedding.adapters.primary.fastapi.app_dependencies import get_find_similar_tracks_use_case

router = APIRouter()


class QueryByDescriptionRequest(BaseModel):
    """Model for query by description request."""

    description: str
    """Description of the tracks to query from the database."""


class QueryByDescriptionContent(BaseModel):
    """Model for query by description content."""

    tracks: tuple[UUID, ...]
    """IDs of the tracks matching the description."""


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
    """Return IDs of embedded tracks matching the given description."""
    tracks = use_case.execute(description=description)
    return QueryByDescriptionResponse(
        status="success",
        content=QueryByDescriptionContent(tracks=tuple(track.id for track in tracks)),
    )
