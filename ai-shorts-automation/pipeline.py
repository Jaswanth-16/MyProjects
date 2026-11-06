"""Review-first 9:16 Shorts builder. Requires ffmpeg, Pillow and a TTS backend."""
import argparse
import asyncio
import json
import shutil
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
from scene_art import generate_scene

WIDTH, HEIGHT = 720, 1280


def validate_story(data):
    if not isinstance(data, dict) or not isinstance(data.get("scenes"), list) or not data["scenes"]:
        raise ValueError("Story must contain a nonempty scenes list")
    if len(data["scenes"]) > 30:
        raise ValueError("Maximum 30 scenes")
    for i, scene in enumerate(data["scenes"], 1):
        if not isinstance(scene, dict) or not isinstance(scene.get("text"), str) or not scene["text"].strip():
            raise ValueError(f"Scene {i} needs nonempty text")
        if len(scene["text"]) > 600:
            raise ValueError(f"Scene {i} exceeds 600 characters")
        duration = scene.get("duration", 6)
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not 1 <= duration <= 30:
            raise ValueError(f"Scene {i} duration must be 1–30 seconds")
    return data


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def probe_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True
    )
    return float(result.stdout.strip())


def font(size):
    for name in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "C:/Windows/Fonts/arialbd.ttf"):
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def scene_image(scene, index, images_dir, out_dir):
    source = images_dir / f"scene_{index:02d}.png"
    if source.exists():
        with Image.open(source) as original:
            image = ImageOps.fit(original.convert("RGB"), (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS)
    else:
        if index <= 6:
            generated = generate_scene(index, out_dir / f"art_{index:02d}.png")
            with Image.open(generated) as original:
                image = original.convert("RGB")
        else:
            image = Image.new("RGB", (WIDTH, HEIGHT), (23, 34, 62))
            ImageDraw.Draw(image).text((70, 80), "ADD SCENE ART", font=font(24), fill="white")
    draw = ImageDraw.Draw(image, "RGBA")
    words = scene["text"].split()
    lines, line = [], ""
    for word in words:
        candidate = (line + " " + word).strip()
        if draw.textbbox((0, 0), candidate, font=font(38))[2] > 620 and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    # Keep all text visible; shrink font when captions are long.
    size = 38
    while len(lines) * (size + 9) > 310 and size > 20:
        size -= 2
    if len(lines) > 8:
        raise ValueError(f"Scene {index} caption too long for screen; split into shorter scenes")
    line_height = size + 10
    top = 1070 - len(lines) * line_height
    draw.rounded_rectangle((30, top - 22, 690, 1090), radius=25, fill=(0, 0, 0, 175))
    for j, text in enumerate(lines):
        f = font(size)
        bbox = draw.textbbox((0, 0), text, font=f)
        draw.text(((WIDTH - (bbox[2] - bbox[0])) // 2, top + j * line_height),
                  text, font=f, fill="white", stroke_width=1, stroke_fill="black")
    destination = out_dir / f"frame_{index:02d}.png"
    image.save(destination)
    return destination


async def edge_speak(text, path, voice):
    import edge_tts
    await edge_tts.Communicate(text, voice).save(str(path))


def narrate(text, path, mode, edge_voice, language):
    if mode == "edge":
        asyncio.run(edge_speak(text, path, edge_voice))
    else:
        if not shutil.which("espeak-ng"):
            raise RuntimeError("espeak-ng is required for offline voice")
        run("espeak-ng", "-v", language, "-s", "135", "-w", path, text)


def build(story_path, output, voice="offline", edge_voice="en-US-AriaNeural"):
    for binary in ("ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            raise RuntimeError(f"{binary} not installed")
    story_path = Path(story_path).resolve()
    data = validate_story(json.loads(story_path.read_text(encoding="utf-8")))
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    images_dir = story_path.parent / "images"
    language = data.get("language", "en")
    clips = []
    for index, scene in enumerate(data["scenes"], 1):
        frame = scene_image(scene, index, images_dir, output)
        audio = output / f"voice_{index:02d}.mp3" if voice == "edge" else output / f"voice_{index:02d}.wav"
        narrate(scene["text"], audio, voice, edge_voice, language)
        duration = max(float(scene.get("duration", 6)), probe_duration(audio) + 0.4)
        clip = output / f"clip_{index:02d}.mp4"
        # Scale/crop the source with a subtle Ken Burns-style zoom.
        vf = ("scale=756:1344:flags=lanczos,"
              "zoompan=z='min(zoom+0.00018,1.045)':"
              "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
              "d=1:s=720x1280:fps=25,format=yuv420p")
        run("ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "25",
            "-i", frame, "-i", audio, "-t", f"{duration:.3f}", "-vf", vf,
            "-c:v", "libx264", "-preset", "veryfast", "-r", "25",
            "-c:a", "aac", "-af", "apad", "-ar", "44100", "-shortest", clip)
        clips.append(clip)
    manifest = output / "concat.txt"
    # FFmpeg concat requires escaped single quotes in paths.
    manifest.write_text("".join("file '" + str(p).replace("'", "'\\''") + "'\n" for p in clips), encoding="utf-8")
    final = output / "short.mp4"
    run("ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
        "-i", manifest, "-c", "copy", "-movflags", "+faststart", final)
    return final


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--story", default=str(Path(__file__).with_name("story.json")))
    parser.add_argument("--output", default=str(Path(__file__).with_name("output")))
    parser.add_argument("--voice", choices=["offline", "edge"], default="offline")
    parser.add_argument("--edge-voice", default="en-US-AriaNeural")
    args = parser.parse_args()
    print("Generated:", build(args.story, args.output, args.voice, args.edge_voice))


if __name__ == "__main__":
    main()
