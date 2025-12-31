"""
Tests for SceneContent Pydantic model.

Following TDD London School methodology:
- RED phase: Write failing tests first
- GREEN phase: Implement model to make tests pass
- REFACTOR phase: Clean up implementation

This module tests the SceneContent model which enforces:
1. Full prose content (min 150 chars)
2. No placeholder text (TODO, FIXME, TBD, [PLACEHOLDER])
3. Word count consistency
4. Ellipsis allowed in prose
"""

import pytest
from pydantic import ValidationError


class TestSceneContentValidation:
    """Test SceneContent model validation - following patterns from test_models.py"""

    def test_create_valid_scene_content(self):
        """Test creating valid SceneContent with proper prose (200+ words)"""
        from Writer.Models import SceneContent

        # Full prose content (200+ words)
        prose_text = (
            "Alex walked through the misty forest, his heart pounding with anticipation. "
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
            "onto the first plank, feeling it creak beneath his weight. The river roared "
            "below, eager and hungry. He forced himself to look ahead, to focus on Sarah's "
            "figure. With each careful step, the distance between them shrank, until finally "
            "he reached the other side and stood before her."
        )

        scene = SceneContent(
            text=prose_text)

        assert scene.text == prose_text
        assert len(scene.text) > 150



    def test_reject_too_short_scene_content(self):
        """Test that text less than 150 chars is rejected"""
        from Writer.Models import SceneContent

        # Too short (less than 150 chars)
        short_text = "This is too short for a scene."

        with pytest.raises(ValidationError) as exc_info:
            SceneContent(
                text=short_text)

        error_message = str(exc_info.value)
        assert "at least 150 characters" in error_message

    def test_reject_placeholder_todo(self):
        """Test that TODO placeholder is rejected"""
        from Writer.Models import SceneContent

        prose_with_todo = (
            "Alex walked through the forest. TODO: Add more description here. "
            "The trees loomed overhead, creating patterns against the sky. "
            "He could hear water flowing in the distance, reminding him of his goal. "
            "Sarah's words echoed in his mind as he continued forward through the mist."
        )

        with pytest.raises(ValidationError) as exc_info:
            SceneContent(
                text=prose_with_todo)

        error_message = str(exc_info.value)
        assert "placeholder text: TODO" in error_message

    def test_reject_placeholder_fixme(self):
        """Test that FIXME placeholder is rejected"""
        from Writer.Models import SceneContent

        prose_with_fixme = (
            "Alex walked through the forest, his heart pounding with anticipation. "
            "FIXME: Need better transition here. The trees loomed overhead, creating "
            "intricate patterns against the twilight sky. He could hear the distant "
            "sound of water flowing, a reminder of the river he needed to cross."
        )

        with pytest.raises(ValidationError) as exc_info:
            SceneContent(
                text=prose_with_fixme)

        error_message = str(exc_info.value)
        assert "placeholder text: FIXME" in error_message

    def test_reject_placeholder_tbd(self):
        """Test that TBD placeholder is rejected"""
        from Writer.Models import SceneContent

        prose_with_tbd = (
            "Alex walked through the forest, his heart pounding with anticipation. "
            "The ancient trees loomed overhead, their branches creating intricate patterns "
            "against the twilight sky. TBD - add more sensory details. He could hear "
            "the distant sound of water flowing, a reminder of the river he needed to cross."
        )

        with pytest.raises(ValidationError) as exc_info:
            SceneContent(
                text=prose_with_tbd)

        error_message = str(exc_info.value)
        assert "placeholder text: TBD" in error_message

    def test_reject_placeholder_bracket(self):
        """Test that [PLACEHOLDER] is rejected"""
        from Writer.Models import SceneContent

        prose_with_placeholder = (
            "Alex walked through the forest, his heart pounding with anticipation. "
            "[PLACEHOLDER] The ancient trees loomed overhead, their branches creating "
            "intricate patterns against the twilight sky. He could hear the distant "
            "sound of water flowing, a reminder of the river he needed to cross."
        )

        with pytest.raises(ValidationError) as exc_info:
            SceneContent(
                text=prose_with_placeholder)

        error_message = str(exc_info.value)
        assert "placeholder text: [PLACEHOLDER]" in error_message

    def test_allow_ellipsis(self):
        """Test that ellipsis (...) is allowed in prose (not treated as placeholder)"""
        from Writer.Models import SceneContent

        # Ellipsis should be allowed in narrative prose
        prose_with_ellipsis = (
            "Alex walked through the forest, his heart pounding... The ancient trees "
            "loomed overhead, their branches creating intricate patterns against the sky. "
            "He could hear the distant sound of water flowing, a reminder of his goal. "
            "Sarah's words echoed: 'Meet me where the old bridge stands...' As he pushed "
            "through the underbrush, thorns caught at his cloak, but he pressed on."
        )

        # Should NOT raise ValidationError
        scene = SceneContent(
            text=prose_with_ellipsis)

        assert "..." in scene.text

    def test_scene_content_strips_whitespace(self):
        """Test whitespace normalization"""
        from Writer.Models import SceneContent

        prose_with_whitespace = """
        Alex walked through the misty forest, his heart pounding with anticipation.
        The ancient trees loomed overhead, their branches creating intricate patterns
        against the twilight sky. He could hear the distant sound of water flowing,
        a reminder of the river he needed to cross. Sarah's words echoed in his mind.
        """

        scene = SceneContent(
            text=prose_with_whitespace)

        # Should strip leading/trailing whitespace
        assert not scene.text.startswith("\n")
        assert not scene.text.endswith("\n")
        assert scene.text.strip() == scene.text

    def test_scene_content_minimum_length_boundary(self):
        """Test exact boundary at 150 characters"""
        from Writer.Models import SceneContent

        # Exactly 150 characters (should pass)
        prose_150_chars = "A" * 150

        scene = SceneContent(
            text=prose_150_chars)

        assert len(scene.text) == 150

        # 149 characters (should fail)
        prose_149_chars = "A" * 149

        with pytest.raises(ValidationError) as exc_info:
            SceneContent(
                text=prose_149_chars)

        error_message = str(exc_info.value)
        assert "at least 150 characters" in error_message

    def test_scene_content_with_dialogue(self):
        """Test that prose with dialogue is properly validated"""
        from Writer.Models import SceneContent

        prose_with_dialogue = (
            "Alex stepped onto the bridge, his boots echoing on the weathered planks. "
            "Sarah turned to face him, her eyes reflecting the fading light. 'You came,' "
            "she whispered, her voice barely audible over the rushing water below. "
            "'I had to,' Alex replied, moving closer. 'I couldn't let you face this alone.' "
            "She smiled, a sad, knowing smile. 'Then we face it together,' she said, "
            "reaching out to take his hand. The mist swirled around them, thick and mysterious."
        )

        scene = SceneContent(
            text=prose_with_dialogue)

        assert '"' in scene.text or "'" in scene.text


