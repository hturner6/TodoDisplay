import sys
from datetime import date, time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models.task import Task
from taskDisplay.screenLayout import (LINE_HEIGHT, MORE_HEIGHT, ROW_PADDING, Message, build_layout, select,
                                      week_bounds, wrap_text)

TODAY = date(2026, 10, 28)  # a Wednesday: the week is Mon 26 Oct to Sun 1 Nov
ROW_HEIGHT = LINE_HEIGHT + 2 * ROW_PADDING  # a one-line row


def measure(text):
    """Ten pixels a character, so no test needs a font."""
    return 10 * len(text)


def task(title, due=TODAY, **extra):
    return Task(title, due, **extra)


def titles(tasks):
    return [t.title for t in tasks]


def layout(tasks, widths=(600,), height=2000):
    return build_layout(tasks, TODAY, list(widths), height, measure, measure)


# --- wrapping ---------------------------------------------------------------------------------

def test_short_text_stays_on_one_line():
    assert wrap_text(measure, "Buy milk", [400], 2) == ["Buy milk"]


def test_long_text_wraps_on_word_boundaries():
    lines = wrap_text(measure, "Book the practical driving test", [250, 400], 2)

    assert len(lines) == 2
    assert " ".join(lines) == "Book the practical driving test"
    assert measure(lines[0]) <= 250 and measure(lines[1]) <= 400


def test_text_cut_after_the_last_line_ends_with_an_ellipsis():
    lines = wrap_text(measure, "word " * 40, [300], 2)

    assert len(lines) == 2
    assert lines[-1].endswith("…")
    assert all(measure(line) <= 300 for line in lines)


def test_a_word_wider_than_the_line_is_broken():
    lines = wrap_text(measure, "x" * 80, [200], 3)

    assert all(measure(line) <= 200 for line in lines)
    assert lines[-1].endswith("…")


def test_first_line_can_be_narrower_than_the_rest():
    lines = wrap_text(measure, "alpha beta gamma delta epsilon", [100, 600], 2)

    assert measure(lines[0]) <= 100
    assert " ".join(lines) == "alpha beta gamma delta epsilon"


# --- selection ---------------------------------------------------------------------------------

def test_weeks_run_monday_to_sunday():
    assert week_bounds(date(2026, 10, 26)) == (date(2026, 10, 26), date(2026, 11, 1))
    assert week_bounds(date(2026, 11, 1)) == (date(2026, 10, 26), date(2026, 11, 1))


def test_selection_keeps_daily_items_up_to_today_and_this_weeks_weekly_items():
    tasks = [
        task("today"),
        task("overdue", date(2026, 10, 27)),
        task("tomorrow", date(2026, 10, 29)),
        task("this week", date(2026, 10, 30), weekly=True),
        task("sunday", date(2026, 11, 1), weekly=True),
        task("last week", date(2026, 10, 25), weekly=True),
        task("next week", date(2026, 11, 2), weekly=True),
    ]

    daily, weekly = select(tasks, TODAY)

    assert titles(daily) == ["overdue", "today"]
    assert titles(weekly) == ["this week", "sunday"]


@pytest.mark.parametrize("state", [Task.DONE, Task.CANCELLED, Task.MOVED])
def test_finished_daily_items_from_past_days_are_not_shown(state):
    tasks = [task("old", date(2026, 10, 20), status=state), task("today", status=state)]

    assert titles(select(tasks, TODAY).daily) == ["today"]


def test_tasks_with_no_date_are_never_shown():
    assert select([task("someday", None)], TODAY) == ([], [])


def test_overdue_daily_items_come_before_todays_whatever_their_time():
    tasks = [task("today early", scheduled_time=time(7, 0)), task("old late", date(2026, 10, 20), scheduled_time=time(22, 0))]

    assert titles(select(tasks, TODAY).daily) == ["old late", "today early"]


def test_daily_items_sort_by_time_with_untimed_last_then_by_title():
    tasks = [task("b untimed"), task("a untimed"), task("late", scheduled_time=time(18, 0)),
             task("early", scheduled_time=time(8, 0))]

    assert titles(select(tasks, TODAY).daily) == ["early", "late", "a untimed", "b untimed"]


def test_items_still_to_do_come_before_finished_ones():
    tasks = [task("done", status=Task.DONE), task("moved", status=Task.MOVED), task("open")]

    assert titles(select(tasks, TODAY).daily) == ["open", "done", "moved"]


