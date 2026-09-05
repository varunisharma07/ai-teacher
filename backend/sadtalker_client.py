"""
SadTalker client - calls the Flask server running inside your Colab
notebook (see colab_sadtalker_server_cell.py), over the internet via
its ngrok URL. This is what makes video generation automatic instead
of manually uploading files each time.

HOW TO USE:
    python sadtalker_client.py
(after the Colab server cell is running and SADTALKER_SERVER_URL is set)
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
SADTALKER_SERVER_URL = os.environ.get("SADTALKER_SERVER_URL")


def generate_avatar_video(photo_path: str, audio_path: str, output_path: str = "scene_video.mp4") -> str:
    """
    photo_path: path to a local face image file
    audio_path: path to a local .wav narration file (e.g. from tts_gemini.py)
    output_path: where to save the finished video

    Returns: output_path, once the video has been downloaded
    """
    if not SADTALKER_SERVER_URL:
        raise RuntimeError(
            "SADTALKER_SERVER_URL is missing from your .env file. "
            "Run the Colab server cell first, then copy its printed URL into .env."
        )

    with open(photo_path, "rb") as img, open(audio_path, "rb") as aud:
        files = {
            "image": ("photo.png", img, "image/png"),
            "audio": ("narration.wav", aud, "audio/wav"),
        }
        # Video generation can take 30-90+ seconds depending on Colab's GPU
        # availability at the time, so we use a generous timeout here.
        response = requests.post(
            f"{SADTALKER_SERVER_URL}/generate-avatar-video",
            files=files,
            timeout=300,
        )

    if response.status_code != 200:
        raise RuntimeError(f"SadTalker server error ({response.status_code}): {response.text}")

    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path


if __name__ == "__main__":
    # Quick manual test - adjust these paths to a real photo and audio file
    # you have on your computer.
    result = generate_avatar_video("my_photo.png", "narration.wav")
    print(f"Video saved to {result}")
