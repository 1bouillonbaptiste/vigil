from typing import Protocol

from vigil.embedding.business_logic.models.embedded_track import Embedding
from vigil.embedding.business_logic.models.image import Image


class EmbeddingModel(Protocol):
    """Abstract embedding model."""

    def embed(self, description: str) -> Embedding:
        """Compute and return a text embedding."""
        ...

    def embed_image_batch(self, data: list[Image]) -> list[Embedding]:
        """Compute and return image embeddings for a batch of crops."""
        ...