def test_the_order_does_not_depend_on_the_order_fetched():
    tasks = [task("a"), task("b", scheduled_time=time(9, 0)), task("c", date(2026, 10, 27))]

    assert select(tasks, TODAY) == select(list(reversed(tasks)), TODAY)


def test_weekly_items_sort_by_date_then_title():
    tasks = [task("b", date(2026, 10, 30), weekly=True), task("c", date(2026, 10, 29), weekly=True),
             task("a", date(2026, 10, 30), weekly=True)]

    assert titles(select(tasks, TODAY).weekly) == ["c", "a", "b"]


# --- two columns ------------------------------------------------------------------------------

def test_daily_items_go_in_the_first_column_and_weekly_items_in_the_second():
    result = layout([task("daily"), task("weekly", weekly=True)], widths=(300, 200))

    today, week = result.columns
    assert (today.heading, week.heading) == ("TODAY", "THIS WEEK")
    assert [row.lines for row in today.rows] == [("daily",)]
    assert [row.lines for row in week.rows] == [("weekly",)]


def test_an_empty_week_still_shows_both_columns_with_their_own_message():
    result = layout([], widths=(300, 200))

    assert result.message is None
    assert [column.empty for column in result.columns] == [("Nothing planned",), ("Nothing this week",)]
    assert all(not column.rows for column in result.columns)


def test_the_daily_label_is_late_in_preference_to_the_time():
    result = layout([task("a", date(2026, 10, 26), scheduled_time=time(9, 30)),
                     task("b", scheduled_time=time(9, 30)), task("c")], widths=(300, 200))

    assert [row.meta for row in result.columns[0].rows] == ["2d late", "09:30", ""]


def test_weekly_items_carry_no_label():
    result = layout([task("w", date(2026, 10, 30), weekly=True)], widths=(300, 200))

    assert result.columns[1].rows[0].meta == ""


def test_rows_carry_status_and_priority_not_the_task():
    result = layout([task("a", status=Task.DONE, priority=True)], widths=(300, 200))

    row = result.columns[0].rows[0]
    assert (row.status, row.priority) == (Task.DONE, True)


def test_a_label_takes_width_from_the_first_line_of_the_title():
    # 300 wide less the glyph column leaves 258; the "09:30" label and its gap take 66 of it.
    title = "alpha beta gamma delta"
    result = layout([task(title, scheduled_time=time(9, 30))], widths=(300, 200))

    first, second = result.columns[0].rows[0].lines
    assert measure(first) <= 258 - (50 + 16) and f"{first} {second}" == title


# --- fitting ----------------------------------------------------------------------------------

def test_tasks_that_do_not_fit_are_counted_not_dropped_silently():
    tasks = [task(f"task {i}") for i in range(10)]

    column = layout(tasks, widths=(300, 200), height=3 * ROW_HEIGHT + MORE_HEIGHT).columns[0]

    assert len(column.rows) == 3
    assert column.more == 7


def test_the_last_task_does_not_reserve_room_for_a_more_line():
    tasks = [task(f"task {i}") for i in range(3)]

    # Two rows plus the "+1 more" line fit exactly; all three rows need no "more" line.
    assert layout(tasks, widths=(300, 200), height=2 * ROW_HEIGHT + MORE_HEIGHT).columns[0].more == 1
    assert layout(tasks, widths=(300, 200), height=3 * ROW_HEIGHT).columns[0].more == 0


# --- single list ------------------------------------------------------------------------------

def test_a_single_width_gives_one_list_with_due_labels():
    result = layout([task("a"), task("b", date(2026, 10, 25))])

    (column,) = result.columns
    assert column.heading is None
    assert [(row.lines, row.meta) for row in column.rows] == [(("b",), "3d overdue"), (("a",), "Today")]


def test_open_tasks_come_before_done_ones_in_the_list():
    result = layout([task("done", status=Task.DONE), task("open")])

    assert [row.lines for row in result.columns[0].rows] == [("open",), ("done",)]


@pytest.mark.parametrize("tasks, expected", [
    ([], Message("Nothing planned", "Enjoy the quiet day")),
    ([task("later", date(2026, 10, 31))], Message("All done", "Nothing left for today")),
    ([task("finished", status=Task.DONE)], Message("All done", "Nothing left for today")),
])
def test_an_empty_list_picks_the_right_message(tasks, expected):
    assert layout(tasks).message == expected
