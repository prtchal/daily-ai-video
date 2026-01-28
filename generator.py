import os
import asyncio
import json
import time
import re

from groq import Groq
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import edge_tts
import PIL.Image

# Pillow compatibility (some environments removed ANTIALIAS)
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

# --- CONFIGURATION ---
BACKGROUND_VIDEO = "background.mp4"
OUTPUT_VIDEO = "daily_video.mp4"
VOICEOVER_FILE = "voiceover.mp3"
FONT = os.environ.get("MOVIEPY_FONT", "DejaVu-Sans-Bold")

# Persisted history (commit this file in GitHub Actions to keep uniqueness across days)
USED_TERMS_PATH = "used_terms.json"

# Keep a bounded history so it effectively never repeats (5000 terms ~ 13.7 years at 1/day)
KEEP_LAST_TERMS = 5000


def _normalize_term(term: str) -> str:
    """
    Normalize term for dedupe:
    - trim
    - lower
    - collapse whitespace
    """
    return re.sub(r"\s+", " ", term.strip().lower())


def _load_used_terms_list() -> list[str]:
    """
    Load used terms as an ORDERED list (oldest -> newest), normalized and de-duped.
    Supports file formats:
      - {"terms": ["a", "b", ...]}
      - ["a", "b", ...]
    If file is missing/corrupt, returns [].
    """
    try:
        with open(USED_TERMS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            terms = data.get("terms", [])
        elif isinstance(data, list):
            terms = data
        else:
            terms = []

        # Normalize + de-dup while preserving order
        seen = set()
        cleaned: list[str] = []
        for t in terms:
            if not isinstance(t, str):
                continue
            norm = _normalize_term(t)
            if not norm or norm in seen:
                continue
            seen.add(norm)
            cleaned.append(norm)

        # Bound to last N (keep most recent)
        if len(cleaned) > KEEP_LAST_TERMS:
            cleaned = cleaned[-KEEP_LAST_TERMS:]

        return cleaned

    except FileNotFoundError:
        return []
    except Exception:
        # If the file is corrupted or unreadable, don't break the pipeline
        return []


def _save_used_terms_list(terms_list: list[str]) -> None:
    """
    Save normalized terms list, keeping only the most recent KEEP_LAST_TERMS entries.
    """
    # Ensure bounded
    if len(terms_list) > KEEP_LAST_TERMS:
        terms_list = terms_list[-KEEP_LAST_TERMS:]

    with open(USED_TERMS_PATH, "w", encoding="utf-8") as f:
        json.dump({"terms": terms_list}, f, indent=2)


def get_daily_term(max_attempts: int = 12) -> dict:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY in environment / GitHub Secrets")

    used_terms_list = _load_used_terms_list()
    used_terms_set = set(used_terms_list)

    print(f"[get_daily_term] Loaded {len(used_terms_set)} prior terms", flush=True)

    client = Groq(api_key=api_key)
    today_utc = time.strftime("%Y-%m-%d", time.gmtime())

    prompt = (
        f"Today is {today_utc}.\n"
        "Generate ONE brand-new futuristic tech term (AI, Quantum, or Space).\n"
        "Return ONLY a JSON object with keys: term, definition, application.\n"
        "Rules:\n"
        "- term must be 2-4 words\n"
        "- term must NOT be common\n"
        "- term must be meaningfully different (avoid tiny variations)\n"
        "- definition: exactly 1 sentence\n"
        "- application: exactly 1 sentence\n"
    )

    for attempt in range(1, max_attempts + 1):
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.9,
            top_p=0.95,
        )

        raw = chat_completion.choices[0].message.content
        data = json.loads(raw)

        term = (data.get("term") or "").strip()
        definition = (data.get("definition") or "").strip()
        application = (data.get("application") or "").strip()

        if not term or not definition or not application:
            print(f"[get_daily_term] Incomplete JSON (attempt {attempt}): {data}", flush=True)
            continue

        norm = _normalize_term(term)

        if norm in used_terms_set:
            print(f"[get_daily_term] Duplicate term, retrying (attempt {attempt}): {term}", flush=True)
            continue

        # Accept and persist
        used_terms_list.append(norm)
        used_terms_set.add(norm)
        _save_used_terms_list(used_terms_list)

        print(f"[get_daily_term] New unique term (attempt {attempt}): {term}", flush=True)
        return {"term": term, "definition": definition, "application": application}

    raise RuntimeError("Failed to generate a unique daily term after retries")


async def generate_video() -> None:
    # Cleanup at start (prevents overlaps on reruns)
    if os.path.exists(VOICEOVER_FILE):
        os.remove(VOICEOVER_FILE)

    if not os.path.exists(BACKGROUND_VIDEO):
        raise FileNotFoundError(f"Missing {BACKGROUND_VIDEO} in repo root")

    # Fetch dynamic data
    data = get_daily_term()
    term = data["term"]
    definition = data["definition"]
    application = data["application"]

    print("DAILY TERM PAYLOAD:", flush=True)
    print(json.dumps(data, indent=2), flush=True)

    full_script = f"{term}... {definition}... {application}"

    # Generate audio
    communicate = edge_tts.Communicate(
        text=full_script,
        voice="en-US-ChristopherNeural",
        rate="+12%",
        pitch="+0Hz",
        volume="+0%",
    )
    await communicate.save(VOICEOVER_FILE)

    audio_clip = None
    bg_clip = None
    final_video = None

    try:
        audio_clip = AudioFileClip(VOICEOVER_FILE)
        duration = audio_clip.duration

        # Prepare background
        bg_clip = (
            VideoFileClip(BACKGROUND_VIDEO)
            .without_audio()
            .resize(height=1920)
            .crop(x1=0, y1=0, width=1080, height=1920)
            .set_duration(duration)
        )

        # 1) TOP BANNER
        banner_clip = (
            TextClip(
                "Future tech term of the day..",
                fontsize=40,
                color="cyan",
                font=FONT,
                method="caption",
                size=(900, None),
            )
            .set_position(("center", 100))
            .set_duration(duration)
        )

        # 2) MAIN TITLE
        title_y = 280
        title_clip = (
            TextClip(
                term.upper(),
                fontsize=55,
                color="yellow",
                font=FONT,
                method="caption",
                size=(900, None),
            )
            .set_position(("center", title_y))
            .set_duration(duration)
        )

        # 3) BODY (dynamic spacing)
        body_y_position = title_y + title_clip.h + 120
        body_text = f"{definition}\n\n🚀 {application}"
        body_clip = (
            TextClip(
                body_text,
                fontsize=45,
                color="white",
                font=FONT,
                method="caption",
                size=(850, None),
            )
            .set_position(("center", body_y_position))
            .set_duration(duration)
        )

        # Compile and export
        final_video = CompositeVideoClip([bg_clip, banner_clip, title_clip, body_clip])
        final_video.audio = audio_clip
        final_video.write_videofile(
            OUTPUT_VIDEO,
            fps=24,
            codec="libx264",
            audio_codec="aac",
        )

    finally:
        # Cleanup / close resources
        try:
            if audio_clip:
                audio_clip.close()
        except Exception:
            pass

        try:
            if bg_clip:
                bg_clip.close()
        except Exception:
            pass

        try:
            if final_video:
                final_video.close()
        except Exception:
            pass

        if os.path.exists(VOICEOVER_FILE):
            try:
                os.remove(VOICEOVER_FILE)
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(generate_video())
