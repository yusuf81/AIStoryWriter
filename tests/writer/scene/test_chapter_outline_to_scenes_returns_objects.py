#!/usr/bin/env python3
"""
Phase 1.1 RED Tests: ChapterOutlineToScenes should return SceneOutline objects
These tests verify that ChapterOutlineToScenes returns full SceneOutline objects,
not just action strings, to preserve metadata for downstream processing.
"""

import pytest  # type: ignore # Needed for pytest fixtures (pyright can't track fixture usage)
from Writer.Models import SceneOutline, SceneOutlineList


class TestChapterOutlineToScenesReturnsObjects:
    """RED Tests: ChapterOutlineToScenes should return SceneOutline objects"""

    def test_returns_list_of_scene_outline_objects_not_strings(self, mock_interface, mock_logger):
        """Verify ChapterOutlineToScenes returns List[SceneOutline], not List[str]"""
        from Writer.Scene.ChapterOutlineToScenes import ChapterOutlineToScenes

        # Arrange: Create REAL Pydantic models (don't mock)
        mock_scenes = SceneOutlineList(scenes=[
            SceneOutline(
                scene_number=1,
                setting="Desa kecil",
                characters_present=["Rian"],
                action="Rian mendengar legenda",
                purpose="Membangun latar",
                estimated_word_count=150
            ),
            SceneOutline(
                scene_number=2,
                setting="Hutan",
                characters_present=["Rian", "Bang Jaga"],
                action="Rian bertemu penjaga hutan",
                purpose="Memperkenalkan konflik",
                estimated_word_count=200
            )
        ])

        # Mock SafeGeneratePydantic return
        mock_iface = mock_interface()
        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "mock messages"}],
            mock_scenes,
            {"tokens": 100}
        )

        # Act: Call ChapterOutlineToScenes
        result = ChapterOutlineToScenes(
            mock_iface,
            mock_logger(),
            1,  # ChapterNum
            2,  # TotalChapters
            "test chapter outline",
            "test story outline"
        )

        # Assert: Should return List[SceneOutline], not List[str]
        assert isinstance(result, list), "Should return a list"
        assert len(result) == 2, "Should return 2 scenes"

        # This is the critical assertion - should return SceneOutline objects
        for scene in result:
            assert isinstance(scene, SceneOutline), \
                f"Expected SceneOutline object, got {type(scene)}"

        # Verify all metadata fields are accessible
        assert result[0].scene_number == 1
        assert result[0].setting == "Desa kecil"
        assert result[0].characters_present == ["Rian"]
        assert result[0].action == "Rian mendengar legenda"
        assert result[0].purpose == "Membangun latar"
        assert result[0].estimated_word_count == 150

    def test_metadata_not_lost_compared_to_old_behavior(self, mock_interface, mock_logger):
        """Document improvement: Metadata preserved vs old behavior (strings only)"""
        from Writer.Scene.ChapterOutlineToScenes import ChapterOutlineToScenes

        # Arrange: Create scenes with rich metadata
        mock_scenes = SceneOutlineList(scenes=[
            SceneOutline(
                scene_number=1,
                setting="Gua yang gelap dan berbahaya",
                characters_present=["Rian", "Naga Kecil"],
                action="Rian menemukan harta karun",
                purpose="Klimaks cerita",
                estimated_word_count=300
            )
        ])

        mock_iface = mock_interface()
        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "mock"}],
            mock_scenes,
            {"tokens": 100}
        )

        # Act: Get result
        result = ChapterOutlineToScenes(
            mock_iface,
            mock_logger(),
            3,  # ChapterNum
            5,  # TotalChapters
            "final chapter outline",
            "story outline"
        )

        # Assert: ALL 6 fields should be accessible (not just action)
        assert len(result) == 1
        scene = result[0]

        # OLD BEHAVIOR (line 46): Only action string available
        # NEW BEHAVIOR: All 6 fields available
        fields_preserved = {
            'scene_number': scene.scene_number,
            'setting': scene.setting,
            'characters_present': scene.characters_present,
            'action': scene.action,
            'purpose': scene.purpose,
            'estimated_word_count': scene.estimated_word_count
        }

        # Verify all fields present
        assert fields_preserved['scene_number'] == 1
        assert fields_preserved['setting'] == "Gua yang gelap dan berbahaya"
        assert fields_preserved['characters_present'] == ["Rian", "Naga Kecil"]
        assert fields_preserved['action'] == "Rian menemukan harta karun"
        assert fields_preserved['purpose'] == "Klimaks cerita"
        assert fields_preserved['estimated_word_count'] == 300

        # Document the improvement
        # OLD: return [scene.action for scene in SceneList_obj.scenes]  # 83% data loss!
        # NEW: return SceneList_obj.scenes  # All metadata preserved!
