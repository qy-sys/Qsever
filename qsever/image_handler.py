import base64
from pathlib import Path
from typing import Optional

from .exceptions import ImageNotFound


class ImageData:
    def __init__(self, data: str, mime_type: str, filename: str):
        self.data = data
        self.mime_type = mime_type
        self.filename = filename


class ImageHandler:
    SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

    def __init__(self, images_dir: Path):
        self.images_dir = images_dir
        self.images_dir.mkdir(exist_ok=True)

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
