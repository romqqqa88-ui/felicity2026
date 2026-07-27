import os
import urllib.request

music_url = "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3"
music_dir = "data/music"
music_path = os.path.join(music_dir, "sunset_drive_real.mp3")

os.makedirs(music_dir, exist_ok=True)
req = urllib.request.Request(music_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        with open(music_path, "wb") as f:
            f.write(resp.read())
    print("REAL MUSIC AUDIO FILE DOWNLOADED! Size:", os.path.getsize(music_path), "bytes")
except Exception as e:
    print("DOWNLOAD ERROR:", e)
