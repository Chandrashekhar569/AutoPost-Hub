from __future__ import annotations
import base64
import logging
from pathlib import Path

LOG = logging.getLogger(__name__)

def generate_image_bytes(prompt: str, width: int, height: int, image_model: str) -> bytes:
    """Calls OpenAI Image API and returns raw PNG bytes."""
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError("openai Python package is required. Install with `pip install openai`. ") from e

    client = OpenAI()
    LOG.info("Generating image via %s ...", image_model)
    img = client.images.generate(
        model=image_model,
        prompt=prompt,
        size=f"{width}x{height}",
        n=1
    )
    
    b64 = img.data[0].b64_json
    return base64.b64decode(b64)

def save_png(png_bytes: bytes, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(png_bytes)
