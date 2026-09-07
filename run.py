import sys
import subprocess
from pathlib import Path

# 确保在 Windows 终端中 UTF-8 字符及日志正常输出
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main():
    root_dir = Path(__file__).resolve().parent
    exe_path = root_dir / "release" / "todo-agent.exe"

    # 如果有用户传入参数则使用，无参数时默认使用 "gui" 模式
    args = sys.argv[1:] if len(sys.argv) > 1 else ["gui"]

    if exe_path.exists():
        cmd = [str(exe_path)] + args
        print(f"[*] 正在启动 Todo Agent 原生 GUI 桌面客户端: {exe_path}")
        if len(sys.argv) > 1:
            print(f"[*] 传递参数: {' '.join(sys.argv[1:])}")

        try:
            result = subprocess.run(cmd)
            sys.exit(result.returncode)
        except KeyboardInterrupt:
            print("\n[退出] 应用已停止。")
        except Exception as e:
            print(f"[异常] 启动失败: {e}")
            sys.exit(1)
    else:
        # 如果尚未打包 EXE，直接以 Python 模式启动原生 GUI 窗口
        print("[*] 未检测到 release/todo-agent.exe，正在直接通过 Python 启动 GUI 桌面应用...")
        from backend.main import run_gui, run_cli, run_server

        if args and args[0] == "cli":
            run_cli()
        elif args and args[0] == "server":
            run_server(open_web=False)
        elif args and args[0] == "--web":
            run_server(open_web=True)
        else:
            run_gui()


if __name__ == "__main__":
    main()
