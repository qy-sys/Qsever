import configparser
from dataclasses import dataclass, field
from pathlib import Path
import sys

from .exceptions import ConfigError


def get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def parse_model_entry(entry: str) -> tuple[str, float, float]:
    parts = entry.strip().split(":")
    model_id = parts[0]
    if len(parts) >= 3:
        return model_id, float(parts[1]), float(parts[2])
    elif len(parts) == 2:
        input_price = float(parts[1])
        return model_id, input_price, input_price * 2.5
    else:
        return model_id, 0.0, 0.0


@dataclass
class ConfigProfile:
    name: str
    api_key: str
    base_url: str
    models: list[tuple[str, float, float]] = field(default_factory=list)


@dataclass
class Settings:
    profiles: dict[str, ConfigProfile] = field(default_factory=dict)
    active_profile: str = ""
    images_dir: Path = field(default_factory=lambda: Path("images"))
    data_dir: Path = field(default_factory=lambda: Path("data"))
    budget_limit: float = 100.0
    auto_open_html: bool = True
    output_dir: Path = field(default_factory=lambda: Path("output"))

    @property
    def api_key(self) -> str:
        if self.active_profile in self.profiles:
            return self.profiles[self.active_profile].api_key
        return ""

    @property
    def base_url(self) -> str:
        if self.active_profile in self.profiles:
            return self.profiles[self.active_profile].base_url
        return ""

    @property
    def models(self) -> list[tuple[str, float, float]]:
        if self.active_profile in self.profiles:
            return self.profiles[self.active_profile].models
        return []

    @property
    def default_model(self) -> str:
        models = self.models
        return models[0][0] if models else ""

    @classmethod
    def from_config(cls, config_file: str = "config.ini", data_dir_override: Path | None = None) -> "Settings":
        base_dir = get_base_dir()
        config_path = base_dir / config_file

        if not config_path.exists():
            raise ConfigError(f"找不到配置文件 {config_path}\n请从 config.example.ini 复制并填写你的 API 信息")

        cp = configparser.ConfigParser()
        cp.read(config_path, encoding='utf-8')

        active = cp.get('main', 'profile', fallback='')

        profiles = {}
        for section in cp.sections():
            if section in ('main', 'settings'):
                continue
            api_key = cp.get(section, 'api_key', fallback='')
            base_url = cp.get(section, 'base_url', fallback='')
            models_str = cp.get(section, 'models', fallback='')
            models = [parse_model_entry(m) for m in models_str.split(',') if m.strip()]
            profiles[section] = ConfigProfile(
                name=section,
                api_key=api_key,
                base_url=base_url,
                models=models,
            )

        if not profiles:
            raise ConfigError("配置文件中没有找到任何配置节")

        if active and active not in profiles:
            raise ConfigError(f"main.profile = {active} 指向的配置不存在\n可用配置: {', '.join(profiles.keys())}")

        if not active:
            active = next(iter(profiles))

        if data_dir_override:
            images_dir = data_dir_override / "images"
            data_dir = data_dir_override / "data"
            output_dir = data_dir_override / "output"
        else:
            images_dir = Path(cp.get('settings', 'images_dir', fallback='images'))
            data_dir = Path(cp.get('settings', 'data_dir', fallback='data'))
            output_dir = Path(cp.get('settings', 'output_dir', fallback='output'))

        budget_limit = cp.getfloat('settings', 'budget_limit', fallback=100.0)
        auto_open_html = cp.get('settings', 'auto_open_html', fallback='true').lower() == 'true'

        return cls(
            profiles=profiles,
            active_profile=active,
            images_dir=images_dir,
            data_dir=data_dir,
            budget_limit=budget_limit,
            auto_open_html=auto_open_html,
            output_dir=output_dir,
        )

    def switch_profile(self, name: str) -> bool:
        if name not in self.profiles:
            return False
        self.active_profile = name
        return True
