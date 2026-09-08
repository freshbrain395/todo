from pathlib import Path
from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH).resolve()
FRONT_DIST = ROOT / "front" / "dist"

if not (FRONT_DIST / "index.html").exists():
    raise SystemExit(
        "找不到前端构建产物 front/dist/index.html，请先运行 `python build.py frontend`。"
    )


datas = [(str(FRONT_DIST), "dist")]
binaries = []
hiddenimports = []

for package in (
    "uvicorn",
    "fastapi",
    "backend",
    "webview",
    "pythonnet",
    "clr_loader",
):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports


a = Analysis(
    [str(ROOT / "backend" / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="todo",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
