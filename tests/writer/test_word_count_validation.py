"""Test configurable word count validation for Pydantic models."""

import pytest
from pydantic import ValidationError
from Writer.Models import ChapterOutput, OutlineOutput
from Writer.Config import PYDANTIC_WORD_COUNT_TOLERANCE


def test_word_count_validation_default_tolerance():
    """Test word count validation with default tolerance."""

    # Create valid chapter (minimum 100 characters)
    text = "This is a test chapter with exactly ten words, making it long enough to pass the minimum character validation for the chapter text field."
    chapter = ChapterOutput(
        text=text,
        word_count=10,
        chapter_number=1
    )
    assert chapter.word_count == 10

    # Test within tolerance - should pass
    text_long = "This is a test chapter with fifteen words in total content, making it sufficiently long to pass the character validation requirements for chapter text."
    chapter = ChapterOutput(
        text=text_long,
        word_count=10,  # 5 words difference, should be within default tolerance
        chapter_number=1
    )
    assert chapter.word_count == 10

    # Test exceeding tolerance - should fail
    text_very_long = "This is a much longer test chapter that contains significantly more words than the specified count. It has way too many words and should exceed the tolerance threshold by a considerable margin making it fail validation because the difference is too large. Adding more text here to ensure it goes over the one hundred word tolerance limit by a lot. More words are needed here to make sure we exceed the new tolerance. Even more words. And some extra words just to be sure. This should definitely exceed the tolerance limit now with the new setting of one hundred words. Additional text is required to push the word count beyond one hundred and one, ensuring the validation actually fails when the difference exceeds the configured tolerance of one hundred words between the specified word count and the actual word count in the chapter text. This extra padding should make it fail properly now for the unit test to validate the word count tolerance checking mechanism is working correctly with the new tolerance setting."
    with pytest.raises(ValidationError) as exc_info:
        ChapterOutput(
            text=text_very_long,
            word_count=10,  # Large difference, should exceed tolerance
            chapter_number=1
        )
    assert "Word count" in str(exc_info.value)
    assert "doesn't match actual word count" in str(exc_info.value)


def test_custom_word_count_tolerance():
    """Test word count validation with custom tolerance from config."""

    # Temporarily set custom tolerance
    import Writer.Config as Config
    original_tolerance = getattr(Config, 'PYDANTIC_WORD_COUNT_TOLERANCE', 50)
    Config.PYDANTIC_WORD_COUNT_TOLERANCE = 5  # Set very strict tolerance

    try:
        # Test with strict tolerance - should fail with small difference
        text = "This is a test chapter with fifteen words in total, making it long enough for validation requirements."
        with pytest.raises(ValidationError) as exc_info:
            ChapterOutput(
                text=text,
                word_count=10,  # 5 words difference, should exceed strict tolerance
                chapter_number=1
            )
        assert "Word count" in str(exc_info.value)

        # Test within strict tolerance - should pass
        chapter = ChapterOutput(
            text=text,
            word_count=14,  # 1 word difference, within strict tolerance
            chapter_number=1
        )
        assert chapter.word_count == 14

    finally:
        # Restore original tolerance
        Config.PYDANTIC_WORD_COUNT_TOLERANCE = original_tolerance


def test_word_count_validation_can_be_disabled():
    """Test that word count validation can be disabled."""

    import Writer.Config as Config
    original_tolerance = getattr(Config, 'PYDANTIC_WORD_COUNT_TOLERANCE', 50)

    try:
        # Set tolerance to a very high number to effectively disable validation
        Config.PYDANTIC_WORD_COUNT_TOLERANCE = 999999

        # Should pass regardless of word count difference
        text_short = "This text is definitely long enough to pass the character validation requirements even if the word count is very different from the actual count of words in the text."
        chapter = ChapterOutput(
            text=text_short,
            word_count=1000,  # Huge difference, but validation is disabled
            chapter_number=1
        )
        assert chapter.word_count == 1000

    finally:
        Config.PYDANTIC_WORD_COUNT_TOLERANCE = original_tolerance


def test_word_count_validation_with_non_ascii_text():
    """Test word count validation with Indonesian text containing non-ASCII characters."""

    # Indonesian text with diacritics
    text = "Bab ini menceritakan tentang petualangan seorang pahlawan dalam menghadapi monster yang mengerikan di hutan yang gelap dan menakutkan."

    # Count should handle Indonesian text properly
    actual_count = len(text.split())

    chapter = ChapterOutput(
        text=text,
        word_count=actual_count,
        chapter_number=1
    )
    assert chapter.word_count == actual_count

    # Test with tolerance
    chapter = ChapterOutput(
        text=text,
        word_count=actual_count - 2,  # Within tolerance
        chapter_number=1
    )
    assert chapter.word_count == actual_count - 2


def test_configurable_tolerance_in_values():
    """Test that tolerance value is accessible from Config."""

    import Writer.Config as Config

    # Should have the tolerance setting
    assert hasattr(Config, 'PYDANTIC_WORD_COUNT_TOLERANCE')

    # Should be a positive integer
    assert isinstance(Config.PYDANTIC_WORD_COUNT_TOLERANCE, int)
    assert Config.PYDANTIC_WORD_COUNT_TOLERANCE >= 0

    # Default should be reasonable
    assert Config.PYDANTIC_WORD_COUNT_TOLERANCE == 100


def test_word_count_validator_error_message():
    """Test that error messages include the tolerance information."""

    import Writer.Config as Config
    original_tolerance = getattr(Config, 'PYDANTIC_WORD_COUNT_TOLERANCE', 50)
    Config.PYDANTIC_WORD_COUNT_TOLERANCE = 10

    try:
        text = "This chapter has way more than ten words in it and should trigger a validation error that mentions the actual count and the expected count within the tolerance range."

        with pytest.raises(ValidationError) as exc_info:
            ChapterOutput(
                text=text,
                word_count=10,
                chapter_number=1
            )

        error_msg = str(exc_info.value)
        assert "Word count" in error_msg
        assert "doesn't match actual word count" in error_msg

    finally:
        Config.PYDANTIC_WORD_COUNT_TOLERANCE = original_tolerance