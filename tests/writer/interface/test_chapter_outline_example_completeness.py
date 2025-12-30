"""
Tests for ChapterOutlineOutput example completeness in Wrapper._LANGUAGE_STRINGS.

These tests verify that the auto-appended ChapterOutlineOutput examples include
proper scene structure to minimize LLM retry attempts.
"""

import pytest
import json
from typing import Dict, Any


class TestChapterOutlineExampleCompleteness:
    """Test suite verifying ChapterOutlineOutput examples are complete and valid."""

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

    def test_english_chapter_outline_example_has_all_fields(self, english_language_config):
        """Test that English ChapterOutlineOutput example includes all fields."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['chapter_outline_output_example']

        # Act
        example_data = self.extract_json_from_example(example_string)

        # Assert - Required fields
        assert 'chapter_number' in example_data, "Missing required field: chapter_number"
        assert 'chapter_title' in example_data, "Missing required field: chapter_title"
        assert 'scenes' in example_data, "Missing required field: scenes"
        assert 'outline_summary' in example_data, "Missing required field: outline_summary"

        # Assert - Optional fields
        assert 'characters_present' in example_data, "Missing optional field: characters_present"
        assert 'setting' in example_data, "Missing optional field: setting"
        assert 'main_conflict' in example_data, "Missing optional field: main_conflict"

    def test_indonesian_chapter_outline_example_has_all_fields(self, indonesian_language_config):
        """Test that Indonesian ChapterOutlineOutput example includes all fields."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['id']['chapter_outline_output_example']

        # Act
        example_data = self.extract_json_from_example(example_string)

        # Assert - Required fields
        assert 'chapter_number' in example_data, "Missing required field: chapter_number"
        assert 'chapter_title' in example_data, "Missing required field: chapter_title"
        assert 'scenes' in example_data, "Missing required field: scenes"
        assert 'outline_summary' in example_data, "Missing required field: outline_summary"

        # Assert - Optional fields
        assert 'characters_present' in example_data, "Missing optional field: characters_present"
        assert 'setting' in example_data, "Missing optional field: setting"
        assert 'main_conflict' in example_data, "Missing optional field: main_conflict"

    def test_scenes_field_structure(self, english_language_config):
        """Test that scenes has correct List[EnhancedSceneOutline] structure."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['chapter_outline_output_example']
        example_data = self.extract_json_from_example(example_string)

        # Act
        scenes = example_data.get('scenes')

        # Assert
        assert scenes is not None, "scenes field is missing"
        assert isinstance(scenes, list), "scenes must be a list"
        assert len(scenes) > 0, "scenes should have at least one scene"

        # Check each scene has EnhancedSceneOutline structure
        for i, scene in enumerate(scenes):
            assert isinstance(scene, dict), f"scenes[{i}] must be a dict (EnhancedSceneOutline)"

            # Check for EnhancedSceneOutline fields
            expected_fields = ['title', 'characters_and_setting', 'conflict_and_tone',
                               'key_events', 'literary_devices', 'resolution']

            for field in expected_fields:
                assert field in scene, f"scenes[{i}] missing field: {field}"
                assert isinstance(scene[field], str), f"scenes[{i}].{field} must be string"
                # Optional fields can be empty, but if present should be string
                if scene[field]:
                    assert len(scene[field].strip()) > 0, f"scenes[{i}].{field} should be non-empty if provided"

    def test_english_example_validates_against_pydantic(self, english_language_config):
        """Test that English example can be validated by ChapterOutlineOutput model."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutlineOutput

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['chapter_outline_output_example']
        example_data = self.extract_json_from_example(example_string)

        # Act & Assert - Should not raise ValidationError
        try:
            chapter_outline = ChapterOutlineOutput(**example_data)
            assert chapter_outline is not None
        except Exception as e:
            pytest.fail(f"English example fails ChapterOutlineOutput validation: {e}")

    def test_indonesian_example_validates_against_pydantic(self, indonesian_language_config):
        """Test that Indonesian example can be validated by ChapterOutlineOutput model."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutlineOutput

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['id']['chapter_outline_output_example']
        example_data = self.extract_json_from_example(example_string)

        # Act & Assert - Should not raise ValidationError
        try:
            chapter_outline = ChapterOutlineOutput(**example_data)
            assert chapter_outline is not None
        except Exception as e:
            pytest.fail(f"Indonesian example fails ChapterOutlineOutput validation: {e}")

    def test_english_indonesian_symmetry(self):
        """Test that English and Indonesian examples have same field structure."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        en_example = interface._LANGUAGE_STRINGS['en']['chapter_outline_output_example']
        id_example = interface._LANGUAGE_STRINGS['id']['chapter_outline_output_example']

        en_data = self.extract_json_from_example(en_example)
        id_data = self.extract_json_from_example(id_example)

        # Assert - Same top-level keys
        assert set(en_data.keys()) == set(id_data.keys()), \
            "English and Indonesian examples have different fields"

        # Assert - Same number of scenes
        assert len(en_data['scenes']) == len(id_data['scenes']), \
            "Number of scenes differ between EN and ID"

        # Assert - Same scene structure
        if en_data['scenes'] and id_data['scenes']:
            en_scene_keys = set(en_data['scenes'][0].keys())
            id_scene_keys = set(id_data['scenes'][0].keys())
            assert en_scene_keys == id_scene_keys, \
                "Scene structure differs between EN and ID"

    def test_scenes_not_strings(self, english_language_config):
        """Test that scenes are objects, NOT simple strings."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        example_string = interface._LANGUAGE_STRINGS['en']['chapter_outline_output_example']
        example_data = self.extract_json_from_example(example_string)

        # Act
        scenes = example_data.get('scenes')

        # Assert
        assert scenes is not None, "scenes field is missing"
        assert isinstance(scenes, list), "scenes must be a list"

        # Assert - scenes should be list of objects, not list of strings
        for i, scene in enumerate(scenes):
            assert not isinstance(scene, str), \
                f"scenes[{i}] should be EnhancedSceneOutline object, not string"
            assert isinstance(scene, dict), \
                f"scenes[{i}] should be EnhancedSceneOutline dict structure"
