from collections import namedtuple
import math
from datetime import date, datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from models.task import Task
from taskDisplay.timeFormat import format_time
from taskDisplay.wordOfTheDay import Word, word_for
from taskFetcher.weather import Weather
from taskDisplay.screenLayout import (GLYPH_COLUMN, LINE_HEIGHT, META_SIZE, ROW_PADDING, TASK_SIZE, Column, Row,
                                      build_layout, wrap_text)

# Space kept clear around the content, in pixels. The picture frame's mat hides the panel's edges,
# so these are a first guess and need measuring against the real frame (see issue #50).
Margins = namedtuple("Margins", "top right bottom left")
DEFAULT_MARGINS = Margins(top=28, right=32, bottom=30, left=32)

BLACK = 0
WHITE = 255

TITLE_SIZE = 38
SMALL_SIZE = 19

LABEL_TRACKING = 0.14  # of the font size, for the uppercase labels (the TodoApp's one label style)
WEATHER_GLYPH = 34  # width of a weather glyph
WEATHER_GAP = 8  # between the glyph and the temperature
WORD_BLOCK_HEIGHT = META_SIZE + SMALL_SIZE + 18  # the example, its translation and their padding, above the footer row
WORD_GAP = 14  # between the word and its meaning, and before 'Updated'
COLUMN_GAP = 24
DAILY_SHARE = 0.56  # of the content width; Daily Items carry a time, Weekly Items only a day


def parse_margins(text: str) -> Margins:
    """Reads "top,right,bottom,left", e.g. from the DISPLAY_MARGINS environment variable."""
    top, right, bottom, left = (int(part) for part in text.split(","))
    return Margins(top, right, bottom, left)


def _hidden(layout) -> int:
    """How many tasks did not fit on the screen."""
    return sum(column.more for column in layout.columns)


