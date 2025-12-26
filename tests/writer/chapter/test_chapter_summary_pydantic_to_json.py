"""
Tests for ChapterGenerator chapter summary generation fix.

Tests the conversion from SafeGeneratePydantic(ChapterOutput) to SafeGenerateJSON
for chapter summary generation in _prepare_initial_generation_context.

Follows TDD London School methodology with mocked dependencies.
Tests SafeGenerateJSON pattern with fallback extraction for chapter summaries.
"""
import pytest
from unittest.mock import Mock, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


@pytest.fixture
def mock_config():
    """Factory for creating mock Config module with required attributes"""
    def _create_mock_config():
        mock_cfg = MagicMock(name='mock_config')
        mock_cfg.CHAPTER_STAGE1_WRITER_MODEL = "ollama://test-model"
        mock_cfg.CHAPTER_MAX_REVISIONS = 3
        mock_cfg.SEED = 42
        return mock_cfg
    return _create_mock_config


class TestChapterSummaryGeneration:
    """Test main functionality of chapter summary generation using SafeGenerateJSON"""

    def test_chapter_summary_uses_safe_generate_json_not_pydantic(
        self, mock_interface, mock_logger, mock_config
    ):
        """Test that chapter summary calls SafeGenerateJSON (not SafeGeneratePydantic)"""
        from Writer.Chapter.ChapterGenerator import _prepare_initial_generation_context
        from Writer.PromptsHelper import get_prompts

        # Arrange
        ActivePrompts = get_prompts()
        chapters = [
            {"text": "Chapter 1 content about dragons and treasure hunts..."},
        ]
        outline = "Story outline with multiple chapters..."

        mock_int = mock_interface()
        mock_log = mock_logger()
        mock_cfg = mock_config()

        # Configure mocks
        # For chapter outline extraction
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant', 'content': '{"text": "..."}'}],
            Mock(text="extracted chapter outline"),
            {'prompt_tokens': 100, 'completion_tokens': 20}
        )

        # For chapter summary (should be SafeGenerateJSON, not SafeGeneratePydantic!)
        mock_int.SafeGenerateJSON.return_value = (
            [{'role': 'assistant', 'content': '{"summary": "chapter 1 summary"}'}],
            {"summary": "Chapter 1 ended with finding the cave"},
            {'prompt_tokens': 150, 'completion_tokens': 30}
        )

        # Act - generating Chapter 2, with Chapter 1 completed
        (message_history, context_history, this_outline,
         formatted_summary, detailed_outline) = _prepare_initial_generation_context(
            mock_int, mock_log, ActivePrompts, outline, chapters, 2, 5, mock_cfg
        )

        # Assert
        # Should call SafeGenerateJSON for summary
        assert mock_int.SafeGenerateJSON.call_count == 1

        # Should NOT call SafeGeneratePydantic for summary
        pydantic_calls = mock_int.SafeGeneratePydantic.call_args_list
        # The only SafeGeneratePydantic call should be for chapter outline, not summary
        assert len(pydantic_calls) == 1
        # Verify the call was for chapter outline (ChapterOutput with first param being messages)
        args, kwargs = pydantic_calls[0]
        # SafeGeneratePydantic call: (_Logger, messages, model, ChapterOutput)
        # Third positional arg (index 2) is the model string
        assert len(args) >= 4
        assert args[0] == mock_log  # First arg is logger
        # Fourth positional arg (index 3) should be ChapterOutput class
        assert "ChapterOutput" in str(args[3])

        # Verify SafeGenerateJSON was called with correct parameters for summary
        json_call_args = mock_int.SafeGenerateJSON.call_args_list[0]
        json_args, json_kwargs = json_call_args
        assert len(json_args) == 3  # log, messages, model
        assert json_args[0] == mock_log
        # Second arg is messages list containing SYSTEM and USER messages
        assert isinstance(json_args[1], list)
        # Third arg is model string
        assert json_args[2] == mock_cfg.CHAPTER_STAGE1_WRITER_MODEL

    def test_summary_extraction_with_summary_field(self, mock_interface, mock_logger, mock_config):
        """Test summary extraction handles 'summary' field correctly"""
        from Writer.Chapter.ChapterGenerator import _prepare_initial_generation_context
        from Writer.PromptsHelper import get_prompts

        # Arrange
        ActivePrompts = get_prompts()
        chapters = [{"text": "Chapter 1 content..."}]
        outline = "Story outline..."

        mock_int = mock_interface()
        mock_log = mock_logger()
        mock_cfg = mock_config()

        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            Mock(text="chapter outline"),
            {}
        )

        # SafeGenerateJSON returns {'summary': '...'}
        mock_int.SafeGenerateJSON.return_value = (
            [{'role': 'assistant'}],
            {"summary": "Arka found the dragon's cave"},
            {}
        )

        # Act
        _, _, _, formatted_summary, _ = _prepare_initial_generation_context(
            mock_int, mock_log, ActivePrompts, outline, chapters, 2, 2, mock_cfg
        )

        # Assert
        assert "Arka found the dragon's cave" in formatted_summary

    def test_summary_extraction_with_text_field(self, mock_interface, mock_logger, mock_config):
        """Test summary extraction handles 'text' field correctly"""
        from Writer.Chapter.ChapterGenerator import _prepare_initial_generation_context
        from Writer.PromptsHelper import get_prompts

        # Arrange
        ActivePrompts = get_prompts()
        chapters = [{"text": "Chapter 1 content..."}]
        outline = "Story outline..."

        mock_int = mock_interface()
        mock_log = mock_logger()
        mock_cfg = mock_config()

        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            Mock(text="chapter outline"),
            {}
        )

        # SafeGenerateJSON returns {'text': '...'}
        mock_int.SafeGenerateJSON.return_value = (
            [{'role': 'assistant'}],
            {"text": "The adventure begins in the cave"},
            {}
        )

        # Act
        _, _, _, formatted_summary, _ = _prepare_initial_generation_context(
            mock_int, mock_log, ActivePrompts, outline, chapters, 2, 2, mock_cfg
        )

        # Assert
        assert "The adventure begins in the cave" in formatted_summary

    def test_summary_extraction_fallback_for_gemma_style(self, mock_interface, mock_logger, mock_config):
        """Test summary extraction handles Gemma-style structured JSON"""
        from Writer.Chapter.ChapterGenerator import _prepare_initial_generation_context
        from Writer.PromptsHelper import get_prompts

        # Arrange
        ActivePrompts = get_prompts()
        chapters = [{"text": "Chapter 1 content..."}]
        outline = "Story outline..."

        mock_int = mock_interface()
        mock_log = mock_logger()
        mock_cfg = mock_config()

        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            Mock(text="chapter outline"),
            {}
        )

        # SafeGenerateJSON returns Gemma-style: {"Bab Sebelumnya": {...}}
        gemma_style_response = {
            "Bab Sebelumnya": {
                "Plot": ["Arka menemukan gua", "bertemu naga hijau"],
                "Latar": ["Hutan Cinder", "Gua Naga"]
            },
            "Hal yang Perlu Diingat": ["Arka terluka", "naga skeptis"]
        }
        mock_int.SafeGenerateJSON.return_value = (
            [{'role': 'assistant'}],
            gemma_style_response,
            {}
        )

        # Act
        _, _, _, formatted_summary, _ = _prepare_initial_generation_context(
            mock_int, mock_log, ActivePrompts, outline, chapters, 2, 2, mock_cfg
        )

        # Assert - should format structured data
        assert formatted_summary
        assert len(formatted_summary) > 0

    def test_no_summary_when_no_previous_chapter(self, mock_interface, mock_logger, mock_config):
        """Test that no summary is generated when there are no previous chapters"""
        from Writer.Chapter.ChapterGenerator import _prepare_initial_generation_context
        from Writer.PromptsHelper import get_prompts

        # Arrange
        ActivePrompts = get_prompts()
        chapters = []  # Empty - no previous chapters
        outline = "Story outline..."

        mock_int = mock_interface()
        mock_log = mock_logger()
        mock_cfg = mock_config()

        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            Mock(text="chapter outline"),
            {}
        )

        # Act
        _, _, _, formatted_summary, _ = _prepare_initial_generation_context(
            mock_int, mock_log, ActivePrompts, outline, chapters, 1, 1, mock_cfg
        )

        # Assert
        assert formatted_summary == ""
        assert mock_int.SafeGenerateJSON.call_count == 0


