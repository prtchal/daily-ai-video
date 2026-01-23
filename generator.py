import os
import asyncio
import random
import json
import edge_tts
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip

# Configuration
BACKGROUND_VIDEO = "background.mp4"
TERMS_FILE = "terms.json"
OUTPUT_VIDEO = "daily_video.mp4"
FONT = 'Liberation-Sans'  # Standard on GitHub Linux runners

def get_daily_term():
    with open(TERMS_FILE, 'r') as f:
        terms = json.load(f)
    return random.choice(terms)

async def generate_voiceover(text):
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save("voiceover.mp3")
    return "voiceover.mp3"

async def main():
    print("--- 🤖 Starting Video Generation ---")
    
    # 1. Safety Check for Background
    if not os.path.exists(BACKGROUND_VIDEO):
        print(f"❌ Error: {BACKGROUND_VIDEO} not found!")
        return

    # 2. Get Content
    data = get_daily_term()
    term = data['term'].upper()
    definition = data['definition']
    application = data['application']
    
    # Create ONE combined script to avoid overlapping voices
    full_script = f"Today's term is {term}. {definition}. Practical application: {application}."
    print(f"🎙️ Generating voice for: {term}")
    
    # 3. Generate Audio
    audio_path = await generate_voiceover(full_script)
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration

    # 4. Process Background
    # We mute it, resize for mobile (9:16), and loop it to match voice length
    bg_clip = (VideoFileClip(BACKGROUND_VIDEO)
               .without_audio()
               .resize(height=1920)
               .crop(x1=0, y1=0, width=1080, height=1920)
               .set_duration(duration))

    # 5. Create Text Overlays
    # Title (The Term)
    title_clip = (TextClip(term, fontsize=120, color='yellow', font=FONT, method='caption', size=(900, None))
                  .set_position(('center', 300))
                  .set_duration(duration))

    # Body (Definition + Application)
    body_text = f"{definition}\n\n🚀 {application}"
    body_clip = (TextClip(body_text, fontsize=60, color='white', font=FONT, method='caption', size=(850, None))
                 .set_position(('center', 600))
                 .set_duration(duration))

    # 6. Combine Everything
    final_video = CompositeVideoClip([bg_clip, title_clip, body_clip])
    final_video.audio = audio_clip

    # 7. Write Output
    print("🎬 Rendering final video...")
    final_video.write_videofile(OUTPUT_VIDEO, fps=24, codec="libx264", audio_codec="aac")
    print(f"✅ Success! Created {OUTPUT_VIDEO}")

if __name__ == "__main__":
    asyncio.run(main())
