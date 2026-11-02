"""Assemble an offline Python runtime for Inno Setup (run on Windows CI)."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PAYLOAD = ROOT / "build" / "windows"


def main():
    if sys.platform != "win32":
        raise SystemExit("Build the Windows installer on Windows")
    PAYLOAD.mkdir(parents=True, exist_ok=True)
    runtime = PAYLOAD / "python"
    shutil.copytree(Path(sys.executable).parent, runtime, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    python = runtime / "python.exe"
    subprocess.run([str(python), "-c", "import sys,tkinter; from pathlib import Path; assert Path(sys.prefix).resolve() == Path(sys.executable).resolve().parent"], check=True)
    subprocess.run([sys.executable, "-m", "uv", "pip", "install", "--python", str(python),
                    "--overrides", str(ROOT / "requirements-security.txt"),
                    "-r", str(ROOT / "requirements.txt")], check=True)
    backend = PAYLOAD / "backend"
    for directory in ("app", "apps/pc"):
        shutil.copytree(ROOT / directory, backend / directory, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(ROOT / "apps/__init__.py", backend / "apps/__init__.py")
    for filename in ("LICENSE", "config.example.toml", "pyproject.toml", "cli.py"):
        shutil.copy2(ROOT / filename, backend / filename)
    fonts = backend / "resource/fonts"
    fonts.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "resource/fonts/BeVietnamPro-Medium.ttf", fonts)
    # ImageIO ships its FFmpeg executable in the installed wheel.
    env = os.environ.copy()
    env["MPT_HOME"] = str(ROOT / "build/smoke-data")
    subprocess.run([str(python), "-c", "import imageio_ffmpeg; import apps.pc.server; from app.asgi import app; print(imageio_ffmpeg.get_ffmpeg_exe()); print('Engine import OK')"], cwd=backend, env=env, check=True)


if __name__ == "__main__":
    main()
