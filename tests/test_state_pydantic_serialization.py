"""
TDD Tests for Pydantic State Serialization - London School Approach
Tests for fixing StoryElements JSON serialization error in save/load state
"""
import pytest
import tempfile
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestStatePydanticSerialization:
    """TDD tests for Pydantic model serialization in state management"""

    def test_save_state_with_pydantic_objects(self, tmp_path, mock_logger):
        """
        GREEN: Test that state can save Pydantic objects without error

        This test PASSES because:
        - StateManager.save_state converts Pydantic to dict before saving
        - Uses container format to separate Pydantic from regular data
        - No more TypeError when saving Pydantic objects
        """
        from Writer.Models import StoryElements, TitleOutput
        from Writer.StateManager import StateManager

        # Create Pydantic objects
        story_elements = StoryElements(
            title="Petualangan Naga",
            genre="Petualangan Fantasi",
            characters={"pemain": "petualang", "penjahat": "naga"},
            settings={
                "gua": {
                    "location": "gua harta karun",
                    "time": "Present day",
                    "culture": "Ancient cave",
                    "mood": "Mysterious"
                },
                "desa": {
                    "location": "desa pertanian",
                    "time": "Present day",
                    "culture": "Farming village",
                    "mood": "Peaceful"
                }
            },
            themes=["petualangan", "keberanian"],
            conflict="petualang vs naga",
            resolution="petualang menang"
        )

        title = TitleOutput(title="Petualangan Naga")

        state = {
            "story_elements": story_elements,
            "title": title,
            "regular_string": "normal data",
            "chapter_number": 1
        }

        # This should now SUCCEED
        StateManager.save_state(state, tmp_path / "state.json")

        # Verify file was created and contains expected structure
        with open(tmp_path / "state.json", 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        # Should have container structure
        assert "pydantic_objects" in saved_data
        assert "other_data" in saved_data

        # Pydantic objects should be serialized with model info
        assert "story_elements" in saved_data["pydantic_objects"]
        assert saved_data["pydantic_objects"]["story_elements"]["__model__"] == "StoryElements"
        assert "__data__" in saved_data["pydantic_objects"]["story_elements"]

        # Regular data should be in other_data
        assert saved_data["other_data"]["regular_string"] == "normal data"
        assert saved_data["other_data"]["chapter_number"] == 1

    def test_load_state_reconstructs_pydantic_objects(self, tmp_path, mock_logger):
        """
        GREEN: Test that Pydantic objects are reconstructed on load

        This test PASSES because:
        - StateManager.load_state reads container format
        - Recreates Pydantic objects using model names and data
        - Returns proper Pydantic instances
        """
        from Writer.Models import StoryElements, TitleOutput
        from Writer.StateManager import StateManager

        # Simulate saved state with container format (will be created by StateManager)
        saved_state = {
            "pydantic_objects": {
                "story_elements": {
                    "__model__": "StoryElements",
                    "__data__": {
                        "title": "Petualangan Naga",
                        "genre": "Petualangan Fantasi",
                        "characters": {"pemain": "petualang", "penjahat": "naga"},
                        "settings": {
                            "gua": {
                                "location": "gua harta karun",
                                "time": "Present day",
                                "culture": "Ancient cave",
                                "mood": "Mysterious"
                            },
                            "desa": {
                                "location": "desa pertanian",
                                "time": "Present day",
                                "culture": "Farming village",
                                "mood": "Peaceful"
                            }
                        },
                        "themes": ["petualangan", "keberanian"],
                        "conflict": "petualang vs naga",
                        "resolution": "petualang menang"
                    }
                },
                "title": {
                    "__model__": "TitleOutput",
                    "__data__": {
                        "title": "Petualangan Naga"
                    }
                }
            },
            "other_data": {
                "regular_string": "normal data",
                "chapter_number": 1
            }
        }

        state_file = tmp_path / "state.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(saved_state, f, indent=4, ensure_ascii=False)

        # This should FAIL initially - returns dict, not Pydantic
        loaded = StateManager.load_state(state_file)

        # Verify Pydantic objects are properly reconstructed
        assert isinstance(loaded["story_elements"], StoryElements)
        assert loaded["story_elements"].characters["pemain"] == "petualang"
        assert loaded["story_elements"].themes == ["petualangan", "keberanian"]

        assert isinstance(loaded["title"], TitleOutput)
        assert loaded["title"].title == "Petualangan Naga"

        # Verify regular data is preserved
        assert loaded["regular_string"] == "normal data"
        assert loaded["chapter_number"] == 1

    def test_state_manager_handles_empty_state(self, tmp_path):
        """
        RED: Test StateManager with empty state

        This test will FAIL initially because:
        - StateManager doesn't exist

        After implementation, this test will PASS because:
        - StateManager handles empty containers gracefully
        - Returns empty dict for empty state
        """
        from Writer.StateManager import StateManager

        # Test saving empty state
        empty_state = {}
        state_file = tmp_path / "empty.json"

        StateManager.save_state(empty_state, state_file)

        # Test loading empty state
        loaded = StateManager.load_state(state_file)
        assert loaded == {}

    def test_state_manager_handles_mixed_data_types(self, tmp_path, mock_logger):
        """
        RED: Test StateManager with various data types

        This test will FAIL initially because:
        - StateManager doesn't exist

        After implementation, this test will PASS because:
        - StateManager preserves all data types correctly
        - Separates Pydantic from regular data properly
        """
        from Writer.Models import StoryElements
        from Writer.StateManager import StateManager

        mixed_state = {
            "pydantic_obj": StoryElements(title="Test Story", genre="Test", themes=["test"], characters={"hero": "brave"}),
            "string": "test string",
            "number": 42,
            "list": [1, 2, 3],
            "nested_dict": {"key": "value"},
            "none_value": None
        }

        state_file = tmp_path / "mixed.json"

        # Save and load
        StateManager.save_state(mixed_state, state_file)
        loaded = StateManager.load_state(state_file)

        # Verify all data types are preserved
        assert isinstance(loaded["pydantic_obj"], StoryElements)
        assert loaded["string"] == "test string"
        assert loaded["number"] == 42
        assert loaded["list"] == [1, 2, 3]
        assert loaded["nested_dict"] == {"key": "value"}
        assert loaded["none_value"] is None

    def test_state_manager_error_handling(self, tmp_path):
        """
        RED: Test StateManager error handling

        This test will FAIL initially because:
        - StateManager doesn't exist

        After implementation, this test will PASS because:
        - StateManager handles malformed JSON gracefully
        - Raises appropriate exceptions for invalid data
        """
        from Writer.StateManager import StateManager

        invalid_file = tmp_path / "invalid.json"

        # Create invalid JSON file
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")

        # Should raise appropriate exception
        with pytest.raises(json.JSONDecodeError):
            StateManager.load_state(invalid_file)

    def test_state_manager_preserves_all_model_registry_types(self, tmp_path, mock_logger):
        """
        RED: Test that StateManager handles all models in MODEL_REGISTRY

        This test will FAIL initially because:
        - StateManager doesn't exist
        - Need to test all models in MODEL_REGISTRY

        After implementation, this test will PASS because:
        - StateManager automatically detects MODEL_REGISTRY models
        - Handles all registered Pydantic models
        """
        from Writer.Models import MODEL_REGISTRY, get_model
        from Writer.StateManager import StateManager

        # Create instances of all models in MODEL_REGISTRY
        all_models_state = {}

        for model_name in MODEL_REGISTRY.keys():
            model_class = get_model(model_name)
            if model_class and model_name != "BaseContext":  # Skip abstract models
                # Create minimal instance for testing
                if model_name == "StoryElements":
                    instance = model_class(title="Test Story", genre="Test", themes=["test"])
                elif model_name == "TitleOutput":
                    instance = model_class(title="Test Title")
                elif model_name == "ReasoningOutput":
                    instance = model_class(reasoning="Test reasoning")
                else:
                    # For other models, try to create with minimal data
                    # This might need adjustment based on actual model requirements
                    try:
                        instance = model_class()
                    except:
                        continue  # Skip models that require specific params

                all_models_state[model_name] = instance

        state_file = tmp_path / "all_models.json"

        # Save and load all models
        StateManager.save_state(all_models_state, state_file)
        loaded = StateManager.load_state(state_file)

        # Verify all models are reconstructed correctly
        for model_name, original_instance in all_models_state.items():
            loaded_instance = loaded[model_name]
            assert type(loaded_instance).__name__ == model_name
            assert hasattr(loaded_instance, 'model_dump')  # It's a Pydantic model