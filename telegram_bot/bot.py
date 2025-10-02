import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import F

# === Import your functions ===
from downloader import download_youtube
from audio_utils import extract_audio
from subtitle_utils import transcribe_audio, translate_and_save

# ====== Replace with your bot token ======
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# FSM States
class PipelineStates(StatesGroup):
    choosing_input = State()
    entering_filename = State()
    entering_url = State()
    entering_resolution = State()
    processing = State()

# Start command
@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎥 Video"), KeyboardButton(text="🎵 Audio")],
            [KeyboardButton(text="🔗 YouTube Link")]
        ],
        resize_keyboard=True
    )
    await state.set_state(PipelineStates.choosing_input)
    await message.answer("🎬 Subtitle Generator Bot 🎬\n\nWhat is your input?", reply_markup=keyboard)

# Handle input choice
@dp.message(PipelineStates.choosing_input)
async def choose_input(message: types.Message, state: FSMContext):
    # Case 1: User clicked button / typed text
    if message.text:
        text = message.text.strip().lower()

        if text in ["🎥 video", "video"]:
            await state.update_data(choice="video")
            await state.set_state(PipelineStates.entering_filename)
            await message.answer("📂 Send me the video file or filename.")

        elif text in ["🎵 audio", "audio"]:
            await state.update_data(choice="audio")
            await state.set_state(PipelineStates.entering_filename)
            await message.answer("📂 Send me the audio file or filename.")

        elif text in ["🔗 youtube link", "youtube", "link", "youtube link"]:
            await state.update_data(choice="youtube")
            await state.set_state(PipelineStates.entering_url)
            await message.answer("🔗 Send me the YouTube link.")

        else:
            await message.answer("❌ Invalid choice. Please pick Video, Audio, or YouTube Link.")

    # Case 2: User directly uploads a file
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name or f"{file_id}.mp4"
        file = await message.bot.get_file(file_id)
        os.makedirs("downloads", exist_ok=True)
        file_path = f"downloads/{file_name}"
        await message.bot.download_file(file.file_path, file_path)

        await state.update_data(choice="video", file_path=file_path)
        await run_pipeline(message, state)

    elif message.document:  # video can also arrive as document
        file_id = message.document.file_id
        file_name = message.document.file_name or f"{file_id}"
        file = await message.bot.get_file(file_id)
        os.makedirs("downloads", exist_ok=True)
        file_path = f"downloads/{file_name}"
        await message.bot.download_file(file.file_path, file_path)

        await state.update_data(choice="video", file_path=file_path)
        await run_pipeline(message, state)

    else:
        await message.answer("⚠️ Please choose Video, Audio, or YouTube link.")


# Handle filename input (for video/audio)
@dp.message(PipelineStates.entering_filename)
async def get_filename(message: types.Message, state: FSMContext):
    data = await state.get_data()
    choice = data.get("choice")

    file_path = None

    # Case 1: User typed filename
    if message.text:
        file_path = f"./{message.text.strip()}"

    # Case 2: User uploaded audio
    elif message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name or f"{file_id}.mp3"
        file = await message.bot.get_file(file_id)
        os.makedirs("downloads", exist_ok=True)
        file_path = f"downloads/{file_name}"
        await message.bot.download_file(file.file_path, file_path)

    # Case 3: User uploaded voice
    elif message.voice:
        file_id = message.voice.file_id
        file_name = f"{file_id}.ogg"
        file = await message.bot.get_file(file_id)
        os.makedirs("downloads", exist_ok=True)
        file_path = f"downloads/{file_name}"
        await message.bot.download_file(file.file_path, file_path)

    # Case 4: User uploaded video
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name or f"{file_id}.mp4"
        file = await message.bot.get_file(file_id)
        os.makedirs("downloads", exist_ok=True)
        file_path = f"downloads/{file_name}"
        await message.bot.download_file(file.file_path, file_path)

    # Case 5: User uploaded file as document (mkv, avi, mov, mp4)
    elif message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or f"{file_id}"
        file = await message.bot.get_file(file_id)
        os.makedirs("downloads", exist_ok=True)
        file_path = f"downloads/{file_name}"
        await message.bot.download_file(file.file_path, file_path)

    else:
        await message.answer("⚠️ Please send a valid file or filename.")
        return

    # Save in state
    await state.update_data(file_path=file_path)

    # Continue
    if choice in ["video", "audio"]:
        await run_pipeline(message, state)



# Handle YouTube link
@dp.message(PipelineStates.entering_url)
async def get_url(message: types.Message, state: FSMContext):
    await state.update_data(url=message.text.strip())
    await state.set_state(PipelineStates.entering_resolution)
    await message.answer("📺 Enter resolution (360p/480p/720p):")

# Handle resolution for YouTube
@dp.message(PipelineStates.entering_resolution)
async def get_resolution(message: types.Message, state: FSMContext):
    resolution = message.text.strip()
    data = await state.get_data()
    url = data.get("url")

    # Download YouTube video
    file_path = download_youtube(url, resolution)
    await state.update_data(file_path=file_path)

    await run_pipeline(message, state)

# === Pipeline runner ===
async def run_pipeline(message: types.Message, state: FSMContext):
    data = await state.get_data()
    file_path = data.get("file_path")

    # Extract audio
    await message.answer("🎧 Extracting audio...")
    audio_path = extract_audio(file_path)

    # Transcribe
    await message.answer("⏳ Transcribing and detecting language...")
    transcription, detected_lang = transcribe_audio(audio_path)

    await message.answer(f"🌍 Detected input language: {detected_lang}")

    # Translate & Save
    generated_files = []
    for lang, fname in [
        ("en", "subtitles_en.srt"),
        ("ur", "subtitles_ur.srt"),
        ("tr", "subtitles_tr.srt")
    ]:
        translate_and_save(transcription, detected_lang, lang, fname)
        generated_files.append(fname)

    # Send generated .srt files to user
    for fname in generated_files:
        if os.path.exists(fname):
            await message.answer_document(types.FSInputFile(fname))

    await message.answer("✅ Subtitles generated and sent!")
    await state.clear()




async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
