"""
Pipeline Title Generation Tests - TDD London School Approach
Tests for migrating _handle_chapter_title_generation to SafeGeneratePydantic
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestChapterTitleGenerationPydantic:
    """Test chapter title generation uses Pydantic model"""

    def test_title_generation_uses_pydantic_not_text(self, mock_interface, mock_logger):
        """Verify title generation uses SafeGeneratePydantic and not SafeGenerateText"""
        from Writer.Pipeline import _handle_chapter_title_generation_pipeline_version
        import Writer.Config as Config

        # Arrange: Create mock interface
        mock_iface = mock_interface()

        # Create a real TitleOutput model
        from Writer.Models import TitleOutput
        title_model = TitleOutput(title="Chapter 1: The Beginning")

        # Mock SafeGeneratePydantic to return our model
        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "Mocked response"}],
            title_model,
            {"prompt_tokens": 100, "completion_tokens": 50}
        )

        # Save original config values
        orig_auto_titles = Config.AUTO_CHAPTER_TITLES
        orig_fast_model = Config.FAST_MODEL
        orig_min_words = Config.MIN_WORDS_FOR_CHAPTER_TITLE
        orig_max_retries = Config.MAX_RETRIES_CHAPTER_TITLE

        try:
            # Set test config values
            Config.AUTO_CHAPTER_TITLES = True
            Config.FAST_MODEL = "test_model"
            Config.MIN_WORDS_FOR_CHAPTER_TITLE = 3
            Config.MAX_RETRIES_CHAPTER_TITLE = 3

            # Mock ActivePrompts and Statistics
            mock_prompts = Mock()
            mock_prompts.GET_CHAPTER_TITLE_PROMPT = "Test prompt template"

            mock_stats = Mock()
            mock_stats.GetWordCount.return_value = 100

            # Act: Call the function
            result = _handle_chapter_title_generation_pipeline_version(
                mock_logger(), mock_iface, Config, mock_prompts,
                "Chapter text content", 1, "Base context", "Chapter outline", mock_stats
            )

            # Assert: SafeGeneratePydantic was called, not SafeGenerateText
            mock_iface.SafeGeneratePydantic.assert_called_once()

            # CRITICAL: Verify SafeGenerateText was NEVER called
            assert not hasattr(mock_iface, 'SafeGenerateText') or \
                   not getattr(mock_iface, 'SafeGenerateText', Mock()).called

            # Verify result is the title string from Pydantic model
            assert result == "Chapter 1: The Beginning"
        finally:
            # Restore original config values
            Config.AUTO_CHAPTER_TITLES = orig_auto_titles
            Config.FAST_MODEL = orig_fast_model
            Config.MIN_WORDS_FOR_CHAPTER_TITLE = orig_min_words
            Config.MAX_RETRIES_CHAPTER_TITLE = orig_max_retries

    def test_title_generation_extracts_title_from_pydantic_model(self, mock_interface, mock_logger):
        """Verify the title is correctly extracted from Pydantic model"""
        from Writer.Pipeline import _handle_chapter_title_generation_pipeline_version
        import Writer.Config as Config

        # Arrange: Create mock interface
        mock_iface = mock_interface()

        # Create a real TitleOutput with title
        from Writer.Models import TitleOutput
        title_model = TitleOutput(title='  "A Mysterious Discovery"  ')  # Test with quotes and spaces

        # Mock SafeGeneratePydantic
        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "Response"}],
            title_model,
            {"tokens": 200}
        )

        # Save original config
        orig_auto = Config.AUTO_CHAPTER_TITLES
        orig_model = Config.FAST_MODEL
        orig_retries = Config.MAX_RETRIES_CHAPTER_TITLE
        orig_min = Config.MIN_WORDS_FOR_CHAPTER_TITLE

        try:
            # Set test config
            Config.AUTO_CHAPTER_TITLES = True
            Config.FAST_MODEL = "test_model"
            Config.MAX_RETRIES_CHAPTER_TITLE = 3
            Config.MIN_WORDS_FOR_CHAPTER_TITLE = 3

            # Mock dependencies
            mock_prompts = Mock()
            mock_prompts.GET_CHAPTER_TITLE_PROMPT = "Prompt template"

            mock_stats = Mock()
            mock_stats.GetWordCount.return_value = 50

            # Act: Generate title
            result = _handle_chapter_title_generation_pipeline_version(
                mock_logger(), mock_iface, Config, mock_prompts,
                "Chapter content here", 2, "Base", "Outline", mock_stats
            )

            # Assert: Title is extracted and cleaned
            assert result == "A Mysterious Discovery"  # Quotes and spaces removed
        finally:
            # Restore config
            Config.AUTO_CHAPTER_TITLES = orig_auto
            Config.FAST_MODEL = orig_model
            Config.MAX_RETRIES_CHAPTER_TITLE = orig_retries
            Config.MIN_WORDS_FOR_CHAPTER_TITLE = orig_min

    def test_title_generation_disabled_returns_placeholder(self, mock_interface, mock_logger):
        """Verify disabled title generation returns placeholder"""
        from Writer.Pipeline import _handle_chapter_title_generation_pipeline_version
        import Writer.Config as Config

        # Arrange: Get original config
        orig_auto = Config.AUTO_CHAPTER_TITLES
        orig_prefix = Config.DEFAULT_CHAPTER_TITLE_PREFIX

        try:
            # Mock config with disabled titles
            Config.AUTO_CHAPTER_TITLES = False  # Disabled
            Config.DEFAULT_CHAPTER_TITLE_PREFIX = "Chapter "

            # Act: Generate title with disabled config
            result = _handle_chapter_title_generation_pipeline_version(
                mock_logger(), mock_interface(), Config, Mock(),
                "Chapter text", 1, "Base", "Outline", Mock()
            )

            # Assert: Returns placeholder
            assert result == "Chapter 1"
        finally:
            # Restore config
            Config.AUTO_CHAPTER_TITLES = orig_auto
            Config.DEFAULT_CHAPTER_TITLE_PREFIX = orig_prefix