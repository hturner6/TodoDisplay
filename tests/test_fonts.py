import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

FONTS = Path(__file__).resolve().parent.parent / "src/screenDisplay/fonts"
POLISH_LETTERS = "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ"


def glyph(font, character):
    image = Image.new("L", (60, 60), 255)
    ImageDraw.Draw(image).text((8, 8), character, font=font, fill=0)
    return image.tobytes()


@pytest.mark.parametrize("name", ["Inter-Bold.ttf", "Newsreader-SemiBoldItalic.ttf"])
def test_the_bundled_fonts_draw_every_polish_letter(name):
    font = ImageFont.truetype(str(FONTS / name), 30)
    missing = glyph(font, "\U0010FFFF")  # a character no font has: the "missing glyph" box

    assert [letter for letter in POLISH_LETTERS if glyph(font, letter) == missing] == []


@pytest.mark.parametrize("name", ["Inter-Bold.ttf", "Newsreader-SemiBoldItalic.ttf"])
def test_the_bundled_fonts_draw_the_marks_the_display_uses(name):
    font = ImageFont.truetype(str(FONTS / name), 30)
    missing = glyph(font, "\U0010FFFF")

    assert [mark for mark in "…–×" if glyph(font, mark) == missing] == []


def test_each_bundled_font_ships_with_its_licence():
    assert (FONTS / "OFL-Inter.txt").exists() and (FONTS / "OFL-Newsreader.txt").exists()
