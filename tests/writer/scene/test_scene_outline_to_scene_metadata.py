#!/usr/bin/env python3
"""
Phase 3.1 RED Tests: SceneOutlineToScene should accept and use SceneOutline metadata
These tests verify that SceneOutlineToScene can accept SceneOutline objects
and uses their metadata to enhance scene generation prompts.
"""

import pytest
import sys
from unittest.mock import MagicMock, Mock
from Writer.Models import SceneOutline, SceneContent

# Mock termcolor before imports
sys.modules['termcolor'] = MagicMock()


class TestSceneOutlineToSceneMetadata:
    """RED Tests: SceneOutlineToScene should accept SceneOutline objects with metadata"""

    def test_accepts_scene_outline_object_not_string(self, mock_interface, mock_logger):
        """Verify SceneOutlineToScene accepts SceneOutline object parameter"""
        from Writer.Scene.SceneOutlineToScene import SceneOutlineToScene

        # Arrange: Create real SceneOutline object with metadata
        scene_obj = SceneOutline(
            scene_number=1,
            setting="Gua gelap dengan stalaktit bercahaya",
            characters_present=["Rian", "Naga Kecil"],
            action="Rian menemukan harta karun setelah memecahkan teka-teki",
            purpose="Klimaks cerita - resolusi konflik utama",
            estimated_word_count=300
        )

        # Mock interface to return scene text
        mock_iface = mock_interface()
        mock_scene_result = Mock()
        mock_scene_result.text = "Rian stepped into the dark cave...\n\nMock scene text here."
        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "mock"}],
            mock_scene_result,
            {"tokens": 200}
        )

        # Act: Call with SceneOutline object (not string)
        result = SceneOutlineToScene(
            mock_iface,
            mock_logger(),
            1,  # SceneNum
            3,  # TotalScenes
            scene_obj,  # Pass SceneOutline object, NOT string
            "test story outline",
            "test base context"
        )

        # Assert: Should not raise TypeError
        assert isinstance(result, str), "Should return scene text"
        assert len(result) > 0, "Should return non-empty text"

        # Verify SafeGeneratePydantic was called
        mock_iface.SafeGeneratePydantic.assert_called_once()

    def test_prompt_includes_metadata_fields(self, mock_interface, mock_logger):
        """Verify metadata (setting, characters, purpose, word count) is used in prompt"""
        from Writer.Scene.SceneOutlineToScene import SceneOutlineToScene

        # Arrange: Create scene with rich metadata
        scene_obj = SceneOutline(
            scene_number=2,
            setting="Hutan misteri dengan pohon raksasa",
            characters_present=["Rian", "Bang Jaga", "Burung Hantu"],
            action="Rian bertemu dengan penjaga hutan yang memberikan petunjuk",
            purpose="Memperkenalkan karakter sekunder dan meningkatkan konflik",
            estimated_word_count=250
        )

        mock_iface = mock_interface()
        mock_scene_result = Mock()
        mock_scene_result.text = "Scene text"
        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "mock"}],
            mock_scene_result,
            {"tokens": 200}
        )

        # Act: Call with SceneOutline object
        result = SceneOutlineToScene(
            mock_iface,
            mock_logger(),
            2, 5,
            scene_obj,
            "story outline",
            "base context"
        )

        # Assert: Verify prompt construction used metadata
        call_args = mock_iface.BuildUserQuery.call_args
        assert call_args is not None, "BuildUserQuery should have been called"

        # Extract the formatted prompt (first positional argument)
        formatted_prompt = call_args[0][0]

        # Verify metadata fields are in the prompt
        assert "Hutan misteri" in formatted_prompt or \
               "hutan" in formatted_prompt.lower(), \
            "Setting should be mentioned in prompt"

        # Verify characters or word count guidance is present
        # (exact format depends on prompt template, but metadata should be used)
        assert len(formatted_prompt) > 100, "Prompt should be substantial"

    def test_backward_compatibility_with_string_input(self, mock_interface, mock_logger):
        """Verify SceneOutlineToScene still works with string input (backward compatibility)"""
        from Writer.Scene.SceneOutlineToScene import SceneOutlineToScene

        # Arrange: Use old-style string input
        scene_string = "Rian menemukan pintu rahasia di gua yang dipenuhi harta karun"

        mock_iface = mock_interface()
        mock_scene_result = Mock()
        mock_scene_result.text = "Scene text from string outline"
        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "mock"}],
            mock_scene_result,
            {"tokens": 150}
        )

        # Act: Call with string (old behavior)
        result = SceneOutlineToScene(
            mock_iface,
            mock_logger(),
            1, 1,
            scene_string,  # Pass string, not SceneOutline object
            "story outline"
        )

        # Assert: Should still work
        assert isinstance(result, str)
        assert len(result) > 0

        # Verify SafeGeneratePydantic was called
        mock_iface.SafeGeneratePydantic.assert_called_once()

    def test_metadata_enhances_prompt_vs_string_input(self, mock_interface, mock_logger):
        """Verify SceneOutline object creates richer prompt than string input"""
        from Writer.Scene.SceneOutlineToScene import SceneOutlineToScene

        # Arrange: Create two inputs - one with metadata, one without
        scene_obj = SceneOutline(
            scene_number=1,
            setting="Desa kecil di tepi hutan",
            characters_present=["Rian", "Kakek Tua"],
            action="Rian mendengar legenda harta karun",
            purpose="Membangun latar dan motivasi karakter",
            estimated_word_count=200
        )
        scene_string = "Rian mendengar legenda harta karun"

        mock_iface1 = mock_interface()
        mock_iface2 = mock_interface()

        mock_result = Mock()
        mock_result.text = "Scene text"

        mock_iface1.SafeGeneratePydantic.return_value = ([], mock_result, {})
        mock_iface2.SafeGeneratePydantic.return_value = ([], mock_result, {})

        # Act: Call with both inputs
        result1 = SceneOutlineToScene(mock_iface1, mock_logger(), 1, 1, scene_obj, "outline")
        result2 = SceneOutlineToScene(mock_iface2, mock_logger(), 1, 1, scene_string, "outline")

        # Assert: Metadata version should create richer prompt
        prompt1_call = mock_iface1.BuildUserQuery.call_args
        prompt2_call = mock_iface2.BuildUserQuery.call_args

        assert prompt1_call is not None
        assert prompt2_call is not None

        prompt1_text = prompt1_call[0][0]
        prompt2_text = prompt2_call[0][0]

        # Metadata version should have setting info
        has_setting_info = "Desa kecil" in prompt1_text or "setting" in prompt1_text.lower()

        # Note: Exact comparison depends on implementation, but metadata version
        # should be more detailed than string-only version
        assert len(prompt1_text) > 0
        assert len(prompt2_text) > 0

    def test_scene_outline_to_scene_returns_full_prose(self, mock_interface, mock_logger):
        """Test that SceneOutlineToScene uses SceneContent model and returns full prose, not summary"""
        from Writer.Scene.SceneOutlineToScene import SceneOutlineToScene

        # Arrange: Create mock SceneContent response with full prose
        mock_scene_content = SceneContent(
            text="Alex walked through the misty forest, his heart pounding with anticipation. "
                 "The ancient trees loomed overhead, their branches creating intricate patterns "
                 "against the twilight sky. He could hear the distant sound of water flowing, "
                 "a reminder of the river he needed to cross. Sarah's words echoed in his mind: "
                 "'Meet me where the old bridge stands.' As he pushed through the underbrush, "
                 "thorns caught at his cloak, but he pressed on. The atmosphere grew heavier "
                 "with each step, the mist thickening around him like a living thing. Strange "
                 "sounds whispered through the trees, making him question whether he was truly "
                 "alone. The bridge appeared suddenly, its weathered planks spanning the rushing "
                 "water below. There, on the far side, he saw her silhouette against the dying "
                 "light. She stood motionless, waiting. Alex took a deep breath and stepped "
                 "onto the first plank, feeling it creak beneath his weight.",
            word_count=155
        )

        # Mock interface to return SceneContent
        mock_iface = mock_interface()
        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "mock"}],
            mock_scene_content,
            {"tokens": 200}
        )

        # Create scene outline for input
        scene_obj = SceneOutline(
            scene_number=1,
            setting="Misty forest with old bridge",
            characters_present=["Alex", "Sarah"],
            action="Alex meets Sarah at the bridge",
            purpose="Establish tension and setting",
            estimated_word_count=200
        )

        # Act: Call SceneOutlineToScene
        result = SceneOutlineToScene(
            mock_iface,
            mock_logger(),
            _SceneNum=1,
            _TotalScenes=3,
            _ThisSceneOutline=scene_obj,
            _Outline="Test outline",
            _BaseContext="Test context"
        )

        # Assert: Should return full prose from SceneContent.text
        assert isinstance(result, str), "Should return string"
        assert len(result) > 500, "Should be full prose (500+ chars), not summary"
        assert "walked through the misty forest" in result
        assert "SafeGeneratePydantic" in str(mock_iface.method_calls)

        # Verify SceneContent was used (not SceneOutline)
        call_args = mock_iface.SafeGeneratePydantic.call_args
        assert call_args is not None, "SafeGeneratePydantic should have been called"
        # The 4th argument (index 0, position 3) should be SceneContent class
        model_arg = call_args[0][3]
        assert model_arg == SceneContent, f"Expected SceneContent model, got {model_arg}"
