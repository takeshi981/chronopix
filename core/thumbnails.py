import os
from PIL import Image

THUMB_DIR = os.path.abspath(os.path.join("data", "thumbs"))

def ensure_thumb_dir():
    os.makedirs(THUMB_DIR, exist_ok=True)

def generate_thumbnail(src_path: str) -> str:
    ensure_thumb_dir()
    filename = os.path.basename(src_path)
    dst_path = os.path.abspath(os.path.join(THUMB_DIR, filename))

    img = Image.open(src_path)
    img.thumbnail((512, 512))
    img.save(dst_path, "JPEG", quality=85)

    return dst_path
