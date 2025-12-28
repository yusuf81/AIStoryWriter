"""
Tests for CHAPTER_OUTLINE_PROMPT (Phase 6 update).

Phase 6: Format instructions removed from prompts because SafeGeneratePydantic
automatically adds them via _build_format_instruction().

This prevents duplication and ensures language-aware format instructions.
"""
from unittest.mock import MagicMock


class TestChapterOutlinePromptFormat:
    """Test that CHAPTER_OUTLINE_PROMPT has NO hardcoded format instructions."""

    def test_english_prompt_has_json_format_section(self):
        """Test that English prompt has NO hardcoded format instructions"""
        # Arrange
        import Writer.Prompts as Prompts

        # Act
        prompt = Prompts.CHAPTER_OUTLINE_PROMPT

        # Assert - Should NOT have format instructions (added by SafeGeneratePydantic)
        assert 'JSON OUTPUT FORMAT' not in prompt, "Format instructions should not be hardcoded"
        assert '{{' not in prompt or 'Example format:' not in prompt, "Should not have JSON examples"
        # Should still have core task
        assert 'outline' in prompt.lower() and 'chapter' in prompt.lower(), "Prompt should describe task"

    def test_indonesian_prompt_has_json_format_section(self):
        """Test that Indonesian prompt has NO hardcoded format instructions"""
        # Arrange
        import Writer.Prompts_id as Prompts_id

        # Act
        prompt = Prompts_id.CHAPTER_OUTLINE_PROMPT

        # Assert - Should NOT have format instructions (added by SafeGeneratePydantic)
        assert 'FORMAT JSON' not in prompt, "Format instructions should not be hardcoded"
        assert '{{' not in prompt or 'Format contoh:' not in prompt, "Should not have JSON examples"
        # Should still have core task
        assert 'outline' in prompt.lower() or 'bab' in prompt.lower(), "Prompt should describe task"

    def test_prompts_define_scene_structure(self):
        """Test that prompts describe scene requirements (no hardcoded structure)"""
        # Arrange
        import Writer.Prompts as Prompts
        import Writer.Prompts_id as Prompts_id

        # Act
        en_prompt = Prompts.CHAPTER_OUTLINE_PROMPT
        id_prompt = Prompts_id.CHAPTER_OUTLINE_PROMPT

        # Assert - Should describe scene requirements (not hardcode JSON structure)
        # Requirements mentioned in text, actual structure added by SafeGeneratePydantic
        assert 'scene' in en_prompt.lower(), "English prompt should mention scenes"
        assert 'character' in en_prompt.lower() or 'setting' in en_prompt.lower(), "English prompt should mention characters/setting"
        assert 'plot' in en_prompt.lower() or 'event' in en_prompt.lower(), "English prompt should mention plot/events"

        assert 'scene' in id_prompt.lower() or 'adegan' in id_prompt.lower(), "Indonesian prompt should mention scenes"
        assert 'karakter' in id_prompt.lower() or 'character' in id_prompt.lower(), "Indonesian prompt should mention characters"


