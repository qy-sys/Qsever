import argparse
import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from qsever.config import Settings
from qsever.exceptions import ConfigError


def main():
    parser = argparse.ArgumentParser(description="Qsever - 高中解题助手")
    parser.add_argument("--clear", action="store_true", help="清空对话历史")
    parser.add_argument("--data-dir", type=str, help="数据目录路径（打包模式使用）")
    parser.add_argument(
        "mode", nargs="?", default="web",
        choices=["web", "cli"],
        help="运行模式：web（默认，启动网页界面）或 cli（命令行）"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Web 监听地址")
    parser.add_argument("--port", type=int, default=8765, help="Web 监听端口")
    args = parser.parse_args()

    data_dir_override = Path(args.data_dir) if args.data_dir else None

    try:
        settings = Settings.from_config(data_dir_override=data_dir_override)
    except ConfigError as e:
        print(f"错误：{e}", file=sys.stderr)
        print("\n请从 config.example.ini 复制为 config.ini 并填写你的 API 信息", file=sys.stderr)
        sys.exit(1)

    if args.mode == "cli":
        from qsever.cli import CLI
        cli = CLI(settings)
        if args.clear:
            cli.conversation.clear()
        cli.run()
    else:
        from qsever.web.server import start_server
        start_server(settings, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
