import os
import tempfile
import unittest
from pathlib import Path

from video_cleaner.core import (
    ProcessingMode,
    build_ffmpeg_command,
    collect_video_files,
    output_path_for_input,
    preferred_start_dir,
    default_ffmpeg_path,
    process_video,
)


class VideoCleanerCoreTests(unittest.TestCase):
    def test_collect_video_files_accepts_single_file_and_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            file_a = root / "a.mp4"
            file_b = root / "b.MP4"
            ignored = root / "note.txt"
            nested = root / "sub"
            nested.mkdir()
            nested_file = nested / "c.mp4"

            file_a.write_text("a")
            file_b.write_text("b")
            ignored.write_text("skip")
            nested_file.write_text("c")

            single = collect_video_files([file_a])
            batch = collect_video_files([root])

            self.assertEqual(single, [file_a.resolve()])
            self.assertEqual(batch, [file_a.resolve(), file_b.resolve(), nested_file.resolve()])

    def test_build_ffmpeg_command_for_lossless_mode(self) -> None:
        command = build_ffmpeg_command(
            ffmpeg_path=Path("D:/ffmpeg/bin/ffmpeg.exe"),
            input_path=Path("D:/video_work/sample.mp4"),
            output_path=Path("D:/video_clean/sample_clean.mp4"),
            mode=ProcessingMode.LOSSLESS,
        )

        self.assertEqual(
            command,
            [
                "D:/ffmpeg/bin/ffmpeg.exe",
                "-y",
                "-i",
                "D:/video_work/sample.mp4",
                "-map",
                "0",
                "-c",
                "copy",
                "-map_metadata",
                "-1",
                "-map_chapters",
                "-1",
                "D:/video_clean/sample_clean.mp4",
            ],
        )

    def test_build_ffmpeg_command_for_reencode_mode(self) -> None:
        command = build_ffmpeg_command(
            ffmpeg_path=Path("D:/ffmpeg/bin/ffmpeg.exe"),
            input_path=Path("D:/video_work/sample.mp4"),
            output_path=Path("D:/video_clean/sample_clean.mp4"),
            mode=ProcessingMode.REENCODE,
        )

        self.assertEqual(
            command,
            [
                "D:/ffmpeg/bin/ffmpeg.exe",
                "-y",
                "-i",
                "D:/video_work/sample.mp4",
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
                "D:/video_clean/sample_clean.mp4",
            ],
        )

    def test_output_path_for_input_appends_clean_suffix(self) -> None:
        output = output_path_for_input(Path("D:/out"), Path("D:/video_work/video_2.mp4"))
        self.assertEqual(output, Path("D:/out/video_2_clean.mp4"))

    def test_preferred_start_dir_uses_selected_video_parent(self) -> None:
        fallback = Path("D:/base")
        selected = [Path("D:/video_work/video_2.mp4")]
        self.assertEqual(preferred_start_dir(selected, fallback), Path("D:/video_work"))

    def test_default_ffmpeg_path_uses_internal_bundle_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            internal_ffmpeg = root / "_internal" / "ffmpeg"
            internal_ffmpeg.mkdir(parents=True)
            executable = internal_ffmpeg / "ffmpeg.exe"
            executable.write_text("stub")

            resolved = default_ffmpeg_path(root)

            self.assertEqual(resolved, executable)

    def test_process_video_raises_when_ffmpeg_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            input_path = root / "sample.mp4"
            input_path.write_text("data")

            with self.assertRaises(FileNotFoundError):
                process_video(
                    ffmpeg_path=root / "missing_ffmpeg",
                    input_path=input_path,
                    output_dir=root / "out",
                    mode=ProcessingMode.LOSSLESS,
                )

    def test_process_video_uses_unique_output_name_when_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            input_path = root / "sample.mp4"
            input_path.write_text("data")

            output_dir = root / "out"
            output_dir.mkdir()
            existing = output_dir / "sample_clean.mp4"
            existing.write_text("existing")

            ffmpeg_stub = root / "fake_ffmpeg"
            ffmpeg_stub.write_text(
                "#!/usr/bin/env python3\n"
                "from pathlib import Path\n"
                "import sys\n"
                "Path(sys.argv[-1]).write_text('generated')\n"
            )
            os.chmod(ffmpeg_stub, 0o755)

            result = process_video(
                ffmpeg_path=ffmpeg_stub,
                input_path=input_path,
                output_dir=output_dir,
                mode=ProcessingMode.LOSSLESS,
            )

            self.assertEqual(result.return_code, 0)
            self.assertEqual(result.output_path, output_dir / "sample_clean_1.mp4")
            self.assertEqual(result.output_path.read_text(), "generated")


if __name__ == "__main__":
    unittest.main()
