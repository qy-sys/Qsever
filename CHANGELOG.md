# 更新日志

## v0.2.1 — 2026-10-19

### 新增

- **图片自动压缩**：上传的图片自动压缩，减少 AI 识别时间和存储占用
  - 使用 Pillow 库进行压缩（已在依赖中）
  - 阈值 500KB：小于该值的图片不压缩
  - 最大尺寸 1920px：超过的按比例缩小
  - JPEG 质量 85%，保持原始格式
  - GIF 不处理（动画处理复杂）
  - 文件名净化：防止路径遍历攻击
- **Web 端可视化配置管理**：在浏览器中管理预设和设置
  - 设置面板（齿轮按钮）：两个 Tab（预设管理、通用设置）
  - 预设 CRUD：添加、编辑、删除预设，无需手动编辑 config.ini
  - API Key 脱敏显示：编辑时保留原值
  - 通用设置：修改预算上限、自动打开 HTML 等
  - 配置持久化：所有修改立即写入 config.ini
  - Toast 通知：操作成功/失败的即时反馈
- **图片库浏览与导入**：重复使用 images 目录中的图片
  - 图片库按钮（🖼️）：网格展示所有图片
  - 点击导入：点击图片加入待发送队列
  - 图片删除：悬浮显示删除按钮
  - 选中状态：蓝色边框标记已选图片

### 改进

- **安全性增强**：
  - 文件名净化：去除路径分隔符和特殊字符
  - 路径遍历防护：所有图片端点验证路径合法性
  - API Key 脱敏：GET /api/config 返回脱敏后的 key
- **用户体验**：
  - 预设切换反馈：切换后显示 toast 通知
  - 图片压缩透明：返回原始大小和压缩后大小

### 技术细节

- **图片压缩**：上传时压缩并保存压缩版本，避免每次发送重新压缩
- **配置持久化**：Settings 类新增 save_config()、add_profile()、update_profile()、delete_profile()、update_settings() 方法
- **API 增强**：新增 5 个配置管理端点（POST/PUT/DELETE /api/config/profile，PUT /api/config/settings）
- **前端组件**：设置模态框、预设表单、图片库网格、Toast 通知系统

---

## v0.2.0 — 2026-10-17

### 新增

- **Web 前端界面**：浏览器访问的聊天界面，无需命令行
  - FastAPI + 纯 HTML/CSS/JS，无构建工具
  - 流式输出：SSE 实时逐字显示 AI 回复
  - MathJax 3 公式渲染：LaTeX 公式美观显示
  - marked.js Markdown 渲染：自动格式化 AI 回复
  - 图片上传：网页端直接上传图片题目
  - 预设切换：下拉菜单切换 API 配置
  - 用量统计：弹窗查看用量和费用
  - 多标签页独立会话：每个标签独立对话
  - 端口冲突自动解决：端口被占用时自动尝试下一个端口（8765 起）
- **双模式启动**：`python main.py` 启动 Web，`python main.py cli` 启动 CLI
- **安装程序改进**：安装到安装程序所在目录（不再固定桌面）
- **启动脚本**：安装后自动创建 `start_web.bat` 和 `start_cli.bat`

### 改进

- **配置系统重构**：完全移除 `.env` 依赖，统一使用 INI 配置
- **简化配置**：一个预设 = 一个模型，去掉运行时增删模型的复杂命令
- **配置模板**：`config.example.ini` 改为空模板，用户首次运行引导添加配置
- **模型价格**：支持用户自定义价格，格式 `模型ID[:输入价[:输出价]]`

### 项目结构

```
Qsever/
├── main.py              # 程序入口，web/cli 双模式
├── requirements.txt     # 依赖：openai, rich, prompt-toolkit, Pillow, fastapi, uvicorn, python-multipart
├── LICENSE              # MIT 许可证
├── README.md            # 项目说明
├── CHANGELOG.md         # 本文件
├── config.example.ini   # 配置模板（空格式）
├── build.spec           # PyInstaller 主程序打包配置
├── build_all.bat        # 一键打包脚本
├── installer.py         # 安装程序模板
├── make_installer.py    # 安装程序生成器
├── .gitignore
├── qsever/              # 核心包
│   ├── __init__.py      # 版本号 v0.2.0
│   ├── cli.py           # CLI 主循环
│   ├── client.py        # OpenAI 兼容 API 客户端
│   ├── config.py        # INI 多预设配置
│   ├── conversation.py  # 对话历史管理
│   ├── image_handler.py # 图片处理
│   ├── html_exporter.py # HTML 导出
│   ├── usage.py         # 用量追踪
│   ├── prompts.py       # 系统提示词
│   ├── exceptions.py    # 异常定义
│   └── web/             # Web 前端（新增）
│       ├── __init__.py
│       ├── server.py    # FastAPI 应用，SSE 流式
│       ├── session.py   # 会话管理
│       └── static/      # 前端静态文件
│           ├── index.html
│           ├── css/style.css
│           └── js/app.js
├── images/              # 图片目录
├── data/                # 数据目录
└── output/              # 输出目录
```

