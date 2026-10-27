from collections import namedtuple
from datetime import date, datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from models.task import Task
from taskDisplay.timeFormat import format_time
from taskDisplay.screenLayout import (GLYPH_COLUMN, LINE_HEIGHT, META_SIZE, ROW_PADDING, TASK_SIZE, Column, Row,
                                      build_layout)

# Space kept clear around the content, in pixels. The picture frame's mat hides the panel's edges,
# so these are a first guess and need measuring against the real frame (see issue #50).
Margins = namedtuple("Margins", "top right bottom left")
DEFAULT_MARGINS = Margins(top=28, right=32, bottom=30, left=32)

BLACK = 0
WHITE = 255

TITLE_SIZE = 38
SMALL_SIZE = 19

LABEL_TRACKING = 0.14  # of the font size, for the uppercase labels (the TodoApp's one label style)
COLUMN_GAP = 24
DAILY_SHARE = 0.56  # of the content width; Daily Items carry a time, Weekly Items only a day


def parse_margins(text: str) -> Margins:
    """Reads "top,right,bottom,left", e.g. from the DISPLAY_MARGINS environment variable."""
    top, right, bottom, left = (int(part) for part in text.split(","))
    return Margins(top, right, bottom, left)


class TaskDrawer():
    def __init__(self, fontPath, width=648, height=480, margins: Margins = DEFAULT_MARGINS,
                 two_columns: bool = False, banner_font_path=None):
        self.width = width
        self.height = height
        self.margins = margins
        # Today's Daily Items beside this week's Weekly Items, or a single list of Daily Items.
        self.two_columns = two_columns
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
                          today: date = None, stale: bool = False, reason: str = "") -> Image:
        self._new_canvas()
        tasks = tasks or []
        today = today or datetime.now().date()

        footer_top = self._draw_footer(updated_at, stale=stale, reason=reason)
        # The Weekly column labels each item with its day, so the week strip would be a
        # repeat that costs a third of the height.
        top = self._draw_header(today, week_strip=not self.two_columns)
        spans, divider = self._column_spans()
        rows_top = top + (6 + META_SIZE + 10 if self.two_columns else 0)
        layout = build_layout(tasks, today, [x1 - x0 for x0, x1 in spans], footer_top - 4 - rows_top,
                              self.taskFont.getlength, self.metaFont.getlength)

        if layout.message:
            self._draw_message(layout.message.heading, layout.message.detail, top, footer_top)
            return self.img
        if self.two_columns:
            self.draw.line((divider, top + 8, divider, footer_top - 8), fill=BLACK, width=2)
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

    def _draw_header(self, today: date, week_strip: bool = True) -> int:
        """Draws the date heading and week strip, and returns the y where the content can start."""
        y = self.margins.top
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
