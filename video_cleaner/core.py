from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}


class ProcessingMode(StrEnum):
    LOSSLESS = "lossless"
    REENCODE = "reencode"


@dataclass(slots=True)
class ProcessingResult:
    input_path: Path
    output_path: Path
    return_code: int
    stdout: str
    stderr: str


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def default_ffmpeg_path(base_dir: Path | None = None) -> Path:
    root = base_dir or app_base_dir()
    executable_names = ["ffmpeg.exe", "ffmpeg"] if sys.platform.startswith("win") else ["ffmpeg", "ffmpeg.exe"]
    candidates: list[Path] = []

    for executable in executable_names:
        candidates.append(root / "ffmpeg" / executable)
        candidates.append(root / "_internal" / "ffmpeg" / executable)

    frozen_bundle_dir = getattr(sys, "_MEIPASS", None)
    if frozen_bundle_dir:
        for executable in executable_names:
            candidates.append(Path(frozen_bundle_dir) / "ffmpeg" / executable)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def collect_video_files(paths: list[Path]) -> list[Path]:
    collected: list[Path] = []

    for source in paths:
        if source.is_file() and source.suffix.lower() in VIDEO_EXTENSIONS:
            collected.append(source.resolve())
            continue

        if source.is_dir():
            for candidate in sorted(source.rglob("*")):
                if candidate.is_file() and candidate.suffix.lower() in VIDEO_EXTENSIONS:
                    collected.append(candidate.resolve())

    return sorted(dict.fromkeys(collected))


def preferred_start_dir(paths: list[Path], fallback: Path) -> Path:
    for source in paths:
        if source.suffix.lower() in VIDEO_EXTENSIONS:
            return source.parent

        resolved = source.resolve()
        if resolved.is_dir():
            return resolved
    return fallback


def output_path_for_input(output_dir: Path, input_path: Path) -> Path:
    return output_dir / f"{input_path.stem}_clean{input_path.suffix}"


def ensure_unique_output_path(output_path: Path) -> Path:
    if not output_path.exists():
        return output_path

    index = 1
    while True:
        candidate = output_path.with_name(f"{output_path.stem}_{index}{output_path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def build_ffmpeg_command(
    ffmpeg_path: Path,
    input_path: Path,
    output_path: Path,
    mode: ProcessingMode,
) -> list[str]:
    command = [str(ffmpeg_path), "-y", "-i", str(input_path)]

    if mode == ProcessingMode.LOSSLESS:
        command.extend(["-map", "0", "-c", "copy", "-map_metadata", "-1", "-map_chapters", "-1"])
    elif mode == ProcessingMode.REENCODE:
        command.extend(
            [
                "-map",
                "0",
                "-map_metadata",
                "-1",
                "-map_chapters",
                "-1",
                "-c:v",
                "libx264",
                "-crf",
                "18",
                "-preset",
                "medium",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-c:s",
                "copy",
            ]
        )
    else:
        raise ValueError(f"Unsupported processing mode: {mode}")

    command.append(str(output_path))
    return command


def process_video(
    ffmpeg_path: Path,
    input_path: Path,
    output_dir: Path,
    mode: ProcessingMode,
) -> ProcessingResult:
    if not ffmpeg_path.exists():
        raise FileNotFoundError(f"找不到 ffmpeg：{ffmpeg_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"找不到输入文件：{input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = ensure_unique_output_path(output_path_for_input(output_dir, input_path))
    command = build_ffmpeg_command(ffmpeg_path, input_path, output_path, mode)
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")

    return ProcessingResult(
        input_path=input_path,
        output_path=output_path,
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
