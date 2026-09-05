"""
Free narration audio using Gemini's native TTS.
---------------------------------------------------
Gemini itself can turn text into speech - officially supported by Google,
using the SAME api key you already have in your .env file. No new
signup, no separate service to break.

HOW TO RUN:
    python tts_gemini.py
"""

import os
import wave
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
# The dedicated text-to-speech model.
TTS_MODEL = "gemini-2.5-flash-preview-tts"

# A few voice options you can try (there are 30 total - these are a
# reasonable starting set). Full list: ai.google.dev/gemini-api/docs/speech-generation
VOICE_OPTIONS = {
    "warm_female": "Kore",
    "energetic_male": "Puck",
    "calm_male": "Charon",
    "friendly_female": "Leda",
}


def save_wave_file(filename: str, pcm_data: bytes, channels=1, rate=24000, sample_width=2):
    """Wraps raw audio data in a proper .wav file header, using Python's
    built-in 'wave' module - no extra tools like ffmpeg needed."""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)


def generate_narration_audio(text: str, output_path: str, voice_name: str = "Kore"):
    """
    text: the narration script (what the teacher should say)
    output_path: where to save the .wav file, e.g. "narration.wav"
    voice_name: one of the voice names from VOICE_OPTIONS (or any of the
                30 official voice names)
    """
    try:
        response = client.models.generate_content(
            model=TTS_MODEL,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                    )
                ),
            ),
        )
    except Exception as e:
        raise RuntimeError(f"Gemini TTS API call failed: {type(e).__name__}: {str(e)}")

    # Defensive checks - if this candidate has no content, something
    # stopped the generation (safety filter, quota limit, deprecated
    # model, etc.). We surface exactly why instead of crashing blindly
    # on .content.parts[0] the way this used to.
    if not response.candidates:
        feedback = getattr(response, "prompt_feedback", None)
        raise RuntimeError(f"Gemini TTS returned no candidates. Prompt feedback: {feedback}")

    candidate = response.candidates[0]
    finish_reason = getattr(candidate, "finish_reason", None)

    if candidate.content is None:
        safety_ratings = getattr(candidate, "safety_ratings", None)
        raise RuntimeError(
            f"Gemini TTS returned empty content. finish_reason={finish_reason}, "
            f"safety_ratings={safety_ratings}. This usually means a safety "
            f"filter blocked it, you hit a rate/quota limit, or the TTS "
            f"model needs updating (same issue we hit with the text model)."
        )

    if not candidate.content.parts:
        raise RuntimeError(f"Gemini TTS content had no parts. finish_reason={finish_reason}")

    pcm_data = candidate.content.parts[0].inline_data.data
    if not pcm_data:
        raise RuntimeError("Gemini TTS returned a part with no audio data inside it.")

    save_wave_file(output_path, pcm_data)
    return output_path


if __name__ == "__main__":
    TEST_TEXT = (
        "Hello! I am your AI teacher. Today we are going to learn something new, "
        "step by step, in a way that is easy to understand."
    )
    path = generate_narration_audio(TEST_TEXT, "narration.wav", voice_name="Kore")
    print(f"Done! Saved narration audio to {path}")
    print("\nNext step: upload this .wav file, along with a face photo, into")
    print("the SadTalker Colab notebook to generate your talking video.")
