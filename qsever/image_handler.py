import base64
import io
from pathlib import Path
from typing import Optional

from PIL import Image

from .exceptions import ImageNotFound


class ImageData:
    def __init__(self, data: str, mime_type: str, filename: str):
        self.data = data
        self.mime_type = mime_type
        self.filename = filename


class ImageHandler:
    SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

    def __init__(self, images_dir: Path, compress_threshold: int = 512_000, 
                 max_dimension: int = 1920, jpeg_quality: int = 85):
        self.images_dir = images_dir
        self.images_dir.mkdir(exist_ok=True)
        self.compress_threshold = compress_threshold
        self.max_dimension = max_dimension
        self.jpeg_quality = jpeg_quality

    def list_images(self) -> list[Path]:
        if not self.images_dir.exists():
            return []
        return sorted([
            f for f in self.images_dir.iterdir()
            if f.is_file() and f.suffix.lower() in self.SUPPORTED_FORMATS
        ])

    def load_image(self, filename: str) -> ImageData:
        path = self.images_dir / filename
        if not path.exists():
            path = Path(filename)
        if not path.exists():
            raise ImageNotFound(f"找不到图片文件: {filename}")

        suffix = path.suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }
        mime_type = mime_map.get(suffix, "image/png")

        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")

        return ImageData(data=data, mime_type=mime_type, filename=path.name)

    def compress_image(self, image_data: bytes, filename: str) -> bytes:
        if len(image_data) < self.compress_threshold:
            return image_data
        
        suffix = Path(filename).suffix.lower()
        if suffix == ".gif":
            return image_data
        
        try:
            img = Image.open(io.BytesIO(image_data))
            
            if img.width > self.max_dimension or img.height > self.max_dimension:
                img.thumbnail((self.max_dimension, self.max_dimension), Image.LANCZOS)
            
            buf = io.BytesIO()
            if suffix in (".jpg", ".jpeg"):
                img.save(buf, format="JPEG", quality=self.jpeg_quality, optimize=True)
            elif suffix == ".png":
                img.save(buf, format="PNG", optimize=True)
            elif suffix == ".webp":
                img.save(buf, format="WEBP", quality=self.jpeg_quality)
            else:
                return image_data
            
            compressed = buf.getvalue()
            return compressed if len(compressed) < len(image_data) else image_data
        except Exception:
            return image_data

    def build_vision_content_from_data(self, text: str, image_data_list: list[ImageData]) -> list[dict]:
        content = []
        if text:
            content.append({"type": "text", "text": text})
        for img in image_data_list:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{img.mime_type};base64,{img.data}"
                }
            })
        return content

    def build_vision_content(self, text: str, image_files: list[str]) -> list[dict]:
        content = []
        if text:
            content.append({"type": "text", "text": text})
        for img_file in image_files:
            img = self.load_image(img_file)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{img.mime_type};base64,{img.data}"
                }
            })
        return content
