"""
Tests for JSON format fix to prevent schema echoing and improve retry logic.
Tests that the new prompt format and retry handling work correctly.
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TestJSONFormatFix:
    """Test the JSON format handling fix for schema echoing issue"""

    def test_build_format_instruction_prevents_schema_echoing(self, mock_logger, english_language_config):
        """Test that format instruction doesn't include full schema"""
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])

        # Create a test schema
        schema = {
            "title": "TestModel",
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text content", "minLength": 10},
                "count": {"type": "integer", "description": "A number", "minimum": 1},
                "optional_field": {"type": "string", "description": "Optional info"}
            },
            "required": ["text", "count"]
        }

        # Build format instruction
        instruction = interface._build_format_instruction(schema)

        # Should NOT contain the full schema JSON
        assert "title" not in instruction
        assert '"type": "object"' not in instruction
        assert '"properties"' not in instruction

        # Should contain field information
        # Note: 'text' field gets translated description from field_descriptions
        assert "text (string, Required): Full chapter text content" in instruction
        assert "count (integer, Required): A number" in instruction
        assert "optional_field (string, Optional): Optional info" in instruction

        # Should contain clear instructions
        assert "JSON SCHEMA (REFERENCE ONLY)" in instruction
        assert "DO NOT repeat the schema" in instruction
        assert "YOUR RESPONSE (JSON ONLY)" in instruction

    def test_safe_generate_pydantic_retries_on_list_response(self, mock_logger):
        """Test that SafeGeneratePydantic retries when getting list response"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])

        # Mock SafeGenerateJSON to return a list (malformed response)
        with patch.object(interface, 'SafeGenerateJSON') as mock_json:
            mock_json.return_value = (
                [{'role': 'user', 'content': 'test'}],
                [{'description': 'schema...'}, {'text': 'actual data...', 'word_count': 100, 'chapter_number': 1}],
                {'prompt_tokens': 10, 'completion_tokens': 20}
            )

            # Mock the retry mechanism - second attempt returns valid dict
            mock_json.side_effect = [
                (
                    [{'role': 'user', 'content': 'test'}],
                    [{'description': 'schema...'}, {'text': 'actual data...', 'word_count': 100, 'chapter_number': 1}],
                    {'prompt_tokens': 10, 'completion_tokens': 20}
                ),
                (
                    [{'role': 'user', 'content': 'test'}],
                    {'text': 'This is a correct chapter text that meets the minimum length requirement of 100 characters for proper validation in our test case.', 'word_count': 22, 'chapter_number': 1},
                    {'prompt_tokens': 10, 'completion_tokens': 20}
                )
            ]

            # Add mock client
            interface.Clients['test'] = Mock()

            # This should succeed after retry
            messages, result, tokens = interface.SafeGeneratePydantic(
                mock_logger(),
                [{'role': 'user', 'content': 'test'}],
                'test',
                ChapterOutput,
                _max_retries_override=2
            )  # type: ignore[misc]  # Tests guarantee success with mock data

            # Should succeed
            assert isinstance(result, ChapterOutput)
            assert result.text == 'This is a correct chapter text that meets the minimum length requirement of 100 characters for proper validation in our test case.'

            # Should have been called twice (initial + retry)
            assert mock_json.call_count == 2

    def test_safe_generate_pydantic_fails_after_max_retries(self, mock_logger):
        """Test that SafeGeneratePydantic fails after max retries with list response"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])

        # Mock SafeGenerateJSON to always return list
        with patch.object(interface, 'SafeGenerateJSON') as mock_json:
            mock_json.return_value = (
                [{'role': 'user', 'content': 'test'}],
                [{'description': 'schema...'}, {'text': 'actual data...'}],
                {'prompt_tokens': 10, 'completion_tokens': 20}
            )

            # Add mock client
            interface.Clients['test'] = Mock()

            # Should fail after max retries
            with pytest.raises(Exception) as exc_info:
                interface.SafeGeneratePydantic(
                    mock_logger(),
                    [{'role': 'user', 'content': 'test'}],
                    'test',
                    ChapterOutput,
                    _max_retries_override=1  # Only allow 1 retry
                )

            assert "Failed to generate valid response after 1 attempts" in str(exc_info.value)

    def test_pre_validation_checks_response_format(self, mock_logger):
        """Test that pre-validation catches various format issues"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])

        test_cases = [
            # Response, Expected error substring
            ([], "list of 0 objects"),  # Empty list
            ([{}], "list of 1 objects"),  # List with empty dict
            (["string"], "list of 1 objects"),  # List with string
            (None, "Expected JSON object"),
            ("string", "Expected JSON object"),
            (123, "Expected JSON object"),
        ]

        for bad_response, error_substring in test_cases:
            with patch.object(interface, 'SafeGenerateJSON') as mock_json:
                mock_json.return_value = (
                    [{'role': 'user', 'content': 'test'}],
                    bad_response,
                    {'prompt_tokens': 10, 'completion_tokens': 20}
                )

                interface.Clients['test'] = Mock()

                with pytest.raises(Exception) as exc_info:
                    interface.SafeGeneratePydantic(
                        mock_logger(),
                        [{'role': 'user', 'content': 'test'}],
                        'test',
                        ChapterOutput,
                        _max_retries_override=1  # Only 1 attempt, no retries
                    )

                assert error_substring in str(exc_info.value)

    def test_valid_dictionary_response_succeeds(self, mock_logger):
        """Test that valid dictionary response succeeds without retry"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])

        with patch.object(interface, 'SafeGenerateJSON') as mock_json:
            mock_json.return_value = (
                [{'role': 'user', 'content': 'test'}],
                {
                    'text': 'This is a valid chapter text that meets the minimum length requirement of 100 characters for proper validation in the test suite.',
                    'word_count': 22,
                    'chapter_number': 1,
                    'scenes': ['Scene 1', 'Scene 2'],
                    'characters_present': ['Character A']
                },
                {'prompt_tokens': 10, 'completion_tokens': 20}
            )

            interface.Clients['test'] = Mock()

            # Should succeed immediately
            messages, result, tokens = interface.SafeGeneratePydantic(
                mock_logger(),
                [{'role': 'user', 'content': 'test'}],
                'test',
                ChapterOutput,
                _max_retries_override=3
            )  # type: ignore[misc]  # Tests guarantee success with mock data

            # Success validation
            assert isinstance(result, ChapterOutput)
            assert result.text == 'This is a valid chapter text that meets the minimum length requirement of 100 characters for proper validation in the test suite.'
            assert result.chapter_number == 1

            # Should only be called once (no retries needed)
            assert mock_json.call_count == 1


