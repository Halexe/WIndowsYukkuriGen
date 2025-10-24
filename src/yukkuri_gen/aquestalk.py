"""Integration utilities for generating audio clips with AquesTalk."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from .parser import DialogueLine


@dataclass
class VoicePreset:
    """Configuration describing how to synthesize audio for a specific speaker."""

    speaker: str
    command_template: str
    voice_id: Optional[str] = None
    speed: Optional[int] = None
    volume: Optional[int] = None

    def build_command(self, text: str, output_path: Path) -> Iterable[str]:
        template = self.command_template.format(
            text=text,
            speaker=self.speaker,
            voice_id=self.voice_id or "",
            speed=self.speed or "",
            volume=self.volume or "",
            output=str(output_path),
        )
        # Windowsのパスでは `C:\Program Files` のように空白やバックスラッシュを含むケースが
        # 多いため、実行環境に合わせて `shlex.split` の `posix` フラグを切り替える。
        # これにより、ユーザーがテンプレートにフルパスを指定した場合でも正しく実行できる。
        return shlex.split(template, posix=os.name != "nt")


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
            command = list(preset.build_command(dialogue.normalized_text(), output_path))
            try:
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError as exc:
                raise AudioGenerationError(
                    f"AquesTalk command failed for speaker {dialogue.speaker!r}: {command}") from exc

            generated.append(output_path)

        return generated
