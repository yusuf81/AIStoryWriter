"""
Tests for Wrapper.py language string dictionaries and _get_text() helper method.

These tests verify that the Interface class provides language-specific strings
for both English and Indonesian through the _get_text() helper method.
"""

import pytest


class TestWrapperLanguageStrings:
    """Test suite for Interface language strings dictionary and helper method."""

    def test_get_text_english_language(self, english_language_config):
        """Test _get_text returns English strings when language='en'."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        interface = Interface(Models=[])

        # Act
        header = interface._get_text('json_schema_header')

        # Assert
        assert header == "=== JSON SCHEMA (REFERENCE ONLY) ==="
        assert 'JSON SCHEMA' in header
        assert 'SKEMA JSON' not in header  # No Indonesian

    def test_get_text_indonesian_language(self, indonesian_language_config):
        """Test _get_text returns Indonesian strings when language='id'."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        interface = Interface(Models=[])

        # Act
        header = interface._get_text('json_schema_header')

        # Assert
        assert header == "=== SKEMA JSON (HANYA REFERENSI) ==="
        assert 'SKEMA JSON' in header  # Indonesian word
        assert 'JSON SCHEMA' not in header  # No English

    def test_get_text_with_formatting(self, english_language_config):
        """Test _get_text handles {placeholder} formatting correctly."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        interface = Interface(Models=[])

        # Act
        formatted = interface._get_text('more_optional_fields', count=5)

        # Assert
        assert '5' in formatted
        assert 'more optional fields' in formatted.lower()

    def test_get_text_fallback_to_english(self):
        """Test _get_text falls back to English for invalid language."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from unittest.mock import patch

        # Patch to invalid language
        with patch('Writer.Config.NATIVE_LANGUAGE', 'invalid'):
            interface = Interface(Models=[])

            # Act
            header = interface._get_text('json_schema_header')

            # Assert - should fall back to English
            assert header == "=== JSON SCHEMA (REFERENCE ONLY) ==="

    def test_get_text_missing_key_returns_empty(self, english_language_config):
        """Test _get_text returns empty string for missing key."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        interface = Interface(Models=[])

        # Act
        result = interface._get_text('nonexistent_key')

        # Assert
        assert result == ""

    def test_all_english_keys_have_indonesian(self):
        """Test all English keys exist in Indonesian dictionary."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        # Access class variable directly
        en_keys = set(Interface._LANGUAGE_STRINGS['en'].keys())
        id_keys = set(Interface._LANGUAGE_STRINGS['id'].keys())

        # Assert
        assert en_keys == id_keys, f"Missing keys in ID: {en_keys - id_keys}"

    def test_json_schema_header_translations(self):
        """Test json_schema_header key exists in both languages."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        en_text = Interface._LANGUAGE_STRINGS['en']['json_schema_header']
        id_text = Interface._LANGUAGE_STRINGS['id']['json_schema_header']

        # Assert
        assert 'JSON SCHEMA' in en_text
        assert 'SKEMA JSON' in id_text

    def test_validation_error_translations(self):
        """Test validation error messages exist in both languages."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        en_header = Interface._LANGUAGE_STRINGS['en']['validation_error_header']
        id_header = Interface._LANGUAGE_STRINGS['id']['validation_error_header']

        # Assert
        assert 'validation errors' in en_header.lower()
        assert 'kesalahan validasi' in id_header.lower()

    def test_constraint_translations(self):
        """Test constraint explanation strings exist in both languages."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        en_constraints = Interface._LANGUAGE_STRINGS['en']['important_constraints']
        id_constraints = Interface._LANGUAGE_STRINGS['id']['important_constraints']

        # Assert
        assert 'IMPORTANT CONSTRAINTS' in en_constraints
        assert 'BATASAN PENTING' in id_constraints

    def test_hint_translations(self):
        """Test hint messages exist in both languages."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        en_hint = Interface._LANGUAGE_STRINGS['en']['hint_single_json']
        id_hint = Interface._LANGUAGE_STRINGS['id']['hint_single_json']

        # Assert
        assert 'Hint:' in en_hint
        assert 'Petunjuk:' in id_hint

    def test_array_type_translations(self):
        """Test array type descriptions exist in both languages."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        en_array = Interface._LANGUAGE_STRINGS['en']['array_of_strings_required']
        id_array = Interface._LANGUAGE_STRINGS['id']['array_of_strings_required']

        # Assert
        assert 'array of strings' in en_array.lower()
        assert 'Required' in en_array or 'Wajib' in id_array

    def test_formatting_preserves_placeholders(self, english_language_config):
        """Test _get_text preserves multiple {var} placeholders with formatting."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        interface = Interface(Models=[])

        # Act
        formatted = interface._get_text(
            'constraint_reasoning_max',
            field='reasoning',
            max_len=500
        )

        # Assert
        assert "'reasoning'" in formatted
        assert '500' in formatted
        assert 'Maximum' in formatted
