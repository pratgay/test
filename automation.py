import os
import feedparser
from datetime import datetime
from zoneinfo import ZoneInfo
from celery_worker import translate_text
from google.cloud import texttospeech
from pydub import AudioSegment
import io
import re

# Define the audio directory path
AUDIO_DIR = '/workspaces/slownewsinthai/audio_files'

# Ensure the directory exists
os.makedirs(AUDIO_DIR, exist_ok=True)

def fetch_daily_articles():
    feed = feedparser.parse("https://www.bangkokpost.com/rss/data/topstories.xml")
    bangkok_tz = ZoneInfo("Asia/Bangkok")
    today = datetime.now(bangkok_tz).date()
    
    daily_articles = []
    for entry in feed.entries:
        pub_date = datetime(*entry.published_parsed[:6]).replace(tzinfo=ZoneInfo("UTC")).astimezone(bangkok_tz).date()
        if pub_date == today:
            daily_articles.append({
                'title': entry.title,
                'content': entry.description,
                'link': entry.link,
                'pub_date': pub_date
            })
    
    return daily_articles

def compile_daily_post():
    articles = fetch_daily_articles()
    compiled_post = f"บทสรุปข่าวประจำวันที่ {datetime.now(ZoneInfo('Asia/Bangkok')).strftime('%Y-%m-%d')}\n\n"
    
    for article in articles:
        thai_title = translate_text(article['title'])
        thai_content = translate_text(article['content'])
        
        compiled_post += f"• {thai_title}\n"
        compiled_post += f"  - {thai_content}\n\n"
        compiled_post += f"English: {article['title']}\n"
        compiled_post += f"English: {article['content']}\n\n"
    
    return compiled_post

def text_to_speech(text, output_file):
    print("Original text sent to text_to_speech:")
    print(text)
    print("=" * 50)

    client = texttospeech.TextToSpeechClient()
    voice = texttospeech.VoiceSelectionParams(
        language_code="th-TH",
        name="th-TH-Neural2-C"
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.8
    )

    # Remove all English content
    thai_only_text = re.sub(r'\(English:.*?\)\n?|English:.*?(?=\n|$)', '', text, flags=re.DOTALL)
    thai_only_text = '\n'.join([line for line in thai_only_text.split('\n') if not line.strip().startswith('English:')])

    print("Thai-only text after filtering:")
    print(thai_only_text)
    print("=" * 50)

    # Split text into smaller chunks
    chunks = split_text(thai_only_text)

    combined_audio = AudioSegment.empty()
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1} of {len(chunks)}:")
        print(chunk)
        print("-" * 30)
        synthesis_input = texttospeech.SynthesisInput(text=chunk)
        try:
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            chunk_audio = AudioSegment.from_mp3(io.BytesIO(response.audio_content))
            combined_audio += chunk_audio
        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")

    combined_audio.export(output_file, format="mp3")
    print(f"Audio content written to file {output_file}")
    print(f"Total characters processed: {len(thai_only_text)}")

def split_text(text, max_chars=1000):
    chunks = []
    current_chunk = ""
    for line in text.split('\n'):
        words = line.split()
        for word in words:
            if len(current_chunk) + len(word) + 1 > max_chars:
                chunks.append(current_chunk.strip())
                current_chunk = word + " "
            else:
                current_chunk += word + " "
        current_chunk += "\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def run_daily_automation():
    try:
        print("Starting daily automation...")
        daily_post = compile_daily_post()
        print(f"Daily post compiled: {daily_post[:100]}...")  # Print first 100 chars
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        audio_filename = f"daily_summary_{timestamp}.mp3"
        audio_file_path = os.path.join(AUDIO_DIR, audio_filename)
        
        print(f"Generating audio file: {audio_file_path}")
        text_to_speech(daily_post, audio_file_path)
        
        if os.path.exists(audio_file_path) and os.path.getsize(audio_file_path) > 0:
            print("Audio file generated successfully")
            return daily_post, audio_filename, daily_post
        else:
            print("Audio file generation failed or file is empty")
            return daily_post, None, daily_post
    except Exception as e:
        print(f"Error in run_daily_automation: {str(e)}")
        return daily_post, None, daily_post