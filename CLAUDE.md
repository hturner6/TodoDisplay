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
- `--fake` takes `empty`, `few`, `many`, `long` or `states`. Check all five after a layout change: an empty screen, a typical day, a full screen, titles too wide for the display and every completion glyph. Add `--safe-area` to outline the frame-safe margins. No credentials are needed.
- Without `--fake` it fetches real tasks, which needs `src/taskFetcher/.env`. Avoid it unless the task is about the fetcher.
- `--raw` skips the 1-bit black/white conversion, showing the unconverted image.

The preview is a layout check, not a contrast check. A photo of the real panel looked paler and smaller than the preview (see issues #41 and #50). Bias towards larger, heavier text, and say when something can only be judged on the real screen.

## Setup and tests

- Use `.venv` (gitignored). The laptop needs only `pillow`, `python-dotenv`, `requests`, `schedule` and `pytest`. Do not install the Pi hardware packages in `requirements.txt` on a laptop.
- Run tests with `.venv/bin/python -m pytest tests`.

## Deployment (Raspberry Pi)

- The Pi (Zero 2 W, Bookworm, hostname `inkpi`, user `hturner`) runs the app as the systemd service `TodoDisplay.service`, which runs `run.sh` (`--run 30`). It is not a cron job, despite older README wording (see #34).
- The service holds the display GPIO. Running the app by hand while it is up fails with `lgpio.error: 'GPIO busy'`. Stop it first: `sudo systemctl stop TodoDisplay`, run `.venv/bin/python ./src/__main__.py --task`, then `sudo systemctl start TodoDisplay`.
- To deploy: merge to `master`, then on the Pi `git pull` and `sudo systemctl restart TodoDisplay`.
- The TickTick token lasts about 180 days. A 401 from the API means it expired. Renew from `src/` on the Pi: `../.venv/bin/python -m taskFetcher --user` prints the authorize URL, then `-m taskFetcher --verify <code>`, put the new token into the Pi's `src/taskFetcher/.env` (mode 600), restart the service. The user does this themselves; never ask for the code or token in chat.
- The agent cannot enter sudo passwords. Give privileged commands for the user to run (`! <command>` in the prompt).

## TodoApp integration (planned)

The user's own Android app (`../TodoApp`, Firestore sync) is becoming the main source of tasks. The plan and decisions are in issues #35 to #39: a read-only service account, a REST fetcher, a two-column layout (today's Daily Items and this week's Weekly Items), and a `--source` option. For the data format read `docs/adr/0015-*.md` and `app/src/main/java/com/hturner/simpletodo/Sync/` in that repo. Project IDs, user ids and key files stay in the Pi's local config, never in this repo or its issues.

## Secrets

This repo is public. Never commit or paste into issues, PRs or chat: the TickTick token or OAuth code, `.env` contents, service-account keys, Firebase project IDs or user ids, wifi passwords. `.env` is gitignored; only `.env.sample` (names, no values) is committed.

## Git and GitHub

- Branch off `develop` as `feature/*` and open a PR into `develop`. Do not commit directly to `develop` or `master`.
- The Pi runs `master`; changes reach it by merge and `git pull`. Only the owner merges.
- GitHub rejects pushes that expose the user's private email. Commit with `GIT_AUTHOR_EMAIL` and `GIT_COMMITTER_EMAIL` set to the user's GitHub noreply address (`gh api user` gives the id and login).
- Work is tracked in GitHub Issues (`gh`), with `priority: high|medium|low` labels. Design work is labelled `design`, TodoApp integration `todoapp`.
