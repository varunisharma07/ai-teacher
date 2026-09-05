"""
Full lesson pipeline - runs the whole teaching flow in one go.
------------------------------------------------------------------
This calls your own running server (main.py) to:
  1. Plan a lesson on a topic (using Gemini), optionally grounded in
     an uploaded document via document_id
  2. Generate a talking-avatar video for every scene (Gemini TTS + Simli)
  3. Generate the supporting visual for every scene (diagram/equation/
     code/slide, based on what the lesson plan decided each scene needs)

Requires your server to already be running in another terminal:
    uvicorn main:app --reload

HOW TO RUN THIS FILE:
    python generate_full_lesson.py
"""

import os
import requests

SERVER_URL = "http://127.0.0.1:8000"


def plan_lesson(topic: str, level: str = "beginner", time_minutes: int = 20,
                 language: str = "English", document_id: str = None) -> dict:
    response = requests.post(
        f"{SERVER_URL}/plan-lesson",
        json={
            "topic": topic,
            "level": level,
            "time_minutes": time_minutes,
            "language": language,
            "document_id": document_id,
        },
    )
    response.raise_for_status()
    return response.json()


def generate_scene_video(narration: str, scene_number: int) -> str:
    response = requests.post(
        f"{SERVER_URL}/generate-scene-video",
        json={
            "narration": narration,
            "scene_number": scene_number,
            # face_id left out on purpose - defaults to the preset "Tina" face
        },
    )
    response.raise_for_status()
    return response.json()["video_file"]


def generate_scene_visual(visual_type: str, visual_description: str, scene_number: int, topic: str) -> str:
    response = requests.post(
        f"{SERVER_URL}/generate-scene-visual",
        json={
            "visual_type": visual_type,
            "visual_description": visual_description,
            "scene_number": scene_number,
            "topic": topic,
        },
    )
    response.raise_for_status()
    return response.json()["visual_file"]


def generate_full_lesson(topic: str, level: str = "beginner", time_minutes: int = 20,
                          language: str = "English", document_id: str = None):
    print(f"Planning lesson on '{topic}'...")
    lesson = plan_lesson(topic, level, time_minutes, language, document_id)
    scenes = lesson["scenes"]
    print(f"Lesson planned with {len(scenes)} scenes.\n")

    results = []
    for scene in scenes:
        scene_number = scene["scene_number"]
        narration = scene["narration"]
        visual_type = scene.get("visual_type", "text_slide")
        visual_description = scene.get("visual_description", narration)
        checkpoint = scene.get("checkpoint_question")

        print(f"--- Scene {scene_number} ---")
        print(f"Narration: {narration[:80]}{'...' if len(narration) > 80 else ''}")
        print(f"Visual type: {visual_type}")
        if checkpoint:
            print(f"Checkpoint question (for later): {checkpoint}")

        print("Generating video (narration + Simli)...")
        video_path = generate_scene_video(narration, scene_number)
        print(f"Saved: {video_path}")

        print("Generating visual...")
        visual_path = generate_scene_visual(visual_type, visual_description, scene_number, topic)
        print(f"Saved: {visual_path}\n")

        results.append({
            "scene_number": scene_number,
            "video": video_path,
            "visual": visual_path,
            "checkpoint_question": checkpoint,
        })

    print("=" * 50)
    print(f"Done! Generated {len(results)} scene(s):")
    for r in results:
        print(f"  Scene {r['scene_number']}: video={r['video']}, visual={r['visual']}")
    print("\nPlay each scene's video alongside its visual, in order, to form the full lesson.")
    return results


if __name__ == "__main__":
    # Change this to whatever topic you want to test with.
    # Set document_id to a name you used with /upload-document to teach
    # from that material instead of general knowledge.
    generate_full_lesson(
        topic="Newton's First Law of Motion",
        level="beginner",
        time_minutes=10,
        language="English",
        document_id=None,
    )
