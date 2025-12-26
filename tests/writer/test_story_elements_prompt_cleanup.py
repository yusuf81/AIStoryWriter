"""
Tests for GENERATE_STORY_ELEMENTS prompt cleanup (Phase 2).

This tests the removal of markdown template conflict from GENERATE_STORY_ELEMENTS.
The prompt should ONLY have JSON format instructions, no markdown template.

Pattern: Keep SafeGeneratePydantic, remove markdown template to eliminate dual-format confusion.
"""
from unittest.mock import MagicMock


class TestStoryElementsPromptFormat:
    """Test that GENERATE_STORY_ELEMENTS prompts have no markdown template."""

    def test_english_prompt_has_no_markdown_template(self):
        """Test that English prompt does not contain markdown RESPONSE_TEMPLATE"""
        # Arrange
        import Writer.Prompts as Prompts

        # Act
        prompt = Prompts.GENERATE_STORY_ELEMENTS

        # Assert - Should NOT have markdown template tags
        assert '<RESPONSE_TEMPLATE>' not in prompt
        assert '</RESPONSE_TEMPLATE>' not in prompt
        # Should NOT have markdown structure instructions
        assert '# Story Title' not in prompt
        assert '## Genre' not in prompt
        assert '## Characters' not in prompt
        assert '### Main Character(s)' not in prompt

    def test_indonesian_prompt_has_no_markdown_template(self):
        """Test that Indonesian prompt does not contain markdown template"""
        # Arrange
        import Writer.Prompts_id as Prompts_id

        # Act
        prompt = Prompts_id.GENERATE_STORY_ELEMENTS

        # Assert - Should NOT have markdown template
        assert '<RESPONSE_TEMPLATE>' not in prompt
        assert '</RESPONSE_TEMPLATE>' not in prompt
        # Should NOT have markdown headers (Indonesian)
        assert '# Judul' not in prompt or '# Story' not in prompt
        assert '## Genre' not in prompt
        assert '## Karakter' not in prompt or '## Characters' not in prompt

    def test_prompts_have_json_format_only(self):
        """Test that both prompts have clear JSON format instructions"""
        # Arrange
        import Writer.Prompts as Prompts
        import Writer.Prompts_id as Prompts_id

        # Act
        en_prompt = Prompts.GENERATE_STORY_ELEMENTS
        id_prompt = Prompts_id.GENERATE_STORY_ELEMENTS

        # Assert - Both should have JSON format
        assert 'JSON' in en_prompt
        assert 'JSON' in id_prompt
        # Should have example JSON
        assert '"title"' in en_prompt
        assert '"genre"' in en_prompt
        assert '"themes"' in en_prompt
        # Should instruct to return ONLY JSON
        assert 'ONLY' in en_prompt or 'only' in en_prompt
        assert 'HANYA' in id_prompt or 'hanya' in id_prompt


