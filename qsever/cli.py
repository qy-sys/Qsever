import re
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from .client import APIClient
from .config import Settings
from .conversation import Conversation
from .exceptions import APIError, ImageNotFound, QseverError
from .html_exporter import HTMLExporter
from .image_handler import ImageHandler
from .prompts import SOLVER_SYSTEM_PROMPT
from .usage import UsageTracker

console = Console()


class CLI:
    COMMANDS = {
        "/help": "显示帮助",
        "/config [名称]": "列出/切换预设",
        "/profile [名称]": "查看预设详情",
        "/images": "列出可用图片",
        "/usage": "查看用量和费用",
        "/html": "导出 HTML（/html on/off 控制自动打开）",
        "/clear": "清空对话历史",
        "/about": "显示作者和开源信息",
        "/exit": "退出",
    }

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = APIClient(settings)
        self.conversation = Conversation(SOLVER_SYSTEM_PROMPT)
        self.image_handler = ImageHandler(settings.images_dir)
        self.usage_tracker = UsageTracker(settings.data_dir, settings.budget_limit)
        self.html_exporter = HTMLExporter(settings.output_dir)
        self.session = PromptSession(history=InMemoryHistory())
        self.last_question = ""
        self.last_answer = ""
        self.auto_open_html = settings.auto_open_html

    def run(self):
        self._show_startup_banner()
        console.print("输入 [bold]/help[/bold] 查看所有命令\n")

        while True:
            try:
                user_input = self.session.prompt("\n[bold green]>[/bold green] ").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]再见！[/yellow]")
                break

            if not user_input:
                continue

            if user_input.startswith("/"):
                if not self._handle_command(user_input):
                    break
            else:
                self._handle_question(user_input)

    def _show_startup_banner(self):
        profile_names = ", ".join(self.settings.profiles.keys())
        current_model = self.settings.current_model
        lines = [
            "[bold cyan]Qsever v0.2.0 — 高中解题助手[/bold cyan]",
            "[dim]by 野山菌 | MIT License[/dim]",
            "[dim]GitHub: github.com/qy-sys/Qsever[/dim]",
            "[dim]B 站：space.bilibili.com/1048757404[/dim]",
            "[dim]QQ: 2575635669[/dim]",
            "",
            f"[bold]当前预设:[/bold] {self.settings.active_profile}",
            f"[bold]当前模型:[/bold] {current_model}",
            f"[bold]可用预设:[/bold] {profile_names}",
        ]
        console.print(Panel("\n".join(lines), border_style="cyan"))

    def _handle_command(self, command: str) -> bool:
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        if cmd == "/help":
            self._cmd_help()
        elif cmd == "/config":
            self._cmd_config(arg)
        elif cmd == "/profile":
            self._cmd_profile(arg)
        elif cmd == "/images":
            self._cmd_images()
        elif cmd == "/usage":
            self._cmd_usage()
        elif cmd == "/clear":
            self._cmd_clear()
        elif cmd == "/html":
            self._cmd_html(arg)
        elif cmd == "/about":
            self._cmd_about()
        elif cmd == "/exit":
            console.print("[yellow]再见！[/yellow]")
            return False
        else:
            console.print(f"[red]未知命令：{cmd}[/red]")
            console.print("输入 [bold]/help[/bold] 查看可用命令")

        return True

    def _handle_question(self, text: str):
        image_refs = self._parse_image_refs(text)
        clean_text = self._remove_image_refs(text)

        try:
            if image_refs:
                console.print(f"[dim]加载图片：{', '.join(image_refs)}[/dim]")
                vision_content = self.image_handler.build_vision_content(clean_text, image_refs)
                self.conversation.add_user_vision(vision_content)
            else:
                self.conversation.add_user_text(clean_text)

            self.conversation.trim_to_token_limit()

            console.print()
            full_response = []
            try:
                for chunk in self.client.chat(self.conversation.full_messages, self.settings.current_model):
                    console.print(chunk, end="")
                    full_response.append(chunk)
            except APIError as e:
                console.print(f"\n[red]{e}[/red]")
                self.conversation.messages.pop()
                return

            response_text = "".join(full_response)
            self.conversation.add_assistant(response_text)

            usage = self.client.last_usage
            if usage:
                prompt_tokens = getattr(usage, "prompt_tokens", 0)
                completion_tokens = getattr(usage, "completion_tokens", 0)
                self.usage_tracker.record(
                    self.settings.current_model,
                    prompt_tokens,
                    completion_tokens,
                    self.settings.input_price,
                    self.settings.output_price,
                )
                console.print(f"\n[dim][tokens: {prompt_tokens} in / {completion_tokens} out][/dim]")

            warning = self.usage_tracker.check_budget_warning()
            if warning:
                console.print(f"[yellow]{warning}[/yellow]")

            self.last_question = clean_text
            self.last_answer = response_text
            self._export_html(clean_text, response_text)

        except ImageNotFound as e:
            console.print(f"[red]{e}[/red]")
            self.conversation.messages.pop()
        except QseverError as e:
            console.print(f"[red]{e}[/red]")

    def _parse_image_refs(self, text: str) -> list[str]:
        pattern = r"@(\S+\.(?:png|jpg|jpeg|webp|gif))"
        return re.findall(pattern, text, re.IGNORECASE)

    def _remove_image_refs(self, text: str) -> str:
        return re.sub(r"@\S+\.(?:png|jpg|jpeg|webp|gif)\s*", "", text, flags=re.IGNORECASE).strip()

    def _cmd_help(self):
        console.print("\n[bold]可用命令:[/bold]")
        for cmd, desc in self.COMMANDS.items():
            console.print(f"  [cyan]{cmd:40}[/cyan] {desc}")

        console.print("\n[bold]配置说明:[/bold]")
        console.print("  配置文件：config.ini")
        console.print("  每个预设包含：api_key + base_url + model")
        console.print("  模型价格格式：模型 ID[:输入价 [:输出价]]（每 1M tokens 美元）")
        console.print("  例：model = qwen/qwen3.8-flash:0.2:0.5")

        console.print("\n[bold]图片引用:[/bold]")
        console.print("  将图片拖入 images/ 目录，然后在题目中使用 @文件名 引用")
        console.print("  例：[green]解这道题 @math1.png[/green]")

    def _cmd_config(self, arg: str | None):
        if not arg:
            self._list_configs()
            return

        profile_name = arg.strip()
        if profile_name not in self.settings.profiles:
            console.print(f"[red]未找到预设：{profile_name}[/red]")
            console.print("输入 [bold]/config[/bold] 查看所有预设")
            return

        self._switch_config(profile_name)

    def _list_configs(self):
        console.print("\n[bold]可用预设:[/bold]\n")
        for name, profile in self.settings.profiles.items():
            current = " [green]← 当前[/green]" if name == self.settings.active_profile else ""
            console.print(f"  [cyan]{name}[/cyan] — {profile.model_id}{current}")
        console.print(f"\n共 {len(self.settings.profiles)} 个预设")

    def _switch_config(self, profile_name: str):
        self.settings.active_profile = profile_name
        self.client = APIClient(self.settings)
        console.print(f"[green]已切换到预设：{profile_name}[/green]")
        console.print(f"  模型：{self.settings.current_model}")

    def _cmd_profile(self, arg: str | None):
        profile_name = arg.strip() if arg else self.settings.active_profile

        if profile_name not in self.settings.profiles:
            console.print(f"[red]未找到预设：{profile_name}[/red]")
            return

        profile = self.settings.profiles[profile_name]
        masked_key = self._mask_api_key(profile.api_key)

        console.print(f"\n[bold]预设：{profile.name}[/bold]\n")
        console.print(f"  API 密钥：{masked_key}")
        console.print(f"  API 地址：{profile.base_url}")
        console.print(f"  模型：{profile.model_id}")
        if profile.input_price or profile.output_price:
            console.print(f"  价格：${profile.input_price:.2f} / ${profile.output_price:.2f} per 1M tokens")
        else:
            console.print(f"  价格：未设置")

    def _mask_api_key(self, key: str) -> str:
        if len(key) <= 8:
            return key[:2] + "****" + key[-2:] if len(key) > 4 else "****"
        return key[:4] + "****" + key[-4:]

    def _cmd_images(self):
        images = self.image_handler.list_images()
        if not images:
            console.print("[dim]images/ 目录中没有图片[/dim]")
            console.print("将图片拖入 images/ 目录后即可使用")
            return

        console.print("\n[bold]可用图片:[/bold]\n")
        for i, img in enumerate(images, 1):
            size_kb = img.stat().st_size / 1024
            console.print(f"  {i}. [cyan]{img.name}[/cyan] ({size_kb:.0f} KB)")
        console.print(f"\n共 {len(images)} 张图片")

    def _cmd_usage(self):
        summary = self.usage_tracker.session_summary()
        console.print("\n[bold]本次会话用量:[/bold]\n")
        console.print(f"  请求数：{summary['total_requests']}")
        console.print(f"  总 tokens: {summary['total_tokens']:,} (入 {summary['total_prompt_tokens']:,} / 出 {summary['total_completion_tokens']:,})")
        console.print(f"  总费用：${summary['total_cost']:.4f}")
        console.print(f"  剩余预算：${summary['remaining_budget']:.4f}")

    def _cmd_clear(self):
        self.conversation.clear()
        console.print("[green]对话历史已清空[/green]")

    def _cmd_html(self, arg: str | None):
        if arg and arg.lower() == "on":
            self.auto_open_html = True
            console.print("[green]已开启自动打开 HTML[/green]")
        elif arg and arg.lower() == "off":
            self.auto_open_html = False
            console.print("[yellow]已关闭自动打开 HTML[/yellow]")
        else:
            if not self.last_question or not self.last_answer:
                console.print("[red]暂无问答记录可导出[/red]")
                return
            filepath = self._export_html(self.last_question, self.last_answer, force_open=True)
            if filepath:
                console.print(f"[green]已生成 HTML：{filepath.name}[/green]")

    def _cmd_about(self):
        console.print("\n[bold]Qsever v0.2.0 — 高中解题助手[/bold]\n")
        console.print("  作者：野山菌")
        console.print("  GitHub：github.com/qy-sys/Qsever")
        console.print("  B 站：space.bilibili.com/1048757404")
        console.print("  QQ：2575635669")
        console.print("\n  开源协议：MIT License")
        console.print("  源码：github.com/qy-sys/Qsever\n")

    def _export_html(self, question: str, answer: str, force_open: bool = False) -> Path | None:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            filepath = self.html_exporter.export(question, answer, timestamp)
            if self.auto_open_html or force_open:
                self.html_exporter.open_in_browser(filepath)
            return filepath
        except Exception as e:
            console.print(f"[red]HTML 导出失败：{e}[/red]")
            return None
