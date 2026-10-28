# Mini Assistant: local rule-based voice assistant

Mini Assistant is a small Windows desktop assistant. It is not an AI model and does not
call an API: it matches spoken or typed phrases to commands stored in
`data/intents.json`.

## Run

Use Python 3.10 or newer:

```powershell
python Main.py
```

If audio is unavailable, type commands in the terminal. The program still
works in that mode. For microphone and speaker support, install the optional
packages:

```powershell
python -m pip install -r requirements.txt
```

On Windows, PyAudio may require a compatible wheel or PortAudio installation.
The optional `pocketsphinx` package recognizes speech locally. Without it,
Mini Assistant automatically uses typed commands instead.

## Features

- Greetings, time, browser and Notepad commands
- Volume controls when `pyautogui` is installed
- Remembers the assistant name, user name, and birthday in `data/profile.json`
- Locks or shuts down Windows only after a spoken/typed `confirm`
- `help` lists available commands; `exit` closes the assistant

Add phrases or commands by editing `data/intents.json`. The matching is fully
local and deterministic, so it cannot answer general knowledge questions.