class TestPromptUnambiguousFormats:
    """Test that prompts are unambiguous and specify JSON output clearly"""

    def test_prompt_specifies_json_format_english(self):
        """Test English prompt clearly specifies JSON format"""
        from Writer.Prompts import CHAPTER_SUMMARY_PROMPT

        # Assert - prompt contains JSON format specification
        assert "JSON" in CHAPTER_SUMMARY_PROMPT.upper()
        assert "summary" in CHAPTER_SUMMARY_PROMPT.lower()
        assert "previous_chapter_number" in CHAPTER_SUMMARY_PROMPT
        assert "key_points" in CHAPTER_SUMMARY_PROMPT

    def test_prompt_specifies_json_format_indonesian(self):
        """Test Indonesian prompt clearly specifies JSON format"""
        from Writer.Prompts_id import CHAPTER_SUMMARY_PROMPT

        # Assert - prompt contains JSON format specification
        assert "JSON" in CHAPTER_SUMMARY_PROMPT.upper()
        assert ("summary" in CHAPTER_SUMMARY_PROMPT.lower() or
                "Ringkasan" in CHAPTER_SUMMARY_PROMPT)
        assert "previous_chapter_number" in CHAPTER_SUMMARY_PROMPT
        assert "key_points" in CHAPTER_SUMMARY_PROMPT

    def test_prompt_requires_only_json_no_other_text(self):
        """Test prompt emphasizes JSON-only output (no extra text)"""
        from Writer.Prompts import CHAPTER_SUMMARY_PROMPT

        # Assert - prompt emphasizes JSON-only output
        assert "ONLY" in CHAPTER_SUMMARY_PROMPT
        assert "JSON" in CHAPTER_SUMMARY_PROMPT
        assert "no other text" in CHAPTER_SUMMARY_PROMPT.lower()


