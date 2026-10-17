import asyncio
import time
from dataclasses import dataclass, field

from ..client import APIClient
from ..config import Settings
from ..conversation import Conversation
from ..image_handler import ImageHandler
from ..prompts import SOLVER_SYSTEM_PROMPT
from ..usage import UsageTracker


@dataclass
class WebSession:
    settings: Settings
    client: APIClient = field(init=False)
    conversation: Conversation = field(init=False)
    usage_tracker: UsageTracker = field(init=False)
    image_handler: ImageHandler = field(init=False)
    last_activity: float = field(default_factory=time.time)

    def __post_init__(self):
        self.client = APIClient(self.settings)
        self.conversation = Conversation(SOLVER_SYSTEM_PROMPT)
        self.usage_tracker = UsageTracker(self.settings.data_dir, self.settings.budget_limit)
        self.image_handler = ImageHandler(self.settings.images_dir)

    def touch(self):
        self.last_activity = time.time()


class SessionManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._sessions: dict[str, WebSession] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, session_id: str) -> WebSession:
        async with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = WebSession(self.settings)
            session = self._sessions[session_id]
            session.touch()
            return session

    async def cleanup(self, max_age_seconds: int = 3600):
        async with self._lock:
            now = time.time()
            expired = [
                sid for sid, s in self._sessions.items()
                if now - s.last_activity > max_age_seconds
            ]
            for sid in expired:
                del self._sessions[sid]

    async def cleanup_all(self):
        async with self._lock:
            self._sessions.clear()
