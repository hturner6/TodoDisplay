from dataclasses import dataclass
from datetime import datetime, time


@dataclass(frozen=True)
class QuietHours:
    """A daily window, such as 23:00 to 06:00, when the screen is left alone."""
    start: time
    end: time

    @classmethod
    def parse(cls, text: str) -> "QuietHours":
        start, end = (datetime.strptime(part.strip(), "%H:%M").time() for part in text.split("-"))
        return cls(start, end)

    @classmethod
    def from_config(cls, text: str | None) -> "QuietHours | None":
        """The QUIET_HOURS setting: "HH:MM-HH:MM", or "off" (or nothing) for no quiet hours."""
        if not text or text.strip().lower() == "off":
            return None
        try:
            return cls.parse(text)
        except ValueError:
            raise ValueError('QUIET_HOURS must look like "23:00-06:00", or be "off"') from None

    def contains(self, moment: time) -> bool:
        # A window that crosses midnight (23:00 to 06:00) is in force late or early.
        if self.start <= self.end:
            return self.start <= moment < self.end
        return moment >= self.start or moment < self.end
