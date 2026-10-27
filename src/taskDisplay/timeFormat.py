from datetime import datetime, time


def format_time(moment: time | datetime) -> str:
    """The 12-hour clock the TodoApp uses, e.g. "9:30 AM". Written out, not strftime, so the locale cannot change it."""
    hour = moment.hour % 12 or 12
    return f"{hour}:{moment.minute:02d} {'AM' if moment.hour < 12 else 'PM'}"
