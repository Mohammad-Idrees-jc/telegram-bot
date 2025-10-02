import os
import whisper
from deep_translator import GoogleTranslator

# Load Whisper model once globally
model = whisper.load_model("tiny")  # lightweight, change to "base" or bigger if needed

def transcribe_audio(audio_file: str):
    """Transcribe audio and auto-detect language."""
    # ✅ Safety check
    if not audio_file or not os.path.exists(audio_file):
        raise FileNotFoundError(f"❌ Audio file not found or invalid: {audio_file}")

    print(f"[DEBUG] Transcribing: {audio_file}")  # helpful for debugging

    try:
        result = model.transcribe(audio_file, verbose=False)
        detected_lang = result.get("language", "en")  # fallback to English
        return result, detected_lang
    except Exception as e:
        print(f"❌ Whisper transcription failed: {e}")
        raise e


def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format."""
    millisec = round((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    mins, sec = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs:02}:{mins:02}:{sec:02},{millisec:03}"


def translate_and_save(transcription, src_lang: str, target_lang: str, file_name: str):
    """Translate transcription to target_lang (skip if same as src_lang) and save as .srt."""
    print(f"📝 Generating {target_lang.upper()} subtitles -> {file_name}")

    with open(file_name, "w", encoding="utf-8") as f:
        for i, seg in enumerate(transcription["segments"], start=1):
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            text = seg["text"].strip()

            # Skip translation if already in target language
            if src_lang == target_lang:
                translated = text
            else:
                try:
                    translated = GoogleTranslator(source=src_lang, target=target_lang).translate(text)
                except Exception as e:
                    print(f"⚠️ Translation failed ({src_lang} -> {target_lang}) for segment {i}: {e}")
                    translated = text  # fallback

            f.write(f"{i}\n{start} --> {end}\n{translated}\n\n")

    print(f"✅ {target_lang.upper()} subtitles saved: {file_name}")