class TestCrossLanguageSupport:
    """Test both English and Indonesian prompts work correctly"""

    def test_english_prompt_generates_valid_summary(self, mock_interface, mock_logger, mock_config):
        """Test English prompt produces valid summary output"""
        from Writer.Chapter.ChapterGenerator import _prepare_initial_generation_context
        from Writer.Prompts import CHAPTER_SUMMARY_INTRO, CHAPTER_SUMMARY_PROMPT

        # Arrange - manually create English prompts
        ActivePrompts = Mock()
        ActivePrompts.CHAPTER_SUMMARY_INTRO = CHAPTER_SUMMARY_INTRO
        ActivePrompts.CHAPTER_SUMMARY_PROMPT = CHAPTER_SUMMARY_PROMPT
        ActivePrompts.CHAPTER_GENERATION_INTRO = "You are a novel writer"
        ActivePrompts.CHAPTER_GENERATION_PROMPT = "Write chapter {_ChapterNum}"
        ActivePrompts.CHAPTER_HISTORY_INSERT = "Outline: {_Outline}"

        chapters = [{"text": "Chapter 1: The dragon sleeps..."}]
        outline = "Epic fantasy story..."

        mock_int = mock_interface()
        mock_log = mock_logger()
        mock_cfg = mock_config()

        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            Mock(text="chapter 1 outline"),
            {}
        )

        mock_int.SafeGenerateJSON.return_value = (
            [{'role': 'assistant'}],
            {"summary": "A brave knight found a sleeping dragon"},
            {}
        )

        # Act - should work with English prompts
        _, _, _, formatted_summary, _ = _prepare_initial_generation_context(
            mock_int, mock_log, ActivePrompts, outline, chapters, 2, 2, mock_cfg
        )

        # Assert
        assert "A brave knight found a sleeping dragon" in formatted_summary

    def test_indonesian_prompt_generates_valid_summary(self, mock_interface, mock_logger, mock_config):
        """Test Indonesian prompt produces valid summary output"""
        from Writer.Chapter.ChapterGenerator import _prepare_initial_generation_context
        from Writer.Prompts import CHAPTER_SUMMARY_INTRO  # Use common INTRO for both languages
        from Writer.Prompts_id import CHAPTER_SUMMARY_PROMPT

        # Arrange - manually create Indonesian prompts
        ActivePrompts = Mock()
        ActivePrompts.CHAPTER_SUMMARY_INTRO = CHAPTER_SUMMARY_INTRO
        ActivePrompts.CHAPTER_SUMMARY_PROMPT = CHAPTER_SUMMARY_PROMPT
        ActivePrompts.CHAPTER_GENERATION_INTRO = "Anda adalah penulis novel"
        ActivePrompts.CHAPTER_GENERATION_PROMPT = "Tulis bab {_ChapterNum}"
        ActivePrompts.CHAPTER_HISTORY_INSERT = "Outline: {_Outline}"

        chapters = [{"text": "Bab 1: Naga tidur..."}]
        outline = "Cerita fantasi epik..."

        mock_int = mock_interface()
        mock_log = mock_logger()
        mock_cfg = mock_config()

        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            Mock(text="outline bab 1"),
            {}
        )

        mock_int.SafeGenerateJSON.return_value = (
            [{'role': 'assistant'}],
            {"summary": "Seorang ksatria berani menemukan naga yang tidur"},
            {}
        )

        # Act
        _, _, _, formatted_summary, _ = _prepare_initial_generation_context(
            mock_int, mock_log, ActivePrompts, outline, chapters, 2, 2, mock_cfg
        )

        # Assert
        assert "Seorang ksatria berani menemukan naga yang tidur" in formatted_summary


