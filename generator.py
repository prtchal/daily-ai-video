import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import edge_tts
import asyncio

# --- Configuration ---
BACKGROUND_VIDEO = "background.mp4"
OUTPUT_VIDEO = "daily_video.mp4"
FONT = "Arial-Bold" 

# --- THE BRAIN: Keep your existing term fetcher here ---
def get_daily_term_data():
    # This represents your existing logic that pulls from a CSV, API, or List
    # Ensure it returns: term, definition, application
    return "Generative Adversarial Networks", "A machine learning model where two neural networks contest with each other.", "Used to create realistic deep-fake videos."

async def generate_video():
    # 1. DYNAMICALLY FETCH DATA (Restored automation)
    term, definition, application = get_daily_term_data()
    
    full_script = f"{term}. {definition}. {application}"
    
    # Generate the audio
    communicate = edge_tts.Communicate(full_script, "en-US-ChristopherNeural")
    await communicate.save("voiceover.mp3")
    audio_clip = AudioFileClip("voiceover.mp3")
    duration = audio_clip.duration

    # Prepare background
    bg_clip = (VideoFileClip(BACKGROUND_VIDEO)
               .without_audio()
               .resize(height=1920)
               .crop(x1=0, y1=0, width=1080, height=1920)
               .set_duration(duration))

    # 2. THE VISUALS (Fixed Layout & Heading)
    # TOP HEADING: Always stays at the top
    banner_clip = (TextClip("Today's Futuristic Tech Term", fontsize=45, color='cyan', 
                            font=FONT, method='caption', size=(900, None))
                   .set_position(('center', 100))
                   .set_duration(duration))

    # MAIN TITLE: Starts at 350px
    title_clip = (TextClip(term.upper(), fontsize=80, color='yellow', 
                           font=FONT, method='caption', size=(900, None))
                  .set_position(('center', 350))
                  .set_duration(duration))

    # DYNAMIC BODY: Pushed down by title_clip.h
    body_y_position = 350 + title_clip.h + 60
    
    body_content = f"{definition}\n\n🚀 {application}"
    body_clip = (TextClip(body_content, fontsize=50, color='white', 
                          font=FONT, method='caption', size=(850, None))
                 .set_position(('center', body_y_position))
                 .set_duration(duration))

    # 3. COMPILE
    final_video = CompositeVideoClip([bg_clip, banner_clip, title_clip, body_clip])
    final_video.audio = audio_clip
    final_video.write_videofile(OUTPUT_VIDEO, fps=24, codec="libx264", audio_codec="aac")
    
    # Cleanup
    audio_clip.close()
    if os.path.exists("voiceover.mp3"): os.remove("voiceover.mp3")

if __name__ == "__main__":
    asyncio.run(generate_video())