class TestStoryElementsGeneration:
    """Test that GenerateOutline uses SafeGeneratePydantic for StoryElements correctly."""

    def test_story_elements_generation_uses_pydantic(self, mock_interface, mock_logger):
        """Test that SafeGeneratePydantic is called with StoryElements model"""
        # Arrange
        from Writer.OutlineGenerator import GenerateOutline
        from Writer.Models import StoryElements, CharacterDetail, OutlineOutput

        mock_int = mock_interface()
        mock_log = mock_logger()

        # Create valid StoryElements Pydantic object
        story_elements = StoryElements(
            title="Test Story",
            genre="Fantasy",
            themes=["adventure", "friendship"],
            characters={
                "Hero": [
                    CharacterDetail(
                        name="Hero",
                        physical_description="Brave warrior",
                        personality=None,
                        background=None,
                        motivation=None
                    )
                ]
            },
            pacing=None,
            style=None,
            plot_structure=None,
            settings={},
            symbolism=None,
            conflict="Hero vs Villain",
            resolution="Hero wins"
        )

        # Mock SafeGenerateJSON for base context
        mock_int.SafeGenerateJSON.return_value = (
            [{'role': 'assistant'}],
            {'context': 'test context'},
            {'prompt_tokens': 50}
        )

        # Mock SafeGeneratePydantic for StoryElements, Outline, and revisions
        outline_output = OutlineOutput(
            title="Test Story Adventure",
            genre="Fantasy",
            theme=None,
            chapters=[
                "Chapter 1: The hero begins their journey in a mysterious land filled with wonder and danger as they seek ancient wisdom",
                "Chapter 2: Rising challenges test the hero's resolve as they face powerful enemies and discover hidden truths about their destiny"
            ],
            character_list=["Hero"],
            character_details=None,
            setting={"time": "Present", "location": "Earth", "culture": "Modern", "mood": "Tense"},
            target_chapter_count=2
        )

        mock_int.SafeGeneratePydantic.side_effect = [
            # StoryElements
            ([{'role': 'assistant'}], story_elements, {'prompt_tokens': 100}),
            # Initial outline
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

        # Assert
        assert mock_int.SafeGeneratePydantic.call_count >= 2
        # Verify StoryElements was called (first SafeGeneratePydantic call)
        first_call_args = mock_int.SafeGeneratePydantic.call_args_list[0][0]
        assert first_call_args[3] == StoryElements

    def test_story_elements_validates_required_fields(self):
        """Test that StoryElements model validates required fields"""
        # Arrange
        from Writer.Models import StoryElements
        import pytest

        # Act & Assert - Missing required fields should raise ValidationError
        with pytest.raises(Exception):  # Pydantic ValidationError
            StoryElements(  # type: ignore[call-arg]
                # Missing title, genre, themes
                characters={},
                conflict="test",
                resolution="test"
            )

    def test_story_elements_validates_character_structure(self):
        """Test that StoryElements correctly validates character structure"""
        # Arrange
        from Writer.Models import StoryElements, CharacterDetail

        # Act - Valid character structure
        story_elements = StoryElements(
            title="Test Story Title",
            genre="Fantasy",
            themes=["adventure"],
            characters={
                "Hero": [
                    CharacterDetail(
                        name="Hero",
                        physical_description="Brave",
                        personality=None,
                        background=None,
                        motivation=None
                    )
                ]
            },
            pacing=None,
            style=None,
            plot_structure=None,
            settings={},
            symbolism=None,
            conflict="test",
            resolution="test"
        )

        # Assert
        assert "Hero" in story_elements.characters
        assert isinstance(story_elements.characters["Hero"], list)
        assert story_elements.characters["Hero"][0].name == "Hero"

    def test_story_elements_accepts_optional_fields(self):
        """Test that StoryElements accepts all optional fields"""
        # Arrange
        from Writer.Models import StoryElements

        # Act - Create with optional fields
        story_elements = StoryElements(
            title="Test Story Title",
            genre="Fantasy",
            themes=["adventure"],
            characters={},
            pacing="Fast",
            style="Descriptive",
            plot_structure={
                "exposition": "Introduction to the world",
                "rising_action": "Hero faces challenges",
                "climax": "Final confrontation",
                "falling_action": "Aftermath of the battle",
                "resolution": "Peace restored"
            },
            settings={"Castle": {"time": "Medieval", "location": "Europe", "culture": "Feudal", "mood": "Dark"}},
            symbolism=[{"symbol": "Sword", "meaning": "Power"}],
            conflict="Good vs Evil",
            resolution="Good wins"
        )

        # Assert
        assert story_elements.pacing == "Fast"
        assert story_elements.style == "Descriptive"
        assert isinstance(story_elements.plot_structure, dict)
        assert story_elements.plot_structure["exposition"] == "Introduction to the world"
        assert "Castle" in story_elements.settings

    def test_story_elements_returned_has_to_prompt_string_method(self):
        """Test that StoryElements object has to_prompt_string method"""
        # Arrange
        from Writer.Models import StoryElements

        story_elements = StoryElements(
            title="Test Story",
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

        # Act & Assert
        assert hasattr(story_elements, 'to_prompt_string')
        assert callable(story_elements.to_prompt_string)
        # Verify it returns a string
        result = story_elements.to_prompt_string()
        assert isinstance(result, str)
        assert len(result) > 0
