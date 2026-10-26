# TodoDisplay

Shows tasks on a Waveshare 5.83" e-paper display (648x480, black/white) driven by a Raspberry Pi. See `README.md`.

## Checking UI changes: use preview mode

Any change to how the display looks (`src/taskDisplay/`, fonts, layout, glyphs, sizes) must be checked by rendering it, not by reading the code. Render the image to a PNG, then look at it with the Read tool:

```
.venv/bin/python src/__main__.py --preview <path>.png --fake few --no-open
```

- Run it from the repo root.
- Write the PNG outside the repo (your scratchpad). The default `previews/` folder and `preview*.png` are gitignored, but any other name inside the repo is not. Never `git add` a preview image.
- `--no-open` stops it launching a viewer on the user's machine. Always pass it.
- `--fake` takes `empty`, `few`, `many` or `long`. Check all four after a layout change: an empty screen, a typical day, a full screen and titles too wide for the display. No credentials are needed.
- Without `--fake` it fetches real tasks, which needs `src/taskFetcher/.env`. Avoid it unless the task is about the fetcher.
- `--raw` skips the 1-bit black/white conversion, showing the unconverted image.

The preview is a layout check, not a contrast check. A photo of the real panel looked paler and smaller than the preview (see issues #41 and #50). Bias towards larger, heavier text, and say when something can only be judged on the real screen.

## Setup and tests

- Use `.venv` (gitignored). The laptop needs only `pillow`, `python-dotenv`, `requests`, `schedule` and `pytest`. Do not install the Pi hardware packages in `requirements.txt` on a laptop.
- Run tests with `.venv/bin/python -m pytest tests`.

## Secrets

This repo is public. Never commit or paste into issues, PRs or chat: the TickTick token or OAuth code, `.env` contents, service-account keys, Firebase project IDs or user ids, wifi passwords. `.env` is gitignored; only `.env.sample` (names, no values) is committed.

## Git and GitHub

- Branch off `develop` as `feature/*` and open a PR into `develop`. Do not commit directly to `develop` or `master`.
- The Pi runs `master`; changes reach it by merge and `git pull`. Only the owner merges.
- GitHub rejects pushes that expose the user's private email. Commit with `GIT_AUTHOR_EMAIL` and `GIT_COMMITTER_EMAIL` set to the user's GitHub noreply address (`gh api user` gives the id and login).
- Work is tracked in GitHub Issues (`gh`), with `priority: high|medium|low` labels. Design work is labelled `design`, TodoApp integration `todoapp`.
