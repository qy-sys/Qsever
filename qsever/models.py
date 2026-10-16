from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelInfo:
    id: str
    display_name: str
    input_price: float = 0
    output_price: float = 0
    is_free: bool = False
    supports_vision: bool = True
    speed_tier: int = 2
    notes: str = ""


class ModelRegistry:
    """模型注册表 — 从配置动态加载"""

    _models: list[ModelInfo] = []
    _model_map: dict[str, ModelInfo] = {}

    @classmethod
    def load_from_config(cls, model_ids: list[str], default_model: str = ""):
        cls._models = []
        cls._model_map = {}
        for mid in model_ids:
            mid = mid.strip()
            if not mid:
                continue
            info = ModelInfo(id=mid, display_name=mid)
            cls._models.append(info)
            cls._model_map[mid] = info

    @classmethod
    def get(cls, model_id: str) -> Optional[ModelInfo]:
        return cls._model_map.get(model_id)

    @classmethod
    def get_default(cls) -> Optional[ModelInfo]:
        return cls._models[0] if cls._models else None

    @classmethod
    def get_fastest(cls) -> Optional[ModelInfo]:
        return cls._models[0] if cls._models else None

    @classmethod
    def get_free(cls) -> Optional[ModelInfo]:
        free = [m for m in cls._models if m.is_free]
        return free[0] if free else (cls._models[0] if cls._models else None)

    @classmethod
    def list_all(cls) -> list[ModelInfo]:
        return cls._models

    @classmethod
    def add(cls, model_id: str) -> ModelInfo:
        if model_id in cls._model_map:
            return cls._model_map[model_id]
        info = ModelInfo(id=model_id, display_name=model_id)
        cls._models.append(info)
        cls._model_map[model_id] = info
        return info

    @classmethod
    def remove(cls, model_id: str) -> bool:
        if model_id not in cls._model_map:
            return False
        del cls._model_map[model_id]
        cls._models = [m for m in cls._models if m.id != model_id]
        return True
