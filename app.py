from __future__ import annotations

import threading
from queue import Empty, Queue
from pathlib import Path
from tkinter import END, BOTH, LEFT, RIGHT, StringVar, Text, Tk, filedialog, messagebox, ttk

from video_cleaner.core import (
    ProcessingMode,
    app_base_dir,
    collect_video_files,
    default_ffmpeg_path,
    preferred_start_dir,
    process_video,
)


class VideoCleanerApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Video Cleaner")
        self.root.geometry("860x620")
        self.root.minsize(760, 560)

        self.base_dir = app_base_dir()
        self.inputs: list[Path] = []
        self.events: Queue[tuple[str, object]] = Queue()
        self.processing = False

        self.ffmpeg_var = StringVar(value=str(default_ffmpeg_path(self.base_dir)))
        self.output_var = StringVar(value=str(self.base_dir / "output"))
        self.mode_var = StringVar(value=ProcessingMode.LOSSLESS.value)
        self.status_var = StringVar(value="待命")

        self._build_ui()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill=BOTH, expand=True)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(5, weight=1)

        ttk.Label(container, text="ffmpeg 路径").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Entry(container, textvariable=self.ffmpeg_var).grid(row=0, column=1, sticky="ew", pady=6)
        ttk.Button(container, text="选择", command=self.choose_ffmpeg).grid(row=0, column=2, padx=(8, 0), pady=6)

        ttk.Label(container, text="输出目录").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(container, textvariable=self.output_var).grid(row=1, column=1, sticky="ew", pady=6)
        ttk.Button(container, text="选择", command=self.choose_output_dir).grid(row=1, column=2, padx=(8, 0), pady=6)

        mode_frame = ttk.LabelFrame(container, text="处理模式", padding=10)
        mode_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(12, 6))
        ttk.Radiobutton(mode_frame, text="无损模式", value=ProcessingMode.LOSSLESS.value, variable=self.mode_var).pack(
            side=LEFT, padx=(0, 12)
        )
        ttk.Radiobutton(mode_frame, text="重新编码模式", value=ProcessingMode.REENCODE.value, variable=self.mode_var).pack(
            side=LEFT
        )

        actions = ttk.Frame(container)
        actions.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(12, 6))
        ttk.Button(actions, text="添加文件", command=self.add_files).pack(side=LEFT)
        ttk.Button(actions, text="添加文件夹", command=self.add_folder).pack(side=LEFT, padx=8)
        ttk.Button(actions, text="清空列表", command=self.clear_inputs).pack(side=LEFT)
        self.process_button = ttk.Button(actions, text="开始处理", command=self.start_processing)
        self.process_button.pack(side=RIGHT)

        list_frame = ttk.LabelFrame(container, text="待处理项目", padding=10)
        list_frame.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(12, 6))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.input_list = Text(list_frame, height=10, wrap="none")
        self.input_list.grid(row=0, column=0, sticky="nsew")

        log_frame = ttk.LabelFrame(container, text="日志", padding=10)
        log_frame.grid(row=5, column=0, columnspan=3, sticky="nsew", pady=(12, 6))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = Text(log_frame, wrap="word")
        self.log_text.grid(row=0, column=0, sticky="nsew")

        ttk.Label(container, textvariable=self.status_var).grid(row=6, column=0, columnspan=3, sticky="w", pady=(8, 0))
        self.root.after(100, self._drain_events)

    def choose_ffmpeg(self) -> None:
        file_path = filedialog.askopenfilename(title="选择 ffmpeg 可执行文件")
        if file_path:
            self.ffmpeg_var.set(file_path)

    def choose_output_dir(self) -> None:
        initial_dir = preferred_start_dir(self.inputs, self.base_dir)
        directory = filedialog.askdirectory(title="选择输出目录", initialdir=str(initial_dir))
        if directory:
            self.output_var.set(directory)

    def add_files(self) -> None:
        file_paths = filedialog.askopenfilenames(
            title="选择视频文件",
            filetypes=[("视频文件", "*.mp4 *.mov *.m4v *.avi *.mkv"), ("全部文件", "*.*")],
        )
        if not file_paths:
            return
        self.inputs.extend(Path(path) for path in file_paths)
        self._refresh_inputs()

    def add_folder(self) -> None:
        directory = filedialog.askdirectory(title="选择视频文件夹")
        if not directory:
            return
        self.inputs.append(Path(directory))
        self._refresh_inputs()

    def clear_inputs(self) -> None:
        self.inputs.clear()
        self._refresh_inputs()

    def _refresh_inputs(self) -> None:
        self.input_list.delete("1.0", END)
        unique_inputs = list(dict.fromkeys(path.resolve() for path in self.inputs))
        self.inputs = unique_inputs
        for path in unique_inputs:
            self.input_list.insert(END, f"{path}\n")

    def log(self, message: str) -> None:
        self.log_text.insert(END, f"{message}\n")
        self.log_text.see(END)

    def start_processing(self) -> None:
        if self.processing:
            return

        self.processing = True
        self.process_button.state(["disabled"])
        self._clear_logs()
        self._set_status("准备处理中")
        worker = threading.Thread(target=self._process_worker, daemon=True)
        worker.start()

    def _process_worker(self) -> None:
        try:
            ffmpeg_path = Path(self.ffmpeg_var.get()).expanduser()
            output_dir = Path(self.output_var.get()).expanduser()
            mode = ProcessingMode(self.mode_var.get())

            if not self.inputs:
                raise ValueError("请先添加文件或文件夹。")

            files = collect_video_files(self.inputs)
            if not files:
                raise ValueError("没有找到可处理的视频文件。")

            self.events.put(("status", f"处理中，共 {len(files)} 个文件"))
            self.events.put(("log", f"ffmpeg：{ffmpeg_path}"))
            self.events.put(("log", f"输出目录：{output_dir}"))
            self.events.put(("log", f"模式：{mode}"))

            failures = 0
            for index, file_path in enumerate(files, start=1):
                self.events.put(("log", f"[{index}/{len(files)}] 开始：{file_path}"))
                result = process_video(ffmpeg_path=ffmpeg_path, input_path=file_path, output_dir=output_dir, mode=mode)
                if result.return_code == 0:
                    self.events.put(("log", f"完成：{result.output_path}"))
                else:
                    failures += 1
                    self.events.put(("log", f"失败：{file_path}"))
                    if result.stderr.strip():
                        self.events.put(("log", result.stderr.strip()))

            self.events.put(("finished", failures))
        except Exception as exc:  # noqa: BLE001
            self.events.put(("error", str(exc)))

    def _clear_logs(self) -> None:
        self.log_text.delete("1.0", END)

    def _set_status(self, value: str) -> None:
        self.status_var.set(value)

    def _finish_processing(self) -> None:
        self.processing = False
        self.process_button.state(["!disabled"])

    def _drain_events(self) -> None:
        try:
            while True:
                event_type, payload = self.events.get_nowait()
                if event_type == "status":
                    self._set_status(str(payload))
                elif event_type == "log":
                    self.log(str(payload))
                elif event_type == "finished":
                    failures = int(payload)
                    self._finish_processing()
                    if failures:
                        self._set_status(f"处理完成，失败 {failures} 个")
                        messagebox.showwarning("处理完成", f"处理结束，但有 {failures} 个文件失败。请看日志。")
                    else:
                        self._set_status("全部处理完成")
                        messagebox.showinfo("处理完成", "所有文件已处理完成。")
                elif event_type == "error":
                    self._finish_processing()
                    self._set_status("处理失败")
                    self.log(f"错误：{payload}")
                    messagebox.showerror("处理失败", str(payload))
        except Empty:
            pass
        finally:
            self.root.after(100, self._drain_events)


def main() -> None:
    root = Tk()
    ttk.Style().theme_use("clam")
    app = VideoCleanerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
