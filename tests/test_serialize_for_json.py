"""
TDD Tests for serialize_for_json() utility function.

Tests for fixing Pydantic JSON serialization error - London School Approach.
Follows TDD RED → GREEN → REFACTOR methodology.
"""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestSerializeForJson:
    """Unit tests for serialize_for_json() function"""

    def test_serialize_single_pydantic_object(self):
        """
        RED: Function doesn't exist yet

        After GREEN: Converts single Pydantic object to dict
        """
        from Writer.Models import StoryElements
        from Writer.StateManager import serialize_for_json

        story = StoryElements(
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

        result = serialize_for_json(story)

        # Should be dict, not Pydantic object
        assert isinstance(result, dict)
        assert result["title"] == "Test Story"
        assert result["genre"] == "Fantasy"
        assert result["themes"] == ["magic", "adventure"]

    def test_serialize_primitives_unchanged(self):
        """
        RED: Function doesn't exist

        After GREEN: Primitives (str, int, float, bool, None) pass through
        """
        from Writer.StateManager import serialize_for_json

        assert serialize_for_json("hello") == "hello"
        assert serialize_for_json(42) == 42
        assert serialize_for_json(3.14) == 3.14
        assert serialize_for_json(True) is True
        assert serialize_for_json(None) is None

    def test_serialize_dict_with_pydantic_values(self):
        """
        RED: Function doesn't exist

        After GREEN: Recursively processes dict values containing Pydantic
        """
        from Writer.Models import StoryElements, TitleOutput
        from Writer.StateManager import serialize_for_json

        story = StoryElements(
            title="Test Story",
            genre="Fantasy",
            themes=["test"],
            characters={},
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )
        title = TitleOutput(title="Chapter 1")

        data = {
            "story_elements": story,
            "title": title,
            "chapter_num": 1,
            "metadata": {"count": 5}
        }

        result = serialize_for_json(data)

        # All Pydantic converted to dict
        assert isinstance(result, dict)
        assert isinstance(result["story_elements"], dict)
        assert isinstance(result["title"], dict)
        assert result["chapter_num"] == 1
        assert result["metadata"]["count"] == 5

    def test_serialize_list_with_pydantic_objects(self):
        """
        RED: Function doesn't exist

        After GREEN: Recursively processes list items containing Pydantic
        """
        from Writer.Models import TitleOutput
        from Writer.StateManager import serialize_for_json

        titles = [
            TitleOutput(title="Chapter 1"),
            TitleOutput(title="Chapter 2"),
            "plain string",
            42
        ]

        result = serialize_for_json(titles)

        assert isinstance(result, list)
        assert isinstance(result[0], dict)
        assert result[0]["title"] == "Chapter 1"
        assert result[1]["title"] == "Chapter 2"
        assert result[2] == "plain string"
        assert result[3] == 42

    def test_serialize_deeply_nested_pydantic(self):
        """
        RED: Function doesn't exist

        After GREEN: Handles arbitrary nesting depth

        This is the CRITICAL test that matches the real error scenario:
        StoryInfoJSON contains nested dicts with Pydantic objects
        """
        from Writer.Models import StoryElements
        from Writer.StateManager import serialize_for_json

        story = StoryElements(
            title="Test Story",
            genre="Fantasy",
            themes=["test"],
            characters={},
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        # Simulates Pipeline.py structure
        deeply_nested = {
            "level1": {
                "level2": {
                    "story_elements": story,
                    "chapters": [
                        {"number": 1, "data": story},
                        {"number": 2, "text": "normal"}
                    ]
                }
            }
        }

        result = serialize_for_json(deeply_nested)

        # All Pydantic at any depth should be converted
        assert isinstance(result["level1"]["level2"]["story_elements"], dict)
        assert isinstance(result["level1"]["level2"]["chapters"][0]["data"], dict)
        assert result["level1"]["level2"]["chapters"][1]["text"] == "normal"

    def test_serialize_empty_containers(self):
        """
        RED: Function doesn't exist

        After GREEN: Handles empty dict, list, tuple correctly
        """
        from Writer.StateManager import serialize_for_json

        assert serialize_for_json({}) == {}
        assert serialize_for_json([]) == []
        assert serialize_for_json(()) == ()

    def test_serialize_story_info_json_structure(self):
        """
        RED: Function doesn't exist

        After GREEN: Handles actual StoryInfoJSON structure from Pipeline.py

        This test DIRECTLY addresses the bug report!
        """
        from Writer.Models import StoryElements
        from Writer.StateManager import serialize_for_json

        story_elements = StoryElements(
            title="Test Story",
            genre="Fantasy",
            themes=["test"],
            characters={},
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        # Exact structure from Pipeline.py:505-512
        StoryInfoJSON = {
            "Outline": "Full outline text",
            "StoryElements": story_elements,  # This is the Pydantic object causing error
            "RoughChapterOutline": "Rough outline",
            "BaseContext": "Base context",
            "TotalChaptersDetected": 10,
            "TotalChaptersGenerated": 10
        }

        # This should NOT raise TypeError
        serialized = serialize_for_json(StoryInfoJSON)

        # Verify it's actually JSON-serializable
        json_string = json.dumps(serialized, indent=4, ensure_ascii=False)
        assert isinstance(json_string, str)

        # Verify structure preserved
        assert serialized["Outline"] == "Full outline text"
        assert isinstance(serialized["StoryElements"], dict)
        assert serialized["TotalChaptersDetected"] == 10

    def test_serialize_tuple_with_pydantic(self):
        """
        RED: Function doesn't exist

        After GREEN: Tuples remain tuples (not converted to lists)
        """
        from Writer.Models import TitleOutput
        from Writer.StateManager import serialize_for_json

        title = TitleOutput(title="Test")
        tuple_with_pydantic = (title, "string", 42)

        result = serialize_for_json(tuple_with_pydantic)

        # Should still be tuple
        assert isinstance(result, tuple)
        assert isinstance(result[0], dict)
        assert result[1] == "string"
        assert result[2] == 42

    def test_serialize_set_to_list(self):
        """
        RED: Function doesn't exist

        After GREEN: Sets converted to lists (JSON limitation)
        """
        from Writer.StateManager import serialize_for_json

        result = serialize_for_json({1, 2, 3})

        assert isinstance(result, list)
        assert set(result) == {1, 2, 3}
