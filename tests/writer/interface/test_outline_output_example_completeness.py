"""
Tests for OutlineOutput example completeness in Wrapper._LANGUAGE_STRINGS.

These tests verify that the auto-appended OutlineOutput examples include
all required and optional fields to minimize LLM retry attempts.
"""

import pytest
import json
from typing import Dict, Any


class TestOutlineOutputExampleCompleteness:
    """Test suite verifying OutlineOutput examples are complete and valid."""

    def extract_json_from_example(self, example_string: str) -> Dict[str, Any]:
        """
        Helper to extract and parse JSON from example string.

        Handles double braces {{...}} which are template syntax, not valid JSON.
        """
        # Fix double braces for template syntax
        fixed_json = example_string.replace('{{', '{').replace('}}', '}')

        try:
            return json.loads(fixed_json)
        except json.JSONDecodeError as e:
            pytest.fail(f"Failed to parse JSON from example: {e}")

    def test_english_outline_example_has_all_fields(self, english_language_config):
        """Test that English OutlineOutput example includes all fields."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['outline_output_example']

        # Act
        example_data = self.extract_json_from_example(example_string)

        # Assert - Required fields
        assert 'title' in example_data, "Missing required field: title"
        assert 'chapters' in example_data, "Missing required field: chapters"
        assert 'character_list' in example_data, "Missing required field: character_list"
        assert 'target_chapter_count' in example_data, "Missing required field: target_chapter_count"

        # Assert - Optional fields that should be in example
        assert 'genre' in example_data, "Missing optional field: genre"
        assert 'theme' in example_data, "Missing optional field: theme"
        assert 'character_details' in example_data, "Missing optional field: character_details"
        assert 'setting' in example_data, "Missing optional field: setting"

    def test_indonesian_outline_example_has_all_fields(self, indonesian_language_config):
        """Test that Indonesian OutlineOutput example includes all fields."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['id']['outline_output_example']

        # Act
        example_data = self.extract_json_from_example(example_string)

        # Assert - Required fields
        assert 'title' in example_data, "Missing required field: title"
        assert 'chapters' in example_data, "Missing required field: chapters"
        assert 'character_list' in example_data, "Missing required field: character_list"
        assert 'target_chapter_count' in example_data, "Missing required field: target_chapter_count"

        # Assert - Optional fields that should be in example
        assert 'genre' in example_data, "Missing optional field: genre"
        assert 'theme' in example_data, "Missing optional field: theme"
        assert 'character_details' in example_data, "Missing optional field: character_details"
        assert 'setting' in example_data, "Missing optional field: setting"

    def test_setting_field_structure(self, english_language_config):
        """Test that setting has correct Dict[str, str] structure."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['outline_output_example']
        example_data = self.extract_json_from_example(example_string)

        # Act
        setting = example_data.get('setting')

        # Assert
        assert setting is not None, "setting field is missing"
        assert isinstance(setting, dict), "setting must be a dictionary"

        # Check required keys (flat dict, not nested!)
        expected_keys = ['time', 'location', 'culture', 'mood']
        for key in expected_keys:
            assert key in setting, f"setting missing key: {key}"
            assert isinstance(setting[key], str), f"setting[{key}] must be string"
            assert len(setting[key].strip()) > 0, f"setting[{key}] cannot be empty"

    def test_character_details_field_structure(self, english_language_config):
        """Test that character_details has correct Dict[str, str] structure."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['outline_output_example']
        example_data = self.extract_json_from_example(example_string)

        # Act
        character_details = example_data.get('character_details')

        # Assert
        assert character_details is not None, "character_details field is missing"
        assert isinstance(character_details, dict), "character_details must be a dictionary"
        assert len(character_details) > 0, "character_details should have at least one character"

        # Check structure (name → description mapping)
        for name, description in character_details.items():
            assert isinstance(name, str), "character name must be string"
            assert isinstance(description, str), "character description must be string"
            assert len(name.strip()) > 0, "character name cannot be empty"
            assert len(description.strip()) > 0, "character description cannot be empty"

    def test_english_example_validates_against_pydantic(self, english_language_config):
        """Test that English example can be validated by OutlineOutput model."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import OutlineOutput

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['outline_output_example']
        example_data = self.extract_json_from_example(example_string)

        # Act & Assert - Should not raise ValidationError
        try:
            outline_output = OutlineOutput(**example_data)
            assert outline_output is not None
        except Exception as e:
            pytest.fail(f"English example fails OutlineOutput validation: {e}")

    def test_indonesian_example_validates_against_pydantic(self, indonesian_language_config):
        """Test that Indonesian example can be validated by OutlineOutput model."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import OutlineOutput

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['id']['outline_output_example']
        example_data = self.extract_json_from_example(example_string)

        # Act & Assert - Should not raise ValidationError
        try:
            outline_output = OutlineOutput(**example_data)
            assert outline_output is not None
        except Exception as e:
            pytest.fail(f"Indonesian example fails OutlineOutput validation: {e}")

    def test_english_indonesian_symmetry(self):
        """Test that English and Indonesian examples have same field structure."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        en_example = interface._LANGUAGE_STRINGS['en']['outline_output_example']
        id_example = interface._LANGUAGE_STRINGS['id']['outline_output_example']

        en_data = self.extract_json_from_example(en_example)
        id_data = self.extract_json_from_example(id_example)

        # Assert - Same top-level keys
        assert set(en_data.keys()) == set(id_data.keys()), \
            "English and Indonesian examples have different fields"

        # Assert - Same setting keys
        if 'setting' in en_data and 'setting' in id_data:
            assert set(en_data['setting'].keys()) == set(id_data['setting'].keys()), \
                "setting keys differ between EN and ID"

        # Assert - Same number of character_details
        if 'character_details' in en_data and 'character_details' in id_data:
            assert len(en_data['character_details']) == len(id_data['character_details']), \
                "Number of character_details differ between EN and ID"
