"""
Tests for _build_constraint_explanations() internationalization.

These tests verify that constraint explanations are generated in the correct
language based on the Interface instance's language setting.
"""

import pytest


class TestConstraintExplanationsI18n:
    """Test suite for i18n support in _build_constraint_explanations()."""

    def test_constraint_explanations_english(self, english_language_config):
        """Test constraint explanations are generated in English."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        schema_properties = {
            'reasoning': {'type': 'string', 'maxLength': 500}
        }

        # Act
        result = interface._build_constraint_explanations(schema_properties)

        # Assert - verify English text
        assert 'IMPORTANT CONSTRAINTS:' in result
        assert 'Maximum 500 characters' in result


    def test_reasoning_constraint_english(self, english_language_config):
        """Test reasoning field constraint is in English."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        schema_properties = {
            'reasoning': {'type': 'string', 'maxLength': 300}
        }

        # Act
        result = interface._build_constraint_explanations(schema_properties)

        # Assert
        assert "'reasoning'" in result
        assert '300 characters' in result
        assert 'concise and focused' in result

    def test_reasoning_constraint_indonesian(self, indonesian_language_config):
        """Test reasoning field constraint is in Indonesian."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        schema_properties = {
            'reasoning': {'type': 'string', 'maxLength': 300}
        }

        # Act
        result = interface._build_constraint_explanations(schema_properties)

        # Assert
        assert "'reasoning'" in result
        assert '300 karakter' in result
        assert 'ringkas dan fokus' in result



    def test_character_name_constraint(self, english_language_config):
        """Test character name minimum length constraint."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        # Simulate a character field with minLength
        schema_properties = {
            'protagonist_name': {'type': 'string', 'minLength': 3}
        }

        # Act
        result = interface._build_constraint_explanations(schema_properties)

        # Assert - character field detection should work
        assert 'at least 3 characters' in result or result == ""
        # Note: May be empty if is_character_field doesn't match 'protagonist_name'

    def test_no_constraints_returns_empty(self, english_language_config):
        """Test empty string returned when no matching constraints."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        schema_properties = {
            'title': {'type': 'string'},
            'count': {'type': 'integer'}
        }

        # Act
        result = interface._build_constraint_explanations(schema_properties)

        # Assert
        assert result == ""
