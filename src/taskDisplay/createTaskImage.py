from collections import namedtuple
from datetime import date, datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from models.task import Task

# Space kept clear around the content, in pixels. The picture frame's mat hides the panel's edges,
# so these are a first guess and need measuring against the real frame (see issue #50).
Margins = namedtuple("Margins", "top right bottom left")
DEFAULT_MARGINS = Margins(top=28, right=32, bottom=30, left=32)

BLACK = 0
WHITE = 255

TITLE_SIZE = 38
TASK_SIZE = 27
META_SIZE = 21
SMALL_SIZE = 19

GLYPH_COLUMN = 42
ROW_PADDING = 8
MAX_TITLE_LINES = 2
STALE_AFTER = timedelta(hours=2)


def parse_margins(text: str) -> Margins:
    """Reads "top,right,bottom,left", e.g. from the DISPLAY_MARGINS environment variable."""
    top, right, bottom, left = (int(part) for part in text.split(","))
    return Margins(top, right, bottom, left)


def wrap_text(font, text: str, max_widths: list[float], max_lines: int) -> list[str]:
    """Wraps text to at most max_lines lines, ending the last one with an ellipsis if it is cut.

    max_widths[i] is the width available to line i; the last entry applies to any later lines.
    Words wider than a whole line are broken mid-word.
    """
    def width_of(line):
        return max_widths[min(len(lines), len(max_widths) - 1)]

    lines: list[str] = []
    current = ""
    words = text.split()
    index = 0
    truncated = False
    while index < len(words):
        word = words[index]
        candidate = f"{current} {word}" if current else word
        if font.getlength(candidate) <= width_of(candidate):
            current = candidate
            index += 1
            continue
        if current:
            lines.append(current)
            current = ""
        else:
            # A single word wider than the line: take as many characters as fit.
            fitted = word
            while len(fitted) > 1 and font.getlength(fitted) > width_of(fitted):
                fitted = fitted[:-1]
            lines.append(fitted)
            words[index] = word[len(fitted):]
            if not words[index]:
                index += 1
        if len(lines) == max_lines and index < len(words):
            truncated = True
            break
    if current:
        lines.append(current)

    if truncated:
        lines[-1] = _with_ellipsis(font, lines[-1], max_widths[min(max_lines - 1, len(max_widths) - 1)])
    return lines


def _with_ellipsis(font, line: str, max_width: float) -> str:
    line = line.rstrip()
    while line and font.getlength(line + "…") > max_width:
        line = line[:-1].rstrip()
    return line + "…"


