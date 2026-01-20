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
        """Stage 2 should fallback to Stage 1 output when shrinkage exceeds threshold.

        With Option 3: Fallback only happens after max retries are exhausted.
        """
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

        # With Option 3: LLMSummaryCheck needs to return False to trigger retry
        # After max retries, fallback happens
        mock_summary_check = Mock()
        mock_summary_check.LLMSummaryCheck.return_value = (False, "Keep trying")

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

        # Assert - should fallback to Stage 1 output after max retries
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
        """Stage 3 should fallback to Stage 2 output when shrinkage exceeds threshold.

        With Option 3: Fallback only happens after max retries are exhausted.
        """
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

        # With Option 3: LLMSummaryCheck needs to return False to trigger retry
        mock_summary_check = Mock()
        mock_summary_check.LLMSummaryCheck.return_value = (False, "Keep trying")

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

        # Assert - should fallback to Stage 2 output after max retries
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


class TestStage2ShrinkageRetryWithFeedback:
    """Test Stage 2 retry behavior with shrinkage feedback (Option 3).

    These tests expect Option 3 behavior:
    - Don't revert immediately on shrinkage
    - Add shrinkage feedback for retry
    - Only revert after max retries exhausted

    RED phase: These tests FAIL with current implementation because of immediate revert.
    """

    def test_stage2_retries_with_shrinkage_feedback(self, mock_interface, mock_logger):
        """Stage 2 should add shrinkage feedback and retry instead of immediate revert.

        Current behavior problem:
        1. Shrinkage detected (150 words from 400)
        2. Immediate revert: Stage2Chapter = Stage1Chapter (400 words)
        3. LLMSummaryCheck validates the REVERTED content (400 words)
        4. Since Stage1Chapter was already valid from Stage 1, validation PASSES
        5. Loop exits - no retry happens, feedback never used

        Expected (Option 3):
        1. Shrinkage detected (150 words from 400)
        2. DON'T revert - add shrinkage feedback to Feedback variable
        3. LLMSummaryCheck validates the SHRUNKEN content (150 words)
        4. Validation FAILS (too short)
        5. Loop continues with feedback
        6. Retry generates 450 words (success)
        """
        from Writer.Chapter.ChapterGenerator import _generate_stage2_character_dev

        # Arrange
        stage1_chapter = " ".join(["word"] * 400)  # 400 words original

        # Attempt 1: Shrinkage (150 words - 62.5% reduction)
        short_stage2 = " ".join(["term"] * 150)
        mock_result1 = Mock()
        mock_result1.text = short_stage2

        # Attempt 2: Success (no shrinkage, 450 words)
        good_stage2 = " ".join(["better"] * 450)
        mock_result2 = Mock()
        mock_result2.text = good_stage2

        mock_iface = mock_interface()
        mock_iface.SafeGeneratePydantic.side_effect = [
            ([{"role": "assistant"}], mock_result1, {"prompt_tokens": 100}),
            ([{"role": "assistant"}], mock_result2, {"prompt_tokens": 100}),
        ]

        mock_prompts = Mock()
        mock_prompts.CHAPTER_GENERATION_STAGE2 = (
            "Stage 2 prompt {ContextHistoryInsert} {_ChapterNum} {_TotalChapters} "
            "{ThisChapterOutline} {FormattedLastChapterSummary} {Stage1Chapter} "
            "{Feedback} {_BaseContext} {PydanticFormatInstructions}"
        )

        # This mock needs to return what LLMSummaryCheck would ACTUALLY return
        # based on what content it receives:
        # - Call 1 (current): Receives Stage1Chapter (400 words) after revert → VALID
        # - Call 1 (Option 3): Receives short_stage2 (150 words) → INVALID with feedback
        mock_summary_check = Mock()

        def llm_summary_check_side_effect(_interface, _logger, _detailed_outline, content):
            # Current: content is Stage1Chapter (400 words) - always valid
            if len(content.split()) >= 360:  # Stage1Chapter is 400 words
                return (True, "")
            # Option 3: content is short_stage2 (150 words) - invalid with feedback
            else:
                return (False, f"\n\nCRITICAL: Output Anda hanya {len(content.split())} kata...")

        mock_summary_check.LLMSummaryCheck.side_effect = llm_summary_check_side_effect

        mock_config = Mock()
        mock_config.CHAPTER_STAGE2_WRITER_MODEL = "test_model"
        mock_config.CHAPTER_MAX_REVISIONS = 2
        mock_config.SEED = 0
        mock_config.USE_REASONING_CHAIN = False
        mock_config.MAX_WORD_COUNT_REDUCTION_RATIO = 0.10

        # Act
        result = _generate_stage2_character_dev(
            mock_iface, mock_logger(), mock_prompts, 1, 2, [], "",
            "outline", "", stage1_chapter, "base",
            "detailed_outline", mock_config, mock_summary_check
        )

        # Assert - Expected (Option 3):
        # - 2 calls to SafeGeneratePydantic (retry with feedback)
        # - Returns good_stage2 (the improved output, NOT stage1_chapter)
        assert mock_iface.SafeGeneratePydantic.call_count == 2, \
            f"Expected 2 calls (Option 3: retry with feedback), got {mock_iface.SafeGeneratePydantic.call_count}"
        assert result == good_stage2, \
            f"Expected good_stage2 (Option 3), got word count {len(result.split())}"

    def test_stage2_fallback_after_max_retries_with_shrinkage(self, mock_interface, mock_logger):
        """Stage 2 should revert to Stage 1 after max retries with persistent shrinkage.

        Current behavior: Immediate revert, exits after 1 call.
        Expected (Option 3): Retries with feedback, then falls back after max retries.
        """
        from Writer.Chapter.ChapterGenerator import _generate_stage2_character_dev

        # Arrange
        stage1_chapter = " ".join(["word"] * 400)

        # All attempts: Shrinkage (100 words - 75% reduction)
        short_result = Mock()
        short_result.text = " ".join(["short"] * 100)

        mock_iface = mock_interface()
        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant"}], short_result, {"prompt_tokens": 100}
        )

        mock_prompts = Mock()
        mock_prompts.CHAPTER_GENERATION_STAGE2 = (
            "Stage 2 prompt {ContextHistoryInsert} {_ChapterNum} {_TotalChapters} "
            "{ThisChapterOutline} {FormattedLastChapterSummary} {Stage1Chapter} "
            "{Feedback} {_BaseContext} {PydanticFormatInstructions}"
        )

        mock_config = Mock()
        mock_config.CHAPTER_STAGE2_WRITER_MODEL = "test_model"
        mock_config.CHAPTER_MAX_REVISIONS = 1
        mock_config.SEED = 0
        mock_config.USE_REASONING_CHAIN = False
        mock_config.MAX_WORD_COUNT_REDUCTION_RATIO = 0.10

        # Option 3: validates the shrunken content (100 words) -> INVALID
        mock_summary_check = Mock()

        def llm_summary_check_side_effect(_interface, _logger, _detailed_outline, content):
            # Shrunken content (100 words) - invalid
            if len(content.split()) < 360:
                return (False, "Too short")
            return (True, "")

        mock_summary_check.LLMSummaryCheck.side_effect = llm_summary_check_side_effect

        # Act
        result = _generate_stage2_character_dev(
            mock_iface, mock_logger(), mock_prompts, 1, 2, [], "",
            "outline", "", stage1_chapter, "base",
            "detailed_outline", mock_config, mock_summary_check
        )

        # Assert - Expected (Option 3):
        # - 2 calls to SafeGeneratePydantic (retries with feedback)
        # - Returns stage1_chapter (fallback after max retries)
        assert mock_iface.SafeGeneratePydantic.call_count == 2, \
            f"Expected 2 calls (Option 3), got {mock_iface.SafeGeneratePydantic.call_count}"
        assert result == stage1_chapter  # Returns stage1_chapter (fallback)

    def test_stage2_no_revert_when_output_expands(self, mock_interface, mock_logger):
        """Stage 2 should NOT revert when output expands (no shrinkage).

        This test should PASS with both current and Option 3 implementations
        because there's no shrinkage detected.
        """
        from Writer.Chapter.ChapterGenerator import _generate_stage2_character_dev

        # Arrange
        stage1_chapter = " ".join(["word"] * 300)

        # Output expands to 500 words (good!)
        expanded_result = Mock()
        expanded_result.text = " ".join(["expanded"] * 500)

        mock_iface = mock_interface()
        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant"}], expanded_result, {"prompt_tokens": 100}
        )

        mock_prompts = Mock()
        mock_prompts.CHAPTER_GENERATION_STAGE2 = (
            "Stage 2 prompt {ContextHistoryInsert} {_ChapterNum} {_TotalChapters} "
            "{ThisChapterOutline} {FormattedLastChapterSummary} {Stage1Chapter} "
            "{Feedback} {_BaseContext} {PydanticFormatInstructions}"
        )

        mock_summary_check = Mock()
        mock_summary_check.LLMSummaryCheck.return_value = (True, "")

        mock_config = Mock()
        mock_config.CHAPTER_STAGE2_WRITER_MODEL = "test_model"
        mock_config.CHAPTER_MAX_REVISIONS = 1
        mock_config.SEED = 0
        mock_config.USE_REASONING_CHAIN = False
        mock_config.MAX_WORD_COUNT_REDUCTION_RATIO = 0.10

        # Act
        result = _generate_stage2_character_dev(
            mock_iface, mock_logger(), mock_prompts, 1, 2, [], "",
            "outline", "", stage1_chapter, "base",
            "detailed_outline", mock_config, mock_summary_check
        )

        # Assert - should use expanded output, NOT Stage 1
        assert result == expanded_result.text


