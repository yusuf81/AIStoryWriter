"""Tests for ChapterGenerator content shrinkage validation.

Tests that Stage 2 and Stage 3 generation fallback to previous stage
output when content shrinkage exceeds the configured threshold.
"""
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TestStage2ContentShrinkage:
    """Test Stage 2 fallback when content shrinks beyond threshold."""

    def test_stage2_fallback_on_content_shrinkage(self, mock_interface, mock_logger):
        """Stage 2 should fallback to Stage 1 output when shrinkage exceeds threshold."""
        from Writer.Chapter.ChapterGenerator import _generate_stage2_character_dev

        # Arrange
        mock_iface = mock_interface()
        mock_log = mock_logger()

        # Stage 1 output: 100 words
        stage1_chapter = " ".join(["word"] * 100)

        # Stage 2 output: 50 words (50% shrinkage - exceeds 10% threshold)
        shrunken_stage2 = " ".join(["word"] * 50)

        # Use mock for pydantic result to avoid validation issues
        mock_pydantic_result = Mock()
        mock_pydantic_result.text = shrunken_stage2

        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant"}],
            mock_pydantic_result,
            {"prompt_tokens": 100}
        )

        mock_prompts = Mock()
        mock_prompts.CHAPTER_GENERATION_STAGE2 = "Stage 2 prompt {ContextHistoryInsert} {_ChapterNum} {_TotalChapters} {ThisChapterOutline} {FormattedLastChapterSummary} {Stage1Chapter} {Feedback} {_BaseContext} {PydanticFormatInstructions}"

        mock_config = Mock()
        mock_config.CHAPTER_STAGE2_WRITER_MODEL = "test_model"
        mock_config.CHAPTER_MAX_REVISIONS = 1
        mock_config.SEED = 0
        mock_config.USE_REASONING_CHAIN = False
        mock_config.MAX_WORD_COUNT_REDUCTION_RATIO = 0.10

        mock_summary_check = Mock()
        mock_summary_check.LLMSummaryCheck.return_value = (True, "")

        # Act
        result = _generate_stage2_character_dev(
            mock_iface,
            mock_log,
            mock_prompts,
            1,  # chapter num
            5,  # total chapters
            [],  # message history
            "",  # context history insert
            "Chapter outline",
            "",  # formatted last chapter summary
            stage1_chapter,  # Stage 1 output
            "Base context",
            "Detailed outline",
            mock_config,
            mock_summary_check
        )

        # Assert - should fallback to Stage 1 output due to shrinkage
        assert result == stage1_chapter

    def test_stage2_uses_llm_output_when_no_shrinkage(self, mock_interface, mock_logger):
        """Stage 2 should use LLM output when content doesn't shrink significantly."""
        from Writer.Chapter.ChapterGenerator import _generate_stage2_character_dev

        # Arrange
        mock_iface = mock_interface()
        mock_log = mock_logger()

        # Stage 1 output: 100 words
        stage1_chapter = " ".join(["word"] * 100)

        # Stage 2 output: 95 words (5% shrinkage - within 10% threshold)
        normal_stage2 = " ".join(["newword"] * 95)

        mock_pydantic_result = Mock()
        mock_pydantic_result.text = normal_stage2

        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant"}],
            mock_pydantic_result,
            {"prompt_tokens": 100}
        )

        mock_prompts = Mock()
        mock_prompts.CHAPTER_GENERATION_STAGE2 = "Stage 2 prompt {ContextHistoryInsert} {_ChapterNum} {_TotalChapters} {ThisChapterOutline} {FormattedLastChapterSummary} {Stage1Chapter} {Feedback} {_BaseContext} {PydanticFormatInstructions}"

        mock_config = Mock()
        mock_config.CHAPTER_STAGE2_WRITER_MODEL = "test_model"
        mock_config.CHAPTER_MAX_REVISIONS = 1
        mock_config.SEED = 0
        mock_config.USE_REASONING_CHAIN = False
        mock_config.MAX_WORD_COUNT_REDUCTION_RATIO = 0.10

        mock_summary_check = Mock()
        mock_summary_check.LLMSummaryCheck.return_value = (True, "")

        # Act
        result = _generate_stage2_character_dev(
            mock_iface,
            mock_log,
            mock_prompts,
            1,  # chapter num
            5,  # total chapters
            [],  # message history
            "",  # context history insert
            "Chapter outline",
            "",  # formatted last chapter summary
            stage1_chapter,  # Stage 1 output
            "Base context",
            "Detailed outline",
            mock_config,
            mock_summary_check
        )

        # Assert - should use Stage 2 output (no significant shrinkage)
        assert result == normal_stage2


