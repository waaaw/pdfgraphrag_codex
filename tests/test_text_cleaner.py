from src.preprocessing.text_cleaner import clean_text, text_preview


def test_clean_text_collapses_spaces_and_blank_lines() -> None:
    text = "  Hello   world  \n\n\n  PDF   QA  "

    assert clean_text(text) == "Hello world\nPDF QA"


def test_text_preview_limits_length() -> None:
    preview = text_preview("a\n" * 300, limit=20)

    assert len(preview) <= 20
    assert preview.endswith("...")
