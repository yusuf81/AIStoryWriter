# tests/writer/test_field_constants.py
"""
TDD London School tests for field constants to replace fragile patterns.

Tests are written first (RED phase) to define expected behavior.
"""
import pytest

# Import the module we're testing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestCharacterFieldConstants:
    """TDD tests for character field constant detection"""

    @pytest.mark.parametrize("field", [
        'characters_present',
        'character_list',
        'character_details',
        'characters',
        'characters_and_setting'
    ])
    def test_character_field_detection_all_fields(self, field):
        """Test that all character fields are detected correctly"""
        from Writer.FieldConstants import CHARACTER_FIELDS, is_character_field

        assert is_character_field(field), f"'{field}' should be detected as character field"
        assert field in CHARACTER_FIELDS, f"'{field}' should be in CHARACTER_FIELDS constant"

    @pytest.mark.parametrize("field", [
        'title',
        'genre',
        'setting',
        'plot',
        'themes',
        'characteristics',  # Similar but not a character field
        'characterization',  # Similar but not a character field
        'main_character_name'  # Would be handled separately
    ])
    def test_non_character_field_rejection(self, field):
        """Test that non-character fields are correctly rejected"""
        from Writer.FieldConstants import CHARACTER_FIELDS, is_character_field

        assert not is_character_field(field), f"'{field}' should NOT be detected as character field"
        assert field not in CHARACTER_FIELDS, f"'{field}' should NOT be in CHARACTER_FIELDS constant"

    @pytest.mark.parametrize("field_name", [
        "characters_present",
        "CHARACTERS_PRESENT",
        "Characters_Present",
        "cHaRaCtErS_pReSeNt"
    ])
    def test_case_insensitive_character_field_detection(self, field_name):
        """Test that character field detection works with different cases"""
        from Writer.FieldConstants import is_character_field

        # Should be case insensitive for robustness
        assert is_character_field(field_name), f"Case-insensitive detection should work for '{field_name}'"

    def test_character_fields_constant_is_set(self):
        """Test that CHARACTER_FIELDS is a proper set constant"""
        from Writer.FieldConstants import CHARACTER_FIELDS

        assert isinstance(CHARACTER_FIELDS, set), "CHARACTER_FIELDS should be a set for O(1) lookup"
        assert len(CHARACTER_FIELDS) > 0, "CHARACTER_FIELDS should not be empty"

        # Verify all entries are strings
        for field in CHARACTER_FIELDS:
            assert isinstance(field, str), f"Field '{field}' should be a string"


class TestSectionPatterns:
    """TDD tests for section pattern constants"""

    def test_section_patterns_constants_exist(self):
        """Test that all section pattern constants exist"""
        from Writer.FieldConstants import (
            STORY_OUTLINE,
            GENERATION_STATISTICS,
            METADATA_SECTIONS
        )

        assert STORY_OUTLINE is not None, "STORY_OUTLINE constant should exist"
        assert GENERATION_STATISTICS is not None, "GENERATION_STATISTICS constant should exist"
        assert isinstance(METADATA_SECTIONS, list), "METADATA_SECTIONS should be a list"
        assert len(METADATA_SECTIONS) > 0, "METADATA_SECTIONS should not be empty"

    def test_story_outline_detection(self):
        """Test story outline section detection"""
        from Writer.FieldConstants import is_story_outline_section

        assert is_story_outline_section("# Story Outline"), "Should detect story outline section"
        assert is_story_outline_section("# Story Outline content"), "Should detect story outline with content"
        assert not is_story_outline_section("# Chapter 1"), "Should not detect regular chapter as story outline"
        assert not is_story_outline_section("Story Outline"), "Should not detect without # prefix"

    def test_generation_statistics_detection(self):
        """Test generation statistics section detection"""
        from Writer.FieldConstants import is_generation_statistics_section

        assert is_generation_statistics_section("# Generation Statistics"), "Should detect generation statistics"
        assert is_generation_statistics_section("# Generation Statistics here"), "Should detect with content"
        assert not is_generation_statistics_section("# Chapter 1"), "Should not detect regular chapter"
        assert not is_generation_statistics_section("Generation Statistics"), "Should not detect without # prefix"

    def test_metadata_section_detection(self):
        """Test metadata section detection"""
        from Writer.FieldConstants import is_metadata_section

        # Test all metadata sections are detected
        assert is_metadata_section("## Summary"), "Should detect Summary section"
        assert is_metadata_section("## Tags"), "Should detect Tags section"
        assert is_metadata_section("## Summary content here"), "Should detect Summary with content"

        # Test non-metadata sections are rejected
        assert not is_metadata_section("## Chapter 1"), "Should not detect chapter as metadata"
        assert not is_metadata_section("# Summary"), "Should not detect wrong heading level"

    def test_whitespace_handling_in_sections(self):
        """Test that section detection handles whitespace properly"""
        from Writer.FieldConstants import (
            is_story_outline_section,
            is_metadata_section
        )

        # Test with extra spaces
        assert is_story_outline_section("#  Story Outline"), "Should handle extra spaces after #"
        assert is_metadata_section("##   Summary"), "Should handle extra spaces after ##"


class TestErrorPatternConstants:
    """TDD tests for error pattern constants"""

    def test_error_pattern_constants_exist(self):
        """Test that error pattern constants exist"""
        from Writer.FieldConstants import (
            MISSING_FIELD_ERROR,
            VALIDATION_ERROR,
            classify_error
        )

        assert MISSING_FIELD_ERROR is not None, "MISSING_FIELD_ERROR constant should exist"
        assert VALIDATION_ERROR is not None, "VALIDATION_ERROR constant should exist"
        assert callable(classify_error), "classify_error should be callable"

    @pytest.mark.parametrize("error_msg", [
        "Field name missing from model",
        "Missing required field: title",
        "The field 'content' is missing"
    ])
    def test_missing_field_classification(self, error_msg):
        """Test missing field error classification"""
        from Writer.FieldConstants import classify_error

        classifications = classify_error(error_msg)
        assert "missing_field" in classifications, f"Should classify '{error_msg}' as missing field"

    @pytest.mark.parametrize("error_msg", [
        "Validation failed for field",
        "ValidationError occurred",
        "Input validation error: field too short"
    ])
    def test_validation_error_classification(self, error_msg):
        """Test validation error classification"""
        from Writer.FieldConstants import classify_error

        classifications = classify_error(error_msg)
        assert "validation_error" in classifications, f"Should classify '{error_msg}' as validation error"

    def test_empty_error_classification(self):
        """Test classification of empty or None errors"""
        from Writer.FieldConstants import classify_error

        assert classify_error("") == [], "Empty string should return empty list"
        assert classify_error("random error message") == [], "Random error should return empty list"
