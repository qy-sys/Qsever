# Qsever

高中解题助手 — 命令行 AI 解题工具，支持文字和图片题目，自动生成带数学公式的网页解答。

## 功能

- 文字题目：直接输入，AI 分步解答
- 图片题目：拖入图片，用 `@文件名` 引用，AI 识别后解答
- 公式渲染：每次回答自动生成 HTML 网页，MathJax 渲染 LaTeX 公式，浏览器打开即可查看
- 多模型支持：兼容任何 OpenAI 格式的 API，支持运行时切换模型
- 用量追踪：记录 token 消耗和费用，预算预警
- 多轮对话：自动维护上下文，支持连续追问

## 快速开始

### 安装

1. 从 [Releases](https://github.com/qy-sys/Qsever/releases) 下载 `Qsever_Setup.exe`
2. 双击运行，自动在桌面创建 `Qsever` 文件夹
3. 安装完成后自动启动

### 配置

编辑 `Qsever` 文件夹中的 `.env` 文件，填入你的 API 密钥：

```env
QSEVER_API_KEY=你的API密钥
QSEVER_BASE_URL=你的API地址
```

兼容任何 OpenAI 格式的 API 端点（如 OpenAI、Azure、本地部署等）。

### 使用

```bash
# 启动程序
Qsever.exe

# 输入题目
> 求函数 f(x) = x² - 2x + 1 的最小值

# 图片题目（先把图片拖入 images/ 文件夹）
> 解这道题 @math1.png

# 切换模型
> /model deepseek/deepseek-v4-pro

# 查看用量
> /usage
```

## 命令列表

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/model [名称]` | 切换模型（无参数列出所有模型） |
| `/fast` | 切换到最快模型 |
| `/free` | 切换到免费模型 |
| `/images` | 列出可用图片 |
| `/usage` | 查看用量和费用 |
| `/html` | 手动导出最近一次问答为 HTML |
| `/html on/off` | 开启/关闭自动打开浏览器 |
| `/clear` | 清空对话历史 |
| `/exit` | 退出 |

## 模型配置

在 `.env` 中设置默认模型：

```env
QSEVER_DEFAULT_MODEL=你的模型名称
```

程序兼容任何 OpenAI 格式的 API 端点。运行时可用 `/model` 命令查看和切换可用模型。

## 从源码运行

```bash
git clone https://github.com/qy-sys/Qsever.git
cd Qsever
pip install -r requirements.txt
python main.py
```

## 打包

```bash
build_all.bat
```

生成 `dist/Qsever_Setup.exe` 安装程序。

## 项目结构

```
Qsever/
├── main.py              # 程序入口
├── requirements.txt     # Python 依赖
├── build.spec           # PyInstaller 打包配置
├── build_all.bat        # 一键打包脚本
├── installer.py         # 安装程序模板
├── make_installer.py    # 安装程序生成器
├── qsever/              # 核心代码包
│   ├── cli.py           # 命令行交互主循环
│   ├── client.py        # API 客户端（流式调用 + 重试）
│   ├── config.py        # 配置管理（.env 加载）
│   ├── models.py        # 模型注册表（可自定义）
│   ├── conversation.py  # 多轮对话历史管理
│   ├── image_handler.py # 图片处理（base64 编码）
│   ├── html_exporter.py # HTML 导出（MathJax 渲染）
│   ├── usage.py         # 用量追踪和费用计算
│   ├── prompts.py       # 解题系统提示词
│   └── exceptions.py    # 自定义异常
├── images/              # 题目图片目录
├── data/                # 运行时数据（用量记录）
── output/              # 生成的 HTML 解答网页
```

## 技术栈

- Python 3.10+
- [openai](https://github.com/openai/openai-python) — API 调用
- [rich](https://github.com/Textualize/rich) — 终端美化
- [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) — 命令行输入增强
- [PyInstaller](https://pyinstaller.org) — 打包为 exe
- [MathJax](https://www.mathjax.org) — 数学公式渲染

## 许可证

[MIT License](LICENSE)
