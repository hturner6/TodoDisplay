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


def load_words(path) -> list[Word]:
    """The words in a CSV with a header row of polish, english, example and example_english."""
    with open(path, encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or any(column not in reader.fieldnames for column in COLUMNS):
            raise ValueError(f"{Path(path).name} needs the columns {', '.join(COLUMNS)}")
        return [Word(*(row[column].strip() for column in COLUMNS)) for row in reader]


def word_for(day: date, words: list[Word]) -> Word | None:
    """The word of the day: stable all day, and every word comes round before any repeats."""
    return words[day.toordinal() % len(words)] if words else None
