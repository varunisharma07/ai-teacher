"""
Simli client - a small wrapper around Simli's REST API.
------------------------------------------------------------
Unlike D-ID, Simli doesn't require a separate "API plan" beyond your
normal account - the same free-tier key works directly on this endpoint.
You also don't need your own photo: Simli provides several ready-made
preset faces you can use immediately.

HOW TO USE THIS FILE ON ITS OWN:
    python test_simli.py
"""

import os
import time
import base64
import requests
from dotenv import load_dotenv

load_dotenv()
SIMLI_API_KEY = os.environ.get("SIMLI_API_KEY")

BASE_URL = "https://api.simli.ai"

# A few of Simli's official preset faces - no photo upload needed to
# start testing. Full list / previews: docs.simli.com/api-reference/preset-faces
PRESET_FACES = {
    "tina": "cace3ef7-a4c4-425d-a8cf-a5358eb0c427",
    "laila": "b9e5fba3-071a-4e35-896e-211c4d6eaa7b",
    "kate": "d2a5c7c6-fed9-4f55-bcb3-062f7cd20103",
    "sabour": "7e74d6e7-d559-4394-bd56-4923a3ab75ad",
    "fred": "1c6aa65c-d858-4721-a4d9-bda9fde03141",
}


def _check_key():
    if not SIMLI_API_KEY:
        raise RuntimeError("SIMLI_API_KEY is missing. Add it to your .env file.")


# ---------------------------------------------------------------------
# OPTIONAL: turn your own photo into a Simli face, if you don't want
# to use one of the presets above. Returns a face_id you can reuse.
# ---------------------------------------------------------------------
def create_face_from_photo(image_path: str, face_name: str = "ai_teacher") -> str:
    _check_key()
    with open(image_path, "rb") as img:
        response = requests.post(
            f"{BASE_URL}/generateFaceID",
            headers={"x-simli-api-key": SIMLI_API_KEY},
            params={"face_name": face_name},
            files={"image": img},
        )
    if response.status_code != 200:
        raise RuntimeError(f"Simli face creation failed ({response.status_code}): {response.text}")
    return response.json()["faceId"]


# ---------------------------------------------------------------------
# MAIN FUNCTION: turn a .wav narration file into a talking video.
# ---------------------------------------------------------------------
def generate_video(audio_wav_path: str, face_id: str, output_path: str = "scene_video.mp4") -> str:
    """
    audio_wav_path: path to a local .wav file (e.g. from tts_gemini.py)
    face_id: one of PRESET_FACES.values(), or your own from create_face_from_photo()
    output_path: where to save the finished video
    """
    _check_key()

    with open(audio_wav_path, "rb") as f:
        audio_bytes = f.read()
    audio_base64 = base64.b64encode(audio_bytes).decode()

    response = requests.post(
        f"{BASE_URL}/static/audio",
        headers={"x-simli-api-key": SIMLI_API_KEY, "Content-Type": "application/json"},
        json={
            "faceId": face_id,
            "audioBase64": audio_base64,
            "audioFormat": "wav",
        },
    )
    if response.status_code != 200:
        raise RuntimeError(f"Simli rejected the request ({response.status_code}): {response.text}")

    mp4_url = response.json()["mp4_url"]

    # The video may still be finishing on Simli's side even after this
    # call returns, so we retry downloading it for a little while.
    waited = 0
    poll_seconds = 3
    timeout_seconds = 120
    while waited < timeout_seconds:
        video_response = requests.get(mp4_url)
        if video_response.status_code == 200 and len(video_response.content) > 0:
            with open(output_path, "wb") as out:
                out.write(video_response.content)
            return output_path
        time.sleep(poll_seconds)
        waited += poll_seconds

    raise TimeoutError(f"Video at {mp4_url} was not ready within {timeout_seconds} seconds")
