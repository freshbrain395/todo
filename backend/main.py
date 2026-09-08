import socket
import sys
import threading
import time
import webbrowser
import uvicorn
from backend.api.app import app
from backend.cli import run_cli


class ServerThread(threading.Thread):
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.config = uvicorn.Config(app, host=host, port=port, log_level="warning")
        self.server = uvicorn.Server(self.config)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def wait_for_server(host: str = "127.0.0.1", port: int = 8000, timeout: float = 6.0) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.3):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.08)
    return False


def open_browser(url: str, delay: float = 1.0):
    def _open():
        time.sleep(delay)
        webbrowser.open(url)

    t = threading.Thread(target=_open, daemon=True)
    t.start()


def run_gui(host: str = "127.0.0.1", port: int = 8000):
    """使用 pywebview 启动无边框/原生桌面客户端窗口"""
    import webview

    server_thread = ServerThread(host, port)
    server_thread.start()

    ready = wait_for_server(host, port)
    if not ready:
        print("[警告] 等待后端服务启动超时，直接尝试启动窗口...")

    url = f"http://{host}:{port}"
    print(f"🚀 正在启动 Todo Agent 原生桌面窗口 ({url})")

    # 创建独立桌面 GUI 窗口
    window = webview.create_window(
        title="Todo Agent",
        url=url,
        width=1240,
        height=820,
        min_size=(960, 600),
        text_select=True,
    )

    # 启动 GUI 事件循环（阻塞直到用户关闭窗口）
    webview.start()
    print("\n👋 窗口已关闭，程序退出。")


def run_server(host: str = "127.0.0.1", port: int = 8000, open_web: bool = False):
    print(f"🚀 Todo Agent 服务正在运行: http://{host}:{port}")
    if open_web:
        open_browser(f"http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "gui":
            sys.argv.pop(1)
            run_gui()
        elif cmd in ["web", "--web"]:
            sys.argv.pop(1)
            run_server(open_web=True)
        elif cmd == "server":
            sys.argv.pop(1)
            run_server(open_web=False)
        elif cmd == "cli":
            sys.argv.pop(1)
            run_cli()
        elif cmd in ["--help", "-h"]:
            print("Todo Agent")
            print("用法:")
            print("  todo                 启动 CLI 聊天模式 (默认)")
            print("  todo gui             启动原生桌面 GUI 客户端")
            print("  todo web             启动 Web 服务并自动打开浏览器")
            print("  todo server          仅启动后端服务 (不弹出浏览器)")
            print("  todo cli             启动交互式智能终端 CLI")
        else:
            # 兼容带有参数直接作为 CLI 启动
            run_cli()
    else:
        # 默认无参数：启动 CLI 聊天模式
        run_cli()


if __name__ == "__main__":
    main()

