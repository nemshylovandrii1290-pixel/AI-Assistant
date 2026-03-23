# AI Assistant

Voice assistant for Windows with a 4-stage app launch pipeline.

## Structure

- `main.py`: assistant loop, wake word, startup index warmup
- `brain/ai.py`: asks OpenAI to classify command vs chat
- `brain/commands.py`: orchestrates 4 launch stages
- `utils/app_finder.py`: app index and search
- `utils/special_launchers.py`: UWP / PWA / special launchers
- `utils/commands_config.py`: fixed non-search commands and prompt examples
- `utils/normalize.py`: fixes common speech-recognition naming mistakes
- `voice/`: microphone, recognition, speech output

## 4 Launch Stages

1. `system`
   Tries normal Windows/PATH launch first.
2. `index`
   Uses the local app index built from useful Windows locations.
3. `special`
   Handles Store/UWP and selected web-app style cases.
4. `failback`
   Returns "not found" if nothing resolved.

## How Indexing Works

- The assistant does not require manual app entries for normal installed apps.
- `utils/app_finder.py` scans useful locations such as:
  - `Program Files`
  - `Program Files (x86)`
  - `LocalAppData\\Programs`
  - Start Menu program folders
  - Desktop / Public Desktop / OneDrive Desktop
- It indexes `.exe`, `.lnk`, and `.url`.
- The index is saved to `.cache/app_index.json`.
- On next launch:
  - if the cache is still valid, it loads from disk fast
  - if the cache is stale or missing, it rebuilds automatically

So if you install a new app, you do not need to manually add it to a list. The index is rebuilt when needed.

## Current Limitation

The index is refreshed on assistant startup, not on Windows boot. If you want, this can later be turned into a background refresher or a startup task.