class TestStage3ContentShrinkage:
    """Test Stage 3 fallback when content shrinks beyond threshold."""

    def test_stage3_fallback_on_content_shrinkage(self, mock_interface, mock_logger):
        """Stage 3 should fallback to Stage 2 output when shrinkage exceeds threshold."""
        from Writer.Chapter.ChapterGenerator import _generate_stage3_dialogue

        # Arrange
        mock_iface = mock_interface()
        mock_log = mock_logger()

        # Stage 2 output: 100 words
        stage2_chapter = " ".join(["word"] * 100)

        # Stage 3 output: 50 words (50% shrinkage - exceeds 10% threshold)
        shrunken_stage3 = " ".join(["word"] * 50)

        mock_pydantic_result = Mock()
        mock_pydantic_result.text = shrunken_stage3

        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant"}],
            mock_pydantic_result,
            {"prompt_tokens": 100}
        )

        mock_prompts = Mock()
        mock_prompts.CHAPTER_GENERATION_STAGE3 = "Stage 3 prompt {ContextHistoryInsert} {_ChapterNum} {_TotalChapters} {ThisChapterOutline} {FormattedLastChapterSummary} {Stage2Chapter} {Feedback} {_BaseContext} {PydanticFormatInstructions}"

        mock_config = Mock()
        mock_config.CHAPTER_STAGE3_WRITER_MODEL = "test_model"
        mock_config.CHAPTER_MAX_REVISIONS = 1
        mock_config.SEED = 0
        mock_config.USE_REASONING_CHAIN = False
        mock_config.MAX_WORD_COUNT_REDUCTION_RATIO = 0.10

        mock_summary_check = Mock()
        mock_summary_check.LLMSummaryCheck.return_value = (True, "")

        # Act
        result = _generate_stage3_dialogue(
            mock_iface,
            mock_log,
            mock_prompts,
            1,  # chapter num
            5,  # total chapters
            [],  # message history
            "",  # context history insert
            "Chapter outline",
            "",  # formatted last chapter summary
            stage2_chapter,  # Stage 2 output
            "Base context",
            "Detailed outline",
            mock_config,
            mock_summary_check
        )

        # Assert - should fallback to Stage 2 output due to shrinkage
        assert result == stage2_chapter

    def test_stage3_uses_llm_output_when_no_shrinkage(self, mock_interface, mock_logger):
        """Stage 3 should use LLM output when content doesn't shrink significantly."""
        from Writer.Chapter.ChapterGenerator import _generate_stage3_dialogue

        # Arrange
        mock_iface = mock_interface()
        mock_log = mock_logger()

        # Stage 2 output: 100 words
        stage2_chapter = " ".join(["word"] * 100)

        # Stage 3 output: 98 words (2% shrinkage - within 10% threshold)
        normal_stage3 = " ".join(["newword"] * 98)

        mock_pydantic_result = Mock()
        mock_pydantic_result.text = normal_stage3

        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant"}],
            mock_pydantic_result,
            {"prompt_tokens": 100}
        )

        mock_prompts = Mock()
        mock_prompts.CHAPTER_GENERATION_STAGE3 = "Stage 3 prompt {ContextHistoryInsert} {_ChapterNum} {_TotalChapters} {ThisChapterOutline} {FormattedLastChapterSummary} {Stage2Chapter} {Feedback} {_BaseContext} {PydanticFormatInstructions}"

        mock_config = Mock()
        mock_config.CHAPTER_STAGE3_WRITER_MODEL = "test_model"
        mock_config.CHAPTER_MAX_REVISIONS = 1
        mock_config.SEED = 0
        mock_config.USE_REASONING_CHAIN = False
        mock_config.MAX_WORD_COUNT_REDUCTION_RATIO = 0.10

        mock_summary_check = Mock()
        mock_summary_check.LLMSummaryCheck.return_value = (True, "")

        # Act
        result = _generate_stage3_dialogue(
            mock_iface,
            mock_log,
            mock_prompts,
            1,  # chapter num
            5,  # total chapters
            [],  # message history
            "",  # context history insert
            "Chapter outline",
            "",  # formatted last chapter summary
            stage2_chapter,  # Stage 2 output
            "Base context",
            "Detailed outline",
            mock_config,
            mock_summary_check
        )

        # Assert - should use Stage 3 output (no significant shrinkage)
        assert result == normal_stage3
