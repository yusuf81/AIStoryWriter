#!/usr/bin/env python3
"""
Phase 6.4 Tests: deduplicate_scene_objects() utility function
Test the utility function for deduplicating SceneOutline objects.
"""

import pytest  # type: ignore # Needed for pytest fixtures
from Writer.Models import SceneOutline
from Writer.Scene.ScenesToJSON import deduplicate_scene_objects


class TestDeduplicateSceneObjects:
    """Test deduplicate_scene_objects() utility function"""

    def test_deduplicate_removes_exact_duplicates(self):
        """Verify exact duplicates are removed"""
        scenes = [
            SceneOutline(
                scene_number=1,
                setting="Cave",
                characters_present=["Hero"],
                action="Hero finds the treasure in the deep cave",
                purpose="Climax",
                estimated_word_count=200
            ),
            SceneOutline(
                scene_number=2,
                setting="Cave",
                characters_present=["Hero"],
                action="Hero finds the treasure in the deep cave",  # EXACT DUPLICATE
                purpose="Climax",
                estimated_word_count=200
            ),
            SceneOutline(
                scene_number=3,
                setting="Exit",
                characters_present=["Hero"],
                action="Hero exits the cave victorious",
                purpose="Resolution",
                estimated_word_count=150
            )
        ]

        result = deduplicate_scene_objects(scenes)

        # Should remove scene 2 (duplicate of scene 1)
        assert len(result) == 2
        assert result[0].action == "Hero finds the treasure in the deep cave"
        assert result[1].action == "Hero exits the cave victorious"

    def test_deduplicate_preserves_metadata(self):
        """Verify metadata is preserved after deduplication"""
        scenes = [
            SceneOutline(
                scene_number=1,
                setting="Forest",
                characters_present=["Rian", "Guide"],
                action="Rian meets the forest guide",
                purpose="Introduce secondary character",
                estimated_word_count=250
            ),
            SceneOutline(
                scene_number=2,
                setting="Forest",
                characters_present=["Rian", "Guide"],
                action="Rian meets the forest guide",  # DUPLICATE
                purpose="Introduce secondary character",
                estimated_word_count=250
            ),
            SceneOutline(
                scene_number=3,
                setting="Cave entrance",
                characters_present=["Rian"],
                action="Rian enters the mysterious cave",
                purpose="Start adventure",
                estimated_word_count=200
            )
        ]

        result = deduplicate_scene_objects(scenes)

        # Should keep 2 unique scenes
        assert len(result) == 2

        # Verify metadata preserved for scene 1
        assert result[0].setting == "Forest"
        assert result[0].characters_present == ["Rian", "Guide"]
        assert result[0].purpose == "Introduce secondary character"
        assert result[0].estimated_word_count == 250

        # Verify metadata preserved for scene 3
        assert result[1].setting == "Cave entrance"
        assert result[1].characters_present == ["Rian"]
        assert result[1].estimated_word_count == 200

    def test_deduplicate_fuzzy_matching(self):
        """Verify fuzzy matching detects similar duplicates"""
        scenes = [
            SceneOutline(
                scene_number=1,
                setting="Village",
                characters_present=["Rian"],
                action="Rian hears about the legend of the dragon treasure cave from the old man",
                purpose="Setup",
                estimated_word_count=200
            ),
            SceneOutline(
                scene_number=2,
                setting="Village",
                characters_present=["Rian"],
                action="Rian hears about the legend of the dragon treasure cave from old man",  # Similar (80%+)
                purpose="Setup",
                estimated_word_count=200
            ),
            SceneOutline(
                scene_number=3,
                setting="Road",
                characters_present=["Rian"],
                action="Rian begins his journey to find the cave",
                purpose="Start journey",
                estimated_word_count=150
            )
        ]

        result = deduplicate_scene_objects(scenes)

        # Should detect fuzzy duplicate and remove scene 2
        assert len(result) == 2
        assert "legend" in result[0].action
        assert "journey" in result[1].action

    def test_deduplicate_preserves_order(self):
        """Verify order is preserved after deduplication"""
        scenes = [
            SceneOutline(
                scene_number=1,
                setting="A",
                characters_present=["Hero"],
                action="First scene action",
                purpose="Start",
                estimated_word_count=100
            ),
            SceneOutline(
                scene_number=2,
                setting="B",
                characters_present=["Hero"],
                action="Second scene action",
                purpose="Middle",
                estimated_word_count=150
            ),
            SceneOutline(
                scene_number=3,
                setting="C",
                characters_present=["Hero"],
                action="First scene action",  # DUPLICATE of scene 1
                purpose="Start",
                estimated_word_count=100
            ),
            SceneOutline(
                scene_number=4,
                setting="D",
                characters_present=["Hero"],
                action="Third scene action",
                purpose="Ending",
                estimated_word_count=200
            )
        ]

        result = deduplicate_scene_objects(scenes)

        # Should keep scenes 1, 2, 4 in that order
        assert len(result) == 3
        assert result[0].action == "First scene action"
        assert result[1].action == "Second scene action"
        assert result[2].action == "Third scene action"

        # Verify order preserved
        assert result[0].setting == "A"
        assert result[1].setting == "B"
        assert result[2].setting == "D"

    def test_deduplicate_empty_list(self):
        """Verify empty list returns empty list"""
        result = deduplicate_scene_objects([])
        assert result == []

    def test_deduplicate_single_scene(self):
        """Verify single scene returns as-is"""
        scenes = [
            SceneOutline(
                scene_number=1,
                setting="Test",
                characters_present=["Test"],
                action="Test action",
                purpose="Testing",
                estimated_word_count=100
            )
        ]

        result = deduplicate_scene_objects(scenes)

        assert len(result) == 1
        assert result[0].action == "Test action"

    def test_deduplicate_no_duplicates(self):
        """Verify list with no duplicates returns unchanged"""
        scenes = [
            SceneOutline(
                scene_number=1,
                setting="A",
                characters_present=["Hero"],
                action="Scene one with unique action",
                purpose="Start",
                estimated_word_count=100
            ),
            SceneOutline(
                scene_number=2,
                setting="B",
                characters_present=["Hero"],
                action="Scene two with different action",
                purpose="Middle",
                estimated_word_count=150
            ),
            SceneOutline(
                scene_number=3,
                setting="C",
                characters_present=["Hero"],
                action="Scene three with another action",
                purpose="Ending",
                estimated_word_count=200
            )
        ]

        result = deduplicate_scene_objects(scenes)

        # All scenes are unique
        assert len(result) == 3
        assert result[0].action == "Scene one with unique action"
        assert result[1].action == "Scene two with different action"
        assert result[2].action == "Scene three with another action"
