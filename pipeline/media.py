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
VISUAL_ACCENT = "0x22d3ee"


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


def _visual_kind(text):
    lowered = text.casefold()
    for words, kind in (
        (("database", "sql", "postgres", "mysql"), "DATABASE SECURITY"),
        (("identity", "credential", "oauth", "access"), "IDENTITY & ACCESS"),
        (("cloud", "saas", "service"), "CLOUD & SERVICES"),
        (("ransomware", "malware", "breach", "incident"), "THREAT ACTIVITY"),
        (("patch", "update", "release", "version"), "PATCH & RELEASE"),
    ):
        if any(word in lowered for word in words):
            return kind
    return "SECURITY UPDATE"


def visual_scenes(episode, cues):
    """Build evidence-safe visual cards aligned to the spoken headings."""
    if not cues:
        return []
    starts = {cue.text: cue.start for cue in cues}
    sections = [(episode["title"], "DAILY SECURITY BRIEFING", episode.get("summary", ""), [])]
    for segment in episode.get("segments", []):
        sections.append((segment["heading"], _visual_kind(segment["heading"] + " " + segment.get("narration", "")), segment.get("narration", ""), segment.get("source_urls", [])))
    sections.append((episode["outro"], "BRIEFING COMPLETE", "", []))
    scenes = []
    for index, (heading, label, detail, sources) in enumerate(sections):
        start = starts.get(heading)
        if start is None:
            continue
        identifiers = sorted(set(re.findall(r"\bCVE-\d{4}-\d{4,}\b", heading + " " + detail, re.I)))[:4]
        scenes.append({
            "start": round(start, 3),
            "end": 0.0,
            "label": label,
            "heading": " ".join(heading.split())[:120],
            "identifiers": identifiers,
            "source_count": len(set(sources)),
        })
    for index, scene in enumerate(scenes):
        scene["end"] = round(scenes[index + 1]["start"] if index + 1 < len(scenes) else cues[-1].end, 3)
    return scenes


def write_visual_ass(scenes, output):
    """Write top-of-frame chapter cards; spoken captions remain independent."""
    def stamp(value):
        hours, remainder = divmod(max(0, value), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}:{int(minutes):02d}:{seconds:05.2f}"

    def safe(value):
        return str(value).replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}").replace("\n", " ")

    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Card,Arial,48,&H00FFFFFF,&H000000FF,&H00231A0B,&H990B1220,1,0,0,0,100,100,0,0,3,2,0,8,120,120,90,1
Style: Label,Arial,25,&H00EED322,&H000000FF,&H00231A0B,&H000B1220,1,0,0,0,100,100,2,0,1,1,0,8,120,120,45,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    rows = [header]
    for scene in scenes:
        ids = "  |  ".join(scene["identifiers"])
        evidence = f"  •  {scene['source_count']} cited source" + ("s" if scene["source_count"] != 1 else "") if scene["source_count"] else ""
        rows.append(f"Dialogue: 0,{stamp(scene['start'])},{stamp(scene['end'])},Label,,0,0,0,,{safe(scene['label'] + (('  •  ' + ids) if ids else '') + evidence)}\n")
        rows.append(f"Dialogue: 0,{stamp(scene['start'])},{stamp(scene['end'])},Card,,0,0,0,,{{\\fad(350,350)}}{safe(scene['heading'])}\n")
    Path(output).write_text("".join(rows), encoding="utf-8")


def _run(command, timeout=900):
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)
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
    scenes = visual_scenes(episode, cues)
    visuals = output / "visuals.ass"
    write_visual_ass(scenes, visuals)
    (output / "visual_plan.json").write_text(json.dumps({"schema_version": 1, "scenes": scenes}, indent=2) + "\n", encoding="utf-8")
    _run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav), "-codec:a", "libmp3lame", "-q:a", "2", str(mp3)])
    subtitle_path = captions.resolve().as_posix().replace(":", r"\:").replace("'", r"\'")
    visual_path = visuals.resolve().as_posix().replace(":", r"\:").replace("'", r"\'")
    filters = (
        "[0:v]drawgrid=w=90:h=90:t=2:c=0x1e3a5f@0.35:x='mod(t*28,90)':y='mod(t*14,90)',"
        f"drawbox=x=0:y=696:w='iw*min(t/{max(duration, 0.001):.3f},1)':h=24:c={VISUAL_ACCENT}@0.9:t=fill[base];"
        "[1:a]showwaves=s=1120x95:mode=line:colors=0x22d3ee@0.65:scale=sqrt[wave];"
        "[base][wave]overlay=x=80:y=540:format=auto,"
        f"ass='{visual_path}',subtitles='{subtitle_path}':force_style='FontSize=26,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=55'[v]"
    )
    encode_timeout = max(900, round(duration * 1.25))
    _run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=0x0b1220:s=1280x720:r=24", "-i", str(wav), "-filter_complex", filters, "-map", "[v]", "-map", "1:a", "-codec:v", "libx264", "-preset", "ultrafast", "-crf", "24", "-pix_fmt", "yuv420p", "-codec:a", "aac", "-b:a", "160k", "-shortest", str(video)], timeout=encode_timeout)
    metadata = {"schema_version": 1, "voice": voice, "speed": speed, "duration_seconds": round(duration, 3), "caption_count": len(cues), "artifacts": {}}
    for path in (wav, mp3, captions, visuals, output / "visual_plan.json", video):
        if not path.is_file() or not path.stat().st_size:
            raise MediaError(f"Missing media artifact: {path.name}")
        metadata["artifacts"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path.read_bytes()).hexdigest()}
    (output / "media.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata
