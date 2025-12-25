"""
ChapterGenerator TDD Tests - London School Approach
Tests for migrating all SafeGenerateText usage to SafeGeneratePydantic
"""
from unittest.mock import Mock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestChapterGeneratorPydanticConversion:
    """Test complete conversion of ChapterGenerator to Pydantic"""

    def test_prepare_initial_context_segment_uses_pydantic(self, mock_interface, mock_logger):
        """Verify _prepare_initial_generation_context uses SafeGeneratePydantic for chapter segment"""
        from Writer.Chapter.ChapterGenerator import _prepare_initial_generation_context

        # Arrange
        mock_iface = mock_interface()

        # Use ChapterOutput model for chapter segment
        from Writer.Models import ChapterOutput
        chapter_segment = ChapterOutput(
            text="This is the chapter outline segment that provides specific guidance for writing this chapter focusing on the key events and character developments.",
            word_count=20,
            chapter_number=1,
            chapter_title=None
        )

        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "Response"}],
            chapter_segment,
            {"prompt_tokens": 100}
        )

        # Mock other dependencies
        mock_prompts = Mock()
        mock_prompts.CHAPTER_GENERATION_INTRO = "Intro"
        mock_prompts.CHAPTER_GENERATION_PROMPT = "Prompt {_Outline} {_ChapterNum}"
        mock_prompts.CHAPTER_HISTORY_INSERT = "History insert {_Outline}"
        mock_prompts.CHAPTER_SUMMARY_INTRO = "Summary Intro"
        mock_prompts.CHAPTER_SUMMARY_PROMPT = "Summary prompt"

        mock_config = Mock()
        mock_config.CHAPTER_STAGE1_WRITER_MODEL = "test_model"
        mock_config.MIN_WORDS_CHAPTER_SEGMENT_EXTRACT = 50
        mock_config.MIN_WORDS_CHAPTER_SUMMARY = 50

        # Act
        result = _prepare_initial_generation_context(
            mock_iface, mock_logger(), mock_prompts,
            "Full outline", [], 1, 5, mock_config
        )

        # Assert: SafeGeneratePydantic was called
        mock_iface.SafeGeneratePydantic.assert_called_once()

    def test_prepare_initial_context_summary_uses_pydantic(self, mock_interface, mock_logger):
        """Verify _prepare_initial_generation_context uses SafeGeneratePydantic for chapter summary"""
        from Writer.Chapter.ChapterGenerator import _prepare_initial_generation_context

        # Arrange
        mock_iface = mock_interface()

        # Use ChapterOutput model for chapter summary
        from Writer.Models import ChapterOutput
        chapter_summary = ChapterOutput(
            text="This is a summary of the previous chapter focusing on the major plot points and character developments that will influence the current chapter.",
            word_count=20,
            chapter_number=1,
            chapter_title=None
        )

        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "Response"}],
            chapter_summary,
            {"prompt_tokens": 100}
        )

        # Mock other dependencies
        mock_prompts = Mock()
        mock_prompts.CHAPTER_GENERATION_INTRO = "Intro"
        mock_prompts.CHAPTER_GENERATION_PROMPT = "Prompt {_Outline} {_ChapterNum}"
        mock_prompts.CHAPTER_HISTORY_INSERT = "History insert {_Outline}"
        mock_prompts.CHAPTER_SUMMARY_INTRO = "Summary Intro"
        mock_prompts.CHAPTER_SUMMARY_PROMPT = "Summary prompt"

        mock_config = Mock()
        mock_config.CHAPTER_STAGE1_WRITER_MODEL = "test_model"
        mock_config.MIN_WORDS_CHAPTER_SEGMENT_EXTRACT = 50
        mock_config.MIN_WORDS_CHAPTER_SUMMARY = 50

        # Act with previous chapters
        result = _prepare_initial_generation_context(
            mock_iface, mock_logger(), mock_prompts,
            "Full outline", [{"text": "Previous chapter"}], 2, 5, mock_config
        )

        # Assert: SafeGeneratePydantic was called twice (segment and summary)
        assert mock_iface.SafeGeneratePydantic.call_count == 2

    def test_revise_chapter_uses_pydantic(self, mock_interface, mock_logger):
        """Verify ReviseChapter uses SafeGeneratePydantic with appropriate model"""
        from Writer.Chapter.ChapterGenerator import ReviseChapter

        # Arrange
        mock_iface = mock_interface()

        # Use ChapterOutput for revision (fixed: was OutlineOutput)
        from Writer.Models import ChapterOutput
        revision = ChapterOutput(
            text="Revised chapter content with more details and better flow that meets the minimum length requirement for validation.",
            word_count=20,
            chapter_number=1,
            chapter_title=None
        )

        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "Response"}],
            revision,
            {"prompt_tokens": 200}
        )

        # Mock dependencies
        mock_prompts = Mock()
        mock_prompts.CHAPTER_REVISION_INTRO = "Revision Intro"
        mock_prompts.CHAPTER_REVISION_PROMPT = "Revision prompt {_Feedback={_Feedback}}"

        mock_config = Mock()
        mock_config.CHAPTER_REVISION_MODEL = "test_model"

        # Act
        result = ReviseChapter(
            mock_iface, mock_logger(),
            1,  # _ChapterNum
            5,  # _TotalChapters
            "Original chapter content",
            "Feedback suggests adding more description"
        )

        # Assert: SafeGeneratePydantic was called
        mock_iface.SafeGeneratePydantic.assert_called_once()

    def test_all_functions_use_pydantic_not_text(self, mock_interface, mock_logger):
        """Verify no ChapterGenerator function uses SafeGenerateText"""
        from Writer.Chapter.ChapterGenerator import _prepare_initial_generation_context, ReviseChapter

        # Arrange
        mock_iface = mock_interface()

        # Mock models
        from Writer.Models import ChapterOutput
        segment = ChapterOutput(
            text="Segment content that is long enough to meet validation requirements. This text is repeated multiple times to ensure it meets the minimum length requirement of 100 characters for the ChapterOutput model validation.",
            word_count=30,
            chapter_number=1,
            chapter_title=None
        )
        summary = ChapterOutput(
            text="Summary content that meets the minimum length requirements for validation. This is a summary of the chapter that includes all major plot points and character developments in sufficient detail.",
            word_count=25,
            chapter_number=1,
            chapter_title=None
        )
        revision = ChapterOutput(
            text="Revised chapter content that meets the minimum length requirements for the ChapterOutput model validation.",
            word_count=15,
            chapter_number=1,
            chapter_title=None
        )

        # Set up different returns for each call
        mock_iface.SafeGeneratePydantic.side_effect = [
            ([{"role": "assistant"}], segment, {"tokens": 100}),  # For _prepare_initial_context with no previous chapters
            ([{"role": "assistant"}], revision, {"tokens": 100})  # For ReviseChapter
        ]

        # Mock dependencies
        mock_prompts = Mock()
        mock_prompts.CHAPTER_GENERATION_INTRO = "Intro"
        mock_prompts.CHAPTER_GENERATION_PROMPT = "Prompt"
        mock_prompts.CHAPTER_HISTORY_INSERT = "History insert {_Outline}"
        mock_prompts.CHAPTER_SUMMARY_INTRO = "Summary Intro"
        mock_prompts.CHAPTER_SUMMARY_PROMPT = "Summary prompt"
        mock_prompts.CHAPTER_REVISION_INTRO = "Revision Intro"
        mock_prompts.CHAPTER_REVISION_PROMPT = "Revision prompt"

        mock_config = Mock()
        mock_config.MIN_WORDS_CHAPTER_SEGMENT_EXTRACT = 10
        mock_config.MIN_WORDS_CHAPTER_SUMMARY = 10

        # Act
        _prepare_initial_generation_context(
            mock_iface, mock_logger(), mock_prompts,
            "outline", [], 1, 2, mock_config
        )
        ReviseChapter(
            mock_iface, mock_logger(),
            1,  # _ChapterNum
            2,  # _TotalChapters
            "content",
            "feedback"
        )

        # Assert: SafeGenerateText should not be called
        assert not hasattr(mock_iface, 'SafeGenerateText') or \
            not mock_iface.SafeGenerateText.called

        # Assert: SafeGeneratePydantic was called multiple times
        assert mock_iface.SafeGeneratePydantic.call_count >= 2
