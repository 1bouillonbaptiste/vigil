from vigil.embedding.business_logic.gateways.embedding_model import EmbeddingModel
from vigil.embedding.business_logic.models.embedded_track import Embedding
from vigil.shared_kernel.models.image import Image


class FakeEmbeddingModel(EmbeddingModel):
    """Placeholder embedding model that always returns a fixed embedding."""

    def embed(self, description: str) -> Embedding:
        """Placeholder embedding model that always returns a fixed embedding."""
        return Embedding((0.5, 0.5))

    def embed_images(self, batch: list[Image]) -> list[Embedding]:
        """Return a fixed embedding for each image in the batch."""
        return [Embedding((0.5, 0.5)) for _ in batch]
