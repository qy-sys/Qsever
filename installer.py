import os
import sys
import base64
import subprocess
from pathlib import Path

# === 构建时自动填充 ===
MAIN_EXE_B64 = "__MAIN_EXE_B64__"
CONFIG_CONTENT = """__CONFIG_CONTENT__"""
# =======================


def get_install_dir() -> Path:
    """安装到安装程序所在目录"""
    return Path(os.path.abspath(sys.argv[0])).parent


def main():
    print("=" * 50)
    print("  Qsever 高中解题助手 - 安装程序")
    print("=" * 50)
    print()

    install_dir = get_install_dir()
    target = install_dir / 'Qsever'

    print(f"[1/5] 创建安装目录: {target}")
    target.mkdir(exist_ok=True)
    (target / 'images').mkdir(exist_ok=True)
    (target / 'data').mkdir(exist_ok=True)
    (target / 'output').mkdir(exist_ok=True)
    print("      已创建 images/, data/, output/ 文件夹")
    print()

    print("[2/5] 释放主程序...")
    exe_data = base64.b64decode(MAIN_EXE_B64)
    exe_path = target / 'Qsever.exe'
    with open(exe_path, 'wb') as f:
        f.write(exe_data)
    print(f"      Qsever.exe ({len(exe_data) / 1024 / 1024:.1f} MB)")
    print()

    print("[3/5] 释放配置文件...")
    config_path = target / 'config.ini'
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(CONFIG_CONTENT)
    print("      config.ini")
    print()

    print("[4/5] 创建启动脚本...")

    web_bat = target / 'start_web.bat'
    web_bat.write_text(
        '@echo off\n'
        'chcp 65001 >nul\n'
        'cd /d "%~dp0"\n'
        'set "APP_DIR=%~dp0."\n'
        'echo Starting Qsever Web...\n'
        'echo Open browser: http://127.0.0.1:8765\n'
        'echo.\n'
        'Qsever.exe web --data-dir "%APP_DIR%"\n'
        'pause\n',
        encoding='utf-8'
    )

    cli_bat = target / 'start_cli.bat'
    cli_bat.write_text(
        '@echo off\n'
        'chcp 65001 >nul\n'
        'cd /d "%~dp0"\n'
        'set "APP_DIR=%~dp0."\n'
        'echo Starting Qsever CLI...\n'
        'echo.\n'
        'Qsever.exe cli --data-dir "%APP_DIR%"\n'
        'pause\n',
        encoding='utf-8'
    )

    print("      start_web.bat")
    print("      start_cli.bat")
    print()

    print("[5/5] 启动 Qsever...")
    print()
    print("安装完成！文件位置:", target)
    print()
    print("文件夹结构:")
    print("  Qsever/")
    print("  ├── Qsever.exe        # 主程序")
    print("  ├── config.ini        # 配置文件（需编辑填写 API 信息）")
    print("  ├── start_web.bat     # 启动 Web 界面")
    print("  ├── start_cli.bat     # 启动 CLI 模式")
    print("  ├── images/           # 图片目录")
    print("  ├── data/             # 数据目录")
    print("  └── output/           # 输出目录")
    print()
    print("使用说明:")
    print("  1. 编辑 config.ini 填写你的 API 信息")
    print("  2. 双击 start_web.bat 启动 Web 界面")
    print("     或双击 start_cli.bat 启动 CLI 模式")
    print()

    try:
        subprocess.Popen(
            [str(exe_path), 'web', '--data-dir', str(target)],
            cwd=str(target),
        )
    except Exception as e:
        print(f"启动失败: {e}")
        print("请手动双击运行: start_web.bat 或 start_cli.bat")

    input("按回车键退出...")


if __name__ == '__main__':
    main()
