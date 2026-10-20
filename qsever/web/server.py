import asyncio
import json
import re
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from ..config import Settings, ConfigProfile
from ..exceptions import APIError
from .session import SessionManager


def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return key[:2] + "****" + key[-2:] if len(key) > 4 else "****"
    return key[:4] + "****" + key[-4:]


def _sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    name = re.sub(r'[^\w\u4e00-\u9fff.\-]', '_', name)
    if not name or name.startswith('.'):
        name = 'upload_' + name
    return name


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
                "input_price": p.input_price,
                "output_price": p.output_price,
            })
        return {
            "profiles": profiles, 
            "active_profile": session.settings.active_profile,
            "settings": {
                "budget_limit": session.settings.budget_limit,
                "auto_open_html": session.settings.auto_open_html,
            }
        }

    @app.put("/api/config/active")
    async def switch_profile(request: Request):
        body = await request.json()
        profile_name = body.get("profile", "")
        session = await session_mgr.get_or_create(_get_session_id(request))
        if session.settings.switch_profile(profile_name):
            from ..client import APIClient
            session.client = APIClient(session.settings)
            session.settings.save_config()
            return {"ok": True, "active_profile": profile_name}
        raise HTTPException(404, f"预设不存在: {profile_name}")

    @app.post("/api/config/profile")
    async def add_profile(request: Request):
        body = await request.json()
        name = body.get("name", "").strip()
        api_key = body.get("api_key", "").strip()
        base_url = body.get("base_url", "").strip()
        if not name or not api_key or not base_url:
            raise HTTPException(400, "预设名、API Key 和 Base URL 不能为空")
        
        session = await session_mgr.get_or_create(_get_session_id(request))
        profile = ConfigProfile(
            name=name,
            api_key=api_key,
            base_url=base_url,
            model_id=body.get("model_id", ""),
            input_price=float(body.get("input_price", 0)),
            output_price=float(body.get("output_price", 0)),
        )
        if not session.settings.add_profile(profile):
            raise HTTPException(409, f"预设名已存在：{name}")
        session.settings.save_config()
        return {"ok": True}

    @app.put("/api/config/profile/{name}")
    async def update_profile(name: str, request: Request):
        body = await request.json()
        session = await session_mgr.get_or_create(_get_session_id(request))
        updates = {}
        for field in ('api_key', 'base_url', 'model_id', 'input_price', 'output_price'):
            if field in body:
                updates[field] = body[field]
        
        if 'api_key' in updates and '****' in updates['api_key']:
            del updates['api_key']
        
        if not session.settings.update_profile(name, updates):
            raise HTTPException(404, f"预设不存在：{name}")
        session.settings.save_config()
        
        if name == session.settings.active_profile:
            from ..client import APIClient
            session.client = APIClient(session.settings)
        return {"ok": True}

    @app.delete("/api/config/profile/{name}")
    async def delete_profile(name: str, request: Request):
        session = await session_mgr.get_or_create(_get_session_id(request))
        if not session.settings.delete_profile(name):
            raise HTTPException(400, "无法删除：预设不存在或为最后一个预设")
        session.settings.save_config()
        return {"ok": True}

    @app.put("/api/config/settings")
    async def update_settings(request: Request):
        body = await request.json()
        session = await session_mgr.get_or_create(_get_session_id(request))
        session.settings.update_settings(body)
        session.settings.save_config()
        return {"ok": True}

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
                {
                    "name": img.name, 
                    "size_kb": round(img.stat().st_size / 1024),
                    "url": f"/api/images/file/{img.name}",
                }
                for img in images
            ]
        }

    @app.post("/api/images/upload")
    async def upload_image(request: Request, file: UploadFile = File(...)):
        session = await session_mgr.get_or_create(_get_session_id(request))
        safe_name = _sanitize_filename(file.filename)
        content = await file.read()
        compressed = session.image_handler.compress_image(content, safe_name)
        dest = session.settings.images_dir / safe_name
        dest.write_bytes(compressed)
        return {"ok": True, "filename": safe_name, 
                "original_size": len(content), "compressed_size": len(compressed)}

    @app.delete("/api/images/{filename}")
    async def delete_image(filename: str, request: Request):
        session = await session_mgr.get_or_create(_get_session_id(request))
        safe_name = Path(filename).name
        path = (session.settings.images_dir / safe_name).resolve()
        if not path.is_relative_to(session.settings.images_dir.resolve()):
            raise HTTPException(403, "非法路径")
        if not path.exists():
            raise HTTPException(404, "图片不存在")
        path.unlink()
        return {"ok": True}

    @app.get("/api/images/file/{filename}")
    async def get_image(filename: str):
        from fastapi.responses import FileResponse
        import mimetypes

        for session in session_mgr._sessions.values():
            path = (session.settings.images_dir / filename).resolve()
            if not path.is_relative_to(session.settings.images_dir.resolve()):
                raise HTTPException(403, "非法路径")
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
    import webbrowser
    import threading
    import sys
    import io
    
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    app = create_app(settings)
    actual_port = _find_available_port(host, port)
    if actual_port != port:
        print(f"\n  端口 {port} 被占用，自动切换到 {actual_port}")
    print(f"\n  Qsever Web 启动中...")
    print(f"  打开浏览器访问: http://{host}:{actual_port}\n")
    
    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open(f"http://{host}:{actual_port}")
    
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host=host, port=actual_port, log_level="info")
