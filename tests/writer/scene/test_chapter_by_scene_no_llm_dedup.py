#!/usr/bin/env python3
"""
Phase 2.1 RED Tests: ChapterByScene should not call ScenesToJSON LLM
These tests verify that ChapterByScene removes the redundant ScenesToJSON LLM call
while preserving deduplication functionality.
"""

import pytest
import sys
from unittest.mock import patch, Mock, MagicMock
from Writer.Models import SceneOutline, SceneOutlineList

# Mock termcolor before imports to avoid ModuleNotFoundError
sys.modules['termcolor'] = MagicMock()


class TestChapterBySceneNoLLMDedup:
    """RED Tests: ChapterByScene should not call ScenesToJSON"""

    def test_chapter_by_scene_does_not_call_scenes_to_json(self, mock_interface, mock_logger):
        """Verify ChapterByScene does NOT call ScenesToJSON (no LLM call)"""
        from Writer.Scene.ChapterByScene import ChapterByScene

        # Arrange: Create mock scenes that ChapterOutlineToScenes will return
        mock_scenes = [
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
        ]

        mock_iface = mock_interface()
        mock_log = mock_logger()

        # Mock ChapterOutlineToScenes to return SceneOutline objects
        with patch('Writer.Scene.ChapterByScene.Writer.Scene.ChapterOutlineToScenes.ChapterOutlineToScenes') as mock_cots:
            mock_cots.return_value = mock_scenes

            # Mock ScenesToJSON - should NOT be called
            with patch('Writer.Scene.ChapterByScene.Writer.Scene.ScenesToJSON.ScenesToJSON') as mock_stj:
                mock_stj.return_value = ["should", "not", "be", "called"]

                # Mock SceneOutlineToScene to return text
                with patch('Writer.Scene.ChapterByScene.Writer.Scene.SceneOutlineToScene.SceneOutlineToScene') as mock_sots:
                    mock_sots.return_value = "Mock scene text\n\n"

                    # Act: Call ChapterByScene
                    result = ChapterByScene(
                        mock_iface,
                        mock_log,
                        1,  # ChapterNum
                        3,  # TotalChapters
                        "test chapter outline",
                        "test story outline",
                        "test base context"
                    )

                    # Assert: ScenesToJSON should NOT have been called
                    mock_stj.assert_not_called()

                    # Verify ChapterOutlineToScenes WAS called
                    mock_cots.assert_called_once()

                    # Verify SceneOutlineToScene WAS called for each scene
                    assert mock_sots.call_count == 2, f"Expected 2 calls to SceneOutlineToScene, got {mock_sots.call_count}"

                    # Verify result contains scene text
                    assert isinstance(result, str)
                    assert "Mock scene text" in result

    def test_deduplication_still_works_without_llm(self, mock_interface, mock_logger):
        """Verify deduplication works without ScenesToJSON LLM call"""
        from Writer.Scene.ChapterByScene import ChapterByScene

        # Arrange: Create scenes with duplicates (similar actions)
        mock_scenes = [
            SceneOutline(
                scene_number=1,
                setting="Desa",
                characters_present=["Rian"],
                action="Rian hears about the legend of the treasure cave",
                purpose="Setup",
                estimated_word_count=150
            ),
            SceneOutline(
                scene_number=2,
                setting="Desa",
                characters_present=["Rian"],
                action="Rian hears about the legend of the treasure cave",  # EXACT DUPLICATE
                purpose="Setup",
                estimated_word_count=150
            ),
            SceneOutline(
                scene_number=3,
                setting="Hutan",
                characters_present=["Rian"],
                action="Rian enters the forest and begins his journey",
                purpose="Start adventure",
                estimated_word_count=200
            )
        ]

        mock_iface = mock_interface()
        mock_log = mock_logger()

        # Mock ChapterOutlineToScenes
        with patch('Writer.Scene.ChapterByScene.Writer.Scene.ChapterOutlineToScenes.ChapterOutlineToScenes') as mock_cots:
            mock_cots.return_value = mock_scenes

            # Mock SceneOutlineToScene to track calls
            with patch('Writer.Scene.ChapterByScene.Writer.Scene.SceneOutlineToScene.SceneOutlineToScene') as mock_sots:
                mock_sots.return_value = "Scene text\n\n"

                # Act: Call ChapterByScene
                result = ChapterByScene(
                    mock_iface,
                    mock_log,
                    1,  # ChapterNum
                    3,  # TotalChapters
                    "test chapter outline",
                    "test story outline"
                )

                # Assert: Deduplication should have removed the duplicate
                # Scene 1 and Scene 2 have identical actions, so only 2 unique scenes should be processed
                assert mock_sots.call_count == 2, \
                    f"Expected 2 calls (duplicate removed), got {mock_sots.call_count}"

                # Verify the calls were for the correct scenes
                calls = mock_sots.call_args_list
                # First call should be scene 1
                assert calls[0][0][2] == 1, "First call should be scene number 1"
                # Second call should be scene 3 (scene 2 was duplicate)
                assert calls[1][0][2] == 2, "Second call should be scene number 2 (after dedup)"

    def test_scene_outline_objects_passed_to_scene_writer(self, mock_interface, mock_logger):
        """Verify SceneOutline objects (not strings) are passed to SceneOutlineToScene"""
        from Writer.Scene.ChapterByScene import ChapterByScene

        # Arrange: Create scenes with rich metadata
        mock_scenes = [
            SceneOutline(
                scene_number=1,
                setting="Gua gelap",
                characters_present=["Rian", "Naga"],
                action="Rian menemukan harta karun",
                purpose="Klimaks",
                estimated_word_count=300
            )
        ]

        mock_iface = mock_interface()
        mock_log = mock_logger()

        # Mock ChapterOutlineToScenes
        with patch('Writer.Scene.ChapterByScene.Writer.Scene.ChapterOutlineToScenes.ChapterOutlineToScenes') as mock_cots:
            mock_cots.return_value = mock_scenes

            # Mock SceneOutlineToScene to capture argument
            with patch('Writer.Scene.ChapterByScene.Writer.Scene.SceneOutlineToScene.SceneOutlineToScene') as mock_sots:
                mock_sots.return_value = "Scene text\n\n"

                # Act: Call ChapterByScene
                result = ChapterByScene(
                    mock_iface,
                    mock_log,
                    1, 3,
                    "test outline",
                    "test story"
                )

                # Assert: SceneOutlineToScene should receive SceneOutline object (not string)
                mock_sots.assert_called_once()
                call_args = mock_sots.call_args[0]
                scene_arg = call_args[4]  # 5th positional argument is _ThisSceneOutline

                # Critical assertion: Should be SceneOutline object, not string
                assert isinstance(scene_arg, SceneOutline), \
                    f"Expected SceneOutline object, got {type(scene_arg)}"

                # Verify metadata is accessible
                assert scene_arg.setting == "Gua gelap"
                assert scene_arg.characters_present == ["Rian", "Naga"]
                assert scene_arg.estimated_word_count == 300
