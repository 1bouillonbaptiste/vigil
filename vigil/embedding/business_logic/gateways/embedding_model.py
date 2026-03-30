from typing import Protocol

from vigil.embedding.business_logic.models.embedded_track import Embedding
from vigil.shared_kernel.models.image import Image


class EmbeddingModel(Protocol):
    """Abstract embedding model."""

    def embed(self, description: str) -> Embedding:
        """Compute and return a text embedding."""
        ...

    def embed_images(self, batch: list[Image]) -> list[Embedding]:
        """Compute and return image embeddings for a batch of crops."""
        ...
