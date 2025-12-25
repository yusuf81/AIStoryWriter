#!/usr/bin/env python3
"""
TDD tests for expanded StoryElements Pydantic model.
Tests that the enhanced model captures all fields requested by GENERATE_STORY_ELEMENTS prompt.
"""
from pydantic import ValidationError
from unittest.mock import patch, MagicMock
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestStoryElementsExpansion:
    """Test expanded StoryElements Pydantic model following London School TDD"""

    def test_expanded_story_elements_minimal(self, mock_logger):
        """Test creating expanded StoryElements with minimal required data"""
        # This should fail at first since we haven't expanded the model yet
        from Writer.Models import StoryElements, CharacterDetail

        elements_data = {
            "title": "Harta Karun Gua Naga",
            "genre": "Fantasy Adventure",
            "themes": ["friendship", "courage", "self-discovery"],
            "characters": {
                "Rian": [CharacterDetail(name="Rian", physical_description="Petualang berani yang mencari harta karun legendaris", personality=None, background=None, motivation=None)],
                "Bang Jaga": [CharacterDetail(name="Bang Jaga", physical_description="Naga kecil bijaksana yang menjaga gua mistis", personality=None, background=None, motivation=None)]
            }
        }

        story_elements = StoryElements(**elements_data)
        assert story_elements.title == "Harta Karun Gua Naga"
        assert story_elements.genre == "Fantasy Adventure"
        assert len(story_elements.themes) == 3
        assert "friendship" in story_elements.themes
        assert len(story_elements.characters) == 2

    def test_expanded_story_elements_full(self, mock_logger):
        """Test creating expanded StoryElements with all fields populated"""
        from Writer.Models import StoryElements, CharacterDetail

        elements_data = {
            "title": "Harta Karun Gua Naga",
            "genre": "Fantasy Adventure",
            "themes": ["friendship", "courage", "self-discovery", "responsibility"],
            "pacing": "Moderate with moments of tension",
            "style": "Descriptive with vivid imagery and character-focused narrative",
            "plot_structure": {
                "exposition": "Rian discovers mysterious cave and meets Bang Jaga",
                "rising_action": "Challenges test Rian's courage and intentions",
                "climax": "Rian proves worthiness and gains Bang Jaga's trust",
                "falling_action": "Friendship forms and treasure is shared",
                "resolution": "Rian leaves with wisdom and new companion"
            },
            "settings": {
                "Forbidden Forest": {
                    "time": "Present day",
                    "location": "Dense, ancient forest untouched by civilization",
                    "culture": "Mystical, magical atmosphere",
                    "mood": "Mysterious and adventurous"
                },
                "Dragon's Cave": {
                    "time": "Timeless",
                    "location": "Ancient cave hidden behind waterfall",
                    "culture": "Ancient, sacred space",
                    "mood": "Awe-inspiring and slightly dangerous"
                }
            },
            "conflict": "Rian must prove his pure intentions to gain Bang Jaga's trust and access to the treasure",
            "symbolism": [
                {"symbol": "The cave", "meaning": "Hidden wisdom and inner journey"},
                {"symbol": "The treasure", "meaning": "Not material wealth but friendship and knowledge"}
            ],
            "characters": {
                "Rian": [CharacterDetail(name="Rian", physical_description="Young adventurer driven by curiosity and courage", personality=None, background=None, motivation=None)],
                "Bang Jaga": [CharacterDetail(name="Bang Jaga", physical_description="Ancient dragon guardian, wise but initially wary", personality=None, background=None, motivation=None)]
            },
            "resolution": "True treasure is the friendship formed and lessons learned"
        }

        story_elements = StoryElements(**elements_data)
        assert story_elements.title == "Harta Karun Gua Naga"
        assert story_elements.pacing == "Moderate with moments of tension"
        assert len(story_elements.plot_structure or {}) == 5
        assert story_elements.plot_structure and "exposition" in story_elements.plot_structure
        assert len(story_elements.settings) == 2
        assert "Forbidden Forest" in story_elements.settings
        assert len(story_elements.symbolism or []) == 2
        assert story_elements.resolution is not None

    def test_model_validation_boundaries(self, mock_logger):
        """Test that validation errors are raised for boundary conditions"""
        from Writer.Models import StoryElements, CharacterDetail

        # Test title too short
        with pytest.raises(ValidationError) as exc_info:
            StoryElements(
                title="H1",  # Too short (min 5)
                genre="Fantasy",
                themes=["theme1"],
                characters={"Character": [CharacterDetail(name="Character", physical_description=None, personality=None, background=None, motivation=None)]},
                pacing=None,
                style=None,
                plot_structure=None,
                conflict=None,
                symbolism=None,
                resolution=None
            )
        assert "at least 5 characters" in str(exc_info.value)

        # Test title too long
        with pytest.raises(ValidationError) as exc_info:
            StoryElements(
                title="A" * 201,  # Too long (max 200)
                genre="Fantasy",
                themes=["theme1"],
                characters={"Character": [CharacterDetail(name="Character", physical_description=None, personality=None, background=None, motivation=None)]},
                pacing=None,
                style=None,
                plot_structure=None,
                conflict=None,
                symbolism=None,
                resolution=None
            )
        assert "at most 200 characters" in str(exc_info.value)

        # Test empty themes
        with pytest.raises(ValidationError) as exc_info:
            StoryElements(
                title="Valid Title",
                genre="Fantasy",
                themes=[],  # Empty themes not allowed
                characters={"Character": [CharacterDetail(name="Character", physical_description=None, personality=None, background=None, motivation=None)]},
                pacing=None,
                style=None,
                plot_structure=None,
                conflict=None,
                symbolism=None,
                resolution=None
            )
        assert "at least 1 item" in str(exc_info.value)

    def test_integration_with_safe_generate_pydantic(self, mock_logger):
        """Test StoryElements integration with SafeGeneratePydantic"""
        from Writer.Models import StoryElements, CharacterDetail
        from Writer.Interface.Wrapper import Interface

        # Create mock interface
        interface = Interface(Models=[])

        # Mock SafeGeneratePydantic to return expanded StoryElements
        mock_elements = StoryElements(
            title="Test Story",
            genre="Test Genre",
            themes=["theme1", "theme2"],
            characters={"Hero": [CharacterDetail(name="Hero", physical_description="Brave protagonist", personality=None, background=None, motivation=None)]},
            conflict="Hero must overcome obstacles",
            pacing=None,
            style=None,
            plot_structure=None,
            symbolism=None,
            resolution=None
        )

        with patch.object(interface, 'SafeGeneratePydantic') as mock_generate:
            mock_generate.return_value = (
                [{"role": "user", "content": "test"}],
                mock_elements,
                {'prompt_tokens': 100, 'completion_tokens': 200}
            )

            # Simulate the call from GenerateMainStoryElements
            messages, result, tokens = interface.SafeGeneratePydantic(  # type: ignore[misc]
                MagicMock(name='mock_logger'),
                [{"role": "user", "content": "test"}],
                "test_model",
                StoryElements
            )

            assert isinstance(result, StoryElements)
            assert result.title == "Test Story"
            assert result.genre == "Test Genre"

    def test_enhanced_story_elements_with_settings(self, mock_logger):
        """Test enhanced StoryElements with settings field containing location details"""
        from Writer.Models import StoryElements, CharacterDetail

        # Test with enhanced data using settings field instead of locations
        enhanced_data = {
            "title": "Harta Karun Naga Penjaga",
            "genre": "Fantasy Petualangan",
            "characters": {
                "Rian": [CharacterDetail(name="Rian", physical_description="Petualang berani", personality=None, background=None, motivation=None)],
                "Bang Jaga": [CharacterDetail(name="Bang Jaga", physical_description="Naga penjaga", personality=None, background=None, motivation=None)]
            },
            "settings": {
                "Gua Naga": {
                    "time": "Present day",
                    "location": "Gua mistis yang penuh harta karun",
                    "culture": "Magical, ancient",
                    "mood": "Mysterious and adventurous"
                }
            },
            "themes": ["petualangan", "persahabatan"],
            "conflict": "Harus membuktikan diri layak"
        }

        # This should work with the enhanced model structure
        story_elements = StoryElements(**enhanced_data)
        assert story_elements.title == "Harta Karun Naga Penjaga"
        assert story_elements.genre == "Fantasy Petualangan"
        assert len(story_elements.characters) == 2
        assert "Gua Naga" in story_elements.settings
        assert story_elements.settings["Gua Naga"]["location"] == "Gua mistis yang penuh harta karun"
        assert "petualangan" in story_elements.themes
        assert story_elements.conflict == "Harus membuktikan diri layak"

    def test_new_required_fields_enforced(self, mock_logger):
        """Test that new required fields are properly enforced"""
        from Writer.Models import StoryElements, CharacterDetail

        # Should fail without required new fields
        with pytest.raises(ValidationError) as exc_info:
            StoryElements(  # type: ignore[arg-type]  # Intentionally missing title, genre to test required fields
                # Missing title, genre - new required fields
                characters={"Character": [CharacterDetail(name="Character", physical_description=None, personality=None, background=None, motivation=None)]},
                themes=["theme1"],
                pacing=None,
                style=None,
                plot_structure=None,
                conflict=None,
                symbolism=None,
                resolution=None
            )
        error_msg = str(exc_info.value)
        assert "title" in error_msg or "genre" in error_msg

    def test_optional_fields_can_be_none(self, mock_logger):
        """Test that optional fields can be None (backwards compatibility)"""
        from Writer.Models import StoryElements, CharacterDetail

        elements_data = {
            "title": "Valid Title",
            "genre": "Fantasy",
            "themes": ["theme1"],
            "characters": {"Character": [CharacterDetail(name="Character", physical_description="Description", personality=None, background=None, motivation=None)]}
            # All optional fields omitted - should work
        }

        story_elements = StoryElements(**elements_data)
        assert story_elements.title == "Valid Title"
        assert story_elements.pacing is None  # Optional field should be None
        assert story_elements.style is None
        assert story_elements.plot_structure is None
        assert story_elements.conflict is None
        assert story_elements.symbolism is None
        assert story_elements.resolution is None
