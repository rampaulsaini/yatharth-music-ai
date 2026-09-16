"""Yatharth Music AI - free-first ACE-Step 1.5 ZeroGPU Space.

The Space runs the official ACE-Step 1.5 XL Turbo Diffusers pipeline directly
on Hugging Face ZeroGPU. No external Yatharth API or paid GPU server is
required for this free-first demo route.
"""

import os
import tempfile

import gradio as gr
import soundfile as sf
import spaces
import torch
from diffusers import AceStepPipeline

MODEL_ID = os.getenv("ACE_STEP_MODEL", "ACE-Step/acestep-v15-xl-turbo-diffusers")

print(f"Loading {MODEL_ID}...")
pipe = AceStepPipeline.from_pretrained(
    MODEL_ID,
    dtype=torch.bfloat16,
)
pipe = pipe.to("cuda")
print("ACE-Step 1.5 pipeline ready.")

LANGUAGE_CODES = {
    "Hindi": "hi",
    "Punjabi": "pa",
    "English": "en",
    "Sanskrit": "sa",
    "Urdu": "ur",
    "Bengali": "bn",
}


def _build_prompt(prompt: str, genre: str, mood: str, voice: str) -> str:
    parts = [prompt.strip() or "cinematic melodic song"]
    if genre:
        parts.append(f"genre: {genre}")
    if mood:
        parts.append(f"mood: {mood}")
    if voice and voice != "Instrumental":
        parts.append(f"vocal style: {voice}")
    return ", ".join(parts)


@spaces.GPU(duration=120)
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
    """Generate one short song directly with ACE-Step on ZeroGPU."""
    duration = max(10, min(int(duration), 60))
    lyrics = (lyrics or "").strip()

    if instrumental or voice == "Instrumental":
        lyrics = ""
        voice = "Instrumental"

    try:
        result = pipe(
            prompt=_build_prompt(prompt, genre, mood, voice),
            lyrics=lyrics,
            audio_duration=float(duration),
            vocal_language=LANGUAGE_CODES.get(language, "en"),
            num_inference_steps=8,
            output_type="pt",
        )

        audio = result.audios[0]
        if isinstance(audio, torch.Tensor):
            audio = audio.detach().float().cpu().numpy()

        # Handle either [channels, samples] or [1, channels, samples].
        if audio.ndim == 3:
            audio = audio[0]
        if audio.ndim == 1:
            audio = audio[:, None]
        elif audio.shape[0] <= 2 and audio.shape[1] > audio.shape[0]:
            audio = audio.T

        with tempfile.NamedTemporaryFile(
            prefix="yatharth_music_",
            suffix=".wav",
            delete=False,
        ) as handle:
            output_path = handle.name

        sf.write(output_path, audio, getattr(pipe, "sample_rate", 48000))
        return output_path, f"Generation complete — {duration}s ACE-Step 1.5 music."
    except Exception as exc:
        return None, f"Generation failed: {type(exc).__name__}: {exc}"


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="Yatharth Music AI") as demo:
        gr.Markdown(
            "# 🎵 Yatharth Music AI\n"
            "### Free ACE-Step 1.5 music generation on Hugging Face ZeroGPU\n"
            "Create short original music directly from your phone."
        )
        with gr.Row():
            with gr.Column():
                prompt = gr.Textbox(
                    label="Music prompt",
                    placeholder="cinematic Hindi love song, warm piano, modern drums",
                )
                lyrics = gr.Textbox(
                    label="Lyrics (optional)",
                    lines=7,
                    placeholder="[verse]\n...\n[chorus]\n...",
                )
                language = gr.Dropdown(
                    list(LANGUAGE_CODES),
                    value="Hindi",
                    label="Language",
                )
                genre = gr.Dropdown(
                    ["Cinematic", "Pop", "Folk", "Rock", "Lo-fi", "Classical", "Electronic"],
                    value="Cinematic",
                    label="Genre",
                )
                mood = gr.Dropdown(
                    ["Emotional", "Uplifting", "Peaceful", "Energetic", "Romantic", "Epic"],
                    value="Emotional",
                    label="Mood",
                )
                voice = gr.Dropdown(
                    ["Male", "Female", "Duet", "Instrumental"],
                    value="Male",
                    label="Voice",
                )
                duration = gr.Slider(
                    10,
                    60,
                    value=30,
                    step=5,
                    label="Duration (seconds)",
                )
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
            "**Free-use note:** ZeroGPU is shared and quota-limited. "
            "The free-first demo intentionally limits each generation to 60 seconds."
        )
    return demo


demo = build_demo()
demo.launch()
