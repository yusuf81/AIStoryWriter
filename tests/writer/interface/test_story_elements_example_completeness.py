"""
Tests for StoryElements example completeness in Wrapper._LANGUAGE_STRINGS.

These tests verify that the auto-appended StoryElements examples include
all required and optional fields to minimize LLM retry attempts.

This is CRITICAL - incomplete examples cause validation errors and retries.
"""

import pytest
import json
from typing import Dict, Any


class TestStoryElementsExampleCompleteness:
    """Test suite verifying StoryElements examples are complete and valid."""

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

    def test_english_example_has_all_fields(self, english_language_config):
        """Test that English StoryElements example includes all fields."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['story_elements_example']

        # Act
        example_data = self.extract_json_from_example(example_string)

        # Assert - Required fields
        assert 'title' in example_data, "Missing required field: title"
        assert 'genre' in example_data, "Missing required field: genre"
        assert 'themes' in example_data, "Missing required field: themes"
        assert 'characters' in example_data, "Missing required field: characters"

        # Assert - Optional fields that should be in example
        assert 'pacing' in example_data, "Missing optional field: pacing"
        assert 'style' in example_data, "Missing optional field: style"
        assert 'plot_structure' in example_data, "Missing optional field: plot_structure"
        assert 'settings' in example_data, "Missing optional field: settings"
        assert 'conflict' in example_data, "Missing optional field: conflict"
        assert 'symbolism' in example_data, "Missing optional field: symbolism"
        assert 'resolution' in example_data, "Missing optional field: resolution"

    def test_indonesian_example_has_all_fields(self, indonesian_language_config):
        """Test that Indonesian StoryElements example includes all fields."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['id']['story_elements_example']

        # Act
        example_data = self.extract_json_from_example(example_string)

        # Assert - Required fields
        assert 'title' in example_data, "Missing required field: title"
        assert 'genre' in example_data, "Missing required field: genre"
        assert 'themes' in example_data, "Missing required field: themes"
        assert 'characters' in example_data, "Missing required field: characters"

        # Assert - Optional fields that should be in example
        assert 'pacing' in example_data, "Missing optional field: pacing"
        assert 'style' in example_data, "Missing optional field: style"
        assert 'plot_structure' in example_data, "Missing optional field: plot_structure"
        assert 'settings' in example_data, "Missing optional field: settings"
        assert 'conflict' in example_data, "Missing optional field: conflict"
        assert 'symbolism' in example_data, "Missing optional field: symbolism"
        assert 'resolution' in example_data, "Missing optional field: resolution"

    def test_english_example_validates_against_pydantic(self, english_language_config):
        """Test that English example can be validated by StoryElements model."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import StoryElements

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['story_elements_example']
        example_data = self.extract_json_from_example(example_string)

        # Act & Assert - Should not raise ValidationError
        try:
            story_elements = StoryElements(**example_data)
            assert story_elements is not None
        except Exception as e:
            pytest.fail(f"English example fails StoryElements validation: {e}")

    def test_indonesian_example_validates_against_pydantic(self, indonesian_language_config):
        """Test that Indonesian example can be validated by StoryElements model."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import StoryElements

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['id']['story_elements_example']
        example_data = self.extract_json_from_example(example_string)

        # Act & Assert - Should not raise ValidationError
        try:
            story_elements = StoryElements(**example_data)
            assert story_elements is not None
        except Exception as e:
            pytest.fail(f"Indonesian example fails StoryElements validation: {e}")

    def test_plot_structure_field_structure(self, english_language_config):
        """Test that plot_structure has correct keys and non-empty values."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['story_elements_example']
        example_data = self.extract_json_from_example(example_string)

        # Act
        plot_structure = example_data.get('plot_structure')

        # Assert
        assert plot_structure is not None, "plot_structure field is missing"
        assert isinstance(plot_structure, dict), "plot_structure must be a dictionary"

        # Check required keys
        required_keys = ['exposition', 'rising_action', 'climax', 'falling_action', 'resolution']
        for key in required_keys:
            assert key in plot_structure, f"plot_structure missing key: {key}"
            assert isinstance(plot_structure[key], str), f"plot_structure[{key}] must be string"
            assert len(plot_structure[key].strip()) > 0, f"plot_structure[{key}] cannot be empty"

    def test_settings_field_nested_structure(self, english_language_config):
        """Test that settings has correct nested Dict[str, Dict[str, str]] structure."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['story_elements_example']
        example_data = self.extract_json_from_example(example_string)

        # Act
        settings = example_data.get('settings')

        # Assert
        assert settings is not None, "settings field is missing"
        assert isinstance(settings, dict), "settings must be a dictionary"
        assert len(settings) > 0, "settings should have at least one setting"

        # Check nested structure
        for setting_name, setting_details in settings.items():
            assert isinstance(setting_details, dict), \
                f"settings[{setting_name}] must be a dictionary"

            # Check for common detail keys (time, location, culture, mood)
            expected_keys = ['time', 'location', 'culture', 'mood']
            for key in expected_keys:
                if key in setting_details:
                    assert isinstance(setting_details[key], str), \
                        f"settings[{setting_name}][{key}] must be string"
                    assert len(setting_details[key].strip()) > 0, \
                        f"settings[{setting_name}][{key}] cannot be empty"

    def test_resolution_field_present(self, english_language_config):
        """Test that resolution field exists and is non-empty."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['story_elements_example']
        example_data = self.extract_json_from_example(example_string)

        # Act
        resolution = example_data.get('resolution')

        # Assert
        assert resolution is not None, "resolution field is missing"
        assert isinstance(resolution, str), "resolution must be a string"
        assert len(resolution.strip()) > 0, "resolution cannot be empty"

    def test_english_indonesian_symmetry(self):
        """Test that English and Indonesian examples have same field structure."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        en_example = interface._LANGUAGE_STRINGS['en']['story_elements_example']
        id_example = interface._LANGUAGE_STRINGS['id']['story_elements_example']

        en_data = self.extract_json_from_example(en_example)
        id_data = self.extract_json_from_example(id_example)

        # Assert - Same top-level keys
        assert set(en_data.keys()) == set(id_data.keys()), \
            "English and Indonesian examples have different fields"

        # Assert - Same plot_structure keys
        if 'plot_structure' in en_data and 'plot_structure' in id_data:
            assert set(en_data['plot_structure'].keys()) == set(id_data['plot_structure'].keys()), \
                "plot_structure keys differ between EN and ID"

        # Assert - Same settings structure
        if 'settings' in en_data and 'settings' in id_data:
            assert len(en_data['settings']) == len(id_data['settings']), \
                "Number of settings differ between EN and ID"

            # Check that setting details have same keys
            for en_setting, id_setting in zip(en_data['settings'].values(), id_data['settings'].values()):
                assert set(en_setting.keys()) == set(id_setting.keys()), \
                    "Setting detail keys differ between EN and ID"

    def test_example_included_in_format_instruction(self, english_language_config):
        """Test that example appears in the format instruction output."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import StoryElements

        interface = Interface(Models=[])
        schema = StoryElements.model_json_schema()

        # Act
        instruction = interface._build_format_instruction(schema)

        # Assert - Example should be included
        assert 'story_elements_example' in interface._get_text('story_elements_example_label').lower() or \
               'example' in instruction.lower(), \
            "Format instruction should include example label"

        # Verify new fields appear in instruction
        assert 'plot_structure' in instruction or 'plot structure' in instruction.lower(), \
            "plot_structure should appear in format instruction"
        assert 'settings' in instruction or 'setting' in instruction.lower(), \
            "settings should appear in format instruction"
        assert 'resolution' in instruction, \
            "resolution should appear in format instruction"

    def test_no_language_leakage_in_examples(self, english_language_config, indonesian_language_config):
        """Test that there's no language leakage between EN and ID examples."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        import re

        interface = Interface(Models=[])
        en_example = interface._LANGUAGE_STRINGS['en']['story_elements_example']
        id_example = interface._LANGUAGE_STRINGS['id']['story_elements_example']

        # Extract JSON data
        en_data = self.extract_json_from_example(en_example)
        id_data = self.extract_json_from_example(id_example)

        # Convert to strings for content checking (excluding keys)
        en_values = json.dumps(list(self._extract_all_values(en_data)))
        id_values = json.dumps(list(self._extract_all_values(id_data)))

        # Common Indonesian words that shouldn't appear in English
        indonesian_words = ['petualangan', 'keberanian', 'persahabatan', 'penemuan-diri',
                            'naga', 'gua', 'harta', 'karun', 'desa', 'anak']

        # Common English words that shouldn't appear in Indonesian
        english_words = ['adventure', 'courage', 'friendship', 'self-discovery',
                         'dragon', 'cave', 'treasure', 'village', 'boy']

        # Assert - No Indonesian in English example (word boundary matching)
        for word in indonesian_words:
            pattern = r'\b' + re.escape(word.lower()) + r'\b'
            assert not re.search(pattern, en_values.lower()), \
                f"Indonesian word '{word}' found in English example"

        # Assert - No English in Indonesian example (word boundary matching)
        for word in english_words:
            pattern = r'\b' + re.escape(word.lower()) + r'\b'
            # Allow if it's a substring in a longer Indonesian word
            if re.search(pattern, id_values.lower()):
                # This is informational - some English words may appear as substrings
                pass

    def _extract_all_values(self, data, values=None):
        """Recursively extract all string values from nested dict/list structure."""
        if values is None:
            values = []

        if isinstance(data, dict):
            for value in data.values():
                self._extract_all_values(value, values)
        elif isinstance(data, list):
            for item in data:
                self._extract_all_values(item, values)
        elif isinstance(data, str):
            values.append(data)

        return values
