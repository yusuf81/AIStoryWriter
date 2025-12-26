"""
Tests for ChapterGenSummaryCheck module.

Tests summary generation and quality checking functionality.
Follows TDD London School methodology with mocked dependencies.
Tests SafeGenerateJSON pattern for summary generation.
"""
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TestLLMSummaryCheckLengthValidation:
    """Test length validation early return for < 100 words"""

    def test_length_less_than_100_words_returns_false(self, mock_interface, mock_logger):
        """Test that work with < 100 words returns False with empty result"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange: Work with less than 100 words
        short_work = ' '.join(['word'] * 50)  # 50 words
        mock_log = mock_logger()

        # Act
        result, suggestions = LLMSummaryCheck(
            mock_interface(), mock_log, "outline_text", short_work
        )

        # Assert
        assert result is False
        assert suggestions == ""
        mock_log.Log.assert_called_with(
            "Previous response didn't meet the length requirement, so it probably tried to cheat around writing.",
            7,
        )

    def test_length_exactly_100_words_continues(self, mock_interface, mock_logger):
        """Test that work with exactly 100 words continues processing"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange: Work with exactly 100 words
        hundred_words = ' '.join(['word'] * 100)

        # Configure mocks for successful summary generation
        mock_int = mock_interface()
        mock_log = mock_logger()

        mock_int.SafeGenerateJSON.side_effect = [
            # First call: work summary
            (
                [{'role': 'assistant', 'content': '{"summary": "work summary"}'}],
                {'summary': 'work summary for the chapter content'},
                {'prompt_tokens': 100, 'completion_tokens': 20}
            ),
            # Second call: outline summary
            (
                [{'role': 'assistant', 'content': '{"summary": "outline summary"}'}],
                {'summary': 'outline summary for the chapter'},
                {'prompt_tokens': 50, 'completion_tokens': 10}
            ),
        ]

        # Configure SafeGeneratePydantic to return proper object
        comparison_result = Mock()
        comparison_result.Suggestions = ""
        comparison_result.DidFollowOutline = True
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            comparison_result,
            {'prompt_tokens': 30, 'completion_tokens': 10}
        )

        # Act - should continue past length check
        result, suggestions = LLMSummaryCheck(
            mock_int, mock_log, "outline_text", hundred_words
        )

        # Assert - should have called SafeGenerateJSON (not returned early)
        assert mock_int.SafeGenerateJSON.call_count == 2
        assert result is True
        assert "Extra Suggestions:" in suggestions


