# Display design system

The display follows the TodoApp's "printed planner" design system (the app's `docs/agents/design-system.md`, ADR-0016 and `docs/design/style-guide.html`), adapted to a 648x480 pure black-and-white panel. When the app's rules and the panel disagree, the panel wins, and the difference is recorded here.

## Matches the app

| Rule in the app | On the display |
|---|---|
| One sans family, Inter | Inter Bold for every text style. |
| Italic serif, Newsreader, for the banner title only | The date heading. |
| One label style: uppercase, letter-spaced (.14 em) | Column headings and the week strip. |
| 12-hour clock ("6:30 PM") | Task times and the "Updated" footer. |
| Day first, sentence case, plain wording, no exclamation marks | Date heading, notices. |
| Hairline rules, no cards or shadows | Ruled rows and a single divider. |
| Bullet-journal glyphs with fixed meanings | Dot, x, chevron, dash, struck dot, asterisk (Priority). Same geometry as the app where the grid allows. |
| Red means "now" only | There is no colour: "today" is the inverted day in the week strip. |

## Adapted for the panel

- **Weight.** The app sets body text in regular weight and labels in medium. The real panel looks paler and smaller than the preview (issues #41, #50), so everything is Inter Bold and the banner is Newsreader SemiBold Italic.
- **Cancelled.** The app fades the dot and title. The panel has no greys, so the dot is a ring with a dash through it and the title is struck through.
- **Sizes.** The app's ten-size type scale is for phone screens. The display keeps its own sizes (banner 38, tasks 27, labels 21, footer 19 px) because it is read from across a room.

## Cannot map

- **Faint ink** for done, moved and cancelled titles: 1-bit has no faint ink. Done and moved titles look like open ones; their glyph carries the state.
- **Paper tone** and **sage/paper colours**: the panel is white.
- **Light weights** (the 300 date numerals): too thin to read on the panel.
- **Motion**: the panel redraws in full, so nothing animates.

## Fonts

Static, Latin-subset instances cut from the TodoApp's variable fonts, with the Polish letters included. Both are SIL OFL 1.1; the licence texts sit beside them in `src/screenDisplay/fonts/`.

| File | Source instance | Use |
|---|---|---|
| `Inter-Bold.ttf` | Inter, weight 700, optical size 28 | Tasks, labels, footer, notices |
| `Newsreader-SemiBoldItalic.ttf` | Newsreader Italic, weight 650, optical size 40 | Date heading |

`DejaVuSans-Bold.ttf` is only used by `benchmark.py` now; `Verdana.ttf` and `BitterPro-Regular.ttf` are unused.
