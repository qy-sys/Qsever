import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class RequestLog:
    timestamp: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    estimated_cost: float


class UsageTracker:
    def __init__(self, data_dir: Path, budget_limit: float):
        self.data_dir = data_dir
        self.budget_limit = budget_limit
        self.logs: list[RequestLog] = []
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._load_history()

    def _load_history(self):
        log_file = self.data_dir / "usage.jsonl"
        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            self.logs.append(RequestLog(**data))
                        except json.JSONDecodeError:
                            pass

    def record(self, model: str, prompt_tokens: int, completion_tokens: int, input_price: float = 0.0, output_price: float = 0.0):
        cost = (prompt_tokens / 1_000_000) * input_price + (completion_tokens / 1_000_000) * output_price

        log = RequestLog(
            timestamp=datetime.now().isoformat(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            estimated_cost=cost,
        )
        self.logs.append(log)

        log_file = self.data_dir / "usage.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(log), ensure_ascii=False) + "\n")

    def session_summary(self) -> dict:
        total_requests = len(self.logs)
        total_prompt = sum(l.prompt_tokens for l in self.logs)
        total_completion = sum(l.completion_tokens for l in self.logs)
        total_cost = sum(l.estimated_cost for l in self.logs)
        remaining = self.budget_limit - total_cost
        return {
            "total_requests": total_requests,
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_prompt + total_completion,
            "total_cost": total_cost,
            "remaining_budget": remaining,
        }

    def check_budget_warning(self) -> str | None:
        if self.budget_limit < 0:
            return None
        summary = self.session_summary()
        usage_ratio = summary["total_cost"] / self.budget_limit if self.budget_limit > 0 else 0
        if usage_ratio >= 0.8:
            return f"️  预算已使用 {usage_ratio:.0%}，剩余 ${summary['remaining_budget']:.2f}"
        return None