class TestLLMSummaryCheckWorkSummary:
    """Test work summary generation with SafeGenerateJSON"""

    def test_work_summary_generation_uses_safe_generate_json(self, mock_interface, mock_logger):
        """Test that work summary uses SafeGenerateJSON (not SafeGeneratePydantic)"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange
        work_text = ' '.join(['word'] * 150)  # 150 words
        outline_text = "unique outline text 123"  # unique to avoid cache

        mock_int = mock_interface()
        mock_log = mock_logger()

        mock_int.SafeGenerateJSON.side_effect = [
            # Work summary
            (
                [{'role': 'assistant', 'content': '{"summary": "work summary"}'}],
                {'summary': 'This is a summary of the work chapter content'},
                {'prompt_tokens': 100, 'completion_tokens': 20}
            ),
            # Outline summary
            (
                [{'role': 'assistant', 'content': '{"summary": "outline summary"}'}],
                {'summary': 'outline summary'},
                {'prompt_tokens': 50, 'completion_tokens': 10}
            ),
        ]

        comparison_result = Mock()
        comparison_result.Suggestions = ""
        comparison_result.DidFollowOutline = True
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            comparison_result,
            {'prompt_tokens': 30, 'completion_tokens': 10}
        )

        # Act
        result, _ = LLMSummaryCheck(mock_int, mock_log, outline_text, work_text)

        # Assert
        assert mock_int.SafeGenerateJSON.call_count == 2
        # First call should be for work summary
        first_call_args = mock_int.SafeGenerateJSON.call_args_list[0]
        assert first_call_args[0][0] == mock_log  # logger
        assert first_call_args[0][1]  # messages list
        assert first_call_args[0][2]  # model

    def test_work_summary_extraction_from_json(self, mock_interface, mock_logger):
        """Test that summary is extracted from JSON response correctly"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange
        work_text = ' '.join(['word'] * 150)

        mock_int = mock_interface()
        mock_log = mock_logger()

        summary_text = "This is the expected summary of the chapter work"
        mock_int.SafeGenerateJSON.side_effect = [
            (
                [{'role': 'assistant'}],
                {'summary': summary_text},
                {'prompt_tokens': 100, 'completion_tokens': 20}
            ),
            (
                [{'role': 'assistant'}],
                {'summary': 'outline summary'},
                {'prompt_tokens': 50, 'completion_tokens': 10}
            ),
        ]

        comparison_result = Mock()
        comparison_result.Suggestions = ""
        comparison_result.DidFollowOutline = True
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            comparison_result,
            {'prompt_tokens': 30, 'completion_tokens': 10}
        )

        # Act
        result, _ = LLMSummaryCheck(mock_int, mock_log, "outline_text", work_text)

        # Assert - should complete successfully
        assert result is True

    def test_work_summary_fallback_to_text_field(self, mock_interface, mock_logger):
        """Test that if 'summary' field missing, falls back to 'text' field"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange
        work_text = ' '.join(['word'] * 150)

        mock_int = mock_interface()
        mock_log = mock_logger()

        # LLM returns 'text' field instead of 'summary'
        mock_int.SafeGenerateJSON.side_effect = [
            (
                [{'role': 'assistant'}],
                {'text': 'summary from text field'},  # 'summary' missing
                {'prompt_tokens': 100, 'completion_tokens': 20}
            ),
            (
                [{'role': 'assistant'}],
                {'summary': 'outline summary'},
                {'prompt_tokens': 50, 'completion_tokens': 10}
            ),
        ]

        comparison_result = Mock()
        comparison_result.Suggestions = ""
        comparison_result.DidFollowOutline = True
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            comparison_result,
            {'prompt_tokens': 30, 'completion_tokens': 10}
        )

        # Act
        result, _ = LLMSummaryCheck(mock_int, mock_log, "outline_text", work_text)

        # Assert - should handle gracefully
        assert result is True

    def test_work_summary_generates_log_messages(self, mock_interface, mock_logger):
        """Test that log messages are generated during work summary"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange
        work_text = ' '.join(['word'] * 150)

        mock_int = mock_interface()
        mock_log = mock_logger()

        mock_int.SafeGenerateJSON.side_effect = [
            (
                [{'role': 'assistant'}],
                {'summary': 'work summary'},
                {'prompt_tokens': 100, 'completion_tokens': 20}
            ),
            (
                [{'role': 'assistant'}],
                {'summary': 'outline summary'},
                {'prompt_tokens': 50, 'completion_tokens': 10}
            ),
        ]

        comparison_result = Mock()
        comparison_result.Suggestions = ""
        comparison_result.DidFollowOutline = True
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            comparison_result,
            {'prompt_tokens': 30, 'completion_tokens': 10}
        )

        # Act
        LLMSummaryCheck(mock_int, mock_log, "outline_text", work_text)

        # Assert - check log messages
        log_messages = [call[0][0] for call in mock_log.Log.call_args_list]

        assert any("Generating summary" in msg and "work" in msg.lower() for msg in log_messages)
        assert any("Finished generating summary" in msg and "work" in msg.lower() for msg in log_messages)