class TestListStrFormatInstructions:
    """Test enhanced format instructions for List[str] fields to prevent object generation"""

    def test_format_instruction_detects_string_arrays(self, mock_logger, english_language_config):
        """Test that List[str] fields get explicit examples in format instruction"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import OutlineOutput

        interface = Interface(Models=[])
        schema = OutlineOutput.model_json_schema()

        instruction = interface._build_format_instruction(schema)

        # Should contain specific string array indicators
        assert "array of strings" in instruction
        assert "chapters (array of strings, Required)" in instruction
        assert "character_list (array of strings, Optional)" in instruction

        # Should contain explicit examples for string arrays
        assert "Example: [\"String 1\", \"String 2\"]" in instruction

    def test_format_instruction_handles_object_arrays(self, mock_logger):
        """Test that non-string arrays get different format instructions"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterWithScenes

        interface = Interface(Models=[])
        schema = ChapterWithScenes.model_json_schema()

        instruction = interface._build_format_instruction(schema)

        # Should identify object arrays differently
        assert "array of objects" in instruction
        # Scene details should be marked as object array
        assert "scene_details (array of objects" in instruction

    def test_outlineoutput_specific_examples(self, mock_logger):
        """Test OutlineOutput gets specific format without StoryElements examples"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import OutlineOutput

        interface = Interface(Models=[])
        schema = OutlineOutput.model_json_schema()

        instruction = interface._build_format_instruction(schema)

        # Should contain OutlineOutput format with chapters list
        assert "chapters" in instruction
        assert "array of strings" in instruction
        assert "character_list" in instruction

        # Should NOT contain StoryElements-specific examples
        assert "Petualangan di Gua Tersembunyi" not in instruction
        assert "Chapter 1: Rian menemukan gua mistis" not in instruction
        assert "The Dragon's Treasure Cave" not in instruction or "Adventure" not in instruction

    def test_chapteroutput_format_instruction(self, mock_logger, english_language_config):
        """Test ChapterOutput gets examples for scenes and characters_present fields"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])
        schema = ChapterOutput.model_json_schema()

        instruction = interface._build_format_instruction(schema)

        # Should identify List[str] fields in ChapterOutput
        assert "scenes (array of strings" in instruction
        assert "characters_present (array of strings" in instruction

        # Should contain examples for these fields
        assert "Example: [\"String 1\", \"String 2\"]" in instruction

    def test_non_array_fields_unchanged(self, mock_logger, english_language_config):
        """Test that non-array fields keep their current format"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import OutlineOutput

        interface = Interface(Models=[])
        schema = OutlineOutput.model_json_schema()

        instruction = interface._build_format_instruction(schema)

        # Non-array fields should keep normal format
        assert "title (string, Required)" in instruction
        assert "target_chapter_count (integer, Required)" in instruction
