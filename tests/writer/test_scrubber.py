"""Tests for Scrubber module - content shrinkage validation.

Tests that the scrubber reverts to original content when
LLM output shrinks beyond the configured threshold.
"""
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestScrubberContentShrinkage:
    """Test Scrubber fallback when content shrinks beyond threshold."""

    def test_reverts_on_content_shrinkage(self, mock_interface, mock_logger):
        """Scrubber should revert to original when shrinkage exceeds threshold."""
        from Writer.Scrubber import ScrubNovel

        # Arrange
        mock_iface = mock_interface()
        mock_log = mock_logger()

        # Original chapters: 100 words each
        original_chapter = " ".join(["word"] * 100)
        chapters = [original_chapter]

        # LLM returns shrunken content: 50 words (50% shrinkage)
        shrunken_chapter = " ".join(["word"] * 50)

        mock_pydantic_result = Mock()
        mock_pydantic_result.text = shrunken_chapter

        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant"}],
            mock_pydantic_result,
            {"prompt_tokens": 100}
        )

        # Act
        result = ScrubNovel(mock_iface, mock_log, chapters, 1)

        # Assert - should revert to original due to shrinkage
        assert result[0] == original_chapter

    def test_uses_llm_output_when_no_shrinkage(self, mock_interface, mock_logger):
        """Scrubber should use LLM output when content doesn't shrink significantly."""
        from Writer.Scrubber import ScrubNovel

        # Arrange
        mock_iface = mock_interface()
        mock_log = mock_logger()

        # Original chapters: 100 words each
        original_chapter = " ".join(["word"] * 100)
        chapters = [original_chapter]

        # LLM returns slightly reduced content: 95 words (5% shrinkage, within 10% threshold)
        normal_scrubbed = " ".join(["scrubbed"] * 95)

        mock_pydantic_result = Mock()
        mock_pydantic_result.text = normal_scrubbed

        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant"}],
            mock_pydantic_result,
            {"prompt_tokens": 100}
        )

        # Act
        result = ScrubNovel(mock_iface, mock_log, chapters, 1)

        # Assert - should use LLM output (no significant shrinkage)
        assert result[0] == normal_scrubbed

    def test_logs_warning_on_shrinkage_revert(self, mock_interface, mock_logger):
        """Scrubber should log warning when reverting due to shrinkage."""
        from Writer.Scrubber import ScrubNovel

        # Arrange
        mock_iface = mock_interface()
        mock_log = mock_logger()

        original_chapter = " ".join(["word"] * 100)
        chapters = [original_chapter]

        # Shrunken content
        shrunken_chapter = " ".join(["word"] * 50)
        mock_pydantic_result = Mock()
        mock_pydantic_result.text = shrunken_chapter

        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant"}],
            mock_pydantic_result,
            {"prompt_tokens": 100}
        )

        # Act
        ScrubNovel(mock_iface, mock_log, chapters, 1)

        # Assert - should have logged shrinkage warning
        log_calls = [call[0][0] for call in mock_log.Log.call_args_list]
        assert any("shrinkage" in msg.lower() for msg in log_calls)

    def test_handles_multiple_chapters_independently(self, mock_interface, mock_logger):
        """Scrubber should handle each chapter's shrinkage independently."""
        from Writer.Scrubber import ScrubNovel

        # Arrange
        mock_iface = mock_interface()
        mock_log = mock_logger()

        # Two chapters
        chapter1 = " ".join(["word"] * 100)
        chapter2 = " ".join(["text"] * 100)
        chapters = [chapter1, chapter2]

        # Chapter 1: shrinks too much -> revert
        # Chapter 2: normal shrinkage -> keep LLM output
        shrunken1 = " ".join(["word"] * 50)  # 50% shrinkage
        normal2 = " ".join(["scrubbed"] * 95)  # 5% shrinkage

        mock_result1 = Mock()
        mock_result1.text = shrunken1
        mock_result2 = Mock()
        mock_result2.text = normal2

        mock_iface.SafeGeneratePydantic.side_effect = [
            ([{"role": "assistant"}], mock_result1, {"prompt_tokens": 100}),
            ([{"role": "assistant"}], mock_result2, {"prompt_tokens": 100}),
        ]

        # Act
        result = ScrubNovel(mock_iface, mock_log, chapters, 2)

        # Assert
        assert result[0] == chapter1  # Reverted due to shrinkage
        assert result[1] == normal2  # Used LLM output
