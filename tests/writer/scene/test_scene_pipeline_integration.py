#!/usr/bin/env python3
"""
Phase 5.1 Integration Tests: Scene Pipeline End-to-End
These tests verify the full pipeline works correctly with metadata preservation
and redundant LLM call removal.
"""

import pytest
import sys
from unittest.mock import MagicMock, Mock, patch
from Writer.Models import SceneOutline, SceneOutlineList

# Mock termcolor before imports
sys.modules['termcolor'] = MagicMock()


class TestScenePipelineIntegration:
    """Integration tests for full scene generation pipeline"""

    def test_full_pipeline_preserves_metadata_end_to_end(self, mock_interface, mock_logger):
        """Verify full pipeline (ChapterOutlineToScenes → ChapterByScene → SceneOutlineToScene) preserves metadata"""
        from Writer.Scene.ChapterByScene import ChapterByScene

        # Arrange: Create scenes with rich metadata
        mock_scenes = [
            SceneOutline(
                scene_number=1,
                setting="Desa kecil di tepi hutan",
                characters_present=["Rian"],
                action="Rian mendengar legenda harta karun dari kakek tua",
                purpose="Membangun latar dan motivasi",
                estimated_word_count=200
            ),
            SceneOutline(
                scene_number=2,
                setting="Hutan gelap dengan pohon raksasa",
                characters_present=["Rian", "Bang Jaga"],
                action="Rian bertemu penjaga hutan yang memberikan petunjuk",
                purpose="Meningkatkan konflik",
                estimated_word_count=250
            )
        ]

        mock_iface = mock_interface()
        mock_log = mock_logger()

        # Track calls to verify metadata flows through
        metadata_received_in_prompt = []

        def capture_prompt_metadata(prompt_text):
            """Capture metadata from prompts"""
            metadata_received_in_prompt.append(prompt_text)
            return prompt_text

        # Mock ChapterOutlineToScenes to return SceneOutline objects
        with patch('Writer.Scene.ChapterByScene.Writer.Scene.ChapterOutlineToScenes.ChapterOutlineToScenes') as mock_cots:
            mock_cots.return_value = mock_scenes

            # Mock SceneOutlineToScene to capture metadata
            with patch('Writer.Scene.ChapterByScene.Writer.Scene.SceneOutlineToScene.SceneOutlineToScene') as mock_sots:
                # Make mock_sots track calls and capture arguments
                def mock_scene_writer(iface, logger, scene_num, total, scene_obj, outline, context=""):
                    # Verify scene_obj is SceneOutline with metadata
                    assert isinstance(scene_obj, SceneOutline), "Should receive SceneOutline object"
                    assert hasattr(scene_obj, 'setting'), "Should have setting"
                    assert hasattr(scene_obj, 'characters_present'), "Should have characters"
                    assert hasattr(scene_obj, 'purpose'), "Should have purpose"
                    assert hasattr(scene_obj, 'estimated_word_count'), "Should have word count"

                    # Capture that metadata was available
                    metadata_received_in_prompt.append({
                        'scene_num': scene_num,
                        'setting': scene_obj.setting,
                        'characters': scene_obj.characters_present,
                        'purpose': scene_obj.purpose,
                        'word_count': scene_obj.estimated_word_count
                    })
                    return f"Scene {scene_num} text\n\n"

                mock_sots.side_effect = mock_scene_writer

                # Act: Run full pipeline
                result = ChapterByScene(
                    mock_iface,
                    mock_log,
                    1,  # ChapterNum
                    3,  # TotalChapters
                    "test chapter outline",
                    "test story outline",
                    "test base context"
                )

                # Assert: Verify end-to-end flow
                assert isinstance(result, str), "Should return chapter text"
                assert "Scene 1 text" in result, "Should contain scene 1"
                assert "Scene 2 text" in result, "Should contain scene 2"

                # Verify metadata was preserved and used
                assert len(metadata_received_in_prompt) == 2, "Should process 2 scenes"

                scene1_meta = metadata_received_in_prompt[0]
                assert scene1_meta['setting'] == "Desa kecil di tepi hutan"
                assert scene1_meta['characters'] == ["Rian"]
                assert scene1_meta['purpose'] == "Membangun latar dan motivasi"
                assert scene1_meta['word_count'] == 200

                scene2_meta = metadata_received_in_prompt[1]
                assert scene2_meta['setting'] == "Hutan gelap dengan pohon raksasa"
                assert scene2_meta['characters'] == ["Rian", "Bang Jaga"]
                assert scene2_meta['word_count'] == 250

    def test_pipeline_removes_only_one_llm_call(self, mock_interface, mock_logger):
        """Verify pipeline no longer calls ScenesToJSON (redundant LLM call removed)"""
        from Writer.Scene.ChapterByScene import ChapterByScene

        # Arrange: Mock scenes
        mock_scenes = [
            SceneOutline(
                scene_number=1,
                setting="Test setting",
                characters_present=["Test char"],
                action="Test action",
                purpose="Test purpose",
                estimated_word_count=100
            )
        ]

        mock_iface = mock_interface()
        mock_log = mock_logger()

        # Track LLM calls
        llm_call_count = {'count': 0}

        def track_llm_call(*args, **kwargs):
            llm_call_count['count'] += 1
            mock_result = Mock()
            mock_result.action = "Scene text"
            return ([], mock_result, {})

        # Mock ChapterOutlineToScenes
        with patch('Writer.Scene.ChapterByScene.Writer.Scene.ChapterOutlineToScenes.ChapterOutlineToScenes') as mock_cots:
            mock_cots.return_value = mock_scenes

            # Mock ScenesToJSON - should NOT be called
            with patch('Writer.Scene.ChapterByScene.Writer.Scene.ScenesToJSON.ScenesToJSON') as mock_stj:
                mock_stj.side_effect = Exception("ScenesToJSON should NOT be called!")

                # Mock SceneOutlineToScene
                with patch('Writer.Scene.ChapterByScene.Writer.Scene.SceneOutlineToScene.SceneOutlineToScene') as mock_sots:
                    mock_sots.return_value = "Scene text\n\n"

                    # Act: Run pipeline
                    result = ChapterByScene(
                        mock_iface, mock_log, 1, 3,
                        "outline", "story", "context"
                    )

                    # Assert: ScenesToJSON was NOT called (no redundant LLM call)
                    mock_stj.assert_not_called()

                    # Verify only necessary components were called
                    mock_cots.assert_called_once()  # ChapterOutlineToScenes called
                    mock_sots.assert_called_once()  # SceneOutlineToScene called
                    # ScenesToJSON NOT called (redundant LLM call eliminated!)

    def test_pipeline_handles_deduplication_without_llm(self, mock_interface, mock_logger):
        """Verify pipeline deduplicates scenes without making LLM call"""
        from Writer.Scene.ChapterByScene import ChapterByScene

        # Arrange: Create scenes with exact duplicates
        mock_scenes = [
            SceneOutline(
                scene_number=1,
                setting="Cave",
                characters_present=["Hero"],
                action="Hero finds treasure in the deep dark cave filled with gold",
                purpose="Climax",
                estimated_word_count=200
            ),
            SceneOutline(
                scene_number=2,
                setting="Cave",
                characters_present=["Hero"],
                action="Hero finds treasure in the deep dark cave filled with gold",  # DUPLICATE
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

        mock_iface = mock_interface()
        mock_log = mock_logger()

        # Mock ChapterOutlineToScenes
        with patch('Writer.Scene.ChapterByScene.Writer.Scene.ChapterOutlineToScenes.ChapterOutlineToScenes') as mock_cots:
            mock_cots.return_value = mock_scenes

            # Mock SceneOutlineToScene to count calls
            with patch('Writer.Scene.ChapterByScene.Writer.Scene.SceneOutlineToScene.SceneOutlineToScene') as mock_sots:
                mock_sots.return_value = "Scene text\n\n"

                # Act: Run pipeline
                result = ChapterByScene(
                    mock_iface, mock_log, 1, 3,
                    "outline", "story"
                )

                # Assert: Deduplication worked - only 2 unique scenes processed
                assert mock_sots.call_count == 2, \
                    f"Expected 2 calls (duplicate removed), got {mock_sots.call_count}"

                # Verify the correct scenes were kept (1 and 3, not 2)
                calls = mock_sots.call_args_list
                scene1_obj = calls[0][0][4]  # 5th argument is scene object
                scene2_obj = calls[1][0][4]

                # First call should be scene 1
                assert scene1_obj.action == "Hero finds treasure in the deep dark cave filled with gold"

                # Second call should be scene 3 (scene 2 was duplicate)
                assert scene2_obj.action == "Hero exits the cave victorious"
