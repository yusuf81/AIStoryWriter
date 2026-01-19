"""
Tests for final text processing in Pipeline.

Tests the paragraph formatting and content validation that happens
at the very end of the pipeline before saving to file.

Uses TDD London School approach.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestLLMParagraphFormatting:
    """Tests for LLM-based paragraph formatting retry."""

    def test_llm_retry_called_when_paragraphs_invalid(self):
        """Should call LLM retry when paragraph validation fails."""
        from Writer.Pipeline import apply_final_text_processing

        wall_of_text = "Text without breaks. " * 50
        formatted_by_llm = "Para 1.\n\nPara 2.\n\nPara 3."
        chapter_num = 1
        native_lang = "en"
        logger = MagicMock()
        interface = MagicMock()

        with patch('Writer.Pipeline.validate_paragraph_breaks') as mock_validate:
            # First call: invalid (initial check), second call (after LLM): valid
            mock_validate.side_effect = [
                (False, "Need more paragraphs"),  # Initial check
                (True, "")  # After LLM formatting
            ]

            with patch('Writer.Pipeline._llm_format_paragraphs') as mock_llm:
                mock_llm.return_value = formatted_by_llm

                with patch('Writer.Pipeline.validate_chapter_editing') as mock_edit:
                    mock_edit.return_value = (True, {})  # Content validation passes

                    result = apply_final_text_processing(
                        wall_of_text, chapter_num, native_lang, logger, interface
                    )

        # LLM should be called
        mock_llm.assert_called_once()
        assert result == formatted_by_llm

    def test_falls_back_to_manual_when_llm_fails(self):
        """Should fallback to manual split when LLM retry fails."""
        from Writer.Pipeline import apply_final_text_processing

        wall_of_text = "Text without breaks. " * 50
        manual_formatted = "Manual.\n\nFormatted."
        chapter_num = 1
        native_lang = "en"
        logger = MagicMock()
        interface = MagicMock()

        with patch('Writer.Pipeline.validate_paragraph_breaks') as mock_validate:
            # Always invalid (LLM can't fix it)
            mock_validate.return_value = (False, "Need more paragraphs")

            with patch('Writer.Pipeline._llm_format_paragraphs') as mock_llm:
                # LLM returns but still wall of text
                mock_llm.return_value = wall_of_text

                with patch('Writer.Pipeline.ensure_paragraph_formatting') as mock_manual:
                    mock_manual.return_value = (manual_formatted, True)

                    with patch('Writer.Pipeline.validate_chapter_editing') as mock_edit:
                        mock_edit.return_value = (True, {})

                        result = apply_final_text_processing(
                            wall_of_text, chapter_num, native_lang, logger, interface
                        )

        # Manual fallback should be called
        mock_manual.assert_called_once()

    def test_skips_llm_when_interface_is_none(self):
        """Should skip LLM retry and go to manual when interface is None."""
        from Writer.Pipeline import apply_final_text_processing

        wall_of_text = "Text without breaks. " * 50
        manual_formatted = "Manual.\n\nFormatted."
        chapter_num = 1
        native_lang = "en"
        logger = MagicMock()

        with patch('Writer.Pipeline.validate_paragraph_breaks') as mock_validate:
            mock_validate.return_value = (False, "Need more paragraphs")

            with patch('Writer.Pipeline._llm_format_paragraphs') as mock_llm:
                with patch('Writer.Pipeline.ensure_paragraph_formatting') as mock_manual:
                    mock_manual.return_value = (manual_formatted, True)

                    with patch('Writer.Pipeline.validate_chapter_editing') as mock_edit:
                        mock_edit.return_value = (True, {})

                        result = apply_final_text_processing(
                            wall_of_text, chapter_num, native_lang, logger, None  # No interface
                        )

        # LLM should NOT be called
        mock_llm.assert_not_called()
        # Manual should be called
        mock_manual.assert_called_once()

    def test_llm_retry_uses_feedback_from_validator(self):
        """Should pass feedback from validator to LLM."""
        from Writer.Pipeline import apply_final_text_processing

        wall_of_text = "Text without breaks."
        feedback = "Need 5 paragraphs minimum"
        chapter_num = 1
        native_lang = "en"
        logger = MagicMock()
        interface = MagicMock()

        with patch('Writer.Pipeline.validate_paragraph_breaks') as mock_validate:
            mock_validate.side_effect = [
                (False, feedback),  # Initial check
                (True, "")  # After LLM formatting
            ]

            with patch('Writer.Pipeline._llm_format_paragraphs') as mock_llm:
                mock_llm.return_value = "Formatted.\n\nText."

                with patch('Writer.Pipeline.validate_chapter_editing') as mock_edit:
                    mock_edit.return_value = (True, {})

                    apply_final_text_processing(
                        wall_of_text, chapter_num, native_lang, logger, interface
                    )

        # Check that feedback was passed to LLM
        call_args = mock_llm.call_args
        assert feedback in str(call_args)


class TestApplyFinalTextProcessing:
    """Tests for apply_final_text_processing function."""

    def test_returns_original_when_paragraphs_valid(self):
        """Should return original text when paragraph breaks are valid."""
        from Writer.Pipeline import apply_final_text_processing

        text = "First paragraph.\n\nSecond paragraph."
        chapter_num = 1
        native_lang = "en"
        logger = MagicMock()

        # Mock validate_paragraph_breaks to return valid
        with patch('Writer.Pipeline.validate_paragraph_breaks') as mock_validate:
            mock_validate.return_value = (True, "Valid paragraphs")

            result = apply_final_text_processing(text, chapter_num, native_lang, logger)

        assert result == text  # No modification needed

    def test_formats_wall_of_text(self):
        """Should format wall of text into paragraphs when validation passes."""
        from Writer.Pipeline import apply_final_text_processing

        wall_of_text = "Text without breaks. " * 20
        formatted_text = "Formatted.\n\nWith breaks."
        chapter_num = 1
        native_lang = "en"
        logger = MagicMock()

        with patch('Writer.Pipeline.validate_paragraph_breaks') as mock_validate:
            mock_validate.return_value = (False, "Wall of text")

            with patch('Writer.Pipeline.ensure_paragraph_formatting') as mock_format:
                mock_format.return_value = (formatted_text, True)

                with patch('Writer.Pipeline.validate_chapter_editing') as mock_edit:
                    mock_edit.return_value = (True, {'content_similarity': 0.95})

                    result = apply_final_text_processing(
                        wall_of_text, chapter_num, native_lang, logger
                    )

        # Should have paragraph breaks now
        assert "\n\n" in result

    def test_keeps_original_when_formatting_causes_content_loss(self):
        """Should keep original text when formatting causes significant content loss."""
        from Writer.Pipeline import apply_final_text_processing

        original_text = "A" * 1000  # Long text
        chapter_num = 1
        native_lang = "en"
        logger = MagicMock()

        # Mock ensure_paragraph_formatting to return truncated text
        with patch('Writer.Pipeline.ensure_paragraph_formatting') as mock_format:
            mock_format.return_value = ("Short", True)  # Truncated result

            # Mock validate_paragraph_breaks to return invalid (to trigger formatting)
            with patch('Writer.Pipeline.validate_paragraph_breaks') as mock_validate:
                mock_validate.return_value = (False, "No paragraphs")

                # Mock validate_chapter_editing to return invalid (content loss)
                with patch('Writer.Pipeline.validate_chapter_editing') as mock_edit_validate:
                    mock_edit_validate.return_value = (False, {'char_ratio': 0.005})

                    result = apply_final_text_processing(
                        original_text, chapter_num, native_lang, logger
                    )

        # Should keep original due to content loss
        assert result == original_text

    def test_accepts_formatting_when_validation_passes(self):
        """Should use formatted text when content validation passes."""
        from Writer.Pipeline import apply_final_text_processing

        original_text = "Wall of text without breaks. " * 20
        formatted_text = "First para.\n\nSecond para.\n\nThird para."
        chapter_num = 1
        native_lang = "en"
        logger = MagicMock()

        with patch('Writer.Pipeline.ensure_paragraph_formatting') as mock_format:
            mock_format.return_value = (formatted_text, True)

            with patch('Writer.Pipeline.validate_paragraph_breaks') as mock_validate:
                mock_validate.return_value = (False, "No paragraphs")

                with patch('Writer.Pipeline.validate_chapter_editing') as mock_edit_validate:
                    mock_edit_validate.return_value = (True, {'char_ratio': 0.95})

                    result = apply_final_text_processing(
                        original_text, chapter_num, native_lang, logger
                    )

        assert result == formatted_text

    def test_logs_when_formatting_applied(self):
        """Should log when paragraph formatting is applied."""
        from Writer.Pipeline import apply_final_text_processing

        wall_of_text = "Text without breaks. " * 20
        formatted_text = "Para one.\n\nPara two."
        chapter_num = 3
        native_lang = "id"
        logger = MagicMock()

        with patch('Writer.Pipeline.ensure_paragraph_formatting') as mock_format:
            mock_format.return_value = (formatted_text, True)

            with patch('Writer.Pipeline.validate_paragraph_breaks') as mock_validate:
                mock_validate.return_value = (False, "Wall of text")

                with patch('Writer.Pipeline.validate_chapter_editing') as mock_edit_validate:
                    mock_edit_validate.return_value = (True, {})

                    apply_final_text_processing(
                        wall_of_text, chapter_num, native_lang, logger
                    )

        # Should have logged the formatting application
        logger.Log.assert_called()

    def test_logs_when_formatting_rejected(self):
        """Should log when formatting is rejected due to content loss."""
        from Writer.Pipeline import apply_final_text_processing

        original_text = "Original content. " * 50
        chapter_num = 2
        native_lang = "en"
        logger = MagicMock()

        with patch('Writer.Pipeline.ensure_paragraph_formatting') as mock_format:
            mock_format.return_value = ("Truncated", True)

            with patch('Writer.Pipeline.validate_paragraph_breaks') as mock_validate:
                mock_validate.return_value = (False, "Wall of text")

                with patch('Writer.Pipeline.validate_chapter_editing') as mock_edit_validate:
                    mock_edit_validate.return_value = (False, {'failure_reasons': ['Too short']})

                    apply_final_text_processing(
                        original_text, chapter_num, native_lang, logger
                    )

        # Should have logged the rejection
        logger.Log.assert_called()


class TestGetFullStoryTextPipelineVersionWithProcessing:
    """Tests for _get_full_story_text_pipeline_version with final processing."""

    def test_processes_each_chapter_text(self):
        """Should apply final processing to each chapter when logger provided."""
        from Writer.Pipeline import _get_full_story_text_pipeline_version

        chapters_data = [
            {"number": 1, "title": "Chapter 1", "text": "Chapter one content."},
            {"number": 2, "title": "Chapter 2", "text": "Chapter two content."},
        ]

        # Create mock config
        mock_config = MagicMock()
        mock_config.CHAPTER_HEADER_FORMAT = "## {chapter_title}"
        mock_config.DEFAULT_CHAPTER_TITLE_PREFIX = "Chapter "
        mock_config.NATIVE_LANGUAGE = "en"

        # Create mock logger and interface
        mock_logger = MagicMock()
        mock_interface = MagicMock()

        with patch('Writer.Pipeline.apply_final_text_processing') as mock_process:
            # Return text unchanged (5 params now: text, chapter_num, lang, logger, interface)
            mock_process.side_effect = lambda t, n, l, log, iface: t

            _get_full_story_text_pipeline_version(
                chapters_data, mock_config, True, mock_logger, mock_interface
            )

        # Should have called processing for each chapter
        assert mock_process.call_count == 2

    def test_uses_processed_text_in_output(self):
        """Should use processed text in final output."""
        from Writer.Pipeline import _get_full_story_text_pipeline_version

        chapters_data = [
            {"number": 1, "title": "Chapter 1", "text": "Wall of text no breaks"},
        ]

        mock_config = MagicMock()
        mock_config.CHAPTER_HEADER_FORMAT = "## {chapter_title}"
        mock_config.DEFAULT_CHAPTER_TITLE_PREFIX = "Chapter "
        mock_config.NATIVE_LANGUAGE = "en"
        mock_logger = MagicMock()

        processed_text = "Formatted.\n\nWith breaks."

        with patch('Writer.Pipeline.apply_final_text_processing') as mock_process:
            mock_process.return_value = processed_text

            result = _get_full_story_text_pipeline_version(
                chapters_data, mock_config, True, mock_logger
            )

        assert processed_text in result

    def test_skips_processing_when_no_logger(self):
        """Should skip processing when logger is None."""
        from Writer.Pipeline import _get_full_story_text_pipeline_version

        chapters_data = [
            {"number": 1, "title": "Chapter 1", "text": "Chapter content."},
        ]

        mock_config = MagicMock()
        mock_config.CHAPTER_HEADER_FORMAT = "## {chapter_title}"
        mock_config.DEFAULT_CHAPTER_TITLE_PREFIX = "Chapter "
        mock_config.NATIVE_LANGUAGE = "en"

        with patch('Writer.Pipeline.apply_final_text_processing') as mock_process:
            _get_full_story_text_pipeline_version(
                chapters_data, mock_config, True, None  # No logger
            )

        # Should NOT have called processing
        assert mock_process.call_count == 0
