from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelInfo:
    id: str
    display_name: str
    input_price: float  # 每 1M tokens 美元
    output_price: float
    is_free: bool
    supports_vision: bool = True
    speed_tier: int = 2  # 1=最快, 2=快, 3=中等, 4=慢
    notes: str = ""


class ModelRegistry:
    """模型注册表"""

    MODELS = [
        # 免费模型
        ModelInfo("deepseek/deepseek-v4-flash", "DeepSeek V4 Flash", 0, 0, True, speed_tier=2, notes="免费，可能排队"),
        ModelInfo("minimax/minimax-m2.7", "MiniMax M2.7", 0, 0, True, speed_tier=2, notes="免费，可能排队"),
        ModelInfo("tencent/hy3", "Tencent HY3", 0, 0, True, speed_tier=2, notes="免费，可能排队"),
        # 付费模型（按价格排序）
        ModelInfo("deepseek/deepseek-v4-flash-0731", "DeepSeek V4 Flash 0731", 0.15, 0.30, False, speed_tier=1),
        ModelInfo("qwen/qwen3.8-flash", "Qwen3.8 Flash", 0.20, 0.50, False, speed_tier=1),
        ModelInfo("deepseek/deepseek-v4.1-flash", "DeepSeek V4.1 Flash", 0.20, 1.00, False, speed_tier=1),
        ModelInfo("minimax/minimax-m3", "MiniMax M3", 0.30, 1.20, False, speed_tier=2),
        ModelInfo("minimax/minimax-m3.1-flash-preview", "MiniMax M3.1 Flash Preview", 0.30, 1.20, False, speed_tier=2),
        ModelInfo("openai/gpt-5.6-luna", "GPT-5.6 Luna", 0.30, 1.30, False, speed_tier=2),
        ModelInfo("deepseek/deepseek-v4-pro", "DeepSeek V4 Pro", 0.50, 1.00, False, speed_tier=2),
        ModelInfo("moonshotai/kimi-k2.6", "Kimi K2.6", 0.95, 4.00, False, speed_tier=3),
        ModelInfo("tencent/hy4-preview", "Tencent HY4 Preview", 1.00, 3.00, False, speed_tier=3),
        ModelInfo("google/gemini-3.8-flash", "Gemini 3.8 Flash", 1.50, 7.50, False, speed_tier=2),
        ModelInfo("moonshotai/kimi-k3", "Kimi K3", 3.00, 15.00, False, speed_tier=3),
        ModelInfo("anthropic/claude-sonnet-5", "Claude Sonnet 5", 2.00, 10.00, False, speed_tier=3),
        ModelInfo("anthropic/claude-opus-5", "Claude Opus 5", 5.00, 25.00, False, speed_tier=4),
        ModelInfo("openai/gpt-5.6-sol", "GPT-5.6 Sol", 5.00, 30.00, False, speed_tier=4),
    ]

    _model_map = {m.id: m for m in MODELS}

    @classmethod
    def get(cls, model_id: str) -> Optional[ModelInfo]:
        return cls._model_map.get(model_id)

    @classmethod
    def get_default(cls) -> ModelInfo:
        return cls._model_map["qwen/qwen3.8-flash"]

    @classmethod
    def get_fastest(cls) -> ModelInfo:
        paid = [m for m in cls.MODELS if not m.is_free]
        return min(paid, key=lambda m: m.speed_tier)

    @classmethod
    def get_cheapest(cls) -> ModelInfo:
        paid = [m for m in cls.MODELS if not m.is_free]
        return min(paid, key=lambda m: m.input_price + m.output_price)

    @classmethod
    def get_free(cls) -> ModelInfo:
        free = [m for m in cls.MODELS if m.is_free]
        return free[0] if free else cls.get_default()

    @classmethod
    def list_all(cls) -> list[ModelInfo]:
        return cls.MODELS

    @classmethod
    def list_free(cls) -> list[ModelInfo]:
        return [m for m in cls.MODELS if m.is_free]

    @classmethod
    def list_paid(cls) -> list[ModelInfo]:
        return [m for m in cls.MODELS if not m.is_free]
