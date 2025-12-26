"""
Tests for base context extraction from GET_IMPORTANT_BASE_PROMPT_INFO.

This tests the change from SafeGeneratePydantic(BaseContext) to SafeGenerateJSON
with flexible extraction helper.

Pattern follows test_chapter_gen_summary_check.py (Level 1 fix).
"""
from unittest.mock import MagicMock


class TestBaseContextExtractionHelper:
    """Test _extract_base_context() helper function with various JSON formats."""

    def test_extract_direct_context_field(self):
        """Test extraction when 'context' field is present"""
        # Arrange
        from Writer.OutlineGenerator import _extract_base_context
        context_json = {'context': 'Important context information'}

        # Act
        result = _extract_base_context(context_json)

        # Assert
        assert result == 'Important context information'
        assert len(result) > 0

    def test_extract_fallback_to_any_string(self):
        """Test fallback extraction when 'context' field is missing"""
        # Arrange
        from Writer.OutlineGenerator import _extract_base_context
        context_json = {'additional_info': 'This is the context in different field'}

        # Act
        result = _extract_base_context(context_json)

        # Assert
        assert result == 'This is the context in different field'
        assert len(result) > 10

    def test_extract_empty_dict_returns_empty(self):
        """Test that empty dict returns empty string"""
        # Arrange
        from Writer.OutlineGenerator import _extract_base_context
        context_json = {}

        # Act
        result = _extract_base_context(context_json)

        # Assert
        assert result == ""

    def test_extract_non_dict_returns_empty(self):
        """Test that non-dict input returns empty string"""
        # Arrange
        from Writer.OutlineGenerator import _extract_base_context

        # Act
        result_list = _extract_base_context(['list', 'not', 'dict'])
        result_str = _extract_base_context("string not dict")
        result_none = _extract_base_context(None)

        # Assert
        assert result_list == ""
        assert result_str == ""
        assert result_none == ""

    def test_extract_validates_minimum_length(self):
        """Test that short strings (<=10 chars) are skipped in fallback"""
        # Arrange
        from Writer.OutlineGenerator import _extract_base_context
        context_json = {
            'short': 'tiny',  # 4 chars - should skip
            'long': 'This is longer than ten characters'  # >10 - should use
        }

        # Act
        result = _extract_base_context(context_json)

        # Assert
        assert result == 'This is longer than ten characters'
        assert 'tiny' not in result