class TestBackwardCompatibility:
    """Test backward compatibility with existing functionality"""

    def test_formatted_last_chapter_summary_integration(self, mock_interface, mock_logger, mock_config):
        """Test FormattedLastChapterSummary integrates correctly with chapter generation"""
        from Writer.Chapter.ChapterGenerator import _prepare_initial_generation_context
        from Writer.PromptsHelper import get_prompts

        # Arrange
        ActivePrompts = get_prompts()
        chapters = [{"text": "Chapter 1: The cave entrance..."}]
        outline = "Adventure story... Chapter 1 finds the dragon, Chapter 2 enters cave"

        mock_int = mock_interface()
        mock_log = mock_logger()
        mock_cfg = mock_config()

        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            Mock(text="Chapter 2 outline"),
            {}
        )

        mock_int.SafeGenerateJSON.return_value = (
            [{'role': 'assistant'}],
            {"summary": "Chapter 1 ended at the cave entrance"},
            {}
        )

        # Act
        (outline_result, context_result, this_outline,
         summary_result, detailed_outline) = _prepare_initial_generation_context(
            mock_int, mock_log, ActivePrompts, outline, chapters, 2, 2, mock_cfg
        )

        # Assert
        assert outline_result is not None
        assert summary_result is not None
        assert "cave entrance" in summary_result

    def test_multiple_chapters_uses_last_chapter_summary(self, mock_interface, mock_logger, mock_config):
        """Test that with multiple chapters, only the last chapter is summarized"""
        from Writer.Chapter.ChapterGenerator import _prepare_initial_generation_context
        from Writer.PromptsHelper import get_prompts

        # Arrange
        ActivePrompts = get_prompts()
        chapters = [
            {"text": "Chapter 1: Finding the map..."},
            {"text": "Chapter 2: Reaching the cave..."},
            {"text": "Chapter 3: Entering the darkness..."},
        ]
        outline = "Adventure story with 5 chapters..."

        mock_int = mock_interface()
        mock_log = mock_logger()
        mock_cfg = mock_config()

        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            Mock(text="Chapter 4 outline"),
            {}
        )

        mock_int.SafeGenerateJSON.return_value = (
            [{'role': 'assistant'}],
            {"summary": "Chapter 3 ended in total darkness"},
            {}
        )

        # Act - requesting summary for chapter 4
        _, _, _, formatted_summary, _ = _prepare_initial_generation_context(
            mock_int, mock_log, ActivePrompts, outline, chapters, 4, 5, mock_cfg
        )

        # Assert - should summarize Chapter 3 (last chapter), not all chapters
        assert "Chapter 3" in formatted_summary
        assert "darkness" in formatted_summary


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_empty_json_response_returns_empty_string(self, mock_interface, mock_logger, mock_config):
        """Test that empty JSON response returns empty summary string"""
        from Writer.Chapter.ChapterGenerator import _prepare_initial_generation_context
        from Writer.PromptsHelper import get_prompts

        # Arrange
        ActivePrompts = get_prompts()
        chapters = [{"text": "Chapter 1..."}]
        outline = "Story..."

        mock_int = mock_interface()
        mock_log = mock_logger()
        mock_cfg = mock_config()

        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            Mock(text="outline"),
            {}
        )

        # Empty JSON response
        mock_int.SafeGenerateJSON.return_value = (
            [{'role': 'assistant'}],
            {},
            {}
        )

        # Act
        _, _, _, formatted_summary, _ = _prepare_initial_generation_context(
            mock_int, mock_log, ActivePrompts, outline, chapters, 2, 2, mock_cfg
        )

        # Assert
        assert formatted_summary == ""

    def test_missing_expected_fields_uses_fallback(self, mock_interface, mock_logger, mock_config):
        """Test that missing expected fields triggers fallback extraction"""
        from Writer.Chapter.ChapterGenerator import _prepare_initial_generation_context
        from Writer.PromptsHelper import get_prompts

        # Arrange
        ActivePrompts = get_prompts()
        chapters = [{"text": "Chapter 1..."}]
        outline = "Story..."

        mock_int = mock_interface()
        mock_log = mock_logger()
        mock_cfg = mock_config()

        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            Mock(text="outline"),
            {}
        )

        # Response without 'summary' or 'text' fields, but has other string field
        mock_int.SafeGenerateJSON.return_value = (
            [{'role': 'assistant'}],
            {"unexpected_field": "The chapter ended in a mysterious cave"},
            {}
        )

        # Act
        _, _, _, formatted_summary, _ = _prepare_initial_generation_context(
            mock_int, mock_log, ActivePrompts, outline, chapters, 2, 2, mock_cfg
        )

        # Assert - should use fallback to find any string field
        assert "mysterious cave" in formatted_summary

    def test_invalid_nested_structure_handled_gracefully(self, mock_interface, mock_logger, mock_config):
        """Test that invalid nested structure doesn't crash but returns empty or partial"""
        from Writer.Chapter.ChapterGenerator import _prepare_initial_generation_context
        from Writer.PromptsHelper import get_prompts

        # Arrange
        ActivePrompts = get_prompts()
        chapters = [{"text": "Chapter 1..."}]
        outline = "Story..."

        mock_int = mock_interface()
        mock_log = mock_logger()
        mock_cfg = mock_config()

        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            Mock(text="outline"),
            {}
        )

        # Response with unusual structure
        mock_int.SafeGenerateJSON.return_value = (
            [{'role': 'assistant'}],
            {"random_key": 123, "another_key": None},
            {}
        )

        # Act - should not crash
        _, _, _, formatted_summary, _ = _prepare_initial_generation_context(
            mock_int, mock_log, ActivePrompts, outline, chapters, 2, 2, mock_cfg
        )

        # Assert - should return empty or handle gracefully
        assert isinstance(formatted_summary, str)
