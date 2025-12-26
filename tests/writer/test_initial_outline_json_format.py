"""
Tests for INITIAL_OUTLINE_PROMPT JSON format addition (Phase 3).

This tests adding clear JSON format instructions to INITIAL_OUTLINE_PROMPT.
The prompt uses SafeGeneratePydantic(OutlineOutput) and needs explicit JSON format.

Pattern: Keep SafeGeneratePydantic, add JSON format instructions.
"""
from unittest.mock import MagicMock


class TestInitialOutlinePromptFormat:
    """Test that INITIAL_OUTLINE_PROMPT has clear JSON format instructions."""

    def test_english_prompt_has_json_format_section(self):
        """Test that English prompt has JSON format instructions"""
        # Arrange
        import Writer.Prompts as Prompts

        # Act
        prompt = Prompts.INITIAL_OUTLINE_PROMPT

        # Assert - Should have JSON format section
        assert 'JSON' in prompt, "Prompt should mention JSON format"
        assert 'OUTPUT FORMAT' in prompt or 'FORMAT' in prompt, "Prompt should have format section"
        # Should request JSON only
        assert 'ONLY' in prompt or 'only' in prompt, "Prompt should request ONLY JSON"

    def test_indonesian_prompt_has_json_format_section(self):
        """Test that Indonesian prompt has JSON format instructions"""
        # Arrange
        import Writer.Prompts_id as Prompts_id

        # Act
        prompt = Prompts_id.INITIAL_OUTLINE_PROMPT

        # Assert - Should have JSON format section
        assert 'JSON' in prompt, "Indonesian prompt should mention JSON format"
        assert 'FORMAT' in prompt or 'format' in prompt, "Indonesian prompt should have format section"
        # Should request JSON only (Indonesian: HANYA)
        assert 'HANYA' in prompt or 'hanya' in prompt, "Indonesian prompt should request HANYA JSON"

    def test_prompts_define_required_fields(self):
        """Test that both prompts define required OutlineOutput fields"""
        # Arrange
        import Writer.Prompts as Prompts
        import Writer.Prompts_id as Prompts_id

        # Act
        en_prompt = Prompts.INITIAL_OUTLINE_PROMPT
        id_prompt = Prompts_id.INITIAL_OUTLINE_PROMPT

        # Assert - Should mention key required fields
        # OutlineOutput required: title, genre, chapters, target_chapter_count
        assert '"title"' in en_prompt, "English prompt should show title field"
        assert '"chapters"' in en_prompt, "English prompt should show chapters field"
        assert '"target_chapter_count"' in en_prompt, "English prompt should show target_chapter_count"

        assert '"title"' in id_prompt, "Indonesian prompt should show title field"
        assert '"chapters"' in id_prompt, "Indonesian prompt should show chapters field"
        assert '"target_chapter_count"' in id_prompt, "Indonesian prompt should show target_chapter_count"


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
