import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.api.routes import router


def get_dist_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "dist"
    root_dir = Path(__file__).resolve().parent.parent.parent
    front_dist = root_dir / "front" / "dist"
    if front_dist.exists():
        return front_dist
    return root_dir / "dist"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Todo Agent Backend",
        version="0.1.0",
        description="Python backend for Todo Agent application",
    )

    # 启用 CORS 跨域支持
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    dist_dir = get_dist_dir()
    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    def root(request: Request):
        accept = request.headers.get("accept", "")
        index_file = dist_dir / "index.html"
        # 浏览器常规请求 HTML 时优先返回前端界面
        if "text/html" in accept and index_file.exists():
            return FileResponse(str(index_file))
        # 兼容 API 状态探活及单元测试
        return {
            "status": "ok",
            "message": "Todo Agent Python Backend is running",
            "version": "0.1.0",
        }

    return app


app = create_app()
