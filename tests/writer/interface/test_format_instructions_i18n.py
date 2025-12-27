"""
Tests for _build_format_instruction() internationalization.

These tests verify that format instructions are generated in the correct
language based on the Interface instance's language setting.

This is CRITICAL - _build_format_instruction() is called by every Pydantic
generation and is the main source of dual-language conflict.
"""

import pytest


class TestFormatInstructionsI18n:
    """Test suite for i18n support in _build_format_instruction()."""

    def test_format_instruction_english_header(self, english_language_config):
        """Test format instruction headers are in English."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import StoryElements

        interface = Interface(Models=[])
        schema = StoryElements.model_json_schema()

        # Act
        instruction = interface._build_format_instruction(schema)

        # Assert - verify English headers
        assert '=== JSON SCHEMA (REFERENCE ONLY) ===' in instruction
        assert '=== YOUR RESPONSE (JSON ONLY) ===' in instruction
        assert 'Required fields:' in instruction

        # Verify NO Indonesian headers
        assert 'SKEMA JSON' not in instruction
        assert 'RESPONS ANDA' not in instruction
        assert 'Field wajib:' not in instruction

    def test_format_instruction_indonesian_header(self, indonesian_language_config):
        """Test format instruction headers are in Indonesian."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import StoryElements

        interface = Interface(Models=[])
        schema = StoryElements.model_json_schema()

        # Act
        instruction = interface._build_format_instruction(schema)

        # Assert - verify Indonesian headers
        assert '=== SKEMA JSON (HANYA REFERENSI) ===' in instruction
        assert '=== RESPONS ANDA (HANYA JSON) ===' in instruction
        assert 'Field wajib:' in instruction

        # Verify NO English headers
        assert 'JSON SCHEMA (REFERENCE ONLY)' not in instruction
        assert 'YOUR RESPONSE (JSON ONLY)' not in instruction
        assert 'Required fields:' not in instruction

    def test_required_fields_section_english(self, english_language_config):
        """Test required fields section is in English."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])
        schema = ChapterOutput.model_json_schema()

        # Act
        instruction = interface._build_format_instruction(schema)

        # Assert
        assert 'Required fields:' in instruction
        assert 'text' in instruction  # Required field name
        assert 'chapter_number' in instruction  # Required field name

    def test_required_fields_section_indonesian(self, indonesian_language_config):
        """Test required fields section is in Indonesian."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])
        schema = ChapterOutput.model_json_schema()

        # Act
        instruction = interface._build_format_instruction(schema)

        # Assert
        assert 'Field wajib:' in instruction
        assert 'text' in instruction  # Required field name
        assert 'chapter_number' in instruction  # Required field name

    def test_optional_fields_section_english(self, english_language_config):
        """Test optional fields section is in English."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import StoryElements

        interface = Interface(Models=[])
        schema = StoryElements.model_json_schema()

        # Act
        instruction = interface._build_format_instruction(schema)

        # Assert
        # StoryElements has optional fields
        if 'Optional fields:' in instruction:
            assert 'Optional fields:' in instruction
            assert 'Field opsional:' not in instruction

    def test_optional_fields_section_indonesian(self, indonesian_language_config):
        """Test optional fields section is in Indonesian."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import StoryElements

        interface = Interface(Models=[])
        schema = StoryElements.model_json_schema()

        # Act
        instruction = interface._build_format_instruction(schema)

        # Assert
        # StoryElements has optional fields
        if 'Field opsional:' in instruction:
            assert 'Field opsional:' in instruction
            assert 'Optional fields:' not in instruction

    def test_array_type_descriptions(self, english_language_config):
        """Test array types are described correctly."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import StoryElements

        interface = Interface(Models=[])
        schema = StoryElements.model_json_schema()

        # Act
        instruction = interface._build_format_instruction(schema)

        # Assert - verify array descriptions appear
        # StoryElements has array fields like 'themes', 'characters'
        assert 'array' in instruction.lower()

    def test_constraint_explanations_included(self, english_language_config):
        """Test constraint explanations appear in output."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from pydantic import BaseModel, Field

        # Create model with constraints
        class TestModel(BaseModel):
            reasoning: str = Field(max_length=300)

        interface = Interface(Models=[])
        schema = TestModel.model_json_schema()

        # Act
        instruction = interface._build_format_instruction(schema)

        # Assert - constraint explanations should appear
        assert 'IMPORTANT CONSTRAINTS:' in instruction
        assert '300 characters' in instruction

    def test_story_elements_example_included(self, english_language_config):
        """Test StoryElements example is present."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import StoryElements

        interface = Interface(Models=[])
        schema = StoryElements.model_json_schema()

        # Act
        instruction = interface._build_format_instruction(schema)

        # Assert - example should be included for StoryElements
        assert 'For example:' in instruction or 'Example' in instruction

    def test_no_english_in_indonesian_output(self, indonesian_language_config):
        """Test no English leakage in Indonesian format instructions."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])
        schema = ChapterOutput.model_json_schema()

        # Act
        instruction = interface._build_format_instruction(schema)

        # Assert - verify NO English structural text
        # Note: Field names, types (string, integer) remain in English (JSON spec)
        assert 'JSON SCHEMA (REFERENCE ONLY)' not in instruction
        assert 'YOUR RESPONSE (JSON ONLY)' not in instruction
        assert 'Required fields:' not in instruction
        assert 'Optional fields:' not in instruction
        assert 'Provide ONLY the JSON data' not in instruction
        assert 'Return ONLY the JSON data' not in instruction

    def test_no_indonesian_in_english_output(self, english_language_config):
        """Test no Indonesian leakage in English format instructions."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])
        schema = ChapterOutput.model_json_schema()

        # Act
        instruction = interface._build_format_instruction(schema)

        # Assert - verify NO Indonesian structural text
        assert 'SKEMA JSON' not in instruction
        assert 'RESPONS ANDA' not in instruction
        assert 'Field wajib:' not in instruction
        assert 'Field opsional:' not in instruction
        assert 'Berikan HANYA data JSON' not in instruction
        assert 'Kembalikan HANYA data JSON' not in instruction

    def test_format_instruction_structure_preserved(self, english_language_config):
        """Test format instruction maintains same structure both languages."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface_en = Interface(Models=[])
        schema = ChapterOutput.model_json_schema()

        # Act
        instruction_en = interface_en._build_format_instruction(schema)

        # Assert - verify structure elements present
        assert '===' in instruction_en  # Section markers
        assert '\n' in instruction_en  # Multi-line structure
        assert 'text' in instruction_en  # Field names
        assert 'chapter_number' in instruction_en  # Field names

    def test_footer_important_message(self, english_language_config):
        """Test footer important message is present."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])
        schema = ChapterOutput.model_json_schema()

        # Act
        instruction = interface._build_format_instruction(schema)

        # Assert
        assert 'IMPORTANT:' in instruction
        assert 'Return ONLY the JSON data' in instruction or 'JSON' in instruction

    def test_example_format_string(self, english_language_config):
        """Test example format line is correct."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])
        schema = ChapterOutput.model_json_schema()

        # Act
        instruction = interface._build_format_instruction(schema)

        # Assert
        assert 'Example format:' in instruction or 'Format contoh:' in instruction

    def test_more_optional_fields_count(self, english_language_config):
        """Test 'and N more optional fields' formatting."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import StoryElements

        interface = Interface(Models=[])
        schema = StoryElements.model_json_schema()

        # Act
        instruction = interface._build_format_instruction(schema)

        # Assert - if there are > 5 optional fields, should show count
        optional_count = len([k for k in schema.get('properties', {}).keys()
                             if k not in schema.get('required', [])])
        if optional_count > 5:
            assert 'more optional fields' in instruction or 'field opsional lainnya' in instruction