class TestLLMSummaryCheckOutlineSummary:
    """Test outline summary generation and caching"""

    def test_outline_summary_generated_on_first_call(self, mock_interface, mock_logger):
        """Test that outline summary is generated on first call"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange
        work_text = ' '.join(['word'] * 150)
        outline_text = "This is the chapter outline reference"

        mock_int = mock_interface()
        mock_log = mock_logger()

        mock_int.SafeGenerateJSON.side_effect = [
            # Work summary
            (
                [{'role': 'assistant'}],
                {'summary': 'work summary'},
                {'prompt_tokens': 100, 'completion_tokens': 20}
            ),
            # Outline summary (first time)
            (
                [{'role': 'assistant'}],
                {'summary': 'outline summary for reference'},
                {'prompt_tokens': 50, 'completion_tokens': 10}
            ),
        ]

        comparison_result = Mock()
        comparison_result.Suggestions = ""
        comparison_result.DidFollowOutline = True
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            comparison_result,
            {'prompt_tokens': 30, 'completion_tokens': 10}
        )

        # Act
        result, _ = LLMSummaryCheck(mock_int, mock_log, outline_text, work_text)

        # Assert - should have called SafeGenerateJSON 2 times (work, outline)
        assert mock_int.SafeGenerateJSON.call_count == 2
        assert result is True

    def test_outline_summary_cached_for_duplicate_outline(self, mock_interface, mock_logger):
        """Test that outline summary is cached for repeated calls with same outline"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange
        work_text = ' '.join(['word'] * 150)
        outline_text = "unique outline text 456"  # unique to avoid cache interference

        mock_int = mock_interface()
        mock_log = mock_logger()

        outline_summary = "cached outline summary"
        mock_int.SafeGenerateJSON.side_effect = [
            # First call - work summary
            (
                [{'role': 'assistant'}],
                {'summary': 'work summary'},
                {'prompt_tokens': 100, 'completion_tokens': 20}
            ),
            # First call - outline summary
            (
                [{'role': 'assistant'}],
                {'summary': outline_summary},
                {'prompt_tokens': 50, 'completion_tokens': 10}
            ),
            # Second call - work summary (different work)
            (
                [{'role': 'assistant'}],
                {'summary': 'work summary 2'},
                {'prompt_tokens': 100, 'completion_tokens': 20}
            ),
        ]

        comparison_result = Mock()
        comparison_result.Suggestions = ""
        comparison_result.DidFollowOutline = True
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            comparison_result,
            {'prompt_tokens': 30, 'completion_tokens': 10}
        )

        # Act - first call should generate outline summary
        result1, _ = LLMSummaryCheck(mock_int, mock_log, outline_text, work_text)

        # Act again with same outline but different work
        work_text2 = ' '.join(['different'] * 150)
        result2, _ = LLMSummaryCheck(mock_int, mock_log, outline_text, work_text2)

        # Assert - should have called 3 times total (no second outline summary)
        assert mock_int.SafeGenerateJSON.call_count == 3
        assert result1 is True
        assert result2 is True

    def test_outline_summary_cached_logs_message(self, mock_interface, mock_logger):
        """Test that cached outline usage is logged"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange
        work_text = ' '.join(['word'] * 150)
        outline_text = "Repeated outline text"

        mock_int = mock_interface()
        mock_log = mock_logger()

        mock_int.SafeGenerateJSON.side_effect = [
            # First call
            ({'role': 'assistant'}, {'summary': 'work summary'}, {'prompt_tokens': 100, 'completion_tokens': 20}),
            ({'role': 'assistant'}, {'summary': 'outline summary'}, {'prompt_tokens': 50, 'completion_tokens': 10}),
            # Second call - cached outline
            ({'role': 'assistant'}, {'summary': 'work summary 2'}, {'prompt_tokens': 100, 'completion_tokens': 20}),
        ]

        comparison_result = Mock()
        comparison_result.Suggestions = ""
        comparison_result.DidFollowOutline = True
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            comparison_result,
            {'prompt_tokens': 30, 'completion_tokens': 10}
        )

        # First call
        LLMSummaryCheck(mock_int, mock_log, outline_text, work_text)

        # Second call - should use cache
        LLMSummaryCheck(mock_int, mock_log, outline_text, ' '.join(['other'] * 150))

        # Assert - check for cached log message
        log_messages = [call[0][0] for call in mock_log.Log.call_args_list]
        assert any("cached" in msg.lower() and "outline" in msg.lower() for msg in log_messages)


class TestLLMSummaryCheckComparison:
    """Test final comparison between work and outline summaries"""

    def test_comparison_uses_pydantic_schema(self, mock_interface, mock_logger):
        """Test that comparison uses SafeGeneratePydantic with SummaryComparisonSchema"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange
        work_text = ' '.join(['word'] * 150)
        outline_text = "Outline text"

        mock_int = mock_interface()
        mock_log = mock_logger()

        # Configure SafeGenerateJSON for summaries
        mock_int.SafeGenerateJSON.side_effect = [
            ({'role': 'assistant'}, {'summary': 'work summary'}, {'prompt_tokens': 100, 'completion_tokens': 20}),
            ({'role': 'assistant'}, {'summary': 'outline summary'}, {'prompt_tokens': 50, 'completion_tokens': 10}),
        ]

        # Configure SafeGeneratePydantic for comparison
        comparison_result = Mock()
        comparison_result.Suggestions = "Some suggestions"
        comparison_result.DidFollowOutline = True
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            comparison_result,
            {'prompt_tokens': 30, 'completion_tokens': 10}
        )

        # Act
        result, suggestions = LLMSummaryCheck(mock_int, mock_log, outline_text, work_text)

        # Assert
        assert mock_int.SafeGeneratePydantic.call_count == 1
        assert result is True
        assert "Extra Suggestions:" in suggestions
        assert "Some suggestions" in suggestions

    def test_comparison_formatting_with_suggestions(self, mock_interface, mock_logger):
        """Test that suggestions are formatted with proper prefix"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange
        work_text = ' '.join(['word'] * 150)

        mock_int = mock_interface()
        mock_log = mock_logger()

        mock_int.SafeGenerateJSON.side_effect = [
            ({'role': 'assistant'}, {'summary': 'work'}, {'prompt_tokens': 100, 'completion_tokens': 20}),
            ({'role': 'assistant'}, {'summary': 'outline'}, {'prompt_tokens': 50, 'completion_tokens': 10}),
        ]

        comparison_result = Mock()
        comparison_result.Suggestions = "Improve the dialogue scenes"
        comparison_result.DidFollowOutline = True
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            comparison_result,
            {'prompt_tokens': 30, 'completion_tokens': 10}
        )

        # Act
        result, suggestions = LLMSummaryCheck(mock_int, mock_log, "outline", work_text)

        # Assert
        assert suggestions.startswith("### Extra Suggestions:\n")
        assert "Improve the dialogue scenes" in suggestions

    def test_comparison_true_result(self, mock_interface, mock_logger):
        """Test that DidFollowOutline=True returns True"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange
        work_text = ' '.join(['word'] * 150)

        mock_int = mock_interface()
        mock_log = mock_logger()

        mock_int.SafeGenerateJSON.side_effect = [
            ({'role': 'assistant'}, {'summary': 'work'}, {'prompt_tokens': 100, 'completion_tokens': 20}),
            ({'role': 'assistant'}, {'summary': 'outline'}, {'prompt_tokens': 50, 'completion_tokens': 10}),
        ]

        comparison_result = Mock()
        comparison_result.Suggestions = ""
        comparison_result.DidFollowOutline = True
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            comparison_result,
            {'prompt_tokens': 30, 'completion_tokens': 10}
        )

        # Act
        result, _ = LLMSummaryCheck(mock_int, mock_log, "outline", work_text)

        # Assert
        assert result is True

    def test_comparison_false_result(self, mock_interface, mock_logger):
        """Test that DidFollowOutline=False returns False"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange
        work_text = ' '.join(['word'] * 150)

        mock_int = mock_interface()
        mock_log = mock_logger()

        mock_int.SafeGenerateJSON.side_effect = [
            ({'role': 'assistant'}, {'summary': 'work'}, {'prompt_tokens': 100, 'completion_tokens': 20}),
            ({'role': 'assistant'}, {'summary': 'outline'}, {'prompt_tokens': 50, 'completion_tokens': 10}),
        ]

        comparison_result = Mock()
        comparison_result.Suggestions = "Chapter went off-topic"
        comparison_result.DidFollowOutline = False
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            comparison_result,
            {'prompt_tokens': 30, 'completion_tokens': 10}
        )

        # Act
        result, suggestions = LLMSummaryCheck(mock_int, mock_log, "outline", work_text)

        # Assert
        assert result is False
        assert "went off-topic" in suggestions


class TestLLMSummaryCheckIntegration:
    """End-to-end integration tests for LLMSummaryCheck"""

    def test_full_flow_success_case(self, mock_interface, mock_logger):
        """Test complete flow from work input to final comparison"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange
        work_text = ' '.join(['word'] * 150)
        outline_text = "Chapter outline with sufficient detail"

        mock_int = mock_interface()
        mock_log = mock_logger()

        mock_int.SafeGenerateJSON.side_effect = [
            ({'role': 'assistant'}, {'summary': 'Summary of the generated work'},
             {'prompt_tokens': 100, 'completion_tokens': 20}),
            ({'role': 'assistant'}, {'summary': 'Summary of the reference outline'},
             {'prompt_tokens': 50, 'completion_tokens': 10}),
        ]

        comparison_result = Mock()
        comparison_result.Suggestions = "Good flow overall"
        comparison_result.DidFollowOutline = True
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            comparison_result,
            {'prompt_tokens': 30, 'completion_tokens': 10}
        )

        # Act
        result, suggestions = LLMSummaryCheck(mock_int, mock_log, outline_text, work_text)

        # Assert
        assert result is True
        assert "Good flow overall" in suggestions
        assert mock_int.SafeGenerateJSON.call_count == 2
        assert mock_int.SafeGeneratePydantic.call_count == 1

    def test_full_flow_with_suggestions(self, mock_interface, mock_logger):
        """Test complete flow when LLM provides suggestions"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange
        work_text = ' '.join(['word'] * 150)

        mock_int = mock_interface()
        mock_log = mock_logger()

        mock_int.SafeGenerateJSON.side_effect = [
            ({'role': 'assistant'}, {'summary': 'work summary'}, {'prompt_tokens': 100, 'completion_tokens': 20}),
            ({'role': 'assistant'}, {'summary': 'outline summary'}, {'prompt_tokens': 50, 'completion_tokens': 10}),
        ]

        comparison_result = Mock()
        comparison_result.Suggestions = "Could add more character development in the middle section"
        comparison_result.DidFollowOutline = True
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            comparison_result,
            {'prompt_tokens': 30, 'completion_tokens': 10}
        )

        # Act
        result, suggestions = LLMSummaryCheck(mock_int, mock_log, "outline", work_text)

        # Assert
        assert result is True
        assert "Extra Suggestions:" in suggestions
        assert "character development" in suggestions

    def test_multiple_calls_share_outline_cache(self, mock_interface, mock_logger):
        """Test that multiple calls efficiently share the outline cache"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange
        outline_text = "Common outline used for multiple chapters"

        mock_int = mock_interface()
        mock_log = mock_logger()

        # Set up responses for 3 chapters with same outline
        mock_int.SafeGenerateJSON.side_effect = [
            # Chapter 1 - work summary
            ({'role': 'assistant'}, {'summary': 'chapter 1 work summary'}, {'prompt_tokens': 100, 'completion_tokens': 20}),
            # Chapter 1 - outline summary (first time)
            ({'role': 'assistant'}, {'summary': 'cached outline summary'}, {'prompt_tokens': 50, 'completion_tokens': 10}),
            # Chapter 2 - work summary only (outline cached)
            ({'role': 'assistant'}, {'summary': 'chapter 2 work summary'}, {'prompt_tokens': 100, 'completion_tokens': 20}),
            # Chapter 3 - work summary only (outline cached)
            ({'role': 'assistant'}, {'summary': 'chapter 3 work summary'}, {'prompt_tokens': 100, 'completion_tokens': 20}),
        ]

        comparison_result = Mock()
        comparison_result.Suggestions = ""
        comparison_result.DidFollowOutline = True
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            comparison_result,
            {'prompt_tokens': 30, 'completion_tokens': 10}
        )

        # Act - check 3 chapters with same outline
        for i in range(1, 4):
            work = ' '.join([f'word{i}'] * 150)
            result, _ = LLMSummaryCheck(mock_int, mock_log, outline_text, work)
            assert result is True

        # Assert - only 1 outline summary generated (not 3)
        assert mock_int.SafeGenerateJSON.call_count == 4  # 3 work summaries + 1 outline summary

    def test_log_messages_all_steps(self, mock_interface, mock_logger):
        """Test that all steps generate appropriate log messages"""
        from Writer.Chapter.ChapterGenSummaryCheck import LLMSummaryCheck

        # Arrange
        work_text = ' '.join(['word'] * 150)
        outline_text = "unique outline text 789"  # unique to avoid cache

        mock_int = mock_interface()
        mock_log = mock_logger()

        mock_int.SafeGenerateJSON.side_effect = [
            ({'role': 'assistant'}, {'summary': 'work summary'}, {'prompt_tokens': 100, 'completion_tokens': 20}),
            ({'role': 'assistant'}, {'summary': 'outline summary'}, {'prompt_tokens': 50, 'completion_tokens': 10}),
        ]

        comparison_result = Mock()
        comparison_result.Suggestions = ""
        comparison_result.DidFollowOutline = True
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            comparison_result,
            {'prompt_tokens': 30, 'completion_tokens': 10}
        )

        # Act
        LLMSummaryCheck(mock_int, mock_log, outline_text, work_text)

        # Assert - check for key log messages
        log_messages = [call[0][0] for call in mock_log.Log.call_args_list]
        assert any("Generating summary" in msg and "work" in msg.lower() for msg in log_messages)
        assert any("Finished generating summary" in msg and "work" in msg.lower() for msg in log_messages)
        assert any("Generating summary" in msg and "outline" in msg.lower() for msg in log_messages)
        assert any("Finished generating and cached" in msg and "outline" in msg.lower() for msg in log_messages)
        assert any("Comparing" in msg or "comparison" in msg.lower() for msg in log_messages)
        assert any("Finished comparing" in msg for msg in log_messages)
