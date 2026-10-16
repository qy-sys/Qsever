import argparse
import sys
from pathlib import Path

from qsever.cli import CLI
from qsever.config import Settings
from qsever.exceptions import ConfigError
from qsever.models import ModelRegistry


def main():
    parser = argparse.ArgumentParser(description="Qsever - 高中解题助手")
    parser.add_argument("--model", type=str, help="指定模型 ID")
    parser.add_argument("--clear", action="store_true", help="清空对话历史")
    parser.add_argument("--data-dir", type=str, help="数据目录路径（打包模式使用）")
    args = parser.parse_args()

    data_dir_override = Path(args.data_dir) if args.data_dir else None

    try:
        settings = Settings.from_config(data_dir_override=data_dir_override)
    except ConfigError as e:
        print(f"错误: {e}", file=sys.stderr)
        print("\n请从 config.example.ini 复制为 config.ini 并填写你的 API 信息", file=sys.stderr)
        sys.exit(1)

    profile = settings.profiles[settings.active_profile]
    ModelRegistry.load_from_config(profile.models)

    cli = CLI(settings)

    if args.model:
        if not ModelRegistry.get(args.model):
            ModelRegistry.add(args.model)
        cli.current_model = args.model

    if args.clear:
        cli.conversation.clear()

    cli.run()


if __name__ == "__main__":
    main()
