import subprocess
import os
import time

def extract_audio(input_file: str) -> str | None:
    """Extract mono 16kHz WAV audio from video or audio file with unique name.
       Returns output filename, or None if failed.
    """
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return None

    output_file = f"audio_{int(time.time())}.wav"  # unique name

    command = [
        "ffmpeg", "-y", "-i", input_file,
        "-ar", "16000", "-ac", "1", output_file
    ]

    try:
        # Capture stderr so we can debug without crashing
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print(result.stderr)  # ffmpeg logs
        return output_file
    except subprocess.CalledProcessError as e:
        print("❌ FFmpeg failed!")
        print("Command:", e.cmd)
        print("Error output:", e.stderr)
        return None
