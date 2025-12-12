# tests/writer/test_pydantic_integration.py
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

# Import the module we're testing
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestPydanticIntegration:
    """Test suite for Pydantic integration following TDD London School approach"""

    @pytest.fixture
    def mock_interface(self):
        """Create mock interface for testing"""
        from Writer.Interface.Wrapper import Interface

        # Create interface with minimal setup
        interface = Interface()
        interface.Clients = {}

        return interface

    @pytest.fixture
    def mock_logger(self):
        """Create mock logger"""
        logger = Mock()
        return logger

    def test_pydantic_available_import(self):
        """Test that Pydantic can be imported"""
        from Writer.Interface.Wrapper import PYDANTIC_AVAILABLE
        # We expect this to be True since we installed pydantic
        assert PYDANTIC_AVAILABLE == True

    def test_safe_generate_pydantic_disabled_in_config(self, mock_interface, mock_logger):
        """Test that SafeGeneratePydantic falls back to SafeGenerateJSON when disabled"""
        from Writer.Models import ChapterOutput

        # Store original config
        from Writer import Config
        original_use_pydantic = Config.USE_PYDANTIC_PARSING
        Config.USE_PYDANTIC_PARSING = False

        try:
            messages = [{"role": "user", "content": "Write a chapter"}]

            with patch.object(mock_interface, 'SafeGenerateJSON') as mock_json:
                mock_json.return_value = ([], {}, None)

                # Call SafeGeneratePydantic
                result = mock_interface.SafeGeneratePydantic(
                    mock_logger, messages, "test_model", ChapterOutput
                )

                # Should call SafeGenerateJSON instead
                mock_json.assert_called_once()

        finally:
            # Restore original config
            Config.USE_PYDANTIC_PARSING = original_use_pydantic

    def test_safe_generate_pydantic_with_model_string(self, mock_interface, mock_logger):
        """Test SafeGeneratePydantic accepts model name as string"""
        from Writer import Config
        from Writer.Models import ChapterOutput

        # Enable pydantic
        original_use_pydantic = Config.USE_PYDANTIC_PARSING
        Config.USE_PYDANTIC_PARSING = True

        try:
            messages = [{"role": "user", "content": "Write a chapter"}]

            with patch.object(mock_interface, 'SafeGenerateJSON') as mock_json:
                # Setup successful JSON response
                mock_json.return_value = (
                    [{"role": "assistant", "content": "Chapter content here"}],
                    {
                        "text": "Alice walked through the dark forest.",
                        "word_count": 5,
                        "scenes": ["Forest walk"],
                        "characters_present": ["Alice"],
                        "chapter_number": 1
                    },
                    {"tokens": 100}
                )

                # Call with model name string
                result = mock_interface.SafeGeneratePydantic(
                    mock_logger, messages, "test_model", "ChapterOutput"
                )

                # Should succeed
                assert result is not None
                mock_json.assert_called_once()

        finally:
            Config.USE_PYDANTIC_PARSING = original_use_pydantic

    def test_safe_generate_pydantic_with_model_class(self, mock_interface, mock_logger):
        """Test SafeGeneratePydantic accepts model class directly"""
        from Writer.Models import ChapterOutput
        from Writer import Config

        # Enable pydantic
        original_use_pydantic = Config.USE_PYDANTIC_PARSING
        Config.USE_PYDANTIC_PARSING = True

        try:
            messages = [{"role": "user", "content": "Write a chapter"}]

            with patch.object(mock_interface, 'SafeGenerateJSON') as mock_json:
                # Setup successful JSON response
                mock_json.return_value = (
                    [{"role": "assistant", "content": "Chapter content here"}],
                    {
                        "text": "Alice walked through the dark forest, her blue eyes scanning the shadows. This chapter is long enough to meet the minimum requirements for validation.",
                        "word_count": 20,
                        "scenes": ["Forest walk"],
                        "characters_present": ["Alice"],
                        "chapter_number": 1,
                        "chapter_title": "The Forest"
                    },
                    {"tokens": 100}
                )

                # Call with model class
                result = mock_interface.SafeGeneratePydantic(
                    mock_logger, messages, "test_model", ChapterOutput
                )

                # Should succeed and return validated model
                assert result is not None
                messages_list, validated_model, token_usage = result

                # Check the validated model
                assert isinstance(validated_model, ChapterOutput)
                assert validated_model.text == "Alice walked through the dark forest, her blue eyes scanning the shadows. This chapter is long enough to meet the minimum requirements for validation."
                assert validated_model.word_count == 20
                assert validated_model.chapter_number == 1
                assert validated_model.chapter_title == "The Forest"

        finally:
            Config.USE_PYDANTIC_PARSING = original_use_pydantic

    def test_safe_generate_pydantic_validation_failure_fallback(self, mock_interface, mock_logger):
        """Test SafeGeneratePydantic falls back when validation fails"""
        from Writer.Models import ChapterOutput
        from Writer import Config

        # Enable pydantic
        original_use_pydantic = Config.USE_PYDANTIC_PARSING
        Config.USE_PYDANTIC_PARSING = True

        try:
            messages = [{"role": "user", "content": "Write a chapter"}]

            with patch.object(mock_interface, 'SafeGenerateJSON') as mock_json:
                # Setup JSON response with validation errors
                mock_json.return_value = (
                    [{"role": "assistant", "content": "Chapter content here"}],
                    {
                        "text": "Alice walked through the dark forest.",
                        "word_count": -1,  # Invalid negative word count
                        "scenes": ["Forest walk"],
                        "characters_present": ["Alice"],
                        "chapter_number": 1
                    },
                    {"tokens": 100}
                )

                # Call with model class
                result = mock_interface.SafeGeneratePydantic(
                    mock_logger, messages, "test_model", ChapterOutput
                )

                # Should return the JSON response as fallback
                assert result is not None
                messages_list, validated_model, token_usage = result

                # When validation fails completely, should return raw JSON
                assert isinstance(validated_model, dict)
                assert validated_model["text"] == "Alice walked through the dark forest."

        finally:
            Config.USE_PYDANTIC_PARSING = original_use_pydantic

    def test_safe_generate_pydantic_invalid_model_name(self, mock_interface, mock_logger):
        """Test SafeGeneratePydantic with invalid model name falls back to JSON"""
        from Writer import Config

        # Enable pydantic
        original_use_pydantic = Config.USE_PYDANTIC_PARSING
        Config.USE_PYDANTIC_PARSING = True

        try:
            messages = [{"role": "user", "content": "Write a chapter"}]

            with patch.object(mock_interface, 'SafeGenerateJSON') as mock_json:
                mock_json.return_value = ([], {"response": "data"}, {"tokens": 50})

                # Call with invalid model name
                result = mock_interface.SafeGeneratePydantic(
                    mock_logger, messages, "test_model", "NonExistentModel"
                )

                # Should call SafeGenerateJSON as fallback
                mock_json.assert_called_once()
                messages_list, json_response, token_usage = result
                assert json_response == {"response": "data"}

        finally:
            Config.USE_PYDANTIC_PARSING = original_use_pydantic

    def test_schema_generation(self, mock_interface, mock_logger):
        """Test that Pydantic schema is properly generated"""
        from Writer.Models import ChapterOutput, OutlineOutput
        from Writer import Config

        # Enable pydantic
        original_use_pydantic = Config.USE_PYDANTIC_PARSING
        Config.USE_PYDANTIC_PARSING = True

        try:
            # Test ChapterOutput schema
            if hasattr(ChapterOutput, 'model_json_schema'):
                schema = ChapterOutput.model_json_schema()
            else:
                schema = ChapterOutput.schema()

            assert 'properties' in schema
            assert 'text' in schema['properties']
            assert 'word_count' in schema['properties']
            assert 'chapter_number' in schema['properties']

            # Test OutlineOutput schema
            if hasattr(OutlineOutput, 'model_json_schema'):
                outline_schema = OutlineOutput.model_json_schema()
            else:
                outline_schema = OutlineOutput.schema()

            assert 'properties' in outline_schema
            assert 'title' in outline_schema['properties']
            assert 'chapters' in outline_schema['properties']

        finally:
            Config.USE_PYDANTIC_PARSING = original_use_pydantic

    def test_fallback_extraction_for_chapter_output(self, mock_interface, mock_logger):
        """Test fallback extraction for ChapterOutput when partial data is available"""
        from Writer.Models import ChapterOutput
        from Writer import Config

        # Enable pydantic
        original_use_pydantic = Config.USE_PYDANTIC_PARSING
        Config.USE_PYDANTIC_PARSING = True

        try:
            messages = [{"role": "user", "content": "Write a chapter"}]

            with patch.object(mock_interface, 'SafeGenerateJSON') as mock_json:
                # Setup JSON response with only text field and invalid other fields
                mock_json.return_value = (
                    [{"role": "assistant", "content": "Chapter content here"}],
                    {
                        "text": "Alice walked through the dark forest. This chapter is long enough to meet the minimum requirements for validation testing purposes and ensure we have adequate word count.",
                        "word_count": "invalid",  # Invalid type
                        "missing_field": "some value"  # Not in model
                    },
                    {"tokens": 100}
                )

                # Call with ChapterOutput
                result = mock_interface.SafeGeneratePydantic(
                    mock_logger, messages, "test_model", ChapterOutput
                )

                # Should successfully extract and validate using fallback
                assert result is not None
                messages_list, validated_model, token_usage = result

                # Check the validated model
                assert isinstance(validated_model, ChapterOutput)
                assert validated_model.text == "Alice walked through the dark forest. This chapter is long enough to meet the minimum requirements for validation testing purposes and ensure we have adequate word count."
                assert validated_model.word_count == len(validated_model.text.split())
                assert validated_model.chapter_number == 1
                assert validated_model.scenes == []
                assert validated_model.characters_present == []

        finally:
            Config.USE_PYDANTIC_PARSING = original_use_pydantic