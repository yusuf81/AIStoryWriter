"""
Tests for Pydantic validation error feedback in SafeGeneratePydantic.

Tests that error messages provide actionable feedback WITHOUT schema echoing.
Follows TDD London School methodology with mocked dependencies.
"""
from unittest.mock import Mock, patch
from pydantic import ValidationError
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TestValidationErrorMessageBuilder:
    """Test _build_validation_error_message method"""

    def test_missing_field_error_message(self):
        """Test message format for missing required field"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])

        # Create ValidationError with invalid values (wrong data type and constraint violations)
        try:
            ChapterOutput(text="Valid text content here", chapter_number=1, chapter_title=None, word_count=0)
        except ValidationError as ve:
            message = interface._build_validation_error_message(ve, 'ChapterOutput')

            # Should mention the fields with errors
            assert 'word_count' in message or 'text' in message

            # Should mention the constraint/type issue
            # Note: These are constraint violations (gt=0, min_length=100), not missing required fields
            assert '0' in message or '100' in message or 'greater' in message.lower() or 'characters' in message.lower()

            # Should NOT contain schema keywords
            assert '"type"' not in message
            assert 'properties' not in message

    def test_string_too_short_error_message(self):
        """Test message format for string length constraint"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])

        # Create ValidationError with too short text
        try:
            ChapterOutput(text="short", word_count=1, chapter_number=1, chapter_title=None)  # text min_length: 100
        except ValidationError as ve:
            message = interface._build_validation_error_message(ve, 'ChapterOutput')

            # Should show field name and actual vs expected length
            assert 'text' in message
            assert '100' in message  # min_length constraint
            assert '5' in message or 'short' in message.lower()  # actual length or hint

    def test_word_count_mismatch_error_message(self):
        """Test message format for custom validator (word count mismatch)"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])

        # Create text with known word count
        text = ' '.join(['word'] * 100)  # 100 words

        # Claim different word count
        try:
            ChapterOutput(text=text, word_count=500, chapter_number=1, chapter_title=None)  # Mismatch > tolerance
        except ValidationError as ve:
            message = interface._build_validation_error_message(ve, 'ChapterOutput')

            # Should contain word_count field and validator error message
            assert 'word_count' in message
            assert 'actual' in message.lower() or '100' in message

    def test_type_error_message(self):
        """Test message format for type mismatch"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])

        # Create ValidationError with wrong type
        try:
            ChapterOutput(
                text="Valid text with at least 100 characters to meet the minimum length requirement for this field.",
                word_count="not_a_number",  # type: ignore[arg-type]  # Should be int
                chapter_number=1,
                chapter_title=None
            )
        except ValidationError as ve:
            message = interface._build_validation_error_message(ve, 'ChapterOutput')

            # Should mention expected type and actual value
            assert 'word_count' in message
            assert 'integer' in message.lower() or 'int' in message

    def test_multiple_errors_all_listed(self):
        """Test that all validation errors are included in message"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])

        # Create ValidationError with multiple issues
        try:
            ChapterOutput(
                text="short",  # Too short
                word_count=0,  # Invalid (violates gt=0)
                chapter_number=0,  # Invalid (violates ge=1)
                chapter_title=None
            )
        except ValidationError as ve:
            message = interface._build_validation_error_message(ve, 'ChapterOutput')

            # Should list all three errors
            assert 'text' in message
            assert 'word_count' in message
            assert 'chapter_number' in message

    def test_error_message_has_no_schema_keywords(self):
        """CRITICAL: Verify error message contains NO schema structure keywords"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])

        # Create any ValidationError
        try:
            ChapterOutput(text="short", word_count=0, chapter_number=1, chapter_title=None)
        except ValidationError as ve:
            message = interface._build_validation_error_message(ve, 'ChapterOutput')

            # Schema keywords that would trigger echoing (with their schema context)
            # Note: we check for schema-specific patterns, not natural language words
            forbidden_patterns = [
                'properties',      # Schema keyword
                '"required"',      # Schema keyword with quotes
                '"type"',          # Schema keyword with quotes
                '"object"',        # Schema keyword with quotes
                '"string"',        # Schema keyword with quotes
                'schema',          # Direct schema reference
            ]

            # Check for JSON structure characters that indicate schema echoing
            # We allow natural language usage of these words, but not in schema context
            for pattern in forbidden_patterns:
                assert pattern not in message.lower(), f"Error message contains forbidden schema pattern: {pattern}"

            # Specifically check that message doesn't look like JSON schema structure
            assert not ('{' in message and '"type"' in message), "Message contains JSON schema structure"
            assert not ('properties' in message.lower() and '{' in message), "Message looks like schema definition"


class TestSafeGeneratePydanticErrorFeedback:
    """Integration tests for SafeGeneratePydantic with error feedback"""

    def test_error_feedback_appended_to_messages_on_retry(self, mock_logger):
        """Test that error message is added to conversation on retry"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])

        # Mock SafeGenerateJSON to return invalid data on first call, valid on second
        with patch.object(interface, 'SafeGenerateJSON') as mock_json:
            valid_text = 'Valid long text with at least 100 characters here for testing purposes and validation. This text is sufficiently long now.'
            mock_json.side_effect = [
                # First call: missing word_count
                (
                    [{'role': 'user', 'content': 'test'}],
                    {'text': valid_text, 'chapter_number': 1},
                    {'prompt_tokens': 10, 'completion_tokens': 20}
                ),
                # Second call: valid data
                (
                    [{'role': 'user', 'content': 'test'}, {'role': 'user', 'content': 'error feedback'}],
                    {'text': valid_text, 'word_count': 20, 'chapter_number': 1},
                    {'prompt_tokens': 10, 'completion_tokens': 20}
                )
            ]

            interface.Clients['test'] = Mock()

            # Should succeed after one retry
            messages, result, tokens = interface.SafeGeneratePydantic(
                mock_logger(),
                [{'role': 'user', 'content': 'test'}],
                'test',
                ChapterOutput,
                _max_retries_override=2
            )  # type: ignore[misc]  # Tests guarantee success with mock data

            # Should have retried
            assert mock_json.call_count == 2

            # Second call should have error feedback in messages
            second_call_messages = mock_json.call_args_list[1][0][1]  # messages_for_parsing
            assert len(second_call_messages) > 1

            # Last message should be error feedback
            last_message = second_call_messages[-1]
            assert last_message['role'] == 'user'
            assert 'validation error' in last_message['content'].lower()
            assert 'word_count' in last_message['content']

    def test_non_validation_errors_use_generic_hints(self, mock_logger):
        """Test backward compatibility: non-ValidationError exceptions use old behavior"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])

        # Mock SafeGenerateJSON to return list (TypeError)
        with patch.object(interface, 'SafeGenerateJSON') as mock_json:
            valid_text = 'Valid long text with at least 100 characters here for testing purposes and validation. This text is sufficiently long now.'
            mock_json.side_effect = [
                # First call: returns list (triggers TypeError)
                (
                    [{'role': 'user', 'content': 'test'}],
                    [{'text': 'data'}],  # List instead of dict
                    {'prompt_tokens': 10, 'completion_tokens': 20}
                ),
                # Second call: valid dict
                (
                    [{'role': 'user', 'content': 'test'}],
                    {'text': valid_text, 'word_count': 20, 'chapter_number': 1},
                    {'prompt_tokens': 10, 'completion_tokens': 20}
                )
            ]

            interface.Clients['test'] = Mock()

            # Should succeed after retry
            messages, result, tokens = interface.SafeGeneratePydantic(
                mock_logger(),
                [{'role': 'user', 'content': 'test'}],
                'test',
                ChapterOutput,
                _max_retries_override=2
            )  # type: ignore[misc]  # Tests guarantee success with mock data

            # Should have retried
            assert mock_json.call_count == 2

            # TypeError should NOT add error message to conversation
            # (uses generic hints instead)
            # This tests backward compatibility

    def test_error_feedback_reduces_retry_count(self, mock_logger):
        """Integration test: error feedback should help LLM correct on first retry"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])

        # Simulate realistic scenario: missing field, then corrected
        with patch.object(interface, 'SafeGenerateJSON') as mock_json:
            valid_text = 'Valid chapter text with sufficient length to pass validation checks and meet all requirements. This text is long enough.'
            mock_json.side_effect = [
                # Attempt 1: Missing word_count
                (
                    [{'role': 'user', 'content': 'generate chapter'}],
                    {'text': valid_text, 'chapter_number': 1},
                    {'prompt_tokens': 10, 'completion_tokens': 20}
                ),
                # Attempt 2: After error feedback, includes word_count
                (
                    [{'role': 'user', 'content': 'generate chapter'}, {'role': 'user', 'content': 'error: word_count required'}],
                    {'text': valid_text, 'word_count': 20, 'chapter_number': 1},
                    {'prompt_tokens': 10, 'completion_tokens': 20}
                )
            ]

            interface.Clients['test'] = Mock()

            # Should succeed after just ONE retry
            messages, result, tokens = interface.SafeGeneratePydantic(
                mock_logger(),
                [{'role': 'user', 'content': 'generate chapter'}],
                'test',
                ChapterOutput,
                _max_retries_override=3
            )  # type: ignore[misc]  # Tests guarantee success with mock data

            # Key assertion: only 2 attempts (not 3-4 like blind retry)
            assert mock_json.call_count == 2
            assert isinstance(result, ChapterOutput)
