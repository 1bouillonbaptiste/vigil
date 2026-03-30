from vigil.embedding.business_logic.gateways.embedding_model import EmbeddingModel
from vigil.embedding.business_logic.models.embedded_track import Embedding


class FakeEmbeddingModel(EmbeddingModel):
    """Placeholder embedding model that always returns a fixed embedding."""

    def embed(self, description: str) -> Embedding:
        """Placeholder embedding model that always returns a fixed embedding."""
        return Embedding((0.5, 0.5))
