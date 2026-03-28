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
        return np.dot(first, second) / (np.linalg.norm(first) * np.linalg.norm(second))


@dataclass(frozen=True)
class EmbeddedTrack:
    """Aggregate for tracks in the embedding context."""

    id: UUID
    """Track unique identifier, shared across contexts."""

    detections: tuple[Embedding, ...]
    """Detections embeddings."""

    def similarity(self, embedding: Embedding) -> float:
        """How close a track is to an embedding."""
        similarities: list[float] = [embedding.cosine(detection) for detection in self.detections]
        return sum(similarities) / len(similarities)
