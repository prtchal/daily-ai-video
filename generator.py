import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import edge_tts
import asyncio

# --- Configuration (Adjust these if needed) ---
BACKGROUND_VIDEO = "background.mp4"  # Your background file name
OUTPUT_VIDEO = "daily_video.mp4"
FONT = "Arial-Bold" # Ensure this font is installed on your system

async def generate_video(term, definition, application):
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

    # 1. TOP BANNER (Your Heading)
    # Positioned at the very top to identify your series
    banner_clip = (TextClip("Today's Futuristic Tech Term", fontsize=45, color='cyan', 
                            font=FONT, method='caption', size=(900, None))
                   .set_position(('center', 100))
                   .set_duration(duration))

    # 2. MAIN TITLE (The Tech Term)
    # Starts at 350px down the screen
    title_clip = (TextClip(term.upper(), fontsize=80, color='yellow', 
                           font=FONT, method='caption', size=(900, None))
                  .set_position(('center', 350))
                  .set_duration(duration))

    # 3. DYNAMIC BODY TEXT (Prevents Overlapping)
    # This calculates exactly where the title ends and adds a 60px gap
    body_y_position = 350 + title_clip.h + 60
    
    body_content = f"{definition}\n\n🚀 {application}"
    body_clip = (TextClip(body_content, fontsize=50, color='white', 
                          font=FONT, method='caption', size=(850, None))
                 .set_position(('center', body_y_position))
                 .set_duration(duration))

    # 4. COMPILE AND EXPORT
    final_video = CompositeVideoClip([bg_clip, banner_clip, title_clip, body_clip])
    final_video.audio = audio_clip

    final_video.write_videofile(OUTPUT_VIDEO, fps=24, codec="libx264", audio_codec="aac")
    
    # Cleanup temporary audio file
    audio_clip.close()
    if os.path.exists("voiceover.mp3"):
        os.remove("voiceover.mp3")

# Example usage (This is what actually runs the code)
if __name__ == "__main__":
    term_input = "Generative Adversarial Networks"
    def_input = "A machine learning model where two neural networks contest with each other to create new data instances."
    app_input = "Used to create realistic deep-fake videos or upscale low-resolution images to 4K."
    
    asyncio.run(generate_video(term_input, def_input, app_input))
