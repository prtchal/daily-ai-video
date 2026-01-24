import os
import asyncio
import json
from groq import Groq
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import edge_tts

# --- CONFIGURATION ---
BACKGROUND_VIDEO = "background.mp4"
OUTPUT_VIDEO = "daily_video.mp4"
FONT = "Arial-Bold" # Make sure this font is available on your system

# --- STEP 1: DYNAMIC DATA FETCHING (YOUR ORIGINAL LOGIC) ---
def get_daily_term():
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    prompt = "Provide a unique futuristic tech term (AI, Quantum, or Space), its definition (1 sentence), and a practical application (1 sentence). Return ONLY as a JSON object with keys: 'term', 'definition', 'application'."
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
        response_format={"type": "json_object"}
    )
    return json.loads(chat_completion.choices[0].message.content)

# --- STEP 2: VIDEO GENERATION ---
async def generate_video():
    # Fetch the dynamic data
    data = get_daily_term()
    term = data['term']
    definition = data['definition']
    application = data['application']
    
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

    # --- VISUAL LAYOUT (FIXED & DYNAMIC) ---

    # 1. TOP BANNER (Series Title)
    banner_clip = (TextClip("Today's Futuristic Tech Term", fontsize=45, color='cyan', 
                            font=FONT, method='caption', size=(900, None))
                   .set_position(('center', 150))
                   .set_duration(duration))

    # 2. MAIN TITLE (The Tech Term)
    # Starts at 400px down the screen
    title_clip = (TextClip(term.upper(), fontsize=80, color='yellow', 
                           font=FONT, method='caption', size=(900, None))
                  .set_position(('center', 400))
                  .set_duration(duration))

    # 3. DYNAMIC BODY (Prevents Overlapping)
    # This measures the height of the title and places the body 60px below it
    body_y_position = 400 + title_clip.h + 60
    
    body_content = f"{definition}\n\n🚀 {application}"
    body_clip = (TextClip(body_content, fontsize=50, color='white', 
                          font=FONT, method='caption', size=(850, None))
                 .set_position(('center', body_y_position))
                 .set_duration(duration))

    # 4. COMPILE AND EXPORT
    final_video = CompositeVideoClip([bg_clip, banner_clip, title_clip, body_clip])
    final_video.audio = audio_clip

    final_video.write_videofile(OUTPUT_VIDEO, fps=24, codec="libx264", audio_codec="aac")
    
    # Cleanup
    audio_clip.close()
    if os.path.exists("voiceover.mp3"):
        os.remove("voiceover.mp3")

if __name__ == "__main__":
    asyncio.run(generate_video())
