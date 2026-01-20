"""Tests for ContentValidator module - content shrinkage validation."""
import pytest
from unittest.mock import MagicMock, patch


class TestValidateContentShrinkage:
    """Tests for validate_content_shrinkage function."""

    def test_valid_when_no_shrinkage(self):
        """Content with no shrinkage should pass validation."""
        from Writer.ContentValidator import validate_content_shrinkage

        logger = MagicMock()
        original = "This is a sample text with many words for testing purposes."
        new_text = "This is a sample text with many words for testing purposes and more."

        is_valid, report = validate_content_shrinkage(original, new_text, logger)

        assert is_valid is True
        assert report['is_valid'] is True
        assert report['reduction_ratio'] <= 0

    def test_valid_when_shrinkage_within_threshold(self):
        """Content shrinkage within 10% threshold should pass."""
        from Writer.ContentValidator import validate_content_shrinkage

        logger = MagicMock()
        # 100 words
        original = " ".join(["word"] * 100)
        # 92 words (8% reduction, within 10% threshold)
        new_text = " ".join(["word"] * 92)

        is_valid, report = validate_content_shrinkage(original, new_text, logger)

        assert is_valid is True
        assert report['is_valid'] is True
        assert report['reduction_ratio'] == pytest.approx(0.08, rel=0.01)

    def test_invalid_when_shrinkage_exceeds_threshold(self):
        """Content shrinkage exceeding 10% should fail validation."""
        from Writer.ContentValidator import validate_content_shrinkage

        logger = MagicMock()
        # 100 words
        original = " ".join(["word"] * 100)
        # 80 words (20% reduction, exceeds 10% threshold)
        new_text = " ".join(["word"] * 80)

        is_valid, report = validate_content_shrinkage(original, new_text, logger)

        assert is_valid is False
        assert report['is_valid'] is False
        assert report['reduction_ratio'] == pytest.approx(0.20, rel=0.01)

    def test_valid_when_original_empty(self):
        """Empty original text should pass (edge case)."""
        from Writer.ContentValidator import validate_content_shrinkage

        logger = MagicMock()
        original = ""
        new_text = "Some new content"

        is_valid, report = validate_content_shrinkage(original, new_text, logger)

        assert is_valid is True
        assert report['reason'] == 'original_empty'

    def test_logs_warning_on_failure(self):
        """Should log warning when validation fails."""
        from Writer.ContentValidator import validate_content_shrinkage

        logger = MagicMock()
        original = " ".join(["word"] * 100)
        new_text = " ".join(["word"] * 50)  # 50% reduction

        validate_content_shrinkage(original, new_text, logger, "Test Context")

        logger.Log.assert_called()
        call_args = logger.Log.call_args[0]
        assert "Content shrinkage validation FAILED" in call_args[0]
        assert "Test Context" in call_args[0]

    def test_uses_config_threshold(self):
        """Should use MAX_WORD_COUNT_REDUCTION_RATIO from Config."""
        from Writer.ContentValidator import validate_content_shrinkage

        logger = MagicMock()
        original = " ".join(["word"] * 100)

        # Test at exactly threshold boundary (10%)
        new_text_at_threshold = " ".join(["word"] * 90)
        is_valid, report = validate_content_shrinkage(original, new_text_at_threshold, logger)

        assert is_valid is True
        assert report['threshold'] == 0.10

    def test_returns_correct_word_counts(self):
        """Should return correct word counts in report."""
        from Writer.ContentValidator import validate_content_shrinkage

        logger = MagicMock()
        original = " ".join(["word"] * 100)
        new_text = " ".join(["word"] * 95)

        is_valid, report = validate_content_shrinkage(original, new_text, logger)

        assert report['original_word_count'] == 100
        assert report['new_word_count'] == 95
        assert report['min_word_count'] == 90  # 100 * (1 - 0.10)

    def test_context_included_in_report(self):
        """Should include context string in report."""
        from Writer.ContentValidator import validate_content_shrinkage

        logger = MagicMock()
        original = "Some text here"
        new_text = "Some text"

        is_valid, report = validate_content_shrinkage(
            original, new_text, logger, "Stage 2: Character Development"
        )

        assert report['context'] == "Stage 2: Character Development"

    def test_boundary_at_exactly_threshold(self):
        """Content at exactly 10% reduction should pass (boundary test)."""
        from Writer.ContentValidator import validate_content_shrinkage

        logger = MagicMock()
        original = " ".join(["word"] * 100)
        # Exactly 10% reduction = 90 words (should still pass)
        new_text = " ".join(["word"] * 90)

        is_valid, report = validate_content_shrinkage(original, new_text, logger)

        assert is_valid is True
        assert report['new_word_count'] >= report['min_word_count']

    def test_boundary_just_over_threshold(self):
        """Content just over 10% reduction should fail."""
        from Writer.ContentValidator import validate_content_shrinkage

        logger = MagicMock()
        original = " ".join(["word"] * 100)
        # Just over 10% reduction = 89 words (should fail)
        new_text = " ".join(["word"] * 89)

        is_valid, report = validate_content_shrinkage(original, new_text, logger)

        assert is_valid is False
        assert report['new_word_count'] < report['min_word_count']
