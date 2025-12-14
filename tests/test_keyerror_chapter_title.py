"""RED tests for KeyError: 'chapter_title' issue in Pipeline.py"""

import pytest
from unittest.mock import Mock


class TestKeyErrorChapterTitle:
    """RED Tests: These should fail with current implementation"""

    def test_mega_outline_chapter_format_with_title(self):
        """GREEN: Test that MEGA_OUTLINE_CHAPTER_FORMAT works with chapter_title"""
        from Writer.PromptsHelper import get_prompts

        prompts = get_prompts()
        format_string = prompts.MEGA_OUTLINE_CHAPTER_FORMAT

        # Test with proper parameters (should work)
        result = format_string.format(
            chapter_num=1,
            chapter_title="Test Chapter Title",
            chapter_content="Test chapter content"
        )

        assert "Test Chapter Title" in result
        assert "Test chapter content" in result

    def test_generate_per_chapter_outline_should_return_title(self, mock_interface, mock_logger):
        """RED: Test that GeneratePerChapterOutline should return both text and title"""
        from Writer.OutlineGenerator import GeneratePerChapterOutline

        # Mock SafeGeneratePydantic to return a ChapterOutlineOutput with title
        from Writer.Models import ChapterOutlineOutput
        mock_chapter_output = ChapterOutlineOutput(
            chapter_number=1,
            chapter_title="Test Chapter Title",
            scenes=["This is scene 1 with proper description", "This is scene 2 with proper description"],
            characters_present=["Character 1"],
            outline_summary="Test chapter summary"
        )

        # Create mock interface instance
        mock_iface = mock_interface()
        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "mock response"}],
            mock_chapter_output,
            {"prompt_tokens": 100, "completion_tokens": 50}
        )

        # Current implementation returns only string
        result = GeneratePerChapterOutline(
            mock_iface, mock_logger(), 1, 2, "Test outline"
        )

        # Should fail because we need tuple with title
        assert isinstance(result, tuple), "Should return (summary, title) tuple"
        assert len(result) == 2, "Should have both summary and title"
        assert result[1] == "Test Chapter Title", "Should return chapter title"