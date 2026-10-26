# TODO Display

An app custom created for displaying tasks from TickTick on the waveshare 5.83 inch e-paper display.
The screen is 648 x 480 pixels

The task fetcher module can be run in the src/ folder via the command `python -m taskFetcher`

## Previewing the layout

Render the screen to a PNG on any machine, without the display or GPIO, from the repo root:

```
.venv/bin/python src/__main__.py --preview                    # real tasks -> preview.png
.venv/bin/python src/__main__.py --preview out.png --fake few # sample tasks, no credentials
```

`--fake` takes `empty`, `few`, `many` or `long`. The PNG is passed through the same resize and 1-bit conversion as the real display; add `--raw` to skip that and see the unconverted greyscale image. The PNG opens in your default viewer afterwards; add `--no-open` to turn that off. If your default PNG handler is not a plain viewer, set `PREVIEW_VIEWER` to a command, e.g. `PREVIEW_VIEWER=feh`.
