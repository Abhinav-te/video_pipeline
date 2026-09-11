import asyncio
import edge_tts
import whisper

async def generate_voice(text, output_file):
    """Generates the TTS MP3 using Microsoft Edge TTS."""
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save(output_file)

def extract_word_timings(audio_path):
    """Extracts word timestamps using Whisper."""
    model = whisper.load_model("base", device="cpu")
    result = model.transcribe(audio_path, word_timestamps=True)
    
    words = []
    for segment in result["segments"]:
        for word in segment["words"]:
            words.append({
                "word": word["word"].strip(),
                "start": word["start"],
                "end": word["end"]
            })
    return words