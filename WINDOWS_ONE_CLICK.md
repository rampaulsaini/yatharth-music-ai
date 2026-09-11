# Windows One-Click Setup

Yatharth Music AI can run locally on Windows with ACE-Step 1.5 as the music engine.

## What you need

- Windows 10/11
- Python 3.11 or newer
- Git for Windows
- Internet connection for the first setup/model download
- A supported GPU is strongly recommended for practical AI music generation

## One-click startup

From the repository folder, double-click:

`START_YATHARTH_AI_WINDOWS.bat`

The script will:

1. Create the Yatharth Python virtual environment.
2. Install Yatharth dependencies.
3. Start ACE-Step in a separate window.
4. Wait for ACE-Step's health endpoint on `127.0.0.1:8001`.
5. Start Yatharth on `127.0.0.1:8000` with the live AI engine enabled.

Then open:

`http://127.0.0.1:8000`

## If you want to start the services separately

### ACE-Step

Double-click:

`start_acestep_windows.bat`

Keep that window open.

### Yatharth

Then run:

`start_yatharth_windows.bat`

The normal starter defaults to DEMO mode. For live AI generation, use the full one-click starter or set:

`DEMO_MODE=false`

and

`MUSIC_ENGINE_URL=http://127.0.0.1:8001`

## First run

ACE-Step may need to download model files/checkpoints. The first run can therefore take substantially longer than later starts and requires enough disk space.

## Troubleshooting

### ACE-Step does not become ready

- Check the ACE-Step terminal for the actual error.
- Confirm that port `8001` is free.
- Confirm that Git and Python are installed.
- Confirm that the computer has enough RAM/VRAM for the selected ACE-Step configuration.

### Yatharth opens but generation fails

Check that ACE-Step is still running and that:

`http://127.0.0.1:8001/health`

responds successfully.

### No compatible GPU

Yatharth can still run in DEMO mode. CPU-only AI generation may also be possible depending on the ACE-Step configuration, but it can be much slower.

## Free-first principle

This setup does not require a paid cloud server. Local execution is the most reliable ₹0 software/development route. Free cloud GPU services such as Google Colab should be treated as temporary development/testing environments, not as guaranteed 24/7 public hosting.

## Security

The Windows starter binds services to `127.0.0.1`, keeping them local to the computer by default. Do not commit API keys, passwords, private tokens, or model credentials to GitHub.

## Official ACE-Step source

The starter downloads ACE-Step from the official ACE-Step-1.5 GitHub repository:

`https://github.com/ace-step/ACE-Step-1.5`
