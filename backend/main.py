import sys
import uvicorn
from backend.api.app import app
from backend.cli import run_cli


def run_server(host: str = "127.0.0.1", port: int = 8000):
    print(f"🚀 Todo Agent Python Server starting on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        sys.argv.pop(1)
        run_cli()
    elif len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Todo Agent")
        print("用法:")
        print("  uv run python -m backend.main [server|cli]")
        print("  uv run todo-server    启动 FastAPI HTTP/RPC 服务 (端口 8000)")
        print("  uv run todo-cli       启动交互式命令行终端")
    else:
        run_server()


if __name__ == "__main__":
    main()
