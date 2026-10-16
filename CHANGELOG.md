# 更新日志

## v0.1.0 — 2026-10-16

初始版本。

### 新增

- CLI 命令行交互，支持多轮对话
- 文字题目解答，AI 分步解题（审题→解题→答案→提示）
- 图片题目支持，拖入 `images/` 后用 `@文件名` 引用
- HTML 公式导出，MathJax 渲染 LaTeX，自动浏览器打开
- 多配置支持：INI 配置文件，支持多组 API 配置运行时切换
- 多模型支持：兼容任何 OpenAI 格式 API，模型价格可配置
- 用量追踪：JSONL 持久化，80% 预算预警，费用自动计算
- PyInstaller 打包，单文件安装程序（桌面自动创建文件夹）
- 流式输出，AI 回答逐字显示
- 作者信息展示：启动 banner 和 /about 命令

### 配置系统

- `config.ini` INI 格式配置文件，`[main]` 节指定默认配置
- 每个配置节包含 `api_key`、`base_url`、`models`
- 模型价格格式：`模型ID[:输入价[:输出价]]`（每 1M tokens 美元）
- `/config` 和 `/profile` 命令运行时查看和切换配置
- `/add-model` 和 `/remove-model` 命令运行时增删模型

### 项目结构

```
Qsever/
├── main.py              # 程序入口，argparse 参数解析
├── requirements.txt     # 5 个依赖：openai, python-dotenv, rich, prompt-toolkit, Pillow
├── LICENSE              # MIT 许可证
├── README.md            # 项目说明
├── CHANGELOG.md         # 本文件
├── config.example.ini   # 配置模板
├── build.spec           # PyInstaller 主程序打包配置
├── build_all.bat        # 一键打包脚本
├── installer.py         # 安装程序模板（base64 占位符）
├── make_installer.py    # 安装程序生成器（读取 exe → base64 → 填充模板）
├── .gitignore
├── qsever/              # 核心包
│   ├── __init__.py      # 版本号 v0.1.0
│   ├── cli.py           # CLI 主循环，指令解析，rich 美化输出
│   ├── client.py        # OpenAI 兼容 API 客户端，流式 + 重试
│   ├── config.py        # Settings dataclass，INI 多配置加载
│   ├── models.py        # ModelRegistry，从配置动态加载
│   ├── conversation.py  # 对话历史，token 截断，会话保存/加载
│   ├── image_handler.py # 图片扫描，base64 编码，vision content 构造
│   ├── html_exporter.py # HTML 模板，Markdown→HTML 转换，浏览器打开
│   ├── usage.py         # UsageTracker，JSONL 持久化，费用计算
│   ├── prompts.py       # 高中解题 system prompt
│   └── exceptions.py    # QseverError, APIError, ImageNotFound, ConfigError
├── images/              # 用户拖入题目图片
├── data/                # 用量记录（usage.jsonl）
└── output/              # 生成的 HTML 解答网页
```

### 技术细节

- 配置文件：INI 格式（Python 内置 configparser），无硬编码
- 模型价格：用户自行填写，用于用量费用计算
- 流式输出：Python generator yield，非多线程
- 打包方案：PyInstaller onefile + Python 自释放安装器（base64 嵌入）
- 安装程序大小：~40MB，主程序 ~33MB