class TaskDrawer():
    def __init__(self, fontPath, width=648, height=480, margins: Margins = DEFAULT_MARGINS,
                 two_columns: bool = False, banner_font_path=None, words: list[Word] = None):
        self.width = width
        self.height = height
        self.margins = margins
        # Today's Daily Items beside this week's Weekly Items, or a single list of Daily Items.
        self.two_columns = two_columns
        # Polish words, one shown each day under the tasks; None for no word of the day.
        self.words = words or []
        # The TodoApp's type: one sans family, with an italic serif for the banner alone. The banner
        # falls back to the task font, so one path is enough.
        self.titleFont = ImageFont.truetype(banner_font_path or fontPath, TITLE_SIZE)
        self.headingFont = ImageFont.truetype(fontPath, TITLE_SIZE)
        self.taskFont = ImageFont.truetype(fontPath, TASK_SIZE)
        self.metaFont = ImageFont.truetype(fontPath, META_SIZE)
        self.smallFont = ImageFont.truetype(fontPath, SMALL_SIZE)
        self.left = margins.left
        self.right = width - margins.right - 1
        self.bottom = height - margins.bottom
        self._new_canvas()

    def _new_canvas(self):
        self.img = Image.new('L', (self.width, self.height), color=WHITE)
        self.draw = ImageDraw.Draw(self.img)
        # No anti-aliasing: the panel is black/white only, so grey edge pixels just come out ragged.
        self.draw.fontmode = "1"

    # --- screens -------------------------------------------------------------------------------

    def create_task_image(self, tasks: list[Task] = None, updated_at: datetime = None,
                          today: date = None, stale: bool = False, reason: str = "",
                          weather: Weather = None) -> Image:
        self._new_canvas()
        tasks = tasks or []
        today = today or datetime.now().date()

        footer_top = self._draw_footer(updated_at, stale=stale, reason=reason)
        # The Weekly column labels each item with its day, so the week strip would be a
        # repeat that costs a third of the height.
        top = self._draw_header(today, week_strip=not self.two_columns, weather=weather)
        spans, divider = self._column_spans()
        rows_top = top + (6 + META_SIZE + 10 if self.two_columns else 0)

        def fit(bottom):
            return build_layout(tasks, today, [x1 - x0 for x0, x1 in spans], bottom - 4 - rows_top,
                                self.taskFont.getlength, self.metaFont.getlength)

        layout = fit(footer_top)
        content_bottom = footer_top
        # A stale footer already has a notice to show, so it gets no word. Tasks come first: the
        # word is only drawn when it costs no task its place.
        word = None if stale else word_for(today, self.words)
        if word:
            with_word = fit(footer_top - WORD_BLOCK_HEIGHT)
            if _hidden(with_word) == _hidden(layout):
                layout = with_word
                content_bottom = self._draw_word(word, footer_top, updated_at)

        if layout.message:
            self._draw_message(layout.message.heading, layout.message.detail, top, content_bottom)
            return self.img
        if self.two_columns:
            self.draw.line((divider, top + 8, divider, content_bottom - 8), fill=BLACK, width=2)
        for column, (x0, x1) in zip(layout.columns, spans):
            self._draw_column(column, top, rows_top, x0, x1)
        return self.img

    def create_message_image(self, heading: str, detail: str = "", updated_at: datetime = None,
                             today: date = None) -> Image:
        """A full-screen notice, e.g. when the tasks could not be fetched."""
        self._new_canvas()
        footer_top = self._draw_footer(updated_at, show_time=updated_at is not None)
        top = self._draw_header(today or datetime.now().date())
        self._draw_message(heading, detail, top, footer_top)
        return self.img

    # --- header and footer ---------------------------------------------------------------------

    def _draw_header(self, today: date, week_strip: bool = True, weather: Weather = None) -> int:
        """Draws the date heading, weather and week strip, and returns the y where the content can start."""
        y = self.margins.top
        if weather:
            self._draw_weather(weather, y + TITLE_SIZE // 2 + 4)
        self._draw_text_inside((self.left, y), today.strftime("%A %-d %B"), self.titleFont)
        y += TITLE_SIZE + 14

        if week_strip:
            monday = today - timedelta(days=today.weekday())
            cell_width = (self.right - self.left) / 7
            strip_height = META_SIZE + 12
            for offset in range(7):
                day = monday + timedelta(days=offset)
                x0 = self.left + offset * cell_width
                label = day.strftime("%a").upper()
                is_today = day == today
                if is_today:
                    self.draw.rectangle((x0, y, x0 + cell_width - 4, y + strip_height), fill=BLACK)
                text_width = self._label_width(label, self.metaFont)
                self._draw_label((x0 + (cell_width - 4 - text_width) / 2, y + 5), label,
                                 fill=WHITE if is_today else BLACK)
            y += strip_height + 12

        self.draw.line((self.left, y, self.right, y), fill=BLACK, width=3)
        return y + 3

    def _draw_weather(self, weather: Weather, cy: int):
        """The weather glyph and temperature, right-aligned with the date heading."""
        text = f"{weather.temperature}\u00b0"
        text_width = self.taskFont.getlength(text)
        self.draw.text((self.right - text_width, cy - TASK_SIZE * 0.62), text, font=self.taskFont, fill=BLACK)
        self._draw_weather_glyph(weather.condition, int(self.right - text_width - WEATHER_GAP - WEATHER_GLYPH // 2), cy)

    def _draw_weather_glyph(self, condition: str, cx: int, cy: int):
        """A fixed-size shape per condition, about 34px across, so it looks the same whatever the font."""
        d = self.draw
        if condition == "clear":
            self._draw_sun(cx, cy, 8)
        elif condition == "fog":
            for i, (inset, dy) in enumerate(((2, -9), (8, -1), (0, 7))):
                d.line((cx - 16 + inset, cy + dy, cx + 16 - (8 if i == 1 else 2), cy + dy), fill=BLACK, width=4)
        elif condition == "partly":
            self._draw_sun(cx - 5, cy - 6, 6)
            self._draw_cloud(cx + 3, cy + 5, outline=True)
        else:
            self._draw_cloud(cx, cy - 4)
            self._draw_precipitation(condition, cx, cy + 8)

    def _draw_sun(self, cx: int, cy: int, r: int):
        self.draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=BLACK, width=3)
        for k in range(8):
            angle = k * math.pi / 4
            ux, uy = math.cos(angle), math.sin(angle)
            self.draw.line((cx + ux * (r + 4), cy + uy * (r + 4), cx + ux * (r + 8), cy + uy * (r + 8)),
                           fill=BLACK, width=3)

    def _draw_cloud(self, cx: int, cy: int, outline: bool = False):
        """A solid cloud about 30px wide; outline leaves a white margin round it, to sit in front of a sun."""
        d = self.draw
        for grow, fill in (((4, WHITE),) if outline else ()) + ((0, BLACK),):
            g = grow
            d.ellipse((cx - 14 - g, cy - 2 - g, cx - 2 + g, cy + 10 + g), fill=fill)
            d.ellipse((cx - 8 - g, cy - 10 - g, cx + 8 + g, cy + 6 + g), fill=fill)
            d.ellipse((cx + 2 - g, cy - 4 - g, cx + 14 + g, cy + 10 + g), fill=fill)
            d.rectangle((cx - 8 - g, cy - 2 - g, cx + 8 + g, cy + 10 + g), fill=fill)

    def _draw_precipitation(self, condition: str, cx: int, y: int):
        d = self.draw
        if condition == "rain":
            for dx in (-9, 0, 9):
                d.line((cx + dx + 2, y, cx + dx - 2, y + 9), fill=BLACK, width=4)
        elif condition == "snow":
            for dx in (-9, 0, 9):
                d.ellipse((cx + dx - 2, y + 2, cx + dx + 2, y + 6), fill=BLACK)
                d.ellipse((cx + dx - 2, y + 9, cx + dx + 2, y + 13), fill=BLACK) if dx == 0 else None
        elif condition == "storm":
            d.polygon([(cx + 3, y - 1), (cx - 5, y + 7), (cx, y + 7), (cx - 3, y + 15), (cx + 6, y + 5), (cx + 1, y + 5)],
                      fill=BLACK)

    def _draw_word(self, word: Word, footer_top: int, updated_at: datetime = None) -> int:
        """Draws the Polish word of the day and returns the y where the content above it must end.

        The word and its meaning share the footer's row, to the left of 'Updated HH:MM'; the example
        sentence and its translation sit on the two lines above, under a hairline.
        """
        def cut(font, text, width):
            return wrap_text(font.getlength, text, [max(width, 0)], 1)[0] if text else ""

        updated = f"Updated {format_time(updated_at or datetime.now())}"
        row_right = self.right - self.smallFont.getlength(updated) - WORD_GAP * 2
        polish = cut(self.metaFont, word.polish, row_right - self.left)
        used = self.metaFont.getlength(polish) + WORD_GAP
        english = cut(self.smallFont, word.english, row_right - self.left - used)
        self._draw_text_inside((self.left, footer_top), polish, self.metaFont)
        self.draw.text((self.left + used, footer_top + 2), english, font=self.smallFont, fill=BLACK)

        width = self.right - self.left
        rule_y = footer_top - WORD_BLOCK_HEIGHT
        example_y = rule_y + 8
        translation_y = example_y + META_SIZE + 4
        self._draw_text_inside((self.left, example_y), cut(self.metaFont, word.example, width), self.metaFont)
        self._draw_text_inside((self.left, translation_y), cut(self.smallFont, word.example_english, width),
                               self.smallFont)
        self.draw.line((self.left, rule_y, self.right, rule_y), fill=BLACK, width=1)
        return rule_y

    def _draw_footer(self, updated_at: datetime = None, show_time: bool = True, stale: bool = False,
                     reason: str = "") -> int:
        """Draws 'Updated HH:MM' bottom-right (or a STALE notice with its cause), and returns the y where the footer starts."""
        top = self.bottom - SMALL_SIZE - 6
        if not show_time:
            return top

        updated_at = updated_at or datetime.now()
        if stale:
            label = f"STALE - {reason + ' - ' if reason else ''}last update {format_time(updated_at)}"
            text_width = self.smallFont.getlength(label)
            x0 = self.right - text_width - 12
            self.draw.rectangle((x0, top, self.right, self.bottom), fill=BLACK)
            self.draw.text((x0 + 6, top + 2), label, font=self.smallFont, fill=WHITE)
        else:
            label = f"Updated {format_time(updated_at)}"
            text_width = self.smallFont.getlength(label)
            self.draw.text((self.right - text_width, top + 2), label, font=self.smallFont, fill=BLACK)
        return top

    def _draw_text_inside(self, xy, text: str, font, fill=BLACK):
        """Draws text so no ink starts left of x: an italic capital or a "j" can lean out past its origin."""
        x, y = xy
        self.draw.text((x - min(0, font.getbbox(text)[0]), y), text, font=font, fill=fill)

    def _label_width(self, text: str, font) -> float:
        return sum(font.getlength(character) + LABEL_TRACKING * font.size for character in text) - LABEL_TRACKING * font.size

    def _draw_label(self, xy, text: str, fill=BLACK):
        """Uppercase label text, letter-spaced as the TodoApp does."""
        x, y = xy
        for character in text:
            self.draw.text((x, y), character, font=self.metaFont, fill=fill)
            x += self.metaFont.getlength(character) + LABEL_TRACKING * self.metaFont.size

    # --- rows ----------------------------------------------------------------------------------

    def _column_spans(self):
        """The x extent of each column, and the x of the divider between two columns."""
        if not self.two_columns:
            return [(self.left, self.right)], None
        content = self.right - self.left
        divider = self.left + round(content * DAILY_SHARE)
        return [(self.left, divider - COLUMN_GAP // 2), (divider + COLUMN_GAP // 2, self.right)], divider

    def _draw_column(self, column: Column, top: int, rows_top: int, x0: int, x1: int):
        if column.heading:
            self._draw_label((x0, top + 6), column.heading)
            self.draw.line((x0, rows_top - 4, x1, rows_top - 4), fill=BLACK, width=1)
        if not column.rows:
            for i, line in enumerate(column.empty):
                self.draw.text((x0, rows_top + ROW_PADDING + i * LINE_HEIGHT), line, font=self.taskFont, fill=BLACK)
            return

        text_x = x0 + GLYPH_COLUMN
        y = rows_top
        for row in column.rows:
            self._draw_row(row, y, text_x, x0, x1)
            y += row.height
            self.draw.line((x0, y - 1, x1, y - 1), fill=BLACK, width=1)
        if column.more:
            self.draw.text((text_x, y + ROW_PADDING), f"+{column.more} more", font=self.metaFont, fill=BLACK)

    def _draw_row(self, row: Row, y: int, text_x: int, x0: int, x1: int):
        for i, line in enumerate(row.lines):
            line_y = y + ROW_PADDING + i * LINE_HEIGHT
            self.draw.text((text_x, line_y), line, font=self.taskFont, fill=BLACK)
            if row.status == Task.CANCELLED:
                strike_y = line_y + TASK_SIZE * 0.58
                self.draw.line((text_x, strike_y, text_x + self.taskFont.getlength(line), strike_y),
                               fill=BLACK, width=2)

        if row.meta:
            meta_width = self.metaFont.getlength(row.meta)
            self.draw.text((x1 - meta_width, y + ROW_PADDING + 4), row.meta, font=self.metaFont, fill=BLACK)

        glyph_cy = y + ROW_PADDING + LINE_HEIGHT // 2
        if row.priority:
            self._draw_asterisk(x0 + 10, glyph_cy)
        self._draw_glyph(row, x0 + 32, glyph_cy)

    # --- glyphs: fixed-size shapes, so they look the same whatever the font ---------------------

    def _draw_glyph(self, row: Row, cx: int, cy: int):
        d = self.draw
        if row.status == Task.DONE:
            r = 7
            d.line((cx - r, cy - r, cx + r, cy + r), fill=BLACK, width=4)
            d.line((cx - r, cy + r, cx + r, cy - r), fill=BLACK, width=4)
        elif row.status == Task.MOVED:
            r = 8
            d.line((cx - 4, cy - r, cx + 5, cy), fill=BLACK, width=4)
            d.line((cx + 5, cy, cx - 4, cy + r), fill=BLACK, width=4)
        elif row.status == Task.NOTE:
            d.line((cx - 7, cy, cx + 7, cy), fill=BLACK, width=4)
        elif row.status == Task.CANCELLED:
            # A struck dot. The TodoApp fades the dot; the panel has no greys, so it is a ring instead.
            r = 6
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=BLACK, width=2)
            d.line((cx - 9, cy, cx + 9, cy), fill=BLACK, width=2)
        else:
            r = 6
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=BLACK)

    def _draw_asterisk(self, cx: int, cy: int):
        """The TodoApp's Priority mark: a vertical stroke and two diagonals, in the gutter left of the bullet."""
        r = 8
        dx, dy = r * 0.87, r * 0.5
        for x, y in ((0, r), (dx, dy), (dx, -dy)):
            self.draw.line((cx - x, cy - y, cx + x, cy + y), fill=BLACK, width=4)

    # --- messages ------------------------------------------------------------------------------

    def _draw_message(self, heading: str, detail: str, top: int, bottom: int):
        heading_width = self.headingFont.getlength(heading)
        block_height = TITLE_SIZE + (TASK_SIZE + 12 if detail else 0)
        y = top + (bottom - top - block_height) / 2
        self.draw.text(((self.width - heading_width) / 2, y), heading, font=self.headingFont, fill=BLACK)
        if detail:
            detail_width = self.taskFont.getlength(detail)
            self.draw.text(((self.width - detail_width) / 2, y + TITLE_SIZE + 12), detail,
                           font=self.taskFont, fill=BLACK)
