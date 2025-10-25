"""Generate Final Cut Pro XML files that Premiere Pro can import."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional
import wave

from .parser import DialogueLine

DEFAULT_FRAME_RATE = 30
DEFAULT_AUDIO_SAMPLERATE = 44100


@dataclass
class TimelineClip:
    """Represents a clip in the generated timeline."""

    dialogue: DialogueLine
    audio_path: Optional[Path]
    duration_seconds: float

    def duration_frames(self, fps: int = DEFAULT_FRAME_RATE) -> int:
        return int(round(self.duration_seconds * fps))

    def start_timecode(self, start_frame: int, fps: int = DEFAULT_FRAME_RATE) -> str:
        seconds = start_frame / fps
        td = dt.timedelta(seconds=seconds)
        return self._format_timedelta(td)

    def end_timecode(self, start_frame: int, fps: int = DEFAULT_FRAME_RATE) -> str:
        end_seconds = (start_frame + self.duration_frames(fps)) / fps
        td = dt.timedelta(seconds=end_seconds)
        return self._format_timedelta(td)

    @staticmethod
    def _format_timedelta(td: dt.timedelta) -> str:
        total_seconds = int(td.total_seconds())
        frames = int(round((td.total_seconds() - total_seconds) * DEFAULT_FRAME_RATE))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"


class PremiereXmlBuilder:
    """Construct a minimal Final Cut XML file that can be imported in Premiere."""

    def __init__(self, fps: int = DEFAULT_FRAME_RATE) -> None:
        self.fps = fps

    def build_timeline(self, dialogues: Iterable[DialogueLine], audio_files: List[Path]) -> List[TimelineClip]:
        clips: List[TimelineClip] = []
        for index, dialogue in enumerate(dialogues):
            audio_path = audio_files[index] if index < len(audio_files) else None
            duration = self._estimate_duration(dialogue, audio_path)
            clips.append(TimelineClip(dialogue=dialogue, audio_path=audio_path, duration_seconds=duration))
        return clips

    def _estimate_duration(self, dialogue: DialogueLine, audio_path: Optional[Path]) -> float:
        if audio_path and audio_path.exists():
            try:
                with wave.open(str(audio_path), "rb") as handle:
                    frames = handle.getnframes()
                    rate = handle.getframerate() or DEFAULT_AUDIO_SAMPLERATE
                    return max(frames / float(rate), 0.1)
            except wave.Error:
                pass
        # Fallback: 0.18 seconds per character + 0.6 buffer
        return max(len(dialogue.normalized_text()) * 0.18 + 0.6, 1.2)

    def build_xml(self, project_name: str, clips: List[TimelineClip]) -> str:
        fps = self.fps
        audio_rate = DEFAULT_AUDIO_SAMPLERATE
        lines = [
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            "<!DOCTYPE xmeml> ",
            "<xmeml version=\"5\">",
            "  <sequence id=\"sequence-1\">",
            f"    <name>{self._escape(project_name)}</name>",
            "    <duration>0</duration>",
            "    <rate>",
            f"      <timebase>{fps}</timebase>",
            "      <ntsc>FALSE</ntsc>",
            "    </rate>",
            "    <media>",
            "      <video>",
            "        <format>",
            "          <samplecharacteristics>",
            f"            <rate><timebase>{fps}</timebase><ntsc>FALSE</ntsc></rate>",
            "            <width>1920</width>",
            "            <height>1080</height>",
            "            <anamorphic>FALSE</anamorphic>",
            "            <pixelaspectratio>square</pixelaspectratio>",
            "          </samplecharacteristics>",
            "        </format>",
            "        <track>",
        ]

        current_frame = 0
        for index, clip in enumerate(clips, start=1):
            start_tc = clip.start_timecode(current_frame, fps)
            end_tc = clip.end_timecode(current_frame, fps)
            lines.extend(
                [
                    f"          <generatoritem id=\"title-{index}\">",
                    f"            <name>{self._escape(clip.dialogue.speaker)} Subtitle</name>",
                    "            <generatoritemtype>text</generatoritemtype>",
                    "            <rate>",
                    f"              <timebase>{fps}</timebase>",
                    "              <ntsc>FALSE</ntsc>",
                    "            </rate>",
                    f"            <start>{start_tc}</start>",
                    f"            <end>{end_tc}</end>",
                    f"            <in>{start_tc}</in>",
                    f"            <out>{end_tc}</out>",
                    "            <alphatype>straight</alphatype>",
                    "            <effect>",
                    "              <name>Text</name>",
                    "              <effectid>text</effectid>",
                    "              <effectcategory>Text</effectcategory>",
                    "              <effecttype>text</effecttype>",
                    "              <mediatype>video</mediatype>",
                    "              <parameter authoringApp=\"PremierePro\">",
                    "                <parameterid>str</parameterid>",
                    "                <name>テキスト</name>",
                    f"                <value>{self._escape(self._build_caption_text(clip))}</value>",
                    "              </parameter>",
                    "              <parameter authoringApp=\"PremierePro\">",
                    "                <parameterid>style</parameterid>",
                    "                <name>スタイル</name>",
                    f"                <value>{self._style_for_speaker(clip.dialogue)}</value>",
                    "              </parameter>",
                    "            </effect>",
                    "          </generatoritem>",
                ]
            )
            current_frame += clip.duration_frames(fps)

        lines.extend([
            "        </track>",
            "      </video>",
            "      <audio>",
            "        <track>",
        ])

        current_frame = 0
        for index, clip in enumerate(clips, start=1):
            start_tc = clip.start_timecode(current_frame, fps)
            end_tc = clip.end_timecode(current_frame, fps)
            if clip.audio_path:
                lines.extend([
                    f"          <clipitem id=\"audio-{index}\">",
                    f"            <name>{self._escape(clip.audio_path.stem)}</name>",
                    f"            <start>{start_tc}</start>",
                    f"            <end>{end_tc}</end>",
                    f"            <in>{start_tc}</in>",
                    f"            <out>{end_tc}</out>",
                    "            <file>",
                    f"              <name>{self._escape(clip.audio_path.name)}</name>",
                    f"              <pathurl>file://{self._escape(str(clip.audio_path.resolve()))}</pathurl>",
                    "              <rate>",
                    f"                <timebase>{audio_rate}</timebase>",
                    "                <ntsc>FALSE</ntsc>",
                    "              </rate>",
                    "            </file>",
                    "          </clipitem>",
                ])
            current_frame += clip.duration_frames(fps)

        lines.extend([
            "        </track>",
            "      </audio>",
            "    </media>",
            "  </sequence>",
            "</xmeml>",
        ])

        return "\n".join(lines)

    def _style_for_speaker(self, dialogue: DialogueLine) -> str:
        speaker = dialogue.normalized_speaker()
        if speaker == "霊夢":
            return "リンクスタイル霊夢"
        if speaker == "魔理沙":
            return "リンクスタイル魔理沙"
        return "デフォルト字幕"

    def _build_caption_text(self, clip: TimelineClip) -> str:
        speaker = clip.dialogue.normalized_speaker()
        text = clip.dialogue.normalized_text()
        return f"{speaker}: {text}"

    @staticmethod
    def _escape(value: str) -> str:
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
