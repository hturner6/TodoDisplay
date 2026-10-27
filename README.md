# TODO Display

An app custom created for displaying tasks from TickTick on the waveshare 5.83 inch e-paper display.
The screen is 648 x 480 pixels

The task fetcher module can be run in the src/ folder via the command `python -m taskFetcher`

## Previewing the layout

Render the screen to a PNG on any machine, without the display or GPIO, from the repo root:

```
.venv/bin/python src/__main__.py --preview                       # real tasks -> previews/preview.png
.venv/bin/python src/__main__.py --preview --fake few              # sample tasks, no credentials
```

`--fake` takes `empty`, `few`, `many`, `long` or `states` (every completion glyph). The PNG is passed through the same resize and 1-bit conversion as the real display; add `--raw` to skip that and see the unconverted greyscale image. The PNG opens in your default viewer afterwards; add `--no-open` to turn that off. If your default PNG handler is not a plain viewer, set `PREVIEW_VIEWER` to a command, e.g. `PREVIEW_VIEWER=feh`.

## Layout and frame margins

The display draws in pure 1-bit black and white (the panel has no greys) in DejaVu Sans Bold, with a date header, a week strip, ruled task rows and an 'Updated HH:MM' footer. The picture frame's mat hides the panel's edges, so content stays inside margins (default top 28, right 32, bottom 30, left 32 px; a first guess, not yet measured). Override them with the `DISPLAY_MARGINS="top,right,bottom,left"` environment variable, and check them with `--preview --safe-area`, which outlines the safe area in red.

## When the screen is redrawn

To limit ghosting and wear, the `--run` loop skips the redraw when the tasks have not changed (it still redraws hourly so the footer time stays honest), wipes the panel once a day, and puts the panel to sleep after each draw. If a fetch fails, the screen is left alone until its data is two hours old, then redrawn with a STALE marker; if nothing has ever been drawn, an error notice (expired sign-in, or cannot reach TickTick) is shown. The driver has no partial refresh, so every update is a full one.

## Forcing a refresh on the Pi

The service only redraws every 30 minutes. To redraw now, run `./refresh.sh` on the Pi (add `--clear` to wipe the screen first and remove ghosting). It stops the `TodoDisplay` service while drawing, since the service holds the display's GPIO, and starts it again afterwards.

## Connecting the Pi to TodoApp (read-only)

The Pi reads TodoApp data from Firestore with a dedicated service account that has only the `Cloud Datastore Viewer` role, because the app's security rules also let members write. Run the guided setup from the repo root on your laptop:

```
./scripts/setup-todoapp-access.sh
```

It walks you through finding the project id and user id, creating the service account and its JSON key, copying the key to the Pi (`~/.config/tododisplay/`, mode 600, outside the checkout) and setting `TODOAPP_PROJECT_ID`, `TODOAPP_SPACE_ID` and `TODOAPP_KEY_FILE` in `src/taskFetcher/.env` on both machines. Never commit the key or those values; the repo is public.
