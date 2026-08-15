from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router


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

    @app.get("/")
    def root():
        return {
            "status": "ok",
            "message": "Todo Agent Python Backend is running",
            "version": "0.1.0",
        }

    return app


app = create_app()
