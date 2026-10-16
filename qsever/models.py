from dataclasses import dataclass


@dataclass
class ModelInfo:
    id: str
    input_price: float = 0.0
    output_price: float = 0.0
