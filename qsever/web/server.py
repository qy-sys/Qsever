import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from ..config import Settings
from ..exceptions import APIError
from .session import SessionManager


def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return key[:2] + "****" + key[-2:] if len(key) > 4 else "****"
    return key[:4] + "****" + key[-4:]


async def _stream_chat(session, messages: list[dict], model: str):
    loop = asyncio.get_event_loop()

    def _get_iterator():
        return session.client.chat(messages, model)

    iterator = await loop.run_in_executor(None, _get_iterator)

    while True:
        try:
            chunk = await loop.run_in_executor(None, next, iterator)
            yield chunk
        except StopIteration:
            break


def create_app(settings: Settings) -> FastAPI:
    session_mgr = SessionManager(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        await session_mgr.cleanup_all()

    app = FastAPI(title="Qsever", lifespan=lifespan)
    app.state.settings = settings
    app.state.session_mgr = session_mgr

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _get_session_id(request: Request) -> str:
        return request.headers.get("X-Session-ID", "default")

    @app.post("/api/chat")
    async def chat(request: Request):
        session_id = _get_session_id(request)
        body = await request.json()
        message = body.get("message", "").strip()
        image_files = body.get("images", [])

        if not message and not image_files:
            raise HTTPException(400, "消息不能为空")

        session = await session_mgr.get_or_create(session_id)

        if image_files:
            vision_content = session.image_handler.build_vision_content(message, image_files)
            session.conversation.add_user_vision(vision_content)
        else:
            session.conversation.add_user_text(message)
        session.conversation.trim_to_token_limit()

        async def event_generator():
            full_response = []
            try:
                async for chunk in _stream_chat(
                    session, session.conversation.full_messages, settings.current_model
                ):
                    full_response.append(chunk)
                    yield f"event: delta\ndata: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

                response_text = "".join(full_response)
                session.conversation.add_assistant(response_text)

                usage = session.client.last_usage
                if usage:
                    prompt_tokens = getattr(usage, "prompt_tokens", 0)
                    completion_tokens = getattr(usage, "completion_tokens", 0)
                    session.usage_tracker.record(
                        settings.current_model,
                        prompt_tokens,
                        completion_tokens,
                        settings.input_price,
                        settings.output_price,
                    )
                    yield f"event: usage\ndata: {json.dumps({'prompt_tokens': prompt_tokens, 'completion_tokens': completion_tokens}, ensure_ascii=False)}\n\n"

                yield "event: done\ndata: {}\n\n"

            except asyncio.CancelledError:
                if full_response:
                    session.conversation.add_assistant("".join(full_response))
            except APIError as e:
                if session.conversation.messages:
                    session.conversation.messages.pop()
                yield f"event: error\ndata: {json.dumps({'message': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.get("/api/config")
    async def get_config(request: Request):
        session = await session_mgr.get_or_create(_get_session_id(request))
        profiles = []
        for name, p in session.settings.profiles.items():
            profiles.append({
                "name": name,
                "model_id": p.model_id,
                "base_url": p.base_url,
                "api_key_masked": _mask_key(p.api_key),
            })
        return {"profiles": profiles, "active_profile": session.settings.active_profile}

    @app.put("/api/config/active")
    async def switch_profile(request: Request):
        body = await request.json()
        profile_name = body.get("profile", "")
        session = await session_mgr.get_or_create(_get_session_id(request))
        if session.settings.switch_profile(profile_name):
            from ..client import APIClient
            session.client = APIClient(session.settings)
            return {"ok": True, "active_profile": profile_name}
        raise HTTPException(404, f"预设不存在: {profile_name}")

    @app.get("/api/conversation")
    async def get_conversation(request: Request):
        session = await session_mgr.get_or_create(_get_session_id(request))
        return {"messages": session.conversation.messages}

    @app.delete("/api/conversation")
    async def clear_conversation(request: Request):
        session = await session_mgr.get_or_create(_get_session_id(request))
        session.conversation.clear()
        return {"ok": True}

    @app.get("/api/usage")
    async def get_usage(request: Request):
        session = await session_mgr.get_or_create(_get_session_id(request))
        return session.usage_tracker.session_summary()

    @app.get("/api/images")
    async def list_images(request: Request):
        session = await session_mgr.get_or_create(_get_session_id(request))
        images = session.image_handler.list_images()
        return {
            "images": [
                {"name": img.name, "size_kb": round(img.stat().st_size / 1024)}
                for img in images
            ]
        }

    @app.post("/api/images/upload")
    async def upload_image(request: Request, file: UploadFile = File(...)):
        session = await session_mgr.get_or_create(_get_session_id(request))
        dest = session.settings.images_dir / file.filename
        content = await file.read()
        dest.write_bytes(content)
        return {"ok": True, "filename": file.filename}

    @app.get("/api/images/file/{filename}")
    async def get_image(filename: str):
        from fastapi.responses import FileResponse
        import mimetypes

        # 遍历所有会话的 images_dir 查找文件
        for session in session_mgr.sessions.values():
            path = session.settings.images_dir / filename
            if path.exists():
                mime_type, _ = mimetypes.guess_type(str(path))
                return FileResponse(path, media_type=mime_type or "image/png")

        raise HTTPException(404, f"图片不存在：{filename}")

    static_dir = Path(__file__).parent / "static"
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app


def _find_available_port(host: str, start_port: int) -> int:
    import socket
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return port
            except OSError:
                port += 1
    raise RuntimeError(f"找不到可用端口（{start_port}-{start_port+99}）")


def start_server(settings: Settings, host: str = "127.0.0.1", port: int = 8765):
    import uvicorn
    app = create_app(settings)
    actual_port = _find_available_port(host, port)
    if actual_port != port:
        print(f"\n  端口 {port} 被占用，自动切换到 {actual_port}")
    print(f"\n  Qsever Web 启动中...")
    print(f"  打开浏览器访问: http://{host}:{actual_port}\n")
    uvicorn.run(app, host=host, port=actual_port, log_level="info")
