"""
Tests for Wrapper.py fragile pattern refactoring.

TDD London School tests for replacing fragile string matching patterns
with robust field constants and proper exception handling.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TestFragilePatternReplacement:
    """TDD tests for replacing fragile patterns in Wrapper.py"""

    def test_character_field_constraint_usesconstants(self):
        """Test that character field constraint uses FIELD constants instead of string matching"""
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])

        # Test constraint building for character field using proper signature
        properties = {
            'characters_present': {'minLength': 3},
            'text': {'minLength': 10},
            'word_count': {'minimum': 50}
        }
        constraint_explanation = interface._build_constraint_explanations(properties)

        # Should use robust character field detection
        assert "characters_present" in constraint_explanation
        assert "3 characters" in constraint_explanation

    def test_non_character_field_no_character_constraints(self):
        """Test that non-character fields don't get character-specific constraints"""
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])

        # Test constraint building for non-character field using proper signature
        properties = {
            'text': {'minLength': 10},  # Non-character field
            'word_count': {'minimum': 50}
        }
        constraint_explanation = interface._build_constraint_explanations(properties)

        # Should NOT trigger character field constraints
        assert "Each name must be at least" not in constraint_explanation

    def test_error_classification_uses_constants(self):
        """Test that error classification uses constants instead of fragile string matching"""
        from Writer.Interface.Wrapper import _is_validation_or_missing_error

        # Test missing field error detection using helper function
        missing_error = ValueError("Field 'title' missing from model")
        is_missing = _is_validation_or_missing_error(missing_error)

        # Should detect missing field without fragile string matching
        assert is_missing, "Should detect missing field error"

        # Test validation error detection
        validation_error = ValueError("Validation failed for field")
        is_validation = _is_validation_or_missing_error(validation_error)

        assert is_validation, "Should detect validation error"

        # Test non-matching error
        other_error = RuntimeError("Some other error")
        is_other = _is_validation_or_missing_error(other_error)

        # Should NOT detect as validation/missing error
        assert not is_other, "Should not detect other error as validation/missing"

    def test_validation_error_classification_uses_constants(self):
        """Test that validation error classification uses robust constants"""
        from Writer.Interface.Wrapper import _is_validation_or_missing_error
        from pydantic import ValidationError

        # Test Pydantic ValidationError detection
        validation_error = ValidationError.from_exception_data(
            "ChapterOutput",
            [
                {
                    "type": "string_too_short",
                    "loc": ("title",),
                    "msg": "String should have at least 1 character",
                    "input": "",
                    "ctx": {"min_length": 1}
                }
            ]
        )
        is_validation = _is_validation_or_missing_error(validation_error)

        # Should detect validation error without fragile string matching
        assert is_validation, "Should detect ValidationError as validation/missing error"

    @pytest.mark.parametrize("field_name", [
        'characters_present',
        'character_list',
        'character_details',
        'characters',
        'characters_and_setting'
    ])
    def test_character_fields_get_minimum_length_constraints(self, field_name):
        """Test that all character fields get appropriate minimum length constraints"""
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])

        # Test constraint building for character field
        properties = {
            field_name: {'minLength': 2}
        }

        constraint_explanation = interface._build_constraint_explanations(properties)

        # Character fields should get minimum length constraints
        assert "Each name must be at least 2 characters" in constraint_explanation

    @pytest.mark.parametrize("field_name", [
        'title',
        'genre',
        'setting',
        'plot',
        'themes',
        'characteristics',  # Similar but not a character field
    ])
    def test_non_character_fields_no_character_constraints(self, field_name):
        """Test that non-character fields don't get character constraints"""
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])

        # Test constraint building for non-character field
        properties = {
            field_name: {'minLength': 5}
        }

        constraint_explanation = interface._build_constraint_explanations(properties)

        # Non-character fields should NOT get character-specific constraints
        assert "Each name must be at least" not in constraint_explanation

    def test_field_constants_import_compatibility(self):
        """Test that FieldConstants can be imported and used in Wrapper"""
        from Writer.FieldConstants import (
            CHARACTER_FIELDS,
            is_character_field,
            classify_error
        )

        # Test that constants are available and functional
        assert isinstance(CHARACTER_FIELDS, set)
        assert callable(is_character_field)
        assert callable(classify_error)

        # Test basic functionality
        assert is_character_field('characters_present')
        assert not is_character_field('title')
        assert 'missing_field' in classify_error('field missing error')



