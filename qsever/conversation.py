import json
from pathlib import Path
from typing import Optional


class Conversation:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.messages: list[dict] = []

    @property
    def full_messages(self) -> list[dict]:
        return [{"role": "system", "content": self.system_prompt}] + self.messages

    def add_user_text(self, text: str):
        self.messages.append({"role": "user", "content": text})

    def add_user_vision(self, content: list[dict]):
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, text: str):
        self.messages.append({"role": "assistant", "content": text})

    def clear(self):
        self.messages.clear()

    def trim_to_token_limit(self, max_tokens: int = 8000):
        """粗略估算 token 数，超出时从最早消息开始截断"""
        while len(self.messages) > 2:
            estimated = sum(len(m.get("content", "")) * 0.5 for m in self.full_messages)
            if estimated <= max_tokens:
                break
            self.messages.pop(0)

    def save_session(self, path: Path):
        data = {
            "system_prompt": self.system_prompt,
            "messages": self.messages,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_session(self, path: Path):
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.system_prompt = data.get("system_prompt", self.system_prompt)
        self.messages = data.get("messages", [])
