"""
Integration tests for StoryElements example Pydantic validation.

These tests verify that the examples in Wrapper._LANGUAGE_STRINGS can be
successfully parsed as JSON and pass all Pydantic model validators.

This is CRITICAL - examples must be valid to serve as good references for LLMs.
"""

import pytest
import json
from typing import Dict, Any


class TestStoryElementsExampleValidation:
    """Integration tests verifying examples pass Pydantic validation."""

    def extract_and_parse_example(self, example_string: str) -> Dict[str, Any]:
        """
        Helper to extract and parse JSON from example string.

        Handles double braces {{...}} template syntax.
        Raises pytest.fail() if JSON parsing fails.
        """
        fixed_json = example_string.replace('{{', '{').replace('}}', '}')

        try:
            return json.loads(fixed_json)
        except json.JSONDecodeError as e:
            pytest.fail(f"Failed to parse JSON: {e}\nContent: {fixed_json[:200]}")

    def test_english_example_parses_as_valid_json(self, english_language_config):
        """Test that English example is valid JSON after fixing template syntax."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['story_elements_example']

        # Act - Should not raise
        parsed_data = self.extract_and_parse_example(example_string)

        # Assert
        assert isinstance(parsed_data, dict), "Parsed example must be a dictionary"
        assert len(parsed_data) > 0, "Parsed example cannot be empty"

    def test_indonesian_example_parses_as_valid_json(self, indonesian_language_config):
        """Test that Indonesian example is valid JSON after fixing template syntax."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['id']['story_elements_example']

        # Act - Should not raise
        parsed_data = self.extract_and_parse_example(example_string)

        # Assert
        assert isinstance(parsed_data, dict), "Parsed example must be a dictionary"
        assert len(parsed_data) > 0, "Parsed example cannot be empty"

    def test_english_example_passes_all_validators(self, english_language_config):
        """Test that English example passes all StoryElements validators."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import StoryElements

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['story_elements_example']
        parsed_data = self.extract_and_parse_example(example_string)

        # Act - Should not raise ValidationError
        try:
            story_elements = StoryElements(**parsed_data)
        except Exception as e:
            pytest.fail(f"English example validation failed: {e}")

        # Assert - Verify key fields are populated
        assert story_elements.title is not None
        assert story_elements.genre is not None
        assert len(story_elements.themes) > 0
        assert len(story_elements.characters) > 0

        # Verify optional fields are present in example
        if parsed_data.get('plot_structure'):
            assert story_elements.plot_structure is not None
            assert len(story_elements.plot_structure) == 5, "plot_structure should have 5 keys"

        if parsed_data.get('settings'):
            assert len(story_elements.settings) > 0, "settings should have at least 1 setting"

        if parsed_data.get('resolution'):
            assert story_elements.resolution is not None

    def test_indonesian_example_passes_all_validators(self, indonesian_language_config):
        """Test that Indonesian example passes all StoryElements validators."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import StoryElements

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['id']['story_elements_example']
        parsed_data = self.extract_and_parse_example(example_string)

        # Act - Should not raise ValidationError
        try:
            story_elements = StoryElements(**parsed_data)
        except Exception as e:
            pytest.fail(f"Indonesian example validation failed: {e}")

        # Assert - Verify key fields are populated
        assert story_elements.title is not None
        assert story_elements.genre is not None
        assert len(story_elements.themes) > 0
        assert len(story_elements.characters) > 0

        # Verify optional fields are present in example
        if parsed_data.get('plot_structure'):
            assert story_elements.plot_structure is not None
            assert len(story_elements.plot_structure) == 5, "plot_structure should have 5 keys"

        if parsed_data.get('settings'):
            assert len(story_elements.settings) > 0, "settings should have at least 1 setting"

        if parsed_data.get('resolution'):
            assert story_elements.resolution is not None

    def test_plot_structure_passes_validator(self, english_language_config):
        """Test that plot_structure field passes the model's validator."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import StoryElements

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['story_elements_example']
        parsed_data = self.extract_and_parse_example(example_string)

        # Act
        story_elements = StoryElements(**parsed_data)

        # Assert - plot_structure validator checks for non-empty values
        if story_elements.plot_structure:
            for key, value in story_elements.plot_structure.items():
                assert len(value.strip()) > 0, \
                    f"plot_structure[{key}] has empty value (validator should catch this)"

    def test_settings_passes_validator(self, english_language_config):
        """Test that settings field passes the model's nested validator."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import StoryElements

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['story_elements_example']
        parsed_data = self.extract_and_parse_example(example_string)

        # Act
        story_elements = StoryElements(**parsed_data)

        # Assert - settings validator checks nested Dict[str, Dict[str, str]]
        if story_elements.settings:
            for setting_name, setting_details in story_elements.settings.items():
                assert isinstance(setting_details, dict), \
                    f"settings[{setting_name}] must be dict"

                for detail_key, detail_value in setting_details.items():
                    assert isinstance(detail_value, str), \
                        f"settings[{setting_name}][{detail_key}] must be string"
                    assert len(detail_value.strip()) > 0, \
                        f"settings[{setting_name}][{detail_key}] cannot be empty"

    def test_symbolism_passes_validator(self, english_language_config):
        """Test that symbolism field passes the model's array-of-dicts validator."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import StoryElements

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['story_elements_example']
        parsed_data = self.extract_and_parse_example(example_string)

        # Act
        story_elements = StoryElements(**parsed_data)

        # Assert - symbolism validator checks List[Dict[str, str]] structure
        if story_elements.symbolism:
            assert isinstance(story_elements.symbolism, list), \
                "symbolism must be a list"

            for symbol_entry in story_elements.symbolism:
                assert isinstance(symbol_entry, dict), \
                    "Each symbolism entry must be a dict"
                assert 'symbol' in symbol_entry, \
                    "symbolism entry must have 'symbol' key"
                assert 'meaning' in symbol_entry, \
                    "symbolism entry must have 'meaning' key"
                assert len(symbol_entry['symbol'].strip()) > 0, \
                    "symbol cannot be empty"
                assert len(symbol_entry['meaning'].strip()) > 0, \
                    "meaning cannot be empty"

    def test_characters_nested_structure_passes_validator(self, english_language_config):
        """Test that characters field with CharacterDetail objects passes validation."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import StoryElements

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['story_elements_example']
        parsed_data = self.extract_and_parse_example(example_string)

        # Act
        story_elements = StoryElements(**parsed_data)

        # Assert - characters is Dict[str, List[CharacterDetail]]
        assert isinstance(story_elements.characters, dict), "characters must be dict"

        for character_type, character_list in story_elements.characters.items():
            assert isinstance(character_list, list), \
                f"characters[{character_type}] must be list"

            for character in character_list:
                # CharacterDetail has a required 'name' field
                assert hasattr(character, 'name'), \
                    "CharacterDetail must have 'name' attribute"
                assert len(character.name) >= 2, \
                    "Character name must be at least 2 characters (validator requirement)"
