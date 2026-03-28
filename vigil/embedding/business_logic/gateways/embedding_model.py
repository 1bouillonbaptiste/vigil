from typing import Protocol

from vigil.embedding.business_logic.models.embedded_track import Embedding


class EmbeddingModel(Protocol):
    """Abstract embedding model."""

    def embed(self, description: str) -> Embedding:
        """Compute and return an embedding."""
        ...
