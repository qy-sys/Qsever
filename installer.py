import os
import sys
import base64
import subprocess
import time
from pathlib import Path

# === 构建时自动填充 ===
MAIN_EXE_B64 = "__MAIN_EXE_B64__"
ENV_CONTENT = """__ENV_CONTENT__"""
# =======================

def get_desktop() -> Path:
    return Path(os.path.join(os.environ['USERPROFILE'], 'Desktop'))

def main():
    print("=" * 50)
    print("  Qsever 高中解题助手 - 安装程序")
    print("=" * 50)
    print()

    desktop = get_desktop()
    target = desktop / 'Qsever'

    print(f"[1/4] 创建安装目录: {target}")
    target.mkdir(exist_ok=True)
    (target / 'images').mkdir(exist_ok=True)
    (target / 'data').mkdir(exist_ok=True)
    (target / 'output').mkdir(exist_ok=True)
    print("      已创建 images/, data/, output/ 文件夹")
    print()

    print("[2/4] 释放主程序...")
    exe_data = base64.b64decode(MAIN_EXE_B64)
    exe_path = target / 'Qsever.exe'
    with open(exe_path, 'wb') as f:
        f.write(exe_data)
    print(f"      Qsever.exe ({len(exe_data) / 1024 / 1024:.1f} MB)")
    print()

    print("[3/4] 释放配置文件...")
    env_path = target / '.env'
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(ENV_CONTENT)
    print("      .env")
    print()

    print("[4/4] 启动 Qsever...")
    print()
    print("安装完成！文件位置:", target)
    print("下次可直接双击运行:", exe_path)
    print()

    try:
        subprocess.Popen(
            [str(exe_path), '--data-dir', str(target)],
            cwd=str(target),
        )
    except Exception as e:
        print(f"启动失败: {e}")
        print("请手动双击运行:", exe_path)

    input("按回车键退出...")

if __name__ == '__main__':
    main()
