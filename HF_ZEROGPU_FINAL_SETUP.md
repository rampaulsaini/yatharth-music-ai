# Yatharth Music AI — Final ZeroGPU Setup

The repository is prepared for the free-first route:

**Phone → Hugging Face ZeroGPU → ACE-Step 1.5 → WAV music**

## One-time account setup

1. Sign in to Hugging Face.
2. Create a new **public Gradio Space** named `yatharth-music-ai`.
3. Select **ZeroGPU** hardware.
4. The Space must use Python 3.12.12 and Gradio; `hf_space/README.md` already declares these settings.

## Put the app into the Space

Copy these three files from this repository's `hf_space/` directory into the Space:

- `app.py`
- `requirements.txt`
- `README.md`

The repository already contains the complete app code and dependency list.

## Optional automatic sync

To use the repository's manual GitHub Actions workflow:

- Add GitHub Actions secret `HF_TOKEN` containing a Hugging Face token with permission to write to the Space.
- Add GitHub Actions variable `HF_SPACE_REPO` with value `rampaulsaini/yatharth-music-ai`.
- Run **Actions → Sync Hugging Face Space → Run workflow**.

Never commit the token to the repository.

## First test

From the phone:

- Language: Hindi
- Genre: Cinematic
- Mood: Emotional
- Voice: Male
- Duration: 30 seconds
- Instrumental: Off
- Prompt: `a beautiful emotional Hindi song about hope, warm piano, soft strings, modern cinematic drums`

Then press **Generate Music**.

## If the Space is building

The first build/model download can take time. Wait for the Space to show the running Gradio application before testing.

## If generation fails

Copy the complete red/error message from the Space and bring it back to this chat. Do not change model names or dependency versions randomly; the repository is configured around the official ACE-Step 1.5 XL Turbo Diffusers pipeline.

## Free-use expectation

ZeroGPU is shared infrastructure with daily usage quotas and queueing. The app deliberately starts at 30 seconds and caps individual generations at 60 seconds. It is a free validation/demo route, not guaranteed unlimited production hosting.
