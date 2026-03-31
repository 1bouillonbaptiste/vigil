from dataclasses import dataclass
from uuid import UUID

import numpy as np
import numpy.typing as npt


@dataclass(frozen=True)
class Embedding:
    """Wrapper for a numpy embedding."""

    _data: tuple[float, ...]

    def numpy(self) -> npt.NDArray[np.float32]:
        """Cast embedding to numpy array."""
        return np.array(self._data)

    def cosine(self, embedding: "Embedding") -> float:
        """Cosine similarity between two embeddings."""
        first = self.numpy()
        second = embedding.numpy()
        norm = np.linalg.norm(first) * np.linalg.norm(second)
        if norm == 0:
            return 0
        return np.dot(first, second) / norm


@dataclass(frozen=True)
class EmbeddedTrack:
    """Aggregate for tracks in the embedding context."""

    id: UUID
    """Track unique identifier, shared across contexts."""

    detections: tuple[Embedding, ...]
    """Detections embeddings."""
