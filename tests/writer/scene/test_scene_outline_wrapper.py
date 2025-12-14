#!/usr/bin/env python3
"""
RED Tests for SceneOutlineList wrapper model (Error 4)
These tests should fail with current implementation because SceneOutlineList doesn't exist yet.
"""

import pytest
from pydantic import ValidationError


class TestSceneOutlineWrapper:
    """RED Tests: These should fail with current implementation"""

    def test_scene_outline_list_model_validation(self):
        """RED: Test SceneOutlineList model accepts multiple SceneOutline objects"""
        from Writer.Models import SceneOutline, SceneOutlineList

        # Test that wrapper model can handle multiple scenes
        scene_data = [
            {
                "scene_number": 1,
                "setting": "Desa kecil di pinggiran hutan",
                "characters_present": ["Rian"],
                "action": "Rian mendengar legenda tentang gua harta karun",
                "purpose": "Membangun latar belakang cerita",
                "estimated_word_count": 150
            },
            {
                "scene_number": 2,
                "setting": "Hutan yang dipenuhi misteri",
                "characters_present": ["Rian", "Bang Jaga"],
                "action": "Rian bertemu dengan penjaga hutan yang memberikan tantangan",
                "purpose": "Memperkenalkan konflik awal",
                "estimated_word_count": 200
            },
            {
                "scene_number": 3,
                "setting": "Gua yang dipenuhi tantangan",
                "characters_present": ["Rian", "Naga Kecil"],
                "action": "Setelah melewati berbagai rintangan, Rian akhirnya bertemu Naga Kecil",
                "purpose": "Menggambarkan pertemuan awal dan konflik utama",
                "estimated_word_count": 250
            }
        ]

        # Should validate successfully with wrapper model
        wrapper = SceneOutlineList(scenes=scene_data)
        assert len(wrapper.scenes) == 3
        assert wrapper.scenes[0].scene_number == 1
        assert wrapper.scenes[0].setting == "Desa kecil di pinggiran hutan"
        assert wrapper.scenes[1].characters_present == ["Rian", "Bang Jaga"]
        assert wrapper.scenes[2].estimated_word_count == 250

    def test_scene_outline_list_single_scene(self):
        """RED: Test SceneOutlineList works with single scene"""
        from Writer.Models import SceneOutline, SceneOutlineList

        # Single scene should also work
        scene_data = [{
            "scene_number": 1,
            "setting": "Desa kecil",
            "characters_present": ["Rian"],
            "action": "Rian memulai perjalanan",
            "purpose": "Membuka cerita",
            "estimated_word_count": 100
        }]

        wrapper = SceneOutlineList(scenes=scene_data)
        assert len(wrapper.scenes) == 1
        assert wrapper.scenes[0].scene_number == 1

    def test_scene_outline_list_validation_error(self):
        """RED: Test SceneOutlineList validation fails for empty scenes"""
        from Writer.Models import SceneOutlineList

        # Empty scenes list should fail validation
        with pytest.raises(ValidationError, match="At least one scene must be provided"):
            SceneOutlineList(scenes=[])

    def test_scene_outline_list_follows_scenelistschema_pattern(self):
        """RED: Verify SceneOutlineList follows SceneListSchema pattern"""
        from Writer.Scene.ScenesToJSON import SceneListSchema
        from Writer.Models import SceneOutline, SceneOutlineList

        # Ensure both models have scenes field (follow same pattern)
        assert 'scenes' in SceneListSchema.model_fields
        assert 'scenes' in SceneOutlineList.model_fields

        # SceneListSchema uses List[str], SceneOutlineList should use List[SceneOutline]
        scene_list = SceneListSchema(scenes=["scene 1", "scene 2"])
        scene_outline_list = SceneOutlineList(scenes=[
            SceneOutline(
                scene_number=1,
                setting="test setting",
                characters_present=["test character"],
                action="test action description",
                purpose="test purpose",
                estimated_word_count=100
            )
        ])

        assert len(scene_list.scenes) == 2
        assert len(scene_outline_list.scenes) == 1
        assert isinstance(scene_list.scenes[0], str)
        assert isinstance(scene_outline_list.scenes[0], SceneOutline)


class TestChapterOutlineToScenesIntegration:
    """RED Tests: These should fail with current implementation due to TypeError"""

    def test_chapter_outline_to_scenes_multiple_scenes_red(self, mock_interface, mock_logger):
        """RED: Test current ChapterOutlineToScenes fails with multiple scene response"""
        from Writer.Scene.ChapterOutlineToScenes import ChapterOutlineToScenes

        # Mock interface to return multiple JSON objects (like current LLM)
        mock_iface = mock_interface()
        mock_iface.SafeGeneratePydantic.side_effect = TypeError("Expected single JSON object, got list of 2 objects")

        # Should fail with current implementation
        with pytest.raises(TypeError, match="Expected single JSON object"):
            ChapterOutlineToScenes(
                mock_iface,
                mock_logger(),
                1,  # ChapterNum
                2,  # TotalChapters
                "Rian mendengar legenda dan memutuskan untuk pergi ke gua",  # ThisChapter
                "Cerita tentang Rian yang mencari harta karun",  # Outline
                "Fantasi petualangan"  # BaseContext
            )

    def test_chapter_outline_to_scenes_backward_compatibility_red(self, mock_interface, mock_logger):
        """RED: Test ChapterOutlineToScenes maintains backward compatibility after fix"""
        from Writer.Scene.ChapterOutlineToScenes import ChapterOutlineToScenes
        from Writer.Models import SceneOutline, SceneOutlineList
        from unittest.mock import patch

        # This test will pass after GREEN implementation
        # For now, it's in RED to verify expected behavior
        mock_iface = mock_interface()

        # Mock the wrapper model response (after GREEN implementation)
        mock_scenes = SceneOutlineList(scenes=[
            SceneOutline(
                scene_number=1,
                setting="Desa",
                characters_present=["Rian"],
                action="Rian berangkat",
                purpose="Memulai perjalanan",
                estimated_word_count=100
            ),
            SceneOutline(
                scene_number=2,
                setting="Gua",
                characters_present=["Rian", "Naga"],
                action="Rian bertemu naga",
                purpose="Konflik utama",
                estimated_word_count=200
            )
        ])

        # Mock SafeGeneratePydantic to return our wrapper model
        mock_iface.SafeGeneratePydantic.return_value = (["mock response"], mock_scenes, {"tokens": 100})

        # This should work after GREEN implementation and return list
        result = ChapterOutlineToScenes(
            mock_iface,
            mock_logger(),
            1,
            2,
            "test chapter outline",
            "test story outline"
        )

        # Verify returns list of scene actions (no backward compatibility)
        assert isinstance(result, list)
        assert len(result) == 2
        # Should contain both scene actions
        assert "Rian berangkat" in result[0]
        assert "Rian bertemu naga" in result[1]