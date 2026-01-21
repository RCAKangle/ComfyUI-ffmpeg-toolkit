import shutil
import subprocess
from typing import Iterable


class FFmpegError(RuntimeError):
    pass


def _ffmpeg_path() -> str | None:
    return shutil.which("ffmpeg")


def run_ffmpeg(args: Iterable[str]) -> None:
    ffmpeg = _ffmpeg_path()
    if not ffmpeg:
        raise FFmpegError("FFmpeg not found. Install it and ensure it is in PATH.")

    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error"]
    cmd.extend(list(args))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        message = result.stderr.strip()
        if not message:
            message = f"FFmpeg failed with exit code {result.returncode}"
        raise FFmpegError(message)