class TaskDrawer():
    def __init__(self, fontPath, width=648, height=480, margins: Margins = DEFAULT_MARGINS,
                 show_week_strip: bool = True, hide_done: bool = False):
        self.width = width
        self.height = height
        self.margins = margins
        self.show_week_strip = show_week_strip
        self.hide_done = hide_done
        self.titleFont = ImageFont.truetype(fontPath, TITLE_SIZE)
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
                          today: date = None) -> Image:
        self._new_canvas()
        tasks = tasks or []
        today = today or datetime.now().date()

        footer_top = self._draw_footer(updated_at)
        top = self._draw_header(today)

        daily = [task for task in tasks if task.is_today_or_overdue()]
        if self.hide_done:
            daily = [task for task in daily if task.status != Task.DONE]
        open_tasks = sorted((task for task in daily if task.status == Task.TODO),
                            key=lambda task: (task.due_date is None, task.due_date))
        closed_tasks = [task for task in daily if task.status != Task.TODO]

        if not daily or not open_tasks and all(task.status == Task.DONE for task in daily):
            if not tasks:
                self._draw_message("Nothing planned", "Enjoy the quiet day", top, footer_top)
            else:
                self._draw_message("All done", "Nothing left for today", top, footer_top)
        else:
            self._draw_rows(open_tasks + closed_tasks, top, footer_top)
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

    def _draw_header(self, today: date) -> int:
        """Draws the date heading and week strip, and returns the y where the content can start."""
        y = self.margins.top
        self.draw.text((self.left, y), today.strftime("%A %-d %B"), font=self.titleFont, fill=BLACK)
        y += TITLE_SIZE + 14

        if self.show_week_strip:
            monday = today - timedelta(days=today.weekday())
            cell_width = (self.right - self.left) / 7
            strip_height = META_SIZE + 12
            for offset in range(7):
                day = monday + timedelta(days=offset)
                x0 = self.left + offset * cell_width
                label = day.strftime("%a")
                is_today = day == today
                if is_today:
                    self.draw.rectangle((x0, y, x0 + cell_width - 4, y + strip_height), fill=BLACK)
                text_width = self.metaFont.getlength(label)
                self.draw.text((x0 + (cell_width - 4 - text_width) / 2, y + 5), label,
                               font=self.metaFont, fill=WHITE if is_today else BLACK)
            y += strip_height + 12

        self.draw.line((self.left, y, self.right, y), fill=BLACK, width=3)
        return y + 3

    def _draw_footer(self, updated_at: datetime = None, show_time: bool = True) -> int:
        """Draws 'Updated HH:MM' bottom-right, and returns the y where the footer starts."""
        top = self.bottom - SMALL_SIZE - 6
        if not show_time:
            return top

        now = datetime.now()
        updated_at = updated_at or now
        if now - updated_at > STALE_AFTER:
            label = f"STALE - last update {updated_at.strftime('%H:%M')}"
            text_width = self.smallFont.getlength(label)
            x0 = self.right - text_width - 12
            self.draw.rectangle((x0, top, self.right, self.bottom), fill=BLACK)
            self.draw.text((x0 + 6, top + 2), label, font=self.smallFont, fill=WHITE)
        else:
            label = f"Updated {updated_at.strftime('%H:%M')}"
            text_width = self.smallFont.getlength(label)
            self.draw.text((self.right - text_width, top + 2), label, font=self.smallFont, fill=BLACK)
        return top

    # --- rows ----------------------------------------------------------------------------------

    def _draw_rows(self, tasks: list[Task], top: int, footer_top: int):
        text_x = self.left + GLYPH_COLUMN
        line_height = TASK_SIZE + 6
        more_height = META_SIZE + 2 * ROW_PADDING
        limit = footer_top - 4
        y = top
        shown = 0

        for task in tasks:
            meta = task.short_due_label()
            meta_width = self.metaFont.getlength(meta) + 16 if meta else 0
            lines = wrap_text(self.taskFont, task.title,
                              [self.right - text_x - meta_width, self.right - text_x], MAX_TITLE_LINES)
            row_height = len(lines) * line_height + 2 * ROW_PADDING
            remaining = len(tasks) - shown - 1
            reserve = more_height if remaining else 0
            if y + row_height + reserve > limit:
                break

            self._draw_row(task, lines, meta, y, text_x, line_height)
            y += row_height
            self.draw.line((self.left, y - 1, self.right, y - 1), fill=BLACK, width=1)
            shown += 1

        if shown < len(tasks):
            self.draw.text((text_x, y + ROW_PADDING), f"+{len(tasks) - shown} more",
                           font=self.metaFont, fill=BLACK)

    def _draw_row(self, task: Task, lines: list[str], meta: str, y: int, text_x: int, line_height: int):
        for i, line in enumerate(lines):
            line_y = y + ROW_PADDING + i * line_height
            self.draw.text((text_x, line_y), line, font=self.taskFont, fill=BLACK)
            if task.status == Task.CANCELLED:
                strike_y = line_y + TASK_SIZE * 0.58
                self.draw.line((text_x, strike_y, text_x + self.taskFont.getlength(line), strike_y),
                               fill=BLACK, width=2)

        if meta:
            meta_width = self.metaFont.getlength(meta)
            self.draw.text((self.right - meta_width, y + ROW_PADDING + 4), meta, font=self.metaFont, fill=BLACK)

        glyph_cy = y + ROW_PADDING + line_height // 2
        self._draw_glyph(task, self.left + 24, glyph_cy)

    # --- glyphs: fixed-size shapes, so they look the same whatever the font ---------------------

    def _draw_glyph(self, task: Task, cx: int, cy: int):
        d = self.draw
        if task.priority:
            self._draw_asterisk(cx - 18, cy)
        if task.status == Task.DONE:
            r = 7
            d.line((cx - r, cy - r, cx + r, cy + r), fill=BLACK, width=4)
            d.line((cx - r, cy + r, cx + r, cy - r), fill=BLACK, width=4)
        elif task.status == Task.MOVED:
            r = 8
            d.line((cx - 4, cy - r, cx + 5, cy), fill=BLACK, width=4)
            d.line((cx + 5, cy, cx - 4, cy + r), fill=BLACK, width=4)
        elif task.status == Task.NOTE:
            d.line((cx - 7, cy, cx + 7, cy), fill=BLACK, width=4)
        else:
            r = 6
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=BLACK)

    def _draw_asterisk(self, cx: int, cy: int):
        r = 6
        for dx, dy in ((r, 0), (0, r), (r * 0.7, r * 0.7), (r * 0.7, -r * 0.7)):
            self.draw.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=BLACK, width=2)

    # --- messages ------------------------------------------------------------------------------

    def _draw_message(self, heading: str, detail: str, top: int, bottom: int):
        heading_width = self.titleFont.getlength(heading)
        block_height = TITLE_SIZE + (TASK_SIZE + 12 if detail else 0)
        y = top + (bottom - top - block_height) / 2
        self.draw.text(((self.width - heading_width) / 2, y), heading, font=self.titleFont, fill=BLACK)
        if detail:
            detail_width = self.taskFont.getlength(detail)
            self.draw.text(((self.width - detail_width) / 2, y + TITLE_SIZE + 12), detail,
                           font=self.taskFont, fill=BLACK)
