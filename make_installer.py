import base64
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
DIST_DIR = PROJECT_DIR / 'dist'

def main():
    main_exe = DIST_DIR / 'Qsever.exe'
    if not main_exe.exists():
        print(f"错误: 找不到主程序 {main_exe}")
        print("请先运行: pyinstaller build.spec --clean --noconfirm")
        return

    env_file = PROJECT_DIR / '.env.example'
    if not env_file.exists():
        print(f"错误: 找不到 .env.example 文件: {env_file}")
        return

    installer_template = PROJECT_DIR / 'installer.py'
    if not installer_template.exists():
        print(f"错误: 找不到 installer.py: {installer_template}")
        return

    print("读取主程序...")
    exe_data = main_exe.read_bytes()
    exe_b64 = base64.b64encode(exe_data).decode('ascii')
    print(f"  大小: {len(exe_data) / 1024 / 1024:.1f} MB -> base64: {len(exe_b64) / 1024 / 1024:.1f} MB")

    print("读取 .env...")
    env_content = env_file.read_text(encoding='utf-8')

    print("生成安装程序源码...")
    template = installer_template.read_text(encoding='utf-8')
    filled = template.replace('__MAIN_EXE_B64__', exe_b64)
    filled = filled.replace('__ENV_CONTENT__', env_content)

    output = DIST_DIR / 'installer_filled.py'
    DIST_DIR.mkdir(exist_ok=True)
    output.write_text(filled, encoding='utf-8')
    print(f"  输出: {output}")
    print()
    print("下一步: pyinstaller --onefile --name Qsever_Setup dist/installer_filled.py")

if __name__ == '__main__':
    main()
