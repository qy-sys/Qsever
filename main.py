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
    parser.add_argument("--fast", action="store_true", help="使用最快模型")
    parser.add_argument("--free", action="store_true", help="使用免费模型")
    parser.add_argument("--clear", action="store_true", help="清空对话历史")
    parser.add_argument("--data-dir", type=str, help="数据目录路径（打包模式使用）")
    args = parser.parse_args()

    data_dir_override = Path(args.data_dir) if args.data_dir else None

    try:
        settings = Settings.from_env(data_dir_override=data_dir_override)
    except ConfigError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

    if args.model:
        model_info = ModelRegistry.get(args.model)
        if not model_info:
            print(f"错误: 未知模型 {args.model}", file=sys.stderr)
            print("可用模型:", ", ".join(m.id for m in ModelRegistry.list_all()))
            sys.exit(1)
        settings.default_model = args.model
    elif args.fast:
        settings.default_model = ModelRegistry.get_fastest().id
    elif args.free:
        settings.default_model = ModelRegistry.get_free().id

    cli = CLI(settings)

    if args.clear:
        cli.conversation.clear()

    cli.run()


if __name__ == "__main__":
    main()
