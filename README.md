# TODO Display

An app custom created for displaying tasks from TodoApp (or TickTick) on the waveshare 5.83 inch e-paper display.
The screen is 648 x 480 pixels

The task fetcher module can be run in the src/ folder via the command `python -m taskFetcher`

## Previewing the layout

Render the screen to a PNG on any machine, without the display or GPIO, from the repo root:

```
.venv/bin/python src/__main__.py --preview                       # real tasks -> previews/preview.png
.venv/bin/python src/__main__.py --preview --fake few              # sample tasks, no credentials
```

`--fake` takes `empty`, `few`, `many`, `long` or `states` (every completion glyph), or `stale` and `error` to see the stale-data footer and the full-screen error notice. The PNG is passed through the same resize and 1-bit conversion as the real display; add `--raw` to skip that and see the unconverted greyscale image. The PNG opens in your default viewer afterwards; add `--no-open` to turn that off. If your default PNG handler is not a plain viewer, set `PREVIEW_VIEWER` to a command, e.g. `PREVIEW_VIEWER=feh`.

## Layout and frame margins

The display draws in pure 1-bit black and white (the panel has no greys) in Inter Bold with an italic Newsreader date heading (the TodoApp's type; see `docs/design-system.md`), with a date header, a week strip, ruled task rows (a priority row has a heavy asterisk before its bullet, as in the TodoApp) and an 'Updated 9:30 AM' footer. The picture frame's mat hides the panel's edges, so content stays inside margins (default top 28, right 32, bottom 30, left 32 px; a first guess, not yet measured). Override them with the `DISPLAY_MARGINS="top,right,bottom,left"` environment variable, and check them with `--preview --safe-area`, which outlines the safe area in red.

## Fonts and licences

The display's text is set in Inter and Newsreader Italic, the TodoApp's typefaces, bundled as static Latin-subset instances in `src/screenDisplay/fonts/` (`Inter-Bold.ttf`, `Newsreader-SemiBoldItalic.ttf`). Both are © their authors and licensed under the SIL Open Font License 1.1, which allows bundling and redistribution; the full licence texts are `OFL-Inter.txt` and `OFL-Newsreader.txt` in the same folder and must stay with the fonts. `docs/design-system.md` explains the choice. The other font files in that folder are not used by the display.

## When the screen is redrawn

To limit ghosting and wear, the `--run` loop skips the redraw when the tasks have not changed (it still redraws hourly so the footer time stays honest), wipes the panel once a day, and puts the panel to sleep after each draw. If a fetch fails, the screen is left alone until its data is two hours old, then redrawn with a STALE marker that names the cause (e.g. "STALE - Cannot reach TodoApp - last update 09:30"); if nothing has ever been drawn, an error notice (expired sign-in, or cannot reach TodoApp or TickTick) is shown. The driver has no partial refresh, so every update is a full one.

**Quiet hours.** The `--run` loop neither fetches nor draws overnight (default 23:00 to 06:00), leaving the last picture on the panel, which keeps it without power. The first refresh after the window always redraws. Set `QUIET_HOURS="HH:MM-HH:MM"` in `src/taskFetcher/.env` to change the window, or `QUIET_HOURS=off` to disable it. A one-off `--task` (and `./refresh.sh`) ignores quiet hours.

## Weather

Set `WEATHER_LATITUDE` and `WEATHER_LONGITUDE` in `src/taskFetcher/.env` (the Pi's own file, never committed) and the header shows a weather glyph and the temperature in whole degrees Celsius, from [Open-Meteo](https://open-meteo.com/) (no key or account). Only the coordinates, rounded to one decimal (about 11 km), are sent. The forecast is asked for at most once an hour (a failed request is retried after ten minutes); if it keeps failing, the last weather stays for up to three hours and is then hidden, with no error shown. Leave both empty for no weather. `--preview --weather rain` (or `clear`, `partly`, `cloud`, `fog`, `snow`, `storm`) shows a sample.

## Weather

Set `WEATHER_LATITUDE` and `WEATHER_LONGITUDE` in `src/taskFetcher/.env` (the Pi's own file, never committed) and the header shows a weather glyph and the temperature in whole degrees Celsius, from [Open-Meteo](https://open-meteo.com/) (no key or account). Only the coordinates, rounded to one decimal (about 11 km), are sent. The forecast is asked for at most once an hour (a failed request is retried after ten minutes); if it keeps failing, the last weather stays for up to three hours and is then hidden, with no error shown. Leave both empty for no weather. `--preview --weather rain` (or `clear`, `partly`, `cloud`, `fog`, `snow`, `storm`) shows a sample.

## Polish word of the day

A beginner Polish word with its meaning and an example sentence (and its translation) sits under the tasks: the word and meaning on the footer line, the example above it. The word comes from `src/taskDisplay/polishWords.csv` (columns `polish`, `english`, `example`, `example_english`; edit or extend it freely, quoting fields that contain commas) and is picked by date, so it is the same all day and every word comes round before any repeats. Tasks come first: the word is only drawn when it costs no task its place, so a full day hides it, and a stale or error screen never shows it. Set `WORD_OF_THE_DAY=off` in `src/taskFetcher/.env` to turn it off. The list is hand-written beginner vocabulary and has not been checked by a Polish speaker.

## Running on the Pi (systemd)

The Pi (Zero 2 W, Raspberry Pi OS Bookworm, hostname `inkpi`) runs the app as the systemd service `TodoDisplay`, not from cron. The service runs `run.sh`, which starts `--run 30`: it draws as soon as it starts, then every 30 minutes. The unit file is `deploy/TodoDisplay.service`; adjust `User` and the paths if your checkout is elsewhere, and compare it with `systemctl cat TodoDisplay` on the Pi.

```
sudo cp deploy/TodoDisplay.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now TodoDisplay
journalctl -u TodoDisplay -f          # follow the log
```

To deploy a change: merge to `master`, then on the Pi `git pull` and `sudo systemctl restart TodoDisplay`.

**GPIO busy.** The service holds the display's GPIO, so running the app by hand while it is up fails with `lgpio.error: 'GPIO busy'`. Stop the service first, then start it again afterwards (`./refresh.sh` does this for you):

```
sudo systemctl stop TodoDisplay
.venv/bin/python ./src/__main__.py --task
sudo systemctl start TodoDisplay
```

## Renewing the TickTick token

Only needed while using `--source ticktick`. The token lasts about 180 days, and a 401 from the API (the screen shows "Sign-in expired") means it has expired. The current one runs out around late April 2027 (`--verify` prints the new date each time you renew). `CLIENT_ID` and `CLIENT_SECRET` must already be set in `src/taskFetcher/.env`. From `src/` on the Pi:

```
../.venv/bin/python -m taskFetcher --user           # prints the authorize URL; open it and approve
../.venv/bin/python -m taskFetcher --verify <code>  # <code> is the `code` in the redirect URL
sudo systemctl restart TodoDisplay
```

`--verify` writes the new `ACCESS_TOKEN` into `src/taskFetcher/.env` (mode 600) and prints the file path and the expiry date, never the token. Type the code into the terminal; never paste it into chat or an issue. `TICKTICK_PROJECT_ID` and `TICKTICK_REDIRECT_URI` can also be set in that file; see `.env.sample`.

## Forcing a refresh on the Pi

The service only redraws every 30 minutes. To redraw now, run `./refresh.sh` on the Pi (add `--clear` to wipe the screen first and remove ghosting). It stops the `TodoDisplay` service while drawing, since the service holds the display's GPIO, and starts it again afterwards.

## Connecting the Pi to TodoApp (read-only)

The Pi reads TodoApp data from Firestore with a dedicated service account that has only the `Cloud Datastore Viewer` role, because the app's security rules also let members write. Run the guided setup from the repo root on your laptop:

```
./scripts/setup-todoapp-access.sh
```

It walks you through finding the project id and user id, creating the service account and its JSON key, copying the key to the Pi (`~/.config/tododisplay/`, mode 600, outside the checkout) and setting `TODOAPP_PROJECT_ID`, `TODOAPP_SPACE_ID` and `TODOAPP_KEY_FILE` in `src/taskFetcher/.env` on both machines. Never commit the key or those values; the repo is public.

## Trying the TodoApp fetcher

Once the Pi (or laptop) has the `TODOAPP_*` values in `src/taskFetcher/.env`, list what the display would show: today's Daily Items, then this week's (Monday to Sunday) Weekly Items.

```
cd src && ../.venv/bin/python -m taskFetcher --todoapp
```

It signs in with `openssl`, which Raspberry Pi OS includes, so no extra Python packages are needed.

## Choosing where tasks come from

The display shows tasks from TodoApp by default (today's Daily Items on the left, this week's Weekly Items on the right). TickTick is kept as a fallback.

- One-off: `--source todoapp` or `--source ticktick`, on any command (`--task`, `--run`, `--preview`).
- For the systemd service: set `TASK_SOURCE=ticktick` (or `todoapp`) in `src/taskFetcher/.env` on the Pi, then `sudo systemctl restart TodoDisplay`.

The flag wins over `TASK_SOURCE`, which wins over the default. An unknown name stops the app with an error naming the choices.
