"""
Tests for INITIAL_OUTLINE_PROMPT (Phase 6 update).

Phase 6: Format instructions removed from prompts because SafeGeneratePydantic
automatically adds them via _build_format_instruction().

This prevents duplication and ensures language-aware format instructions.
"""
from unittest.mock import MagicMock


class TestInitialOutlinePromptFormat:
    """Test that INITIAL_OUTLINE_PROMPT has NO hardcoded format instructions."""

    def test_english_prompt_has_json_format_section(self):
        """Test that English prompt has NO hardcoded format instructions"""
        # Arrange
        import Writer.Prompts as Prompts

        # Act
        prompt = Prompts.INITIAL_OUTLINE_PROMPT

        # Assert - Should NOT have format instructions (added by SafeGeneratePydantic)
        assert 'JSON OUTPUT FORMAT' not in prompt, "Format instructions should not be hardcoded"
        assert '{{' not in prompt or 'Example format:' not in prompt, "Should not have JSON examples"
        # Should still have core task
        assert 'outline' in prompt.lower(), "Prompt should describe task"

    def test_indonesian_prompt_has_json_format_section(self):
        """Test that Indonesian prompt has NO hardcoded format instructions"""
        # Arrange
        import Writer.Prompts_id as Prompts_id

        # Act
        prompt = Prompts_id.INITIAL_OUTLINE_PROMPT

        # Assert - Should NOT have format instructions (added by SafeGeneratePydantic)
        assert 'FORMAT JSON' not in prompt, "Format instructions should not be hardcoded"
        assert '{{' not in prompt or 'Format contoh:' not in prompt, "Should not have JSON examples"
        # Should still have core task
        assert 'outline' in prompt.lower(), "Prompt should describe task"

    def test_prompts_define_required_fields(self):
        """Test that prompts describe requirements (not hardcode JSON structure)"""
        # Arrange
        import Writer.Prompts as Prompts
        import Writer.Prompts_id as Prompts_id

        # Act
        en_prompt = Prompts.INITIAL_OUTLINE_PROMPT
        id_prompt = Prompts_id.INITIAL_OUTLINE_PROMPT

        # Assert - Should describe outline requirements (not show JSON structure)
        # Requirements mentioned in text, actual structure added by SafeGeneratePydantic
        assert 'chapter' in en_prompt.lower(), "English prompt should mention chapters"
        assert 'character' in en_prompt.lower(), "English prompt should mention characters"
        assert 'detail' in en_prompt.lower(), "English prompt should request detail"

        assert 'bab' in id_prompt.lower() or 'chapter' in id_prompt.lower(), "Indonesian prompt should mention chapters"
        assert 'karakter' in id_prompt.lower() or 'character' in id_prompt.lower(), "Indonesian prompt should mention characters"


