from pathlib import Path

import numpy as np
import pytest
from PIL import Image as PILImage

from vigil.embedding.adapters.secondary.clip_embedding_model import ClipEmbeddingModel
from vigil.shared_kernel.models.image import Image

_DATA_DIR = Path(__file__).parent.parent.parent / "data"


@pytest.fixture(scope="module")
def model() -> ClipEmbeddingModel:
    """Scope-level fixture to keep the model cached."""
    return ClipEmbeddingModel()

@pytest.fixture(scope="function")
def realistic_cat_image(test_data_dir: Path) -> Image:
    pil_image = PILImage.open(_DATA_DIR / "cat.jpg")
    return Image(np.array(pil_image, dtype=np.uint8))


def make_image(height: int = 64, width: int = 64) -> Image:
    return Image(np.zeros((height, width, 3), dtype=np.uint8))


def test_should_embed_text_description(model: ClipEmbeddingModel) -> None:
    embedding = model.embed("a person walking in the street")

    assert len(embedding.numpy()) == 512


def test_should_embed_image_batch(model: ClipEmbeddingModel) -> None:
    embeddings = model.embed_images([make_image(), make_image()])

    assert len(embeddings) == 2
    assert len(embeddings[0].numpy()) == 512


def test_similar_descriptions_should_have_higher_similarity_than_dissimilar(model: ClipEmbeddingModel) -> None:
    cat = model.embed("a cat sitting on a mat")
    another_cat = model.embed("a cat resting on a rug")
    car = model.embed("a red sports car on the highway")

    assert cat.cosine(another_cat) > cat.cosine(car)


def test_cat_image_should_be_closer_to_cat_description_than_car_description(model: ClipEmbeddingModel, realistic_cat_image: Image) -> None:
    [cat_embedding] = model.embed_images([realistic_cat_image])

    cat_text = model.embed("a sitting cat and looking at me")
    assert cat_embedding.cosine(cat_text) > 0.9


    car_text = model.embed("two blue cars")
    assert cat_embedding.cosine(cat_text) > cat_embedding.cosine(car_text)
