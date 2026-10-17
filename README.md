# Qsever

高中解题助手 — 支持 Web 网页界面和命令行两种模式，AI 智能解题，自动生成带数学公式的网页解答。

## 功能

- **Web 网页界面**：浏览器打开即可使用，无需命令行基础
  - 流式输出，AI 回答逐字显示
  - MathJax 渲染 LaTeX 数学公式
  - Markdown 格式化，代码高亮
  - 图片上传，直接上传题目图片
  - 多标签页独立会话
- **CLI 命令行模式**：传统命令行交互，适合习惯终端的用户
- **文字题目**：直接输入，AI 分步解答（审题→解题→答案→提示）
- **图片题目**：上传图片，AI 识别后解答
- **公式渲染**：每次回答自动生成 HTML 网页，MathJax 渲染 LaTeX 公式
- **多预设支持**：支持多组 API 配置，运行时切换
- **用量追踪**：记录 token 消耗和费用，预算预警
- **多轮对话**：自动维护上下文，支持连续追问

## 快速开始

### 安装

1. 从 [Releases](https://github.com/qy-sys/Qsever/releases) 下载 `Qsever_Setup.exe`
2. 双击运行，自动安装到安装程序所在目录
3. 编辑 `config.ini` 填写你的 API 信息
4. 双击 `start_web.bat` 启动 Web 界面，或 `start_cli.bat` 启动命令行模式

### 配置

首次运行会提示你编辑配置文件。打开安装目录中的 `config.ini`：

```ini
[main]
profile = 我的API

[settings]
images_dir = images
data_dir = data
budget_limit = 100.0
auto_open_html = true
output_dir = output

[我的API]
api_key = 你的API密钥
base_url = 你的API地址（OpenAI兼容格式）
model = 模型名称:输入价格:输出价格
```

**配置说明：**
- `[main]` 的 `profile` 指定默认激活的配置名
- 每个配置节包含：`api_key`、`base_url`、`model`
- 模型价格格式：`模型ID[:输入价[:输出价]]`（美元/百万tokens），价格可选
  - 不填价格：`model = gpt-4o`
  - 只填输入价：`model = gpt-4o:2.5`（输出价自动按 2.5 倍计算）
  - 完整价格：`model = gpt-4o:2.5:10`

兼容任何 OpenAI 格式的 API 端点（如 OpenAI、Azure、本地部署等）。

### 使用

**Web 模式（推荐）：**

双击 `start_web.bat`，自动打开浏览器访问 `http://127.0.0.1:8765`

- 在输入框输入题目，按 Enter 发送
- 点击图片按钮上传题目图片
- 顶部下拉菜单切换 API 预设
- 点击"用量"查看使用情况

**CLI 模式：**

双击 `start_cli.bat`，在命令行中交互：

```bash
# 输入题目
> 求函数 f(x) = x² - 2x + 1 的最小值

# 图片题目（先把图片拖入 images/ 文件夹）
> 解这道题 @math1.png

# 查看当前配置
> /profile

# 查看用量
> /usage
```

## 命令列表（CLI 模式）

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/config [名称]` | 列出/切换预设 |
| `/profile [名称]` | 查看预设详情 |
| `/images` | 列出可用图片 |
| `/usage` | 查看用量和费用 |
| `/html` | 手动导出最近一次问答为 HTML |
| `/html on/off` | 开启/关闭自动打开浏览器 |
| `/clear` | 清空对话历史 |
| `/about` | 显示作者和开源信息 |
| `/exit` | 退出 |

## 从源码运行

```bash
git clone https://github.com/qy-sys/Qsever.git
cd Qsever
pip install -r requirements.txt
cp config.example.ini config.ini
# 编辑 config.ini 填写你的 API 信息

# 启动 Web 模式（默认）
python main.py

# 或启动 CLI 模式
python main.py cli
```

## 打包

```bash
build_all.bat
```

生成 `dist/Qsever_Setup.exe` 安装程序。

## 项目结构

```
Qsever/
├── main.py              # 程序入口，web/cli 双模式
├── requirements.txt     # Python 依赖
├── config.example.ini   # 配置模板
├── build.spec           # PyInstaller 打包配置
├── build_all.bat        # 一键打包脚本
├── installer.py         # 安装程序模板
├── make_installer.py    # 安装程序生成器
├── qsever/              # 核心代码包
│   ├── cli.py           # 命令行交互主循环
│   ├── client.py        # API 客户端（流式调用 + 重试）
│   ├── config.py        # 配置管理（INI 多预设）
│   ├── conversation.py  # 多轮对话历史管理
│   ├── image_handler.py # 图片处理（base64 编码）
│   ├── html_exporter.py # HTML 导出（MathJax 渲染）
│   ├── usage.py         # 用量追踪和费用计算
│   ├── prompts.py       # 解题系统提示词
│   ├── exceptions.py    # 自定义异常
│   └── web/             # Web 前端
│       ├── server.py    # FastAPI 应用（SSE 流式）
│       ├── session.py   # 会话管理
│       └── static/      # 前端静态文件
│           ├── index.html
│           ├── css/style.css
│           └── js/app.js
├── images/              # 题目图片目录
├── data/                # 运行时数据（用量记录）
└── output/              # 生成的 HTML 解答网页
```

## 技术栈

- Python 3.10+
- [openai](https://github.com/openai/openai-python) — API 调用
- [FastAPI](https://fastapi.tiangolo.com) — Web 后端框架
- [uvicorn](https://www.uvicorn.org) — ASGI 服务器
- [rich](https://github.com/Textualize/rich) — 终端美化（CLI 模式）
- [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) — 命令行输入增强
- [PyInstaller](https://pyinstaller.org) — 打包为 exe
- [MathJax](https://www.mathjax.org) — 数学公式渲染
- [marked.js](https://marked.js.org) — Markdown 解析

## 作者

- 作者：野山菌
- GitHub：[qy-sys](https://github.com/qy-sys)
- B 站：[space.bilibili.com/1048757404](https://space.bilibili.com/1048757404)
- QQ：2575635669

## 许可证

[MIT License](LICENSE)
