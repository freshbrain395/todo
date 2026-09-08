from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FRONT_DIR = ROOT / "front"
FRONT_DIST = FRONT_DIR / "dist"
RELEASE_DIR = ROOT / "release"
BUILD_DIR = ROOT / "build"
PYINSTALLER_WORK_DIR = BUILD_DIR / "pyinstaller"
SPEC_FILE = ROOT / "todo-agent.spec"
INSTALLER_FILE = ROOT / "installer.iss"
EXE_FILE = RELEASE_DIR / "todo.exe"
INSTALLER_EXE = RELEASE_DIR / "Todo-Agent-Setup.exe"


def run(command: list[str], *, cwd: Path = ROOT) -> None:
    print(f"\n> {' '.join(command)}")
    subprocess.run(command, cwd=cwd, check=True)


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def find_iscc() -> str | None:
    if command_exists("iscc"):
        return shutil.which("iscc")

    candidates = [
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Inno Setup 6" / "ISCC.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def clean() -> None:
    print("==> Cleaning build outputs")
    for path in (FRONT_DIST, PYINSTALLER_WORK_DIR):
        if path.exists():
            shutil.rmtree(path)
    if EXE_FILE.exists():
        EXE_FILE.unlink()
    if INSTALLER_EXE.exists():
        INSTALLER_EXE.unlink()
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)


def build_frontend() -> None:
    print("==> Building frontend")
    if not command_exists("pnpm"):
        raise RuntimeError("未找到 pnpm，请先安装 Node.js 和 pnpm。")
    run(["pnpm", "--dir", "front", "build"])
    if not (FRONT_DIST / "index.html").exists():
        raise RuntimeError("前端构建完成，但 front/dist/index.html 不存在。")


def build_exe() -> None:
    print("==> Building Windows executable")
    if sys.platform != "win32":
        print("[警告] 当前不是 Windows。PyInstaller/安装器建议在 Windows 上构建最终发布包。")

    run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--noupx",
            "--onefile",
            "--name",
            "todo",
            "--distpath",
            str(RELEASE_DIR),
            "--workpath",
            str(PYINSTALLER_WORK_DIR),
            "--add-data",
            f"{FRONT_DIST}{os.pathsep}dist",
            "--collect-all",
            "uvicorn",
            "--collect-all",
            "fastapi",
            "--collect-all",
            "backend",
            "--collect-all",
            "webview",
            "--collect-all",
            "pythonnet",
            "--collect-all",
            "clr_loader",
            str(ROOT / "backend" / "main.py"),
        ]
    )

    if not EXE_FILE.exists():
        raise RuntimeError(f"PyInstaller 完成，但没有找到 {EXE_FILE}")
    print(f"✓ EXE: {EXE_FILE}")


def build_installer() -> None:
    print("==> Building installer")
    if not INSTALLER_FILE.exists():
        raise RuntimeError(f"找不到安装器脚本: {INSTALLER_FILE}")
    if not EXE_FILE.exists():
        raise RuntimeError(f"找不到 {EXE_FILE}，请先执行 exe 构建。")

    iscc = find_iscc()
    if not iscc:
        raise RuntimeError(
            "未找到 Inno Setup (ISCC.exe)。请安装 Inno Setup 6，或将 ISCC.exe 加入 PATH。"
        )

    run([iscc, str(INSTALLER_FILE)])

    if not INSTALLER_EXE.exists():
        raise RuntimeError(f"Inno Setup 完成，但没有找到 {INSTALLER_EXE}")
    print(f"✓ Installer: {INSTALLER_EXE}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Todo Agent Windows build/package tool")
    parser.add_argument(
        "target",
        nargs="?",
        choices=("all", "frontend", "exe", "installer", "clean"),
        default="all",
        help="构建目标：all/frontend/exe/installer/clean",
    )
    args = parser.parse_args()

    try:
        if args.target == "clean":
            clean()
            return 0

        RELEASE_DIR.mkdir(parents=True, exist_ok=True)

        if args.target == "frontend":
            build_frontend()
        elif args.target == "exe":
            build_frontend()
            build_exe()
        elif args.target == "installer":
            build_installer()
        else:
            clean()
            build_frontend()
            build_exe()
            build_installer()

        print("\n========================================")
        print(" Todo Agent build completed successfully")
        print("========================================")
        if EXE_FILE.exists():
            print(f"EXE:       {EXE_FILE}")
        if INSTALLER_EXE.exists():
            print(f"Installer: {INSTALLER_EXE}")
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"\n[失败] 命令执行失败，退出码: {exc.returncode}")
        return exc.returncode or 1
    except Exception as exc:
        print(f"\n[失败] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
