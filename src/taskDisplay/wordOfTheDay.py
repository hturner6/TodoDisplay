import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

COLUMNS = ("polish", "english", "example", "example_english")


@dataclass(frozen=True)
class Word:
    polish: str
    english: str
    example: str
    example_english: str
    gender: str = ""  # m, f, n or pl, for a noun
    forms: str = ""  # what else helps: a verb's "I" form, "pf." for a perfective one, an adjective's "f." form


def load_words(path) -> list[Word]:
    """The words in a CSV with a header row of polish, english, example and example_english, and optionally
    gender and forms."""
    with open(path, encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or any(column not in reader.fieldnames for column in COLUMNS):
            raise ValueError(f"{Path(path).name} needs the columns {', '.join(COLUMNS)}")
        return [Word(*(row[column].strip() for column in COLUMNS),
                     gender=(row.get("gender") or "").strip(), forms=(row.get("forms") or "").strip())
                for row in reader]


def word_for(day: date, words: list[Word]) -> Word | None:
    """The word of the day: stable all day, and every word comes round before any repeats."""
    return words[day.toordinal() % len(words)] if words else None
