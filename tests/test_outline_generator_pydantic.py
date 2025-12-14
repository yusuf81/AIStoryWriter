"""
Outline Generator TDD Tests - London School Approach
Tests for migrating remaining SafeGenerateText usage to SafeGeneratePydantic
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestOutlineGeneratorPydanticConversion:
    """Test complete conversion of OutlineGenerator to Pydantic"""

    def test_extract_base_context_uses_pydantic(self, mock_interface, mock_logger, mocker):
        """Verify ExtractBaseContext uses SafeGeneratePydantic with BaseContext model"""
        from Writer.OutlineGenerator import GenerateOutline

        # Arrange: Create real BaseContext model
        from Writer.Models import BaseContext as BaseContextModel, StoryElements

        base_context = BaseContextModel(context="Important story elements extracted from prompt")
        story_elements = StoryElements(
            title="Hero's Journey",
            genre="Fantasy Adventure",
            characters={
                "Hero": [{"name": "Hero", "physical_description": "Brave protagonist"}],
                "Villain": [{"name": "Dark wizard", "physical_description": "Evil antagonist"}]
            },
            settings={
                "Castle": {
                    "location": "Magical fortress",
                    "time": "Present day",
                    "culture": "Medieval fantasy",
                    "mood": "Mysterious"
                },
                "Forest": {
                    "location": "Dark woods",
                    "time": "Present day",
                    "culture": "Wild magical",
                    "mood": "Dangerous"
                }
            },
            themes=["Courage", "Good vs Evil"],
            conflict="Hero must defeat dark wizard",
            resolution="Hero saves the kingdom"
        )

        mock_iface = mock_interface()
        # Mock SafeGeneratePydantic to return BaseContext first
        base_context_return = (
            [{"role": "assistant", "content": "Response"}],
            base_context,
            {"tokens": 50}
        )
        # Then return StoryElements with all required attributes
        story_elements_return = (
            [{"role": "assistant", "content": "Response"}],
            story_elements,
            {"tokens": 50}
        )
        # Finally return a valid OutlineOutput
        from Writer.Models import OutlineOutput
        outline_model = OutlineOutput(
            title="Hero's Journey",
            genre="Fantasy",
            chapters=["Chapter 1: Beginning where the hero starts his journey", "Chapter 2: Journey through the dark forest"],
            character_list=["Hero"],
            setting={
                "time": "Fantasy era",
                "location": "Fantasy world",
                "culture": "Magical society with heroes and mythical creatures",
                "mood": "Adventurous and mysterious"
            },
            target_chapter_count=5
        )
        outline_return = (
            [{"role": "assistant", "content": "Response"}],
            outline_model,
            {"tokens": 50}
        )
        # Also need one for the ReviseOutline call
        revised_outline = OutlineOutput(
            title="Revised Hero's Journey",
            genre="Fantasy",
            chapters=["Revised Chapter 1: Beginning where the hero starts his journey with more detail", "Revised Chapter 2: Journey through the dark forest with challenges"],
            character_list=["Hero"],
            setting={
                "time": "Fantasy era",
                "location": "Fantasy world",
                "culture": "Magical society with heroes and mythical creatures",
                "mood": "Adventurous and mysterious"
            },
            target_chapter_count=5
        )
        revised_outline_return = (
            [{"role": "assistant", "content": "Response"}],
            revised_outline,
            {"tokens": 50}
        )

        # Set up the mock to return our Pydantic objects in sequence
        mock_iface.SafeGeneratePydantic.side_effect = [base_context_return, story_elements_return, outline_return, revised_outline_return]

        # Mock LLMEditor methods
        mock_llm_editor = mocker.patch('Writer.LLMEditor')
        mock_llm_editor.GetFeedbackOnOutline.return_value = "Good outline, maybe add more detail"
        mock_llm_editor.GetOutlineRating.return_value = True  # Meets quality standards

        # Mock Config attributes
        mocker.patch('Writer.Config.INITIAL_OUTLINE_WRITER_MODEL', "test_model")
        mocker.patch('Writer.Config.OUTLINE_MAX_REVISIONS', 1)
        mocker.patch('Writer.Config.OUTLINE_MIN_REVISIONS', 1)

        # Act: Call GenerateOutline
        result = GenerateOutline(
            mock_iface,
            mock_logger(),
            "A story about a hero's journey",
            "Fantasy"
        )

        # Assert: SafeGeneratePydantic was called 4 times (BaseContext, StoryElements, Outline, ReviseOutline)
        assert mock_iface.SafeGeneratePydantic.call_count == 4

    def test_revise_outline_uses_pydantic(self, mock_interface, mock_logger):
        """Verify ReviseOutline uses SafeGeneratePydantic with OutlineOutput model"""
        from Writer.OutlineGenerator import ReviseOutline

        # Arrange
        mock_iface = mock_interface()

        from Writer.Models import OutlineOutput
        revised_outline = OutlineOutput(
            title="Revised Story Title",
            genre="Fantasy",
            theme="Good vs Evil",
            chapters=["Chapter 1: Beginning where the hero starts his journey", "Chapter 2: Journey through the dark forest"],
            character_list=["Alice", "Bob"],
            setting={
                "time": "Fairytale era",
                "location": "Fairy land",
                "culture": "Magical realm with enchantments",
                "mood": "Whimsical and wondrous"
            },
            target_chapter_count=10
        )

        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "Response"}],
            revised_outline,
            {"tokens": 100}
        )

        mock_config = Mock()
        mock_config.OUTLINE_REVISION_MODEL = "test_model"

        mock_prompts = Mock()
        mock_prompts.REVISE_OUTLINE_PROMPT.format.return_value = "Revision prompt"

        # Act
        result_outline, result_history = ReviseOutline(
            mock_iface,
            mock_logger(),
            "Original outline",
            "Good story, but needs more details",
            mock_config,
            mock_prompts
        )

        # Assert: SafeGeneratePydantic was called, not SafeGenerateText
        mock_iface.SafeGeneratePydantic.assert_called_once()

        # Verify result is the OutlineOutput text
        assert isinstance(result_outline, str)
        assert "Revised Story Title" in result_outline

    def test_generate_outline_with_structured_setting(self, mock_interface, mock_logger, mocker):
        """Integration test: Verify GenerateOutline handles structured dict setting correctly"""
        from Writer.OutlineGenerator import GenerateOutline

        # Arrange: Create OutlineOutput with structured setting to verify it validates properly
        from Writer.Models import OutlineOutput

        # This should validate successfully with dict setting after our GREEN fix
        outline_with_structured_setting = OutlineOutput(
            title="Story with Structured Setting",
            genre="Fantasy Adventure",
            chapters=[
                "Chapter 1: The hero begins their journey in a mystical land",
                "Chapter 2: Challenges arise in the enchanted forest"
            ],
            character_list=["Hero", "Mentor"],
            setting={
                "time": "Medieval fantasy era",
                "location": "Enchanted kingdom with magical creatures",
                "culture": "Feudal society with wizards and knights",
                "mood": "Mysterious and adventurous"
            },
            target_chapter_count=5
        )

        # Assert: The structured setting is properly validated and stored
        assert isinstance(outline_with_structured_setting.setting, dict)
        assert outline_with_structured_setting.setting["time"] == "Medieval fantasy era"
        assert outline_with_structured_setting.setting["location"] == "Enchanted kingdom with magical creatures"
        assert outline_with_structured_setting.setting["culture"] == "Feudal society with wizards and knights"
        assert outline_with_structured_setting.setting["mood"] == "Mysterious and adventurous"

        # Arrange: Mock the full GenerateOutline process
        mock_iface = mock_interface()

        # Create proper mocks for BaseContext and StoryElements
        from Writer.Models import BaseContext, StoryElements

        mock_base_context = BaseContext(context="Important context extracted")
        mock_story_elements = StoryElements(
            title="Fantasy Adventure",
            genre="Fantasy",
            characters={
                "Hero": [{"name": "Hero", "description": "Main protagonist"}],
                "Mentor": [{"name": "Mentor", "description": "Guide character"}]
            },
            settings={},
            themes=["Courage", "Good vs Evil"],
            conflict="Hero faces challenges",
            resolution="Hero succeeds"
        )

        # Set up the mock to return our structured objects in sequence
        mock_iface.SafeGeneratePydantic.side_effect = [
            ([{"role": "assistant", "content": "Base context extracted"}], mock_base_context, {"tokens": 50}),
            ([{"role": "assistant", "content": "Story elements generated"}], mock_story_elements, {"tokens": 100}),
            ([{"role": "assistant", "content": "Outline generated"}], outline_with_structured_setting, {"tokens": 150}),
            ([{"role": "assistant", "content": "Outline revised"}], outline_with_structured_setting, {"tokens": 100})
        ]

        # Mock LLMEditor methods
        mock_llm_editor = mocker.patch('Writer.LLMEditor')
        mock_llm_editor.GetFeedbackOnOutline.return_value = "Good outline with structured setting"
        mock_llm_editor.GetOutlineRating.return_value = True

        # Mock Config attributes
        mocker.patch('Writer.Config.INITIAL_OUTLINE_WRITER_MODEL', "test_model")
        mocker.patch('Writer.Config.OUTLINE_MAX_REVISIONS', 1)
        mocker.patch('Writer.Config.OUTLINE_MIN_REVISIONS', 1)

        # Act: Generate outline
        final_outline, story_elements_obj, outline_text, base_context = GenerateOutline(
            mock_iface,
            mock_logger(),
            "Create a fantasy story with detailed setting",
            "Fantasy"
        )

        # Assert: Generation succeeded without validation errors
        assert final_outline is not None
        assert isinstance(final_outline, str)
        assert "Story with Structured Setting" in final_outline

        # Verify SafeGeneratePydantic was called 4 times, accepting our structured setting
        assert mock_iface.SafeGeneratePydantic.call_count == 4


class TestBaseContextModel:
    """Test BaseContext Pydantic model when created"""

    def test_base_context_model_extracts_context_field(self):
        """Verify BaseContext model properly stores and validates context"""
        from Writer.Models import BaseContext

        # This will fail until we create BaseContext model
        context = BaseContext(context="This is important context from the prompt")

        assert context.context == "This is important context from the prompt"
        assert len(context.context) > 10  # Ensure it's substantial