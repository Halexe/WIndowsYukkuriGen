"""Desktop GUI tool for generating Premiere Pro assets from a script."""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from typing import List

from src.yukkuri_gen.aquestalk import AquesTalkGenerator, AudioGenerationError
from src.yukkuri_gen.parser import DialogueLine, ScriptParser, ScriptParseError
from src.yukkuri_gen.premiere import PremiereXmlBuilder


class Application(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)
        self.master = master
        self.pack(fill=tk.BOTH, expand=True)
        self.master.title("WIndows Yukkuri Generator")
        self._build_widgets()

    def _build_widgets(self) -> None:
        # Configuration frame
        config_frame = ttk.LabelFrame(self, text="設定")
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        self.project_name_var = tk.StringVar(value="YukkuriProject")
        self.config_path_var = tk.StringVar(value=str(Path("aquestalk_presets.json")))
        self.audio_dir_var = tk.StringVar(value=str(Path("output/audio")))
        self.xml_output_var = tk.StringVar(value=str(Path("output/premiere")))

        self._add_labeled_entry(config_frame, "プロジェクト名", self.project_name_var, row=0)
        self._add_labeled_entry(config_frame, "AquesTalk設定", self.config_path_var, row=1, button=lambda: self._choose_file(self.config_path_var))
        self._add_labeled_entry(config_frame, "音声出力フォルダ", self.audio_dir_var, row=2, button=lambda: self._choose_directory(self.audio_dir_var))
        self._add_labeled_entry(config_frame, "Premiere XML出力", self.xml_output_var, row=3, button=lambda: self._choose_directory(self.xml_output_var))

        # Script text area
        script_frame = ttk.LabelFrame(self, text="台本")
        script_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.script_text = tk.Text(script_frame, wrap=tk.WORD, height=20)
        self.script_text.pack(fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(button_frame, text="台本を読み込み", command=self._load_script_file).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="音声生成", command=self._generate_audio).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Premiere XML生成", command=self._generate_premiere_xml).pack(side=tk.LEFT)

        # Log output
        log_frame = ttk.LabelFrame(self, text="ログ")
        log_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _add_labeled_entry(self, parent: ttk.Frame, label: str, variable: tk.StringVar, row: int, button=None) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, padx=5, pady=3, sticky=tk.W)
        entry = ttk.Entry(parent, textvariable=variable, width=50)
        entry.grid(row=row, column=1, padx=5, pady=3, sticky=tk.W)
        if button is not None:
            ttk.Button(parent, text="参照", command=button).grid(row=row, column=2, padx=5, pady=3)

    def _choose_file(self, variable: tk.StringVar) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if path:
            variable.set(path)

    def _choose_directory(self, variable: tk.StringVar) -> None:
        path = filedialog.askdirectory()
        if path:
            variable.set(path)

    def _load_script_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("読み込みエラー", str(exc))
            return
        self.script_text.delete("1.0", tk.END)
        self.script_text.insert(tk.END, text)
        self._log(f"台本を読み込みました: {path}")

    def _parse_script(self) -> List[DialogueLine]:
        content = self.script_text.get("1.0", tk.END)
        parser = ScriptParser()
        try:
            return parser.parse(content)
        except ScriptParseError as exc:
            messagebox.showerror("台本エラー", str(exc))
            raise

    def _generate_audio(self) -> None:
        try:
            dialogues = self._parse_script()
        except ScriptParseError:
            return

        config_path = Path(self.config_path_var.get())
        if not config_path.exists():
            messagebox.showerror("設定エラー", f"AquesTalk設定ファイルが見つかりません: {config_path}")
            return

        generator = AquesTalkGenerator.from_config(Path(self.audio_dir_var.get()), config_path)

        try:
            files = generator.synthesize(dialogues)
        except AudioGenerationError as exc:
            messagebox.showerror("音声生成エラー", str(exc))
            self._log(f"音声生成に失敗: {exc}")
            return

        self._log(f"音声を生成しました ({len(files)}件) -> {generator.output_dir}")

    def _generate_premiere_xml(self) -> None:
        try:
            dialogues = self._parse_script()
        except ScriptParseError:
            return

        audio_dir = Path(self.audio_dir_var.get())
        audio_files = sorted(audio_dir.glob("*.wav")) if audio_dir.exists() else []
        builder = PremiereXmlBuilder()
        clips = builder.build_timeline(dialogues, audio_files)
        xml_content = builder.build_xml(self.project_name_var.get(), clips)

        output_dir = Path(self.xml_output_var.get())
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{self.project_name_var.get()}.xml"
        output_path.write_text(xml_content, encoding="utf-8")
        self._log(f"Premiere XMLを出力しました: {output_path}")
        messagebox.showinfo("完了", f"Premiere XMLを出力しました\n{output_path}")

    def _log(self, message: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.configure(state=tk.DISABLED)
        self.log_text.see(tk.END)


def main() -> None:
    root = tk.Tk()
    app = Application(root)
    root.geometry("900x800")
    root.mainloop()


if __name__ == "__main__":
    main()