class TestStage3ShrinkageRetryWithFeedback:
    """Test Stage 3 retry behavior with shrinkage feedback (Option 3).

    RED phase: These tests FAIL with current implementation because of immediate revert.
    """

    def test_stage3_retries_with_shrinkage_feedback(self, mock_interface, mock_logger):
        """Stage 3 should add shrinkage feedback and retry instead of immediate revert.

        Current behavior problem: Same as Stage 2.
        Expected (Option 3): Adds shrinkage feedback, retries with feedback.
        """
        from Writer.Chapter.ChapterGenerator import _generate_stage3_dialogue

        # Arrange
        stage2_chapter = " ".join(["word"] * 400)

        # Attempt 1: Shrinkage (150 words)
        short_stage3 = " ".join(["term"] * 150)
        mock_result1 = Mock()
        mock_result1.text = short_stage3

        # Attempt 2: Success
        good_stage3 = " ".join(["better"] * 450)
        mock_result2 = Mock()
        mock_result2.text = good_stage3

        mock_iface = mock_interface()
        mock_iface.SafeGeneratePydantic.side_effect = [
            ([{"role": "assistant"}], mock_result1, {"prompt_tokens": 100}),
            ([{"role": "assistant"}], mock_result2, {"prompt_tokens": 100}),
        ]

        mock_prompts = Mock()
        mock_prompts.CHAPTER_GENERATION_STAGE3 = (
            "Stage 3 prompt {ContextHistoryInsert} {_ChapterNum} {_TotalChapters} "
            "{ThisChapterOutline} {FormattedLastChapterSummary} {Stage2Chapter} "
            "{Feedback} {_BaseContext} {PydanticFormatInstructions}"
        )

        mock_summary_check = Mock()

        def llm_summary_check_side_effect(_interface, _logger, _detailed_outline, content):
            # Current: content is Stage2Chapter (400 words) - always valid
            if len(content.split()) >= 360:
                return (True, "")
            # Option 3: content is short_stage3 (150 words) - invalid
            else:
                return (False, f"\n\nCRITICAL: Output Anda hanya {len(content.split())} kata...")

        mock_summary_check.LLMSummaryCheck.side_effect = llm_summary_check_side_effect

        mock_config = Mock()
        mock_config.CHAPTER_STAGE3_WRITER_MODEL = "test_model"
        mock_config.CHAPTER_MAX_REVISIONS = 2
        mock_config.SEED = 0
        mock_config.USE_REASONING_CHAIN = False
        mock_config.MAX_WORD_COUNT_REDUCTION_RATIO = 0.10

        # Act
        result = _generate_stage3_dialogue(
            mock_iface, mock_logger(), mock_prompts, 1, 2, [], "",
            "outline", "", stage2_chapter, "base",
            "detailed_outline", mock_config, mock_summary_check
        )

        # Assert - Expected (Option 3):
        assert mock_iface.SafeGeneratePydantic.call_count == 2, \
            f"Expected 2 calls (Option 3: retry with feedback), got {mock_iface.SafeGeneratePydantic.call_count}"
        assert result == good_stage3, \
            f"Expected good_stage3 (Option 3), got word count {len(result.split())}"
