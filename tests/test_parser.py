import pytest

from core.models import ParsedNote
from tests.test_objects import parsed_note


@pytest.fixture(scope="session")
def test_note():
    return parsed_note


# --- output type ---


def test_returns_parsed_note(test_note: ParsedNote):
    assert isinstance(test_note, ParsedNote)


def test_title_is_string(test_note: ParsedNote):
    assert isinstance(test_note.title, str) and test_note.title


def test_source_path_exists(test_note: ParsedNote):
    assert test_note.source_path.exists()


def test_content_is_string(test_note: ParsedNote):
    assert isinstance(test_note.content, str)


# --- headings ---


def test_headings_are_sorted_by_char_pos(test_note: ParsedNote):
    positions = [h.char_pos for h in test_note.headings]
    assert positions == sorted(positions)


def test_heading_levels_are_valid(test_note: ParsedNote):
    assert all(1 <= h.level <= 6 for h in test_note.headings)


def test_heading_text_nonempty(test_note: ParsedNote):
    assert all(h.text for h in test_note.headings)


def test_heading_char_pos_within_content(test_note: ParsedNote):
    assert all(0 <= h.char_pos < len(test_note.content) for h in test_note.headings)


# --- content cleaning ---


def test_no_frontmatter_in_content(test_note: ParsedNote):
    assert not test_note.content.startswith("---")


def test_no_wikilink_syntax_in_content(test_note: ParsedNote):
    assert "[[" not in test_note.content


def test_no_trailing_whitespace_on_lines(test_note: ParsedNote):
    assert all(not line.endswith(" ") for line in test_note.content.splitlines())
