"""
Tests for ChapterGenerator paragraph fallback integration.

TDD London School: Tests written first (RED phase).
"""

from unittest.mock import MagicMock, patch


class TestChapterGeneratorParagraphFallback:
    """Test paragraph formatting fallback in ChapterGenerator."""

    def test_stage2_applies_fallback_after_max_revisions(self):
        """Stage 2 should apply paragraph fallback when max revisions exceeded."""
        from Writer.Chapter.ChapterGenerator import _generate_stage2_character_dev

        # Mock dependencies
        mock_interface = MagicMock()
        mock_logger = MagicMock()
        mock_prompts = MagicMock()
        mock_prompts.CHAPTER_GENERATION_STAGE2 = MagicMock()
        mock_prompts.CHAPTER_GENERATION_STAGE2.format = MagicMock(return_value="prompt")
        mock_config = MagicMock()
        mock_config.CHAPTER_MAX_REVISIONS = 0  # Force immediate exit
        mock_config.USE_PYDANTIC_PARSING = False
        mock_config.USE_REASONING_CHAIN = False
        mock_config.NATIVE_LANGUAGE = "en"
        mock_summary_check = MagicMock()

        # Wall of text without paragraph breaks
        wall_of_text = "Sentence one. " * 100

        # Mock SafeGeneratePydantic to return wall of text
        mock_result = MagicMock()
        mock_result.text = wall_of_text
        mock_interface.SafeGeneratePydantic.return_value = ([], mock_result, None)

        with patch('Writer.Chapter.ChapterGenerator.validate_paragraph_breaks') as mock_validate, \
             patch('Writer.Chapter.ChapterGenerator.ensure_paragraph_formatting') as mock_fallback:
            # Validation fails
            mock_validate.return_value = (False, "Need more paragraphs")
            # Fallback returns formatted text
            mock_fallback.return_value = ("Para 1.\n\nPara 2.\n\nPara 3.", True)

            _ = _generate_stage2_character_dev(
                mock_interface, mock_logger, mock_prompts,
                _ChapterNum=1, _TotalChapters=5,
                MessageHistory=[], ContextHistoryInsert="",
                ThisChapterOutline="outline", FormattedLastChapterSummary="",
                Stage1Chapter="stage1", _BaseContext="context",
                DetailedChapterOutlineForCheck="detailed",
                Config_module=mock_config,
                ChapterGenSummaryCheck_module=mock_summary_check
            )

            # Fallback should be called
            mock_fallback.assert_called_once()
            # Logger should log warning about fallback
            log_calls = [str(call) for call in mock_logger.Log.call_args_list]
            assert any("fallback" in call.lower() for call in log_calls)

    def test_stage3_applies_fallback_after_max_revisions(self):
        """Stage 3 should apply paragraph fallback when max revisions exceeded."""
        from Writer.Chapter.ChapterGenerator import _generate_stage3_dialogue

        # Mock dependencies
        mock_interface = MagicMock()
        mock_logger = MagicMock()
        mock_prompts = MagicMock()
        mock_prompts.CHAPTER_GENERATION_STAGE3 = MagicMock()
        mock_prompts.CHAPTER_GENERATION_STAGE3.format = MagicMock(return_value="prompt")
        mock_config = MagicMock()
        mock_config.CHAPTER_MAX_REVISIONS = 0  # Force immediate exit
        mock_config.USE_PYDANTIC_PARSING = False
        mock_config.USE_REASONING_CHAIN = False
        mock_config.NATIVE_LANGUAGE = "en"
        mock_summary_check = MagicMock()

        # Wall of text without paragraph breaks
        wall_of_text = "Sentence one. " * 100

        # Mock SafeGeneratePydantic to return wall of text
        mock_result = MagicMock()
        mock_result.text = wall_of_text
        mock_interface.SafeGeneratePydantic.return_value = ([], mock_result, None)

        with patch('Writer.Chapter.ChapterGenerator.validate_paragraph_breaks') as mock_validate, \
             patch('Writer.Chapter.ChapterGenerator.ensure_paragraph_formatting') as mock_fallback:
            # Validation fails
            mock_validate.return_value = (False, "Need more paragraphs")
            # Fallback returns formatted text
            mock_fallback.return_value = ("Para 1.\n\nPara 2.\n\nPara 3.", True)

            _ = _generate_stage3_dialogue(
                mock_interface, mock_logger, mock_prompts,
                _ChapterNum=1, _TotalChapters=5,
                MessageHistory=[], ContextHistoryInsert="",
                ThisChapterOutline="outline", FormattedLastChapterSummary="",
                Stage2Chapter="stage2", _BaseContext="context",
                DetailedChapterOutlineForCheck="detailed",
                Config_module=mock_config,
                ChapterGenSummaryCheck_module=mock_summary_check
            )

            # Fallback should be called
            mock_fallback.assert_called_once()

    def test_fallback_not_called_when_validation_passes(self):
        """Fallback should NOT be called when paragraph validation passes."""
        from Writer.Chapter.ChapterGenerator import _generate_stage3_dialogue

        # Mock dependencies
        mock_interface = MagicMock()
        mock_logger = MagicMock()
        mock_prompts = MagicMock()
        mock_prompts.CHAPTER_GENERATION_STAGE3 = MagicMock()
        mock_prompts.CHAPTER_GENERATION_STAGE3.format = MagicMock(return_value="prompt")
        mock_config = MagicMock()
        mock_config.CHAPTER_MAX_REVISIONS = 5
        mock_config.USE_PYDANTIC_PARSING = False
        mock_config.USE_REASONING_CHAIN = False
        mock_config.NATIVE_LANGUAGE = "en"
        mock_summary_check = MagicMock()
        mock_summary_check.LLMSummaryCheck.return_value = (True, "")

        # Well-formatted text
        good_text = "Para 1.\n\nPara 2.\n\nPara 3."

        # Mock SafeGeneratePydantic to return good text
        mock_result = MagicMock()
        mock_result.text = good_text
        mock_interface.SafeGeneratePydantic.return_value = ([], mock_result, None)

        with patch('Writer.Chapter.ChapterGenerator.validate_paragraph_breaks') as mock_validate, \
             patch('Writer.Chapter.ChapterGenerator.ensure_paragraph_formatting') as mock_fallback:
            # Validation passes
            mock_validate.return_value = (True, "")

            _ = _generate_stage3_dialogue(
                mock_interface, mock_logger, mock_prompts,
                _ChapterNum=1, _TotalChapters=5,
                MessageHistory=[], ContextHistoryInsert="",
                ThisChapterOutline="outline", FormattedLastChapterSummary="",
                Stage2Chapter="stage2", _BaseContext="context",
                DetailedChapterOutlineForCheck="detailed",
                Config_module=mock_config,
                ChapterGenSummaryCheck_module=mock_summary_check
            )

            # Fallback should NOT be called
            mock_fallback.assert_not_called()

    def test_fallback_logs_warning_level(self):
        """Fallback should log at warning level (6)."""
        from Writer.Chapter.ChapterGenerator import _generate_stage3_dialogue

        # Mock dependencies
        mock_interface = MagicMock()
        mock_logger = MagicMock()
        mock_prompts = MagicMock()
        mock_prompts.CHAPTER_GENERATION_STAGE3 = MagicMock()
        mock_prompts.CHAPTER_GENERATION_STAGE3.format = MagicMock(return_value="prompt")
        mock_config = MagicMock()
        mock_config.CHAPTER_MAX_REVISIONS = 0  # Force immediate exit
        mock_config.USE_PYDANTIC_PARSING = False
        mock_config.USE_REASONING_CHAIN = False
        mock_config.NATIVE_LANGUAGE = "en"
        mock_summary_check = MagicMock()

        wall_of_text = "Sentence. " * 100

        mock_result = MagicMock()
        mock_result.text = wall_of_text
        mock_interface.SafeGeneratePydantic.return_value = ([], mock_result, None)

        with patch('Writer.Chapter.ChapterGenerator.validate_paragraph_breaks') as mock_validate, \
             patch('Writer.Chapter.ChapterGenerator.ensure_paragraph_formatting') as mock_fallback:
            mock_validate.return_value = (False, "Need more paragraphs")
            mock_fallback.return_value = ("Para 1.\n\nPara 2.", True)

            _generate_stage3_dialogue(
                mock_interface, mock_logger, mock_prompts,
                _ChapterNum=1, _TotalChapters=5,
                MessageHistory=[], ContextHistoryInsert="",
                ThisChapterOutline="outline", FormattedLastChapterSummary="",
                Stage2Chapter="stage2", _BaseContext="context",
                DetailedChapterOutlineForCheck="detailed",
                Config_module=mock_config,
                ChapterGenSummaryCheck_module=mock_summary_check
            )

            # Check that warning (level 6) was logged
            log_calls = mock_logger.Log.call_args_list
            fallback_log = [c for c in log_calls if 'fallback' in str(c).lower()]
            assert len(fallback_log) > 0
            # The fallback log should be at level 6 (warning)
            assert any(c[0][1] == 6 for c in fallback_log if len(c[0]) > 1)