### 技术细节

- **Web 框架**：FastAPI（异步）+ uvicorn（ASGI 服务器）
- **前端**：纯 HTML/CSS/JS，CDN 加载 MathJax 3 和 marked.js v12
- **流式传输**：SSE（Server-Sent Events），fetch + ReadableStream 解析
- **同步兼容**：`asyncio.run_in_executor()` 包装同步 API 客户端，核心模块零改动
- **会话隔离**：每个浏览器标签独立会话，UUID 标识（localStorage）
- **LaTeX 渲染**：占位符保护机制，避免 marked.js 破坏 LaTeX 分隔符
- **安装程序**：安装到安装程序所在目录，自动创建启动脚本
- **依赖变化**：移除 python-dotenv，新增 fastapi、uvicorn、python-multipart

---

## v0.1.0 — 2026-10-17

初始版本，CLI 命令行解题助手。

### 功能

- **CLI 命令行交互**：支持多轮对话，rich 美化输出
- **文字题目解答**：AI 分步解题（审题→解题→答案→提示）
- **图片题目支持**：拖入 `images/` 后用 `@文件名` 引用，AI 识别后解答
- **HTML 公式导出**：MathJax 渲染 LaTeX，自动浏览器打开
- **多预设支持**：INI 配置文件，每个预设包含 API 密钥 + 地址 + 模型
- **用量追踪**：JSONL 持久化，80% 预算预警，费用自动计算
- **流式输出**：AI 回答逐字显示
- **作者信息**：启动 banner 和 `/about` 命令

### 配置系统

- `config.ini` INI 格式配置文件，`[main]` 节指定默认预设
- 每个预设包含 `api_key`、`base_url`、`model`（一个预设对应一个模型）
- 模型价格格式：`模型 ID[:输入价[:输出价]]`（每 1M tokens 美元）
- `/config` 和 `/profile` 命令运行时查看和切换预设

### 项目结构

```
Qsever/
├── main.py              # 程序入口，argparse 参数解析
├── requirements.txt     # 依赖：openai, rich, prompt-toolkit, Pillow
├── LICENSE              # MIT 许可证
├── README.md            # 项目说明
├── CHANGELOG.md         # 本文件
├── config.example.ini   # 配置模板
├── build.spec           # PyInstaller 主程序打包配置
├── build_all.bat        # 一键打包脚本
├── installer.py         # 安装程序模板
├── make_installer.py    # 安装程序生成器
├── .gitignore
├── qsever/              # 核心包
│   ├── __init__.py      # 版本号 v0.1.0
│   ├── cli.py           # CLI 主循环，指令解析，rich 美化输出
│   ├── client.py        # OpenAI 兼容 API 客户端，流式 + 重试
│   ├── config.py        # Settings dataclass，INI 多预设加载
│   ├── conversation.py  # 对话历史，token 截断，会话保存/加载
│   ├── image_handler.py # 图片扫描，base64 编码，vision content 构造
│   ├── html_exporter.py # HTML 模板，Markdown→HTML 转换，浏览器打开
│   ├── usage.py         # UsageTracker，JSONL 持久化，费用计算
│   ├── prompts.py       # 高中解题 system prompt
│   └── exceptions.py    # 自定义异常
├── images/              # 图片目录
├── data/                # 数据目录
└── output/              # 输出目录
```

### 技术细节

- **配置文件**：INI 格式（Python 内置 configparser），无硬编码
- **流式输出**：Python generator yield，非多线程
- **打包方案**：PyInstaller onefile + Python 自释放安装器（base64 嵌入）
- **安装程序大小**：~40MB，主程序 ~33MB
