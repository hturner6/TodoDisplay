import csv
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest
from PIL import ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from taskDisplay.wordOfTheDay import Word, load_words, word_for

WORDS_FILE = Path(__file__).resolve().parent.parent / "src/taskDisplay/polishWords.csv"
FONTS = Path(__file__).resolve().parent.parent / "src/screenDisplay/fonts"
DAY = date(2026, 10, 27)


def test_the_shipped_list_is_a_few_dozen_complete_distinct_beginner_words():
    words = load_words(WORDS_FILE)

    assert len(words) >= 300
    assert all(word.polish and word.english and word.example and word.example_english for word in words)
    assert len({word.polish for word in words}) == len(words)


def rows():
    with open(WORDS_FILE, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def test_every_sentence_taken_from_tatoeba_credits_its_authors_and_ids():
    # CC BY 2.0 FR: using a sentence needs its author named. Hand-written rows have no ids and no authors.
    sourced = [row for row in rows() if row["polish_sentence_id"]]

    assert len(sourced) >= 300
    assert all(row["polish_author"] and row["english_sentence_id"] and row["english_author"] for row in sourced)
    assert all(not row["polish_author"] and not row["english_author"] for row in rows() if not row["polish_sentence_id"])


def test_no_example_is_drawn_from_the_same_sentence_twice():
    ids = [row["polish_sentence_id"] for row in rows() if row["polish_sentence_id"]]

    assert len(ids) == len(set(ids))


def test_every_example_fits_the_footer_without_being_cut_short():
    inter = FONTS / "Inter-Bold.ttf"
    width = 648 - 32 - 32 - 1  # the content width between the default margins
    for word in load_words(WORDS_FILE):
        assert ImageFont.truetype(str(inter), 21).getlength(word.example) <= width, word.polish
        assert ImageFont.truetype(str(inter), 19).getlength(word.example_english) <= width, word.polish


def test_nothing_rude_or_morbid_is_on_a_wall_display():
    text = " ".join(f"{w.example} {w.example_english}" for w in load_words(WORDS_FILE)).lower()

    for avoid in ("kurw", "chuj", "srał", "szlag", "idiot", "zabi", "śmierć", "umar", "fuck", "shit", "bloody", "kill", "dead", "murder"):
        assert avoid not in text, avoid


def test_the_example_sentences_use_polish_letters():
    examples = " ".join(word.example for word in load_words(WORDS_FILE))

    assert all(letter in examples for letter in "ąćęłńóśźż")


def test_loading_reads_quoted_fields_with_commas(tmp_path):
    path = tmp_path / "words.csv"
    path.write_text('polish,english,example,example_english\ntak,yes,"Tak, to jest dobre.","Yes, that is good."\n',
                    encoding="utf-8")

    assert load_words(path) == [Word("tak", "yes", "Tak, to jest dobre.", "Yes, that is good.")]


def test_a_list_missing_a_column_is_an_error(tmp_path):
    path = tmp_path / "words.csv"
    path.write_text("polish,english\ntak,yes\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_words(path)


def test_the_word_is_the_same_all_day_and_changes_the_next_day():
    words = load_words(WORDS_FILE)

    assert word_for(DAY, words) == word_for(DAY, words)
    assert word_for(DAY, words) != word_for(DAY + timedelta(days=1), words)


def test_every_word_comes_round_once_before_any_repeats():
    words = load_words(WORDS_FILE)

    seen = [word_for(DAY + timedelta(days=offset), words) for offset in range(len(words))]

    assert sorted(seen, key=lambda w: w.polish) == sorted(words, key=lambda w: w.polish)


def test_no_words_means_no_word_of_the_day():
    assert word_for(DAY, []) is None