class TestInitialOutlineGeneration:
    """Test that GenerateOutline uses SafeGeneratePydantic for OutlineOutput correctly."""

    def test_initial_outline_uses_pydantic_model(self, mock_interface, mock_logger):
        """Test that SafeGeneratePydantic is called with OutlineOutput model"""
        # Arrange
        from Writer.OutlineGenerator import GenerateOutline
        from Writer.Models import StoryElements, OutlineOutput

        mock_int = mock_interface()
        mock_log = mock_logger()

        # Mock SafeGenerateJSON for base context
        mock_int.SafeGenerateJSON.return_value = (
            [{'role': 'assistant'}],
            {'context': 'test context'},
            {'prompt_tokens': 50}
        )

        # Create valid Pydantic objects
        story_elements = StoryElements(
            title="Test Story Title",
            genre="Fantasy",
            themes=["adventure"],
            characters={},
            pacing=None,
            style=None,
            plot_structure=None,
            settings={},
            symbolism=None,
            conflict="Hero vs Villain",
            resolution="Hero wins"
        )

        outline_output = OutlineOutput(
            title="Test Story Adventure Title",
            genre="Fantasy",
            theme=None,
            chapters=[
                "Chapter 1: The hero begins their journey through ancient lands filled with mystery and wonder",
                "Chapter 2: Rising challenges test the hero as they discover hidden truths about their destiny"
            ],
            character_list=["Hero"],
            character_details=None,
            setting={"time": "Present", "location": "Earth", "culture": "Modern", "mood": "Tense"},
            target_chapter_count=2
        )

        # Mock SafeGeneratePydantic for StoryElements and Outline with full revision loop
        mock_int.SafeGeneratePydantic.side_effect = [
            # StoryElements
            ([{'role': 'assistant'}], story_elements, {'prompt_tokens': 100}),
            # Initial outline - THIS IS THE KEY TEST
            ([{'role': 'assistant'}], outline_output, {'prompt_tokens': 200}),
            # Review feedback (iteration 1)
            ([{'role': 'assistant'}], MagicMock(feedback="Good"), {'prompt_tokens': 50}),
            # Outline complete check (iteration 1) - not ready yet
            ([{'role': 'assistant'}], MagicMock(IsComplete=False), {'prompt_tokens': 20}),
            # Revised outline (iteration 1)
            ([{'role': 'assistant'}], outline_output, {'prompt_tokens': 150}),
            # Review feedback (iteration 2)
            ([{'role': 'assistant'}], MagicMock(feedback="Excellent"), {'prompt_tokens': 50}),
            # Outline complete check (iteration 2) - ready to exit
            ([{'role': 'assistant'}], MagicMock(IsComplete=True), {'prompt_tokens': 20}),
        ]

        # Act
        GenerateOutline(mock_int, mock_log, "Test story prompt")

        # Assert - Verify OutlineOutput was used (second SafeGeneratePydantic call)
        assert mock_int.SafeGeneratePydantic.call_count >= 2
        second_call_args = mock_int.SafeGeneratePydantic.call_args_list[1][0]
        assert second_call_args[3] == OutlineOutput

    def test_outline_output_validates_required_fields(self):
        """Test that OutlineOutput model validates required fields"""
        # Arrange
        from Writer.Models import OutlineOutput
        import pytest

        # Act & Assert - Missing required fields should raise ValidationError
        with pytest.raises(Exception):  # Pydantic ValidationError
            OutlineOutput(  # type: ignore[call-arg]
                # Missing title, genre, chapters, target_chapter_count
                theme="Adventure",
                character_list=["Hero"]
            )

    def test_outline_output_validates_chapter_length(self):
        """Test that OutlineOutput validates minimum chapter outline length"""
        # Arrange
        from Writer.Models import OutlineOutput
        import pytest

        # Act & Assert - Too short chapters should raise ValidationError
        with pytest.raises(Exception):  # Pydantic ValidationError
            OutlineOutput(
                title="Test Story Title",
                genre="Fantasy",
                theme=None,
                chapters=["Short"],  # Too short - needs 100+ chars
                character_list=["Hero"],
                character_details=None,
                setting={"time": "Now", "location": "Here", "culture": "Modern", "mood": "Tense"},
                target_chapter_count=1
            )

    def test_outline_output_accepts_valid_structure(self):
        """Test that OutlineOutput accepts valid chapter structure"""
        # Arrange
        from Writer.Models import OutlineOutput

        # Act - Create with valid structure
        outline = OutlineOutput(
            title="Valid Story Title",
            genre="Fantasy Adventure",
            theme="Courage and friendship",
            chapters=[
                "Chapter 1: The hero begins their epic journey through mysterious ancient lands filled with danger and wonder as they seek the legendary artifact",
                "Chapter 2: Rising challenges test the hero's courage as they face powerful enemies and discover hidden truths about their own destiny and purpose"
            ],
            character_list=["Hero", "Mentor", "Villain"],
            character_details={"Hero": "Brave protagonist", "Mentor": "Wise guide"},
            setting={
                "time": "Medieval fantasy era",
                "location": "Enchanted kingdom with magical forests",
                "culture": "Feudal society with wizards and knights",
                "mood": "Mysterious and adventurous"
            },
            target_chapter_count=2
        )

        # Assert
        assert outline.title == "Valid Story Title"
        assert len(outline.chapters) == 2
        assert outline.target_chapter_count == 2
        assert "Hero" in outline.character_list

    def test_outline_output_has_to_prompt_string_method(self):
        """Test that OutlineOutput has to_prompt_string method for formatting"""
        # Arrange
        from Writer.Models import OutlineOutput

        outline = OutlineOutput(
            title="Test Story Title",
            genre="Fantasy",
            theme=None,
            chapters=[
                "Chapter 1: The hero begins their journey through ancient lands filled with mystery and wonder as they seek ancient wisdom",
                "Chapter 2: Rising challenges test the hero as they discover hidden truths about their destiny and confront powerful enemies"
            ],
            character_list=["Hero"],
            character_details=None,
            setting={"time": "Present", "location": "Earth", "culture": "Modern", "mood": "Tense"},
            target_chapter_count=2
        )

        # Act & Assert
        assert hasattr(outline, 'to_prompt_string')
        assert callable(outline.to_prompt_string)
        result = outline.to_prompt_string()
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain key information
        assert outline.title in result
