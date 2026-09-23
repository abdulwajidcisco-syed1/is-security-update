"""Kokoro narration and FFmpeg captioned-video generation."""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import wave


class MediaError(RuntimeError):
    pass


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str


MIN_ACTIVE_DURATION_SECONDS = 1_800
CAPTION_MAX_CHARS = 110


def narration_sections(episode):
    if episode.get("status") not in {"approved", "no_news"}:
        raise MediaError("Only approved content may be narrated")
    sections = [episode["title"], episode["summary"]]
    for segment in episode.get("segments", []):
        sections.extend((segment["heading"], segment["narration"]))
    sections.append(episode["outro"])
    return [text.strip() for text in sections if text and text.strip()]


def caption_chunks(text, maximum=CAPTION_MAX_CHARS):
    """Split narration into readable cues without changing spoken text."""
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    chunks = []
    for sentence in sentences:
        words = sentence.split()
        current = []
        for word in words:
            candidate = " ".join((*current, word))
            if current and len(candidate) > maximum:
                chunks.append(" ".join(current)); current = [word]
            else:
                current.append(word)
        if current:
            chunks.append(" ".join(current))
    return chunks


def _audio_array(result):
    audio = getattr(result, "audio", None)
    if audio is None and isinstance(result, tuple) and len(result) >= 3:
        audio = result[2]
    if audio is None:
        return None
    if hasattr(audio, "detach"):
        audio = audio.detach()
    if hasattr(audio, "cpu"):
        audio = audio.cpu()
    if hasattr(audio, "numpy"):
        audio = audio.numpy()
    return audio


def synthesize_wav(episode, output, voice="af_heart", speed=1.0, pipeline_factory=None):
    if pipeline_factory is None:
        try:
            from kokoro import KPipeline
        except ImportError as exc:
            raise MediaError("Kokoro is not installed; install pipeline/requirements-media.txt") from exc
        pipeline_factory = lambda: KPipeline(lang_code="a")
    try:
        import numpy as np
    except ImportError as exc:
        raise MediaError("NumPy is required for narration") from exc
    pipeline = pipeline_factory()
    output = Path(output); output.parent.mkdir(parents=True, exist_ok=True)
    cues, frame_count, sample_rate = [], 0, 24_000
    with wave.open(str(output), "wb") as target:
        target.setparams((1, 2, sample_rate, 0, "NONE", "not compressed"))
        for section in narration_sections(episode):
            for chunk in caption_chunks(section):
                chunk_start = frame_count / sample_rate
                wrote_chunk = False
                for result in pipeline(chunk, voice=voice, speed=speed, split_pattern=r"\n+"):
                    audio = _audio_array(result)
                    if audio is None:
                        continue
                    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
                    target.writeframes(pcm.tobytes()); frame_count += len(pcm); wrote_chunk = True
                if not wrote_chunk:
                    raise MediaError("Kokoro produced no audio for a narration chunk")
                cues.append(Cue(chunk_start, frame_count / sample_rate, chunk))
    if not frame_count:
        raise MediaError("Kokoro produced empty audio")
    return cues, frame_count / sample_rate


def _timestamp(seconds):
    milliseconds = max(0, round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    whole, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole:02d},{milliseconds:03d}"


def write_srt(cues, output):
    previous = 0.0; rows = []
    for index, cue in enumerate(cues, 1):
        if cue.start < previous or cue.end <= cue.start:
            raise MediaError("Caption timings must be positive and monotonic")
        rows.extend((str(index), f"{_timestamp(cue.start)} --> {_timestamp(cue.end)}", cue.text, ""))
        previous = cue.end
    Path(output).write_text("\n".join(rows), encoding="utf-8")


def _run(command):
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=900)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MediaError("Media encoder could not be executed") from exc
    if result.returncode:
        detail = (result.stderr or result.stdout)[-1000:]
        raise MediaError("Media encoding failed: " + detail)


def render_media(episode, output, voice="af_heart", speed=1.0, ffmpeg="ffmpeg", minimum_duration_seconds=0):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    wav, mp3, captions, video = (output / name for name in ("audio.wav", "audio.mp3", "captions.srt", "video.mp4"))
    cues, duration = synthesize_wav(episode, wav, voice, speed)
    if minimum_duration_seconds and duration < minimum_duration_seconds:
        raise MediaError(f"Scheduled video is shorter than {minimum_duration_seconds} seconds")
    write_srt(cues, captions)
    _run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav), "-codec:a", "libmp3lame", "-q:a", "2", str(mp3)])
    subtitle_path = captions.resolve().as_posix().replace(":", r"\:").replace("'", r"\'")
    _run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=0x0b1220:s=1920x1080:r=30", "-i", str(wav), "-vf", f"subtitles='{subtitle_path}':force_style='FontSize=34,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=80'", "-codec:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-codec:a", "aac", "-b:a", "160k", "-shortest", str(video)])
    metadata = {"schema_version": 1, "voice": voice, "speed": speed, "duration_seconds": round(duration, 3), "caption_count": len(cues), "artifacts": {}}
    for path in (wav, mp3, captions, video):
        if not path.is_file() or not path.stat().st_size:
            raise MediaError(f"Missing media artifact: {path.name}")
        metadata["artifacts"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path.read_bytes()).hexdigest()}
    (output / "media.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata
