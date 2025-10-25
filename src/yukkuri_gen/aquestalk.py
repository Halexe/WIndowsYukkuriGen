"""Integration utilities for generating audio clips with AquesTalk."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Optional, Tuple

from .parser import DialogueLine


@dataclass
class VoicePreset:
    """Configuration describing how to synthesize audio for a specific speaker.

    When ``use_text_file`` is enabled the dialogue text is written to a temporary
    file using ``text_file_encoding`` and the resulting path is provided via the
    ``{text_file}`` placeholder so command line tools such as ``aquostalk.exe``
    can consume it.
    """

    speaker: str
    command_template: str
    voice_id: Optional[str] = None
    speed: Optional[int] = None
    volume: Optional[int] = None

    use_text_file: bool = False
    text_file_encoding: str = "utf-8"
    text_file_suffix: str = ".txt"

    def build_command(self, text: str, output_path: Path) -> Tuple[List[str], Optional[Path]]:
        context = {
            "text": text,
            "speaker": self.speaker,
            "voice_id": self.voice_id or "",
            "speed": self.speed or "",
            "volume": self.volume or "",
            "output": str(output_path),
        }
        temp_path: Optional[Path] = None
        if self.use_text_file:
            with NamedTemporaryFile(
                "w",
                encoding=self.text_file_encoding,
                delete=False,
                suffix=self.text_file_suffix,
            ) as temp:
                temp.write(text)
                temp_path = Path(temp.name)
            context["text_file"] = str(temp_path)
        else:
            context["text_file"] = ""
        # コマンドテンプレートは引数単位でプレースホルダを差し替えるため、先に分解してから
        # `str.format` を適用する。こうすることで `{output}` や `{text}` に空白が含まれていても
        # 単一の引数として扱われ、Windows環境でも安全に実行できる。
        tokens = shlex.split(self.command_template, posix=os.name != "nt")
        return [token.format(**context) for token in tokens], temp_path


class AudioGenerationError(RuntimeError):
    pass


class AquesTalkGenerator:
    """Generate voice clips via the user supplied AquesTalk command templates."""

    def __init__(self, output_dir: Path, presets: dict[str, VoicePreset]) -> None:
        self.output_dir = output_dir
        self.presets = presets

    @classmethod
    def from_config(cls, output_dir: Path, config_path: Path) -> "AquesTalkGenerator":
        data = json.loads(config_path.read_text(encoding="utf-8"))
        presets = {
            entry["speaker"]: VoicePreset(**entry)
            for entry in data.get("presets", [])
        }
        return cls(output_dir=output_dir, presets=presets)

    def ensure_output_dir(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def synthesize(self, dialogues: Iterable[DialogueLine]) -> list[Path]:
        self.ensure_output_dir()
        generated: list[Path] = []
        for index, dialogue in enumerate(dialogues, start=1):
            preset = self.presets.get(dialogue.normalized_speaker())
            if preset is None:
                raise AudioGenerationError(f"No voice preset configured for speaker {dialogue.speaker!r}")

            output_path = self.output_dir / f"{index:04d}_{preset.speaker}.wav"
            command, temp_path = preset.build_command(dialogue.normalized_text(), output_path)
            command_args = list(command)
            try:
                subprocess.run(command_args, check=True)
            except subprocess.CalledProcessError as exc:
                raise AudioGenerationError(
                    f"AquesTalk command failed for speaker {dialogue.speaker!r}: {command_args}") from exc
            finally:
                if temp_path is not None:
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass

            generated.append(output_path)

        return generated
