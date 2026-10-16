from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelInfo:
    id: str
    display_name: str
    input_price: float = 0
    output_price: float = 0
    supports_vision: bool = True
    notes: str = ""


class ModelRegistry:
    """模型注册表 — 从配置动态加载"""

    _models: list[ModelInfo] = []
    _model_map: dict[str, ModelInfo] = {}

    @classmethod
    def load_from_config(cls, model_entries: list[tuple[str, float, float]]):
        cls._models = []
        cls._model_map = {}
        for model_id, input_price, output_price in model_entries:
            model_id = model_id.strip()
            if not model_id:
                continue
            info = ModelInfo(
                id=model_id,
                display_name=model_id,
                input_price=input_price,
                output_price=output_price,
            )
            cls._models.append(info)
            cls._model_map[model_id] = info

    @classmethod
    def get(cls, model_id: str) -> Optional[ModelInfo]:
        return cls._model_map.get(model_id)

    @classmethod
    def get_default(cls) -> Optional[ModelInfo]:
        return cls._models[0] if cls._models else None

    @classmethod
    def list_all(cls) -> list[ModelInfo]:
        return cls._models

    @classmethod
    def add(cls, model_id: str, input_price: float = 0, output_price: float = 0) -> ModelInfo:
        if model_id in cls._model_map:
            return cls._model_map[model_id]
        info = ModelInfo(
            id=model_id,
            display_name=model_id,
            input_price=input_price,
            output_price=output_price,
        )
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
