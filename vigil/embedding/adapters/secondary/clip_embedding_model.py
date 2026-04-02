from pathlib import Path
from typing import Final

import torch
from PIL import Image as PILImage
from transformers import CLIPModel, CLIPProcessor

from vigil.embedding.business_logic.models.embedded_track import Embedding
from vigil.shared_kernel.models.image import Image

_MODELS_DIR: Final[Path] = Path.home() / ".cache" / "vigil" / "models"
_CLIP_MODEL_NAME: Final[str] = "openai/clip-vit-base-patch32"


class ClipEmbeddingModel:
    """EmbeddingModel adapter backed by CLIP ViT-B/32.

    On first instantiation the model weights are downloaded from
    HuggingFace and stored in ``~/.cache/vigil/models``.  Subsequent
    instantiations load from that directory without network access.
    """

    def __init__(self) -> None:
        _MODELS_DIR.mkdir(parents=True, exist_ok=True)
        self._processor: CLIPProcessor = CLIPProcessor.from_pretrained(  # type: ignore[assignment]
            _CLIP_MODEL_NAME, cache_dir=_MODELS_DIR
        )
        self._model: CLIPModel = CLIPModel.from_pretrained(  # type: ignore[assignment]
            _CLIP_MODEL_NAME, cache_dir=_MODELS_DIR
        )
        self._model.eval()

    def embed(self, description: str) -> Embedding:
        """Return a normalized CLIP text embedding for the given description."""
        inputs = self._processor(text=description, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            features: torch.Tensor = self._model.get_text_features(**inputs)
        normalized = features / features.norm(dim=-1, keepdim=True)
        return Embedding(tuple(float(x) for x in normalized.squeeze().cpu().numpy()))

    @staticmethod
    def _pad_to_square(image: PILImage.Image) -> PILImage.Image:
        """Pad image to a square with black, centering the original content."""
        w, h = image.size
        side = max(w, h)
        padded = PILImage.new("RGB", (side, side), (0, 0, 0))
        padded.paste(image, ((side - w) // 2, (side - h) // 2))
        return padded

    def embed_images(self, batch: list[Image]) -> list[Embedding]:
        """Return normalized CLIP image embeddings for a batch of crops."""
        pil_images = [self._pad_to_square(PILImage.fromarray(img.numpy())) for img in batch]
        inputs = self._processor(images=pil_images, return_tensors="pt", padding=True)
        with torch.no_grad():
            features: torch.Tensor = self._model.get_image_features(**inputs)
        normalized = features / features.norm(dim=-1, keepdim=True)
        return [Embedding(tuple(float(x) for x in row.cpu().numpy())) for row in normalized]