class TestChapterOutlineGeneration:
    """Test that GeneratePerChapterOutline uses SafeGeneratePydantic correctly."""

    def test_chapter_outline_uses_pydantic_model(self, mock_interface, mock_logger):
        """Test that SafeGeneratePydantic is called with ChapterOutlineOutput model"""
        # Arrange
        from Writer.OutlineGenerator import GeneratePerChapterOutline
        from Writer.Models import ChapterOutlineOutput, EnhancedSceneOutline

        mock_int = mock_interface()
        mock_log = mock_logger()

        # Create valid ChapterOutlineOutput
        chapter_outline = ChapterOutlineOutput(  # type: ignore[call-arg]
            chapter_number=1,
            chapter_title="The Beginning",
            scenes=[
                EnhancedSceneOutline(
                    title="Opening Scene",
                    characters_and_setting="Hero in village market at dawn, bustling atmosphere with merchants and travelers",
                    conflict_and_tone="Internal conflict about leaving home, nostalgic and bittersweet tone",
                    key_events="Hero receives mysterious message, decides to embark on journey, says goodbye to mentor",
                    literary_devices="Foreshadowing through the mysterious message, symbolism of dawn representing new beginnings",
                    resolution="Hero departs at sunrise, setting off on the adventure with determination and uncertainty"
                )
            ],
            outline_summary="Hero begins their journey from the village after receiving a mysterious summons"
        )

        # Mock SafeGeneratePydantic
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            chapter_outline,
            {'prompt_tokens': 200}
        )

        # Act
        summary, title = GeneratePerChapterOutline(
            mock_int, mock_log, 1, 10, "Test outline"
        )

        # Assert
        assert mock_int.SafeGeneratePydantic.called
        # Verify ChapterOutlineOutput was used
        call_args = mock_int.SafeGeneratePydantic.call_args[0]
        from Writer.Models import ChapterOutlineOutput as ExpectedModel
        assert call_args[3] == ExpectedModel
        assert title == "The Beginning"

    def test_chapter_outline_validates_required_fields(self):
        """Test that ChapterOutlineOutput validates required fields"""
        # Arrange
        from Writer.Models import ChapterOutlineOutput
        import pytest

        # Act & Assert - Missing required fields should raise ValidationError
        with pytest.raises(Exception):  # Pydantic ValidationError
            ChapterOutlineOutput(  # type: ignore[call-arg]
                # Missing chapter_number, chapter_title, scenes, outline_summary
                chapter_number=1
            )

    def test_enhanced_scene_outline_accepts_detailed_content(self):
        """Test that EnhancedSceneOutline accepts detailed scene content"""
        # Arrange
        from Writer.Models import EnhancedSceneOutline

        # Act - Create with detailed content (validates it accepts proper scenes)
        scene = EnhancedSceneOutline(
            title="The Dawn Meeting",
            characters_and_setting="Hero and Mentor meet in village square at dawn",
            conflict_and_tone="Internal conflict about leaving, bittersweet tone",
            key_events="Hero receives sword, mentor gives warning, villagers gather",
            literary_devices="Foreshadowing through mentor's cryptic words",
            resolution="Hero departs with renewed determination"
        )

        # Assert
        assert scene.title == "The Dawn Meeting"
        assert scene.characters_and_setting is not None and len(scene.characters_and_setting) > 10
        assert scene.key_events is not None and len(scene.key_events) > 10

    def test_chapter_outline_accepts_valid_structure(self):
        """Test that ChapterOutlineOutput accepts valid scene structure"""
        # Arrange
        from Writer.Models import ChapterOutlineOutput, EnhancedSceneOutline

        # Act - Create with valid structure
        chapter = ChapterOutlineOutput(  # type: ignore[call-arg]
            chapter_number=1,
            chapter_title="The Hero's Departure",
            scenes=[
                EnhancedSceneOutline(
                    title="Morning Preparation Scene",
                    characters_and_setting="Hero and Mentor in the village square at dawn with morning mist",
                    conflict_and_tone="External pressure to leave versus internal reluctance, somber and reflective tone",
                    key_events="Hero packs supplies, receives magic sword from mentor, villagers gather to bid farewell",
                    literary_devices="Symbolism of the sword representing responsibility, foreshadowing through mentor's cryptic warning",
                    resolution="Hero crosses the village boundary, looking back one last time before the journey truly begins"
                ),
                EnhancedSceneOutline(
                    title="Journey Begins",
                    characters_and_setting="Hero alone on forest path, dense trees and dappled sunlight filtering through",
                    conflict_and_tone="Uncertainty about the path ahead, adventurous yet anxious tone",
                    key_events="Hero encounters first obstacle, uses skills taught by mentor, gains confidence in abilities",
                    literary_devices="Metaphor of the winding path representing life's journey, natural imagery reflecting inner state",
                    resolution="Hero reaches first milestone marker, feels renewed determination to continue the quest forward"
                )
            ],
            outline_summary="Hero departs village with mentor's blessing and magic sword, beginning the adventure into unknown territories"
        )

        # Assert
        assert chapter.chapter_number == 1
        assert len(chapter.scenes) == 2
        assert chapter.scenes[0].title == "Morning Preparation Scene"
        assert len(chapter.outline_summary) > 50

    def test_chapter_outline_extracts_full_scene_content(self):
        """Test that GeneratePerChapterOutline extracts full scene content (not just summary)"""
        # Arrange
        from Writer.OutlineGenerator import GeneratePerChapterOutline
        from Writer.Models import ChapterOutlineOutput, EnhancedSceneOutline

        mock_int = MagicMock()
        mock_log = MagicMock()

        # Create chapter with detailed scenes
        chapter_outline = ChapterOutlineOutput(  # type: ignore[call-arg]
            chapter_number=1,
            chapter_title="Test Chapter",
            scenes=[
                EnhancedSceneOutline(
                    title="Detailed Scene Title",
                    characters_and_setting="Hero and companion in ancient temple ruins at midnight, eerie atmosphere",
                    conflict_and_tone="Mystery about temple's secrets, suspenseful and tense tone",
                    key_events="Discovery of hidden chamber, deciphering ancient inscriptions, trap activation",
                    literary_devices="Dramatic irony as reader knows more than characters, suspense building",
                    resolution="Narrow escape from trap, gaining crucial information about the quest's true purpose"
                )
            ],
            outline_summary="Brief 40-word summary that would trigger MegaOutline fallback if used alone"
        )

        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            chapter_outline,
            {'prompt_tokens': 200}
        )

        # Act
        summary, _ = GeneratePerChapterOutline(
            mock_int, mock_log, 1, 10, "Test outline"
        )

        # Assert - Should extract full scene content, not just outline_summary
        assert "Detailed Scene Title" in summary
        assert "characters_and_setting" in summary.lower() or "ancient temple" in summary.lower()
        assert len(summary) > 100, "Should extract full scenes content to avoid MegaOutline fallback"
