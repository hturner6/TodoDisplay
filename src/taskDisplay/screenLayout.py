from dataclasses import dataclass
from datetime import date, time, timedelta
from typing import NamedTuple
from models.task import Task
from taskDisplay.timeFormat import format_time

# Text sizes the rows are measured in, and the spacing around them, in pixels.
TASK_SIZE = 27
META_SIZE = 21
LINE_HEIGHT = TASK_SIZE + 6
GLYPH_COLUMN = 42
ROW_PADDING = 8
MAX_TITLE_LINES = 2
META_GAP = 16  # kept clear between a title and the label to its right
MORE_HEIGHT = META_SIZE + 2 * ROW_PADDING  # the "+N more" line a full column reserves room for


def wrap_text(measure, text: str, max_widths: list[float], max_lines: int) -> list[str]:
    """Wraps text to at most max_lines lines, ending the last one with an ellipsis if it is cut.

    measure(text) is the width of text. max_widths[i] is the width available to line i; the last
    entry applies to any later lines. Words wider than a whole line are broken mid-word.
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
        if measure(candidate) <= width_of(candidate):
            current = candidate
            index += 1
            continue
        if current:
            lines.append(current)
            current = ""
        else:
            # A single word wider than the line: take as many characters as fit.
            fitted = word
            while len(fitted) > 1 and measure(fitted) > width_of(fitted):
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
        lines[-1] = _with_ellipsis(measure, lines[-1], max_widths[min(max_lines - 1, len(max_widths) - 1)])
    return lines


def _with_ellipsis(measure, line: str, max_width: float) -> str:
    line = line.rstrip()
    while line and measure(line + "…") > max_width:
        line = line[:-1].rstrip()
    return line + "…"


# --- selection: which Tasks are on the screen, and in what order ---------------------------------

class Selection(NamedTuple):
    daily: list[Task]
    weekly: list[Task]


def week_bounds(today: date):
    """Monday and Sunday of the week containing today."""
    monday = today - timedelta(days=today.weekday())
    return monday, monday + timedelta(days=6)


def select(tasks: list[Task], today: date) -> Selection:
    """Overdue and today's Daily Items, and this week's Weekly Items, each in the order shown.

    Overdue Daily Items are only those still to do; finished, cancelled or moved ones are done
    with. Items still to do come first, then the rest, each by date, then time (untimed last),
    then title. Tasks with no date are never shown.
    """
    monday, sunday = week_bounds(today)
    dated = [task for task in tasks if task.due_date is not None]
    daily = [t for t in dated if not t.weekly
             and (t.due_date == today or (t.due_date < today and t.status == Task.TODO))]
    weekly = [t for t in dated if t.weekly and monday <= t.due_date <= sunday]
    return Selection(_in_order(daily, daily=True), _in_order(weekly, daily=False))


def _in_order(tasks: list[Task], daily: bool) -> list[Task]:
    def key(task):
        if daily:
            return (task.due_date, task.scheduled_time is None, task.scheduled_time or time.min, task.title)
        return (task.due_date, task.title)

    ordered = sorted(tasks, key=key)
    return ([t for t in ordered if t.status == Task.TODO]
            + [t for t in ordered if t.status != Task.TODO])


# --- fitting: what the rows look like and how many fit ---------------------------------------

@dataclass(frozen=True)
class Row:
    lines: tuple[str, ...]  # the title, wrapped
    meta: str  # the label at the right of the first line, e.g. "2d late" or "09:30"
    status: str
    priority: bool

    @property
    def height(self) -> int:
        return len(self.lines) * LINE_HEIGHT + 2 * ROW_PADDING


@dataclass(frozen=True)
class Column:
    heading: str | None
    rows: tuple[Row, ...]
    more: int  # Tasks that did not fit
    empty: tuple[str, ...]  # what to say when there are no Tasks


@dataclass(frozen=True)
class Message:
    heading: str
    detail: str


@dataclass(frozen=True)
class Layout:
    """What to paint: either columns of rows, or a message that replaces them."""
    columns: tuple[Column, ...] = ()
    message: Message | None = None


def daily_meta(task: Task, today: date) -> str:
    """Overdue wins over the time, because a late item matters more than when it was due."""
    # "late", not "overdue": the label shares the first line with the title, and a longer
    # one forces a word that would otherwise fit to be broken in two.
    days_late = (today - task.due_date).days
    if days_late > 0:
        return f"{days_late}d late"
    return format_time(task.scheduled_time) if task.scheduled_time else ""


def list_meta(task: Task, today: date) -> str:
    """The due text of the single list, e.g. "Today" or "2d overdue"."""
    days_late = (today - task.due_date).days
    return "Today" if days_late <= 0 else f"{days_late}d overdue"


def build_layout(tasks: list[Task], today: date, widths: list[float], height: float,
                 measure_task, measure_meta) -> Layout:
    """Chooses and fits what the screen shows.

    One width means a single list of Daily Items; two mean Daily Items then Weekly Items side by
    side. height is the space under the column headings. measure_task and measure_meta give the
    width of text in the title and label fonts.
    """
    def fit(column_tasks, width, meta_for, heading, empty):
        text_width = width - GLYPH_COLUMN
        rows = []
        used = 0
        for index, task in enumerate(column_tasks):
            meta = meta_for(task, today)
            meta_width = measure_meta(meta) + META_GAP if meta else 0
            lines = wrap_text(measure_task, task.title, [text_width - meta_width, text_width], MAX_TITLE_LINES)
            row = Row(tuple(lines), meta, task.status, task.priority)
            reserve = MORE_HEIGHT if index < len(column_tasks) - 1 else 0
            if used + row.height + reserve > height:
                break
            rows.append(row)
            used += row.height
        empty_lines = tuple(wrap_text(measure_task, empty, [width], 2))
        return Column(heading, tuple(rows), len(column_tasks) - len(rows), empty_lines)

    daily, weekly = select(tasks, today)
    if len(widths) == 2:
        return Layout(columns=(
            fit(daily, widths[0], daily_meta, "TODAY", "Nothing planned"),
            fit(weekly, widths[1], lambda task, today: "", "THIS WEEK", "Nothing this week"),
        ))

    # A Weekly Item belongs to the week, not a day (TodoApp stores it on the week's Monday), so
    # the single list has nowhere to put one and shows Daily Items only.
    nothing_open = not any(task.status == Task.TODO for task in daily)
    if not daily or nothing_open and all(task.status == Task.DONE for task in daily):
        if not tasks:
            return Layout(message=Message("Nothing planned", "Enjoy the quiet day"))
        return Layout(message=Message("All done", "Nothing left for today"))
    return Layout(columns=(fit(daily, widths[0], list_meta, None, ""),))
