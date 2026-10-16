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
        settings = Settings.from_env(data_dir_override=data_dir_override)
    except ConfigError as e:
        print(f"错误: {e}", file=sys.stderr)
        print("\n请在 .env 文件中配置：")
        print("  QSEVER_API_KEY=你的API密钥")
        print("  QSEVER_BASE_URL=你的API地址")
        print("  QSEVER_MODELS=模型1,模型2")
        sys.exit(1)

    ModelRegistry.load_from_config(settings.models, settings.default_model)

    if args.model:
        if not ModelRegistry.get(args.model):
            ModelRegistry.add(args.model)
        settings.default_model = args.model

    if not settings.default_model and ModelRegistry.list_all():
        settings.default_model = ModelRegistry.list_all()[0].id

    cli = CLI(settings)

    if args.clear:
        cli.conversation.clear()

    cli.run()


if __name__ == "__main__":
    main()
