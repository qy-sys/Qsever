import time
from typing import Iterator, Optional

import openai
from rich.console import Console

from .config import Settings
from .exceptions import APIError

console = Console()


class APIClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = openai.OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
        )

    def chat(
        self,
        messages: list[dict],
        model: str,
        stream: bool = True,
    ) -> Iterator[str]:
        max_retries = 3

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=stream,
                )

                if stream:
                    full_content = []
                    usage = None
                    for chunk in response:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_content.append(content)
                            yield content
                        if chunk.usage:
                            usage = chunk.usage

                    if usage:
                        self._last_usage = usage
                    else:
                        estimated = sum(len(c) for c in full_content)
                        self._last_usage = type("Usage", (), {
                            "prompt_tokens": 0,
                            "completion_tokens": estimated,
                        })()
                    return
                else:
                    self._last_usage = response.usage
                    yield response.choices[0].message.content
                    return

            except openai.APITimeoutError as e:
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 3
                    console.print(f"[yellow]请求超时，{wait}秒后重试...[/yellow]")
                    time.sleep(wait)
                else:
                    raise APIError(f"API 请求超时: {e}")
            except openai.RateLimitError as e:
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 5
                    console.print(f"[yellow]请求限流，{wait}秒后重试...[/yellow]")
                    time.sleep(wait)
                else:
                    raise APIError(f"API 请求限流: {e}")
            except openai.APIError as e:
                raise APIError(f"API 错误: {e}")

    @property
    def last_usage(self) -> Optional[object]:
        return getattr(self, "_last_usage", None)