class TestBaseContextGeneration:
    """Test that GenerateOutline uses SafeGenerateJSON for base context."""

    def test_uses_safe_generate_json(self, mock_interface, mock_logger):
        """Test that SafeGenerateJSON is called instead of SafeGeneratePydantic"""
        # Arrange
        mock_int = mock_interface()
        mock_log = mock_logger()

        # Configure mocks for the complete flow
        mock_int.SafeGenerateJSON.side_effect = [
            # First call: base context
            (
                [{'role': 'assistant', 'content': '{"context": "test context"}'}],
                {'context': 'test context'},
                {'prompt_tokens': 50, 'completion_tokens': 10}
            ),
        ]
        mock_int.SafeGeneratePydantic.side_effect = [
            # Story elements
            (
                [{'role': 'assistant'}],
                MagicMock(
                    title="Test Story",
                    to_prompt_string=lambda: "Story elements text"
                ),
                {'prompt_tokens': 100}
            ),
            # Initial outline
            (
                [{'role': 'assistant'}],
                MagicMock(
                    to_prompt_string=lambda: "Outline text",
                    target_chapter_count=2,
                    title="Test",
                    chapters=["Chapter 1", "Chapter 2"]
                ),
                {'prompt_tokens': 200}
            ),
            # Review/Feedback (iteration 1)
            (
                [{'role': 'assistant'}],
                MagicMock(feedback="Good feedback"),
                {'prompt_tokens': 50}
            ),
            # OutlineCompleteSchema (iteration 1) - not ready yet
            (
                [{'role': 'assistant'}],
                MagicMock(IsComplete=False),
                {'prompt_tokens': 20}
            ),
            # Revised outline (iteration 1)
            (
                [{'role': 'assistant'}],
                MagicMock(
                    title="Revised Test",
                    chapters=["Revised Chapter 1", "Revised Chapter 2"]
                ),
                {'prompt_tokens': 150}
            ),
            # Review/Feedback (iteration 2)
            (
                [{'role': 'assistant'}],
                MagicMock(feedback="Excellent"),
                {'prompt_tokens': 50}
            ),
            # OutlineCompleteSchema (iteration 2) - ready to exit
            (
                [{'role': 'assistant'}],
                MagicMock(IsComplete=True),
                {'prompt_tokens': 20}
            ),
        ]

        # Act
        from Writer.OutlineGenerator import GenerateOutline
        outline, _, _, base_context = GenerateOutline(
            mock_int, mock_log, "test prompt"
        )

        # Assert
        assert mock_int.SafeGenerateJSON.called
        assert mock_int.SafeGenerateJSON.call_count >= 1
        # Verify it was NOT called with BaseContext model
        for call in mock_int.SafeGeneratePydantic.call_args_list:
            args = call[0]
            if len(args) >= 4:
                # SafeGeneratePydantic signature: (logger, messages, model, PydanticClass)
                # Make sure BaseContext is NOT in the calls
                assert 'BaseContext' not in str(args[3].__name__ if hasattr(args[3], '__name__') else args[3])

    def test_extraction_from_json_response(self, mock_interface, mock_logger):
        """Test that context is extracted from JSON response correctly"""
        # Arrange
        mock_int = mock_interface()
        mock_log = mock_logger()
        context_text = "Expected context from JSON"

        mock_int.SafeGenerateJSON.side_effect = [
            (
                [{'role': 'assistant'}],
                {'context': context_text},
                {'prompt_tokens': 50}
            ),
        ]
        mock_int.SafeGeneratePydantic.side_effect = [
            (
                [{'role': 'assistant'}],
                MagicMock(
                    title="Test",
                    to_prompt_string=lambda: "Story elements"
                ),
                {'prompt_tokens': 100}
            ),
            (
                [{'role': 'assistant'}],
                MagicMock(
                    to_prompt_string=lambda: "Outline",
                    target_chapter_count=2,
                    title="Test",
                    chapters=["Chapter 1", "Chapter 2"]
                ),
                {'prompt_tokens': 200}
            ),
            # Review/Feedback (iteration 1)
            (
                [{'role': 'assistant'}],
                MagicMock(feedback="Good feedback"),
                {'prompt_tokens': 50}
            ),
            # OutlineCompleteSchema (iteration 1) - not ready yet
            (
                [{'role': 'assistant'}],
                MagicMock(IsComplete=False),
                {'prompt_tokens': 20}
            ),
            # Revised outline (iteration 1)
            (
                [{'role': 'assistant'}],
                MagicMock(
                    title="Revised Test",
                    chapters=["Revised Chapter 1", "Revised Chapter 2"]
                ),
                {'prompt_tokens': 150}
            ),
            # Review/Feedback (iteration 2)
            (
                [{'role': 'assistant'}],
                MagicMock(feedback="Excellent"),
                {'prompt_tokens': 50}
            ),
            # OutlineCompleteSchema (iteration 2) - ready to exit
            (
                [{'role': 'assistant'}],
                MagicMock(IsComplete=True),
                {'prompt_tokens': 20}
            ),
        ]

        # Act
        from Writer.OutlineGenerator import GenerateOutline
        outline, _, _, base_context = GenerateOutline(
            mock_int, mock_log, "test prompt"
        )

        # Assert
        assert context_text in base_context

    def test_generates_log_messages(self, mock_interface, mock_logger):
        """Test that appropriate log messages are generated"""
        # Arrange
        mock_int = mock_interface()
        mock_log = mock_logger()

        mock_int.SafeGenerateJSON.side_effect = [
            (
                [{'role': 'assistant'}],
                {'context': 'test context'},
                {'prompt_tokens': 50}
            ),
        ]
        mock_int.SafeGeneratePydantic.side_effect = [
            (
                [{'role': 'assistant'}],
                MagicMock(
                    title="Test",
                    to_prompt_string=lambda: "Story"
                ),
                {'prompt_tokens': 100}
            ),
            (
                [{'role': 'assistant'}],
                MagicMock(
                    to_prompt_string=lambda: "Outline",
                    target_chapter_count=2,
                    title="Test",
                    chapters=["Chapter 1", "Chapter 2"]
                ),
                {'prompt_tokens': 200}
            ),
            # Review/Feedback (iteration 1)
            (
                [{'role': 'assistant'}],
                MagicMock(feedback="Good feedback"),
                {'prompt_tokens': 50}
            ),
            # OutlineCompleteSchema (iteration 1) - not ready yet
            (
                [{'role': 'assistant'}],
                MagicMock(IsComplete=False),
                {'prompt_tokens': 20}
            ),
            # Revised outline (iteration 1)
            (
                [{'role': 'assistant'}],
                MagicMock(
                    title="Revised Test",
                    chapters=["Revised Chapter 1", "Revised Chapter 2"]
                ),
                {'prompt_tokens': 150}
            ),
            # Review/Feedback (iteration 2)
            (
                [{'role': 'assistant'}],
                MagicMock(feedback="Excellent"),
                {'prompt_tokens': 50}
            ),
            # OutlineCompleteSchema (iteration 2) - ready to exit
            (
                [{'role': 'assistant'}],
                MagicMock(IsComplete=True),
                {'prompt_tokens': 20}
            ),
        ]

        # Act
        from Writer.OutlineGenerator import GenerateOutline
        GenerateOutline(mock_int, mock_log, "test prompt")

        # Assert
        log_messages = [call[0][0] for call in mock_log.Log.call_args_list]
        # Should have logged something about getting base context
        assert any("base" in msg.lower() or "context" in msg.lower() for msg in log_messages)


class TestPromptFormat:
    """Test that prompts have clear JSON format instructions."""

    def test_english_prompt_requests_json_format(self):
        """Test that English prompt has JSON format section"""
        # Arrange
        import Writer.Prompts as Prompts

        # Act
        prompt = Prompts.GET_IMPORTANT_BASE_PROMPT_INFO

        # Assert
        assert '# JSON OUTPUT FORMAT' in prompt or 'JSON' in prompt
        assert 'context' in prompt.lower()
        assert 'Return ONLY' in prompt or 'ONLY' in prompt

    def test_indonesian_prompt_requests_json_format(self):
        """Test that Indonesian prompt has JSON format section"""
        # Arrange
        import Writer.Prompts_id as Prompts_id

        # Act
        prompt = Prompts_id.GET_IMPORTANT_BASE_PROMPT_INFO

        # Assert
        assert 'JSON' in prompt
        assert 'context' in prompt.lower()
        # Indonesian: "HANYA kembalikan JSON" or similar
        assert 'HANYA' in prompt or 'hanya' in prompt