class TestSceneContentEdgeCases:
    """Test edge cases and special scenarios for SceneContent"""

    def test_scene_content_with_numbers(self):
        """Test that prose with numbers is properly handled"""
        from Writer.Models import SceneContent

        prose_with_numbers = (
            "Alex had waited 3 long years for this moment. The bridge stretched 200 feet "
            "across the chasm, each of its 47 planks worn smooth by time and weather. "
            "He took his first step at exactly 7:30 PM, just as Sarah had instructed. "
            "The temperature had dropped to 15 degrees, and his breath formed small clouds "
            "in the frigid air as he made his way across, counting each step carefully."
        )

        scene = SceneContent(
            text=prose_with_numbers)

        assert "3" in scene.text
        assert "200" in scene.text

    def test_scene_content_case_insensitive_placeholder_detection(self):
        """Test that placeholder detection is case-insensitive"""
        from Writer.Models import SceneContent

        # Lowercase 'todo' should also be caught
        prose_lowercase = (
            "Alex walked through the forest. todo: add description. "
            "The trees loomed overhead, creating patterns against the sky. "
            "He could hear water flowing in the distance, reminding him of his goal. "
            "Sarah's words echoed in his mind as he continued forward through the mist."
        )

        with pytest.raises(ValidationError) as exc_info:
            SceneContent(
                text=prose_lowercase)

        error_message = str(exc_info.value)
        assert "placeholder text: TODO" in error_message
