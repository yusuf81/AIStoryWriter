"""
Test StateManager.save_state with nested Pydantic objects
Bug fix verification for: "Object of type StoryElements is not JSON serializable"
"""
import tempfile
import json
from pathlib import Path
from Writer.StateManager import StateManager
from Writer.Models import StoryElements, CharacterDetail


class TestStateManagerNestedPydantic:
    """Test that StateManager.save_state handles nested Pydantic objects"""

    def test_save_state_with_nested_pydantic_in_list(self):
        """Verify save_state handles list containing Pydantic objects"""
        # Arrange: Create state with nested Pydantic objects in list
        story_elements = StoryElements(
            title="Test Story",
            genre="Fantasy",
            themes=["magic", "adventure"],
            characters={},
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        character = CharacterDetail(
            name="Hero",
            physical_description="Brave warrior with a mysterious past",
            personality=None,
            background="Brave warrior with a mysterious past",
            motivation="Seeks to protect the kingdom"
        )

        state_data = {
            "story_name": "Test",
            "completed_chapters_data": [
                {"number": 1, "title": "Chapter 1", "text": "Content"},
                {"number": 2, "title": "Chapter 2", "text": "More content"}
            ],
            "character_list": [character],  # Nested Pydantic in list!
            "metadata": {
                "story_elements": story_elements  # Nested Pydantic in dict!
            }
        }

        # Act: Save to temp file (should not raise)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            # This should NOT raise "Object of type ... is not JSON serializable"
            StateManager.save_state(state_data, temp_path)

            # Assert: File should exist and be valid JSON
            assert Path(temp_path).exists()

            with open(temp_path, 'r') as f:
                saved_data = json.load(f)

            # Verify structure
            assert "other_data" in saved_data
            assert "character_list" in saved_data["other_data"]
            assert "metadata" in saved_data["other_data"]

            # Verify nested Pydantic was serialized to dict
            character_data = saved_data["other_data"]["character_list"][0]
            assert isinstance(character_data, dict)
            assert character_data["name"] == "Hero"

            story_data = saved_data["other_data"]["metadata"]["story_elements"]
            assert isinstance(story_data, dict)
            assert story_data["title"] == "Test Story"

        finally:
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)

    def test_save_state_with_story_elements_in_nested_dict(self):
        """Verify the exact error case from logs: StoryElements in nested structure"""
        # Arrange: Replicate the error scenario
        story_elements = StoryElements(
            title="Gua Harta Karun Naga",
            genre="Adventure",
            themes=["treasure", "dragons"],
            characters={},
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        state_data = {
            "story_name": "Test Story",
            "nested_info": {
                "elements": story_elements,  # This caused: "Object of type StoryElements is not JSON serializable"
                "other": "data"
            }
        }

        # Act: Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            # Should NOT raise anymore after fix
            StateManager.save_state(state_data, temp_path)

            # Assert: Verify saved correctly
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)

            # StoryElements should be serialized to dict
            elements_data = saved_data["other_data"]["nested_info"]["elements"]
            assert isinstance(elements_data, dict)
            assert elements_data["title"] == "Gua Harta Karun Naga"
            assert elements_data["genre"] == "Adventure"

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_save_state_with_deeply_nested_pydantic(self):
        """Verify deeply nested structures with Pydantic objects"""
        # Arrange: Create deeply nested structure
        character = CharacterDetail(
            name="Rian",
            physical_description="Young adventurer seeking treasure",
            personality=None,
            background="Young adventurer seeking treasure",
            motivation="Find the dragon's treasure"
        )

        state_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "character": character,  # Deep nesting!
                        "data": [character, character]  # In list too!
                    }
                }
            }
        }

        # Act: Save
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            StateManager.save_state(state_data, temp_path)

            # Assert: All nested Pydantic serialized
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)

            nested = saved_data["other_data"]["level1"]["level2"]["level3"]
            assert isinstance(nested["character"], dict)
            assert nested["character"]["name"] == "Rian"
            assert len(nested["data"]) == 2
            assert all(isinstance(c, dict) for c in nested["data"])

        finally:
            Path(temp_path).unlink(missing_ok=True)
