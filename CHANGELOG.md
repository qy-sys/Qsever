# 更新日志

## v0.1.0 — 2026-10-15

初始版本。

### 新增

- CLI 命令行交互，支持多轮对话
- 文字题目解答，AI 分步解题（审题→解题→答案→提示）
- 图片题目支持，拖入 `images/` 后用 `@文件名` 引用
- HTML 公式导出，MathJax 渲染 LaTeX，自动浏览器打开
- 17 个 AI 模型支持（3 免费 + 14 付费），运行时切换
- 用量追踪，JSONL 持久化，80% 预算预警
- PyInstaller 打包，单文件安装程序（桌面自动创建文件夹）
- 免费模型自动重试（超时/限流最多 3 次）
- 流式输出，AI 回答逐字显示

### 项目结构

```
Qsever/
├── main.py              # 程序入口，argparse 参数解析
├── requirements.txt     # 5 个依赖：openai, python-dotenv, rich, prompt-toolkit, Pillow
├── LICENSE              # MIT 许可证
├── README.md            # 项目说明
├── CHANGELOG.md         # 本文件
├── build.spec           # PyInstaller 主程序打包配置
├── build_all.bat        # 一键打包脚本
├── installer.py         # 安装程序模板（base64 占位符）
├── make_installer.py    # 安装程序生成器（读取 exe → base64 → 填充模板）
├── .env.example         # 环境变量模板
── .gitignore
├── qsever/              # 核心包
│   ├── __init__.py      # 版本号 v0.1.0
│   ├── cli.py           # CLI 主循环，指令解析，rich 美化输出
│   ├── client.py        # OpenAI 兼容 API 客户端，流式 + 重试
│   ├── config.py        # Settings dataclass，dotenv 加载，frozen 检测
│   ├── models.py        # ModelRegistry，17 个模型元数据
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

- 默认模型：`qwen/qwen3.8-flash`（$0.20/$0.50 per 1M tokens）
- 流式输出：Python generator yield，非多线程
- 打包方案：PyInstaller onefile + Python 自释放安装器（base64 嵌入）
- 安装程序大小：~40MB，主程序 ~33MB
