"""Hugging Face Gradio adapter for Yatharth Music AI.

This Space is intentionally a thin public/demo adapter. Real generation is
performed by the configured Yatharth Music AI API, so secrets and production
engine credentials never need to be committed to the repository.
"""

import os
import time
from typing import Any

import gradio as gr

from bridge import YatharthAPIError, YatharthBridge

API_BASE_URL = os.getenv("YATHARTH_API_BASE_URL", "").strip().rstrip("/")
API_TOKEN = os.getenv("YATHARTH_API_TOKEN", "").strip()
POLL_SECONDS = max(0.5, float(os.getenv("YATHARTH_POLL_SECONDS", "2")))
POLL_TIMEOUT = max(30, int(os.getenv("YATHARTH_POLL_TIMEOUT_SECONDS", "300")))


def generate_music(
    prompt: str,
    lyrics: str,
    language: str,
    genre: str,
    mood: str,
    voice: str,
    duration: int,
    instrumental: bool,
) -> tuple[str | None, str]:
    """Generate music through the configured Yatharth Music AI API bridge."""
    if not API_BASE_URL:
        return None, (
            "YATHARTH_API_BASE_URL is not configured. "
            "Set it in the Space secrets/environment before generating."
        )

    bridge = YatharthBridge(API_BASE_URL, token=API_TOKEN, timeout=90)
    try:
        created = bridge.generate(
            prompt=prompt,
            lyrics=lyrics,
            language=language,
            genre=genre,
            mood=mood,
            voice=voice,
            duration=int(duration),
            instrumental=instrumental,
        )
        task_id = str(created["task_id"])
        deadline = time.monotonic() + POLL_TIMEOUT
        last: dict[str, Any] = created

        while time.monotonic() < deadline:
            last = bridge.task(task_id)
            status = last.get("status")
            if status == "completed":
                audio_url = last.get("audio_url")
                if not audio_url:
                    return None, "Generation completed but no audio URL was returned."
                return bridge.absolute_url(str(audio_url)), "Generation complete."
            if status == "failed":
                return None, f"Generation failed: {last.get('error') or 'unknown error'}"
            time.sleep(POLL_SECONDS)

        return None, f"Generation timed out. Task: {task_id}"
    except YatharthAPIError as exc:
        return None, f"Yatharth API error: {exc}"
    except Exception as exc:
        return None, f"Unexpected adapter error: {exc}"


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="Yatharth Music AI") as demo:
        gr.Markdown(
            "# 🎵 Yatharth Music AI\n"
            "Create original music in Hindi, Punjabi, English and more."
        )
        with gr.Row():
            with gr.Column():
                prompt = gr.Textbox(label="Music prompt", placeholder="cinematic love song, warm piano, modern drums")
                lyrics = gr.Textbox(label="Lyrics (optional)", lines=6)
                language = gr.Dropdown(["Hindi", "Punjabi", "English", "Sanskrit", "Urdu", "Bengali"], value="Hindi", label="Language")
                genre = gr.Dropdown(["Cinematic", "Pop", "Folk", "Rock", "Lo-fi", "Classical", "Electronic"], value="Cinematic", label="Genre")
                mood = gr.Dropdown(["Emotional", "Uplifting", "Peaceful", "Energetic", "Romantic", "Epic"], value="Emotional", label="Mood")
                voice = gr.Dropdown(["Male", "Female", "Duet", "Instrumental"], value="Male", label="Voice")
                duration = gr.Slider(10, 300, value=60, step=1, label="Duration (seconds)")
                instrumental = gr.Checkbox(label="Instrumental", value=False)
                button = gr.Button("Generate Music", variant="primary")
            with gr.Column():
                audio = gr.Audio(label="Generated music", type="filepath")
                status = gr.Textbox(label="Status", interactive=False)

        button.click(
            fn=generate_music,
            inputs=[prompt, lyrics, language, genre, mood, voice, duration, instrumental],
            outputs=[audio, status],
        )
        gr.Markdown(
            "**Demo note:** availability depends on the configured Yatharth API and its AI engine. "
            "Hugging Face ZeroGPU has daily usage quotas; it is not unlimited production compute."
        )
    return demo


demo = build_demo()
demo.launch()
