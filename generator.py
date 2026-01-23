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
FONT = 'Liberation-Sans' 

def get_daily_term():
    with open(TERMS_FILE, 'r') as f:
        terms = json.load(f)
    return random.choice(terms)

async def main():
    # CLEANUP: Remove old audio files if they exist to prevent overlaps
    if os.path.exists("voiceover.mp3"):
        os.remove("voiceover.mp3")

    data = get_daily_term()
    term = data['term'].upper()
    definition = data['definition']
    application = data['application']
    
    # We combine everything into ONE single string for ONE voice
    full_script = f"Today's term is {term}. {definition}. Practical application. {application}."
    
    # Generate the audio
    communicate = edge_tts.Communicate(full_script, "en-US-ChristopherNeural")
    await communicate.save("voiceover.mp3")
    
    audio_clip = AudioFileClip("voiceover.mp3")
    duration = audio_clip.duration

    bg_clip = (VideoFileClip(BACKGROUND_VIDEO)
               .without_audio()
               .resize(height=1920)
               .crop(x1=0, y1=0, width=1080, height=1920)
               .set_duration(duration))

    title_clip = (TextClip(term, fontsize=100, color='yellow', font=FONT, method='caption', size=(900, None))
                  .set_position(('center', 300))
                  .set_duration(duration))

    body_text = f"{definition}\n\n🚀 {application}"
    body_clip = (TextClip(body_text, fontsize=55, color='white', font=FONT, method='caption', size=(850, None))
                 .set_position(('center', 600))
                 .set_duration(duration))

    final_video = CompositeVideoClip([bg_clip, title_clip, body_clip])
    final_video.audio = audio_clip

    final_video.write_videofile(OUTPUT_VIDEO, fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    asyncio.run(main())
