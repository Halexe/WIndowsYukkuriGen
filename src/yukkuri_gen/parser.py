"""Utilities for parsing scenario scripts into structured dialogue entries."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

SPEAKER_SEPARATOR = "\u3000"  # full width space


@dataclass
class DialogueLine:
    """Represents one line of dialogue in the script."""

    speaker: str
    text: str
    section: Optional[str] = None

    def normalized_speaker(self) -> str:
        return self.speaker.strip()

    def normalized_text(self) -> str:
        return " ".join(self.text.strip().split())


class ScriptParseError(Exception):
    """Raised when a script could not be parsed properly."""


class ScriptParser:
    """Parser that converts the domain specific script into dialogue entries."""

    def __init__(self, default_section: str | None = None) -> None:
        self.default_section = default_section

    def parse(self, text: str) -> List[DialogueLine]:
        section = self.default_section
        dialogues: List[DialogueLine] = []

        for raw_line in self._iter_lines(text):
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("- "):
                section = line[2:].strip() or section
                continue

            if SPEAKER_SEPARATOR in line:
                speaker, content = line.split(SPEAKER_SEPARATOR, 1)
                dialogues.append(DialogueLine(speaker=speaker.strip(), text=content.strip(), section=section))
                continue

            raise ScriptParseError(f"Invalid line format: {raw_line!r}")

        return dialogues

    def parse_file(self, path: Path) -> List[DialogueLine]:
        return self.parse(path.read_text(encoding="utf-8"))

    @staticmethod
    def _iter_lines(text: str) -> Iterable[str]:
        for raw_line in text.splitlines():
            yield raw_line
