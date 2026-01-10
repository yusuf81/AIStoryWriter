"""Test chapter revision validation with word count reduction check."""

from unittest.mock import Mock, patch
from Writer.Chapter.ChapterGenerator import ReviseChapter
from Writer.Models import ChapterOutput


class TestChapterRevisionValidation:
    """Test that revision validates word count reduction."""

    @patch('Writer.PromptsHelper.get_prompts')
    def test_revision_accepts_minor_reduction_under_20_percent(self, mock_get_prompts, mock_interface, mock_logger):
        """Revision should succeed if word count reduction < 20%."""
        mock_prompts = Mock()
        mock_prompts.CHAPTER_REVISION = "Revise: {_Chapter} with {_Feedback}"
        mock_get_prompts.return_value = mock_prompts

        interface = mock_interface()
        logger = mock_logger()

        # Original: 500 words, Revised: 420 words (16% reduction - acceptable)
        mock_response = ChapterOutput(
            text="Word " * 420,
            chapter_number=1,
            chapter_title=None
        )

        # Mock SafeGeneratePydantic to return our response
        interface.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant', 'content': '{"text": "revised"}'}],
            mock_response,
            {'prompt_tokens': 100, 'completion_tokens': 100}
        )

        revised_text, _ = ReviseChapter(
            Interface=interface,
            _Logger=logger,
            _ChapterNum=1,
            _TotalChapters=2,
            _Chapter="Word " * 500,
            _Feedback="Improve quality",
            _History=[],
            _Iteration=0
        )

        # Should succeed without retry
        assert interface.SafeGeneratePydantic.call_count == 1
        assert len(revised_text.split()) == 420

    @patch('Writer.PromptsHelper.get_prompts')
    def test_revision_retries_on_excessive_reduction_over_20_percent(self, mock_get_prompts, mock_interface, mock_logger):
        """Revision should retry if word count reduction > 20%."""
        mock_prompts = Mock()
        mock_prompts.CHAPTER_REVISION = "Revise: {_Chapter} with {_Feedback}"
        mock_prompts.CHAPTER_REVISION_STRICT = "STRICT: Preserve all content! {_Chapter} {_Feedback}"
        mock_get_prompts.return_value = mock_prompts

        interface = mock_interface()
        logger = mock_logger()

        # First attempt: 500 -> 100 words (80% reduction - too much!)
        # Second attempt: 500 -> 450 words (10% reduction - acceptable)
        mock_response_1 = ChapterOutput(text="Word " * 100, chapter_number=1, chapter_title=None)
        mock_response_2 = ChapterOutput(text="Word " * 450, chapter_number=1, chapter_title=None)

        # Mock SafeGeneratePydantic to return different responses on each call
        interface.SafeGeneratePydantic.side_effect = [
            (
                [{'role': 'assistant', 'content': '{"text": "revised"}'}],
                mock_response_1,
                {'prompt_tokens': 100, 'completion_tokens': 100}
            ),
            (
                [{'role': 'assistant', 'content': '{"text": "revised"}'}],
                mock_response_2,
                {'prompt_tokens': 100, 'completion_tokens': 100}
            )
        ]

        revised_text, _ = ReviseChapter(
            Interface=interface,
            _Logger=logger,
            _ChapterNum=1,
            _TotalChapters=2,
            _Chapter="Word " * 500,
            _Feedback="Improve quality",
            _History=[],
            _Iteration=0
        )

        # Should retry once (total 2 calls)
        assert interface.SafeGeneratePydantic.call_count == 2
        assert len(revised_text.split()) == 450

    @patch('Writer.PromptsHelper.get_prompts')
    def test_revision_retries_up_to_3_times_with_strict_prompt(self, mock_get_prompts, mock_interface, mock_logger):
        """Should retry up to 3 times with strict prompt before giving up."""
        mock_prompts = Mock()
        mock_prompts.CHAPTER_REVISION = "Revise: {_Chapter} with {_Feedback}"
        mock_prompts.CHAPTER_REVISION_STRICT = "STRICT: Preserve! {_Chapter} {_Feedback}"
        mock_get_prompts.return_value = mock_prompts

        interface = mock_interface()
        logger = mock_logger()

        # All attempts return bad output (80% reduction)
        bad_response = ChapterOutput(text="Word " * 100, chapter_number=1, chapter_title=None)

        interface.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant', 'content': '{"text": "revised"}'}],
            bad_response,
            {'prompt_tokens': 100, 'completion_tokens': 100}
        )

        revised_text, _ = ReviseChapter(
            Interface=interface,
            _Logger=logger,
            _ChapterNum=1,
            _TotalChapters=2,
            _Chapter="Word " * 500,
            _Feedback="Improve quality",
            _History=[],
            _Iteration=0
        )

        # Should call: 1 initial + 3 strict attempts (0, 1, 2) = 4 total calls
        assert interface.SafeGeneratePydantic.call_count == 4

        # Should fall back to original content (500 words)
        assert len(revised_text.split()) == 500

    @patch('Writer.PromptsHelper.get_prompts')
    def test_revision_logs_each_retry_attempt(self, mock_get_prompts, mock_interface, mock_logger):
        """Should log each strict prompt retry attempt."""
        mock_prompts = Mock()
        mock_prompts.CHAPTER_REVISION = "Revise: {_Chapter} with {_Feedback}"
        mock_prompts.CHAPTER_REVISION_STRICT = "STRICT: Preserve! {_Chapter} {_Feedback}"
        mock_get_prompts.return_value = mock_prompts

        interface = mock_interface()
        logger = mock_logger()

        # All attempts return bad output (80% reduction)
        bad_response = ChapterOutput(text="Word " * 100, chapter_number=1, chapter_title=None)

        interface.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant', 'content': '{"text": "revised"}'}],
            bad_response,
            {'prompt_tokens': 100, 'completion_tokens': 100}
        )

        ReviseChapter(
            Interface=interface,
            _Logger=logger,
            _ChapterNum=1,
            _TotalChapters=2,
            _Chapter="Word " * 500,
            _Feedback="Improve quality",
            _History=[],
            _Iteration=0
        )

        # Check logs contain retry messages (3 total retries, shown as 1/3, 2/3)
        log_messages = [str(msg) for _, msg in logger.logs]
        assert any("Strict prompt retry 1/3" in msg for msg in log_messages)
        assert any("Strict prompt retry 2/3" in msg for msg in log_messages)
        assert any("Falling back to original chapter content" in msg for msg in log_messages)

    @patch('Writer.PromptsHelper.get_prompts')
    def test_second_retry_succeeds_returns_improved_content(self, mock_get_prompts, mock_interface, mock_logger):
        """If second retry succeeds, should return improved content not original."""
        mock_prompts = Mock()
        mock_prompts.CHAPTER_REVISION = "Revise: {_Chapter} with {_Feedback}"
        mock_prompts.CHAPTER_REVISION_STRICT = "STRICT: Preserve! {_Chapter} {_Feedback}"
        mock_get_prompts.return_value = mock_prompts

        interface = mock_interface()
        logger = mock_logger()

        # First: bad (80% reduction), Second: bad (80%), Third: good (10% reduction)
        bad_response = ChapterOutput(text="Word " * 100, chapter_number=1, chapter_title=None)
        good_response = ChapterOutput(text="Word " * 450, chapter_number=1, chapter_title=None)

        interface.SafeGeneratePydantic.side_effect = [
            # Initial attempt - bad
            (
                [{'role': 'assistant', 'content': '{"text": "revised"}'}],
                bad_response,
                {'prompt_tokens': 100, 'completion_tokens': 100}
            ),
            # Strict retry 1 - bad
            (
                [{'role': 'assistant', 'content': '{"text": "revised"}'}],
                bad_response,
                {'prompt_tokens': 100, 'completion_tokens': 100}
            ),
            # Strict retry 2 - good!
            (
                [{'role': 'assistant', 'content': '{"text": "revised"}'}],
                good_response,
                {'prompt_tokens': 100, 'completion_tokens': 100}
            )
        ]

        revised_text, _ = ReviseChapter(
            Interface=interface,
            _Logger=logger,
            _ChapterNum=1,
            _TotalChapters=2,
            _Chapter="Word " * 500,
            _Feedback="Improve quality",
            _History=[],
            _Iteration=0
        )

        # Should call 3 times: initial + 2 strict retries (third retry not needed)
        assert interface.SafeGeneratePydantic.call_count == 3

        # Should return the improved content (450 words), not original (500)
        assert len(revised_text.split()) == 450

    @patch('Writer.PromptsHelper.get_prompts')
    def test_revision_logs_reduction_warning(self, mock_get_prompts, mock_interface, mock_logger):
        """Should log warning when reduction exceeds threshold."""
        mock_prompts = Mock()
        mock_prompts.CHAPTER_REVISION = "Revise: {_Chapter} with {_Feedback}"
        mock_prompts.CHAPTER_REVISION_STRICT = "STRICT: Preserve all content! {_Chapter} {_Feedback}"
        mock_get_prompts.return_value = mock_prompts

        interface = mock_interface()
        logger = mock_logger()

        # First attempt: excessive reduction (500 -> 100 = 80%)
        # Second attempt: acceptable (500 -> 450 = 10%)
        mock_response_1 = ChapterOutput(text="Word " * 100, chapter_number=1, chapter_title=None)
        mock_response_2 = ChapterOutput(text="Word " * 450, chapter_number=1, chapter_title=None)

        interface.SafeGeneratePydantic.side_effect = [
            (
                [{'role': 'assistant', 'content': '{"text": "revised"}'}],
                mock_response_1,
                {'prompt_tokens': 100, 'completion_tokens': 100}
            ),
            (
                [{'role': 'assistant', 'content': '{"text": "revised"}'}],
                mock_response_2,
                {'prompt_tokens': 100, 'completion_tokens': 100}
            )
        ]

        ReviseChapter(
            Interface=interface,
            _Logger=logger,
            _ChapterNum=1,
            _TotalChapters=2,
            _Chapter="Word " * 500,
            _Feedback="Improve quality",
            _History=[],
            _Iteration=0
        )

        # Should log warning about excessive reduction
        log_messages = [str(msg) for _, msg in logger.logs]
        assert any("Warning: Word count reduction" in msg for msg in log_messages)
        assert any("80.0%" in msg for msg in log_messages)
