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
    exe_path = root_dir / "release" / "todo.exe"
    if not exe_path.exists() and (root_dir / "release" / "todo-agent.exe").exists():
        exe_path = root_dir / "release" / "todo-agent.exe"

    # 如果有用户传入参数则使用，无参数时运行 run.py 默认拉起桌面客户端 "gui"
    args = sys.argv[1:] if len(sys.argv) > 1 else ["gui"]

    if exe_path.exists():
        cmd = [str(exe_path)] + args
        print(f"[*] 启动 Todo Agent ({exe_path})")
        if len(sys.argv) > 1:
            print(f"[*] 参数: {' '.join(sys.argv[1:])}")

        try:
            result = subprocess.run(cmd)
            sys.exit(result.returncode)
        except KeyboardInterrupt:
            print("\n[退出] 应用已停止。")
        except Exception as e:
            print(f"[异常] 启动失败: {e}")
            sys.exit(1)
    else:
        # 如果尚未打包 EXE，直接以 Python 模式调度
        from backend.main import main as backend_main
        sys.argv = [sys.argv[0]] + args
        backend_main()


if __name__ == "__main__":
    main()
