import json
import random
import asyncio
import edge_tts
from moviepy.editor import *
from moviepy.config import change_settings

# CONFIG
BACKGROUND_VIDEO = "background.mp4"
OUTPUT_FILE = "daily_video.mp4"
TERMS_FILE = "terms.json"

def get_daily_term():
    with open(TERMS_FILE, 'r') as f:
        data = json.load(f)
    return random.choice(data)

async def generate_voiceover(text, filename):
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save(filename)

def create_text_clip(text, duration, font_size=50, color='white', height=1920, width=1080):
    # We use a standard linux font 'DejaVu-Sans-Bold' to avoid errors
    return TextClip(
        text, 
        fontsize=font_size, 
        color=color, 
        font='DejaVu-Sans-Bold',
        method='caption', 
        size=(width * 0.8, None), 
        align='center'
    ).set_position('center').set_duration(duration)

async def main():
    print("--- 🤖 Agent Starting ---")

    content = get_daily_term()
    print(f"Topic: {content['term']}")

    script_1 = f"What is {content['term']}?"
    script_2 = content['definition']
    script_3 = f"Application: {content['application']}"

    await generate_voiceover(script_1, "audio1.mp3")
    await generate_voiceover(script_2, "audio2.mp3")
    await generate_voiceover(script_3, "audio3.mp3")

    audio1 = AudioFileClip("audio1.mp3")
    audio2 = AudioFileClip("audio2.mp3")
    audio3 = AudioFileClip("audio3.mp3")

    total_duration = audio1.duration + audio2.duration + audio3.duration + 1.5
    background = VideoFileClip(BACKGROUND_VIDEO).resize(height=1920).crop(x1=0, y1=0, width=1080, height=1920).loop(duration=total_duration)

    clip1 = create_text_clip(content['term'].upper(), audio1.duration, font_size=80, color='yellow').set_start(0).set_audio(audio1)
    clip2 = create_text_clip(content['definition'], audio2.duration, font_size=55).set_start(audio1.duration).set_audio(audio2)
    clip3 = create_text_clip(script_3, audio3.duration, font_size=55, color='lightgreen').set_start(audio1.duration + audio2.duration).set_audio(audio3)

    final_video = CompositeVideoClip([background, clip1, clip2, clip3])
    final_video.write_videofile(OUTPUT_FILE, fps=24, codec='libx264', audio_codec='aac')
    print("--- ✅ Video Generated Successfully ---")

if __name__ == "__main__":
    loop = asyncio.get_event_loop_policy().get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
