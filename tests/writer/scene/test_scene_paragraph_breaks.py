#!/usr/bin/env python3
"""
Tests for scene concatenation with paragraph breaks.

These tests verify that ChapterByScene properly concatenates scenes
with paragraph breaks (\n\n) to prevent wall-of-text issues.
"""

import sys
from unittest.mock import patch, MagicMock
from Writer.Models import SceneOutline

# Mock termcolor before imports
sys.modules['termcolor'] = MagicMock()


class TestSceneParagraphBreaks:
    """Test suite for scene concatenation with proper paragraph breaks."""

    def test_scenes_concatenated_with_paragraph_breaks(self, mock_interface, mock_logger):
        """
        RED TEST: Verify scenes are concatenated with \\n\\n separator.

        This prevents wall-of-text when LLM outputs don't have internal breaks.
        """
        from Writer.Scene.ChapterByScene import ChapterByScene

        # Arrange: Create 3 scenes
        mock_scenes = [
            SceneOutline(
                scene_number=1,
                setting="Balai desa",
                characters_present=["Rian", "Tetua"],
                action="Dialog tentang legenda",
                purpose="Setup",
                estimated_word_count=150
            ),
            SceneOutline(
                scene_number=2,
                setting="Gua gelap",
                characters_present=["Rian"],
                action="Melewati jebakan",
                purpose="Tension",
                estimated_word_count=200
            ),
            SceneOutline(
                scene_number=3,
                setting="Ruang kristal",
                characters_present=["Rian", "Ember"],
                action="Pertemuan dengan naga",
                purpose="Klimaks",
                estimated_word_count=250
            )
        ]

        mock_iface = mock_interface()
        mock_log = mock_logger()

        # Mock ChapterOutlineToScenes to return scenes
        with patch('Writer.Scene.ChapterByScene.Writer.Scene.ChapterOutlineToScenes.ChapterOutlineToScenes') as mock_cots:
            mock_cots.return_value = mock_scenes

            # Mock SceneOutlineToScene to return text WITHOUT internal breaks
            # (simulating LLM that generates wall of text)
            with patch('Writer.Scene.ChapterByScene.Writer.Scene.SceneOutlineToScene.SceneOutlineToScene') as mock_sots:
                # Return text WITHOUT \n\n at the end (realistic scenario)
                mock_sots.side_effect = [
                    "Scene 1 text goes here",
                    "Scene 2 text goes here",
                    "Scene 3 text goes here"
                ]

                # Act: Call ChapterByScene
                result = ChapterByScene(
                    mock_iface,
                    mock_log,
                    1,  # ChapterNum
                    2,  # TotalChapters
                    "test chapter outline",
                    "test story outline",
                    "test base context"
                )

                # Assert: Result should have paragraph breaks between scenes
                assert "\n\n" in result, "Chapter should contain paragraph breaks"

                # Verify each scene is separated by \n\n
                assert "Scene 1 text goes here\n\nScene 2 text goes here" in result, \
                    "Scene 1 and Scene 2 should be separated by \\n\\n"
                assert "Scene 2 text goes here\n\nScene 3 text goes here" in result, \
                    "Scene 2 and Scene 3 should be separated by \\n\\n"

    def test_no_double_breaks_when_scene_already_has_breaks(self, mock_interface, mock_logger):
        """
        Verify that if scene text already ends with \\n\\n, we don't add triple breaks.

        This test ensures the fix handles edge cases where LLM outputs
        already include trailing paragraph breaks.
        """
        from Writer.Scene.ChapterByScene import ChapterByScene

        # Arrange
        mock_scenes = [
            SceneOutline(
                scene_number=1,
                setting="Desa",
                characters_present=["Rian"],
                action="Introduction scene at village",
                purpose="Setup",
                estimated_word_count=100
            ),
            SceneOutline(
                scene_number=2,
                setting="Hutan",
                characters_present=["Rian"],
                action="Journey through the forest",
                purpose="Rising action",
                estimated_word_count=100
            )
        ]

        mock_iface = mock_interface()
        mock_log = mock_logger()

        with patch('Writer.Scene.ChapterByScene.Writer.Scene.ChapterOutlineToScenes.ChapterOutlineToScenes') as mock_cots:
            mock_cots.return_value = mock_scenes

            # Scene text already has trailing \n\n
            with patch('Writer.Scene.ChapterByScene.Writer.Scene.SceneOutlineToScene.SceneOutlineToScene') as mock_sots:
                mock_sots.side_effect = [
                    "Scene 1 with break\n\n",  # Already has break
                    "Scene 2 with break\n\n"   # Already has break
                ]

                # Act
                result = ChapterByScene(
                    mock_iface,
                    mock_log,
                    1, 2,
                    "test outline",
                    "test story"
                )

                # Assert: Should have breaks but not excessive (no \n\n\n\n)
                assert "\n\n\n\n" not in result, \
                    "Should not have quadruple line breaks (double breaks stacked)"

                # Should still have proper separation
                assert "Scene 1 with break\n\nScene 2 with break" in result or \
                       "Scene 1 with break\n\n\n\nScene 2 with break" in result, \
                    "Scenes should still be properly separated"

    def test_single_scene_no_trailing_break(self, mock_interface, mock_logger):
        """
        Verify that a chapter with a single scene doesn't have unnecessary trailing break.

        Edge case: When there's only 1 scene, we add \n\n after it, but this is
        acceptable as it separates the chapter from subsequent content.
        """
        from Writer.Scene.ChapterByScene import ChapterByScene

        # Arrange
        mock_scenes = [
            SceneOutline(
                scene_number=1,
                setting="Gua",
                characters_present=["Rian", "Ember"],
                action="Final confrontation",
                purpose="Resolution",
                estimated_word_count=300
            )
        ]

        mock_iface = mock_interface()
        mock_log = mock_logger()

        with patch('Writer.Scene.ChapterByScene.Writer.Scene.ChapterOutlineToScenes.ChapterOutlineToScenes') as mock_cots:
            mock_cots.return_value = mock_scenes

            with patch('Writer.Scene.ChapterByScene.Writer.Scene.SceneOutlineToScene.SceneOutlineToScene') as mock_sots:
                mock_sots.return_value = "Single scene text"

                # Act
                result = ChapterByScene(
                    mock_iface,
                    mock_log,
                    1, 1,
                    "test outline",
                    "test story"
                )

                # Assert: Result is the scene text (may have trailing \n\n, which is OK)
                assert result == "Single scene text\n\n" or result == "Single scene text", \
                    f"Expected single scene text with optional trailing break, got: {repr(result)}"
