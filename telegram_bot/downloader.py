import yt_dlp

def download_youtube(url: str, resolution: str = "360p") -> str:
    """Download YouTube video, try given resolution, fallback to best available."""
    try:
        ydl_opts = {
            "format": f"bestvideo[height<={resolution[:-1]}]+bestaudio/best[height<={resolution[:-1]}]/best",
            "outtmpl": "youtube_input.%(ext)s",   # keep ext consistent
            "merge_output_format": "mp4"          # force mp4 container
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return "youtube_input.mp4"

    except Exception as e:
        print(f"⚠️ Requested resolution {resolution} not available. Falling back to best format. ({e})")
        ydl_opts = {
            "format": "best",
            "outtmpl": "youtube_input.%(ext)s",
            "merge_output_format": "mp4"
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        return "youtube_input.mp4"
