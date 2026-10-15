from dataclasses import dataclass, field
from pathlib import Path
import os
import sys
from dotenv import load_dotenv

from .exceptions import ConfigError


def get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    api_key: str
    base_url: str
    default_model: str = "qwen/qwen3.8-flash"
    images_dir: Path = field(default_factory=lambda: Path("images"))
    data_dir: Path = field(default_factory=lambda: Path("data"))
    budget_limit: float = 100.0
    auto_open_html: bool = True
    output_dir: Path = field(default_factory=lambda: Path("output"))

    @classmethod
    def from_env(cls, env_file: str = ".env", data_dir_override: Path | None = None) -> "Settings":
        base_dir = get_base_dir()
        env_path = base_dir / env_file
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()

        api_key = os.getenv("QSEVER_API_KEY", "")
        base_url = os.getenv("QSEVER_BASE_URL", "")

        if not api_key:
            raise ConfigError("未设置 QSEVER_API_KEY，请在 .env 文件中配置")
        if not base_url:
            raise ConfigError("未设置 QSEVER_BASE_URL，请在 .env 文件中配置")

        if data_dir_override:
            images_dir = data_dir_override / "images"
            data_dir = data_dir_override / "data"
            output_dir = data_dir_override / "output"
        else:
            images_dir = Path(os.getenv("QSEVER_IMAGES_DIR", "images"))
            data_dir = Path(os.getenv("QSEVER_DATA_DIR", "data"))
            output_dir = Path(os.getenv("QSEVER_OUTPUT_DIR", "output"))

        budget_limit = float(os.getenv("QSEVER_BUDGET_LIMIT", "100.0"))
        default_model = os.getenv("QSEVER_DEFAULT_MODEL", "qwen/qwen3.8-flash")
        auto_open_html = os.getenv("QSEVER_AUTO_OPEN_HTML", "true").lower() == "true"

        return cls(
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
            images_dir=images_dir,
            data_dir=data_dir,
            budget_limit=budget_limit,
            auto_open_html=auto_open_html,
            output_dir=output_dir,
        )
