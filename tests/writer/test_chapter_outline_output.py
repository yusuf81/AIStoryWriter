#!/usr/bin/env python3
"""
TDD tests for ChapterOutlineOutput Pydantic model.
Tests that the new model correctly handles chapter outline data structure.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pydantic import ValidationError


class TestChapterOutlineOutput:
    """Test ChapterOutlineOutput Pydantic model following London School TDD"""

    def test_valid_chapter_outline_creation_minimal(self, mock_logger):
        """Test creating ChapterOutlineOutput with minimal valid data"""
        # This should fail at first since ChapterOutlineOutput doesn't exist yet
        from Writer.Models import ChapterOutlineOutput

        outline_data = {
            "chapter_number": 1,
            "chapter_title": "Bab 1: Pertemuan di Gua",
            "scenes": [
                "Rian menemukan gua misterius di hutan",
                "Pertemuan dengan Bang Jaga penjaga gua",
                "Bang Jaga menguji keberanian Rian"
            ],
            "characters_present": ["Rian", "Bang Jaga"],
            "outline_summary": "Rian bertemu naga penjaga gua dan menghadapi tantangan keberanian"
        }

        outline = ChapterOutlineOutput(**outline_data)
        assert outline.chapter_number == 1
        assert outline.chapter_title == "Bab 1: Pertemuan di Gua"
        assert len(outline.scenes) == 3
        assert set(outline.characters_present) == {"Rian", "Bang Jaga"}
        assert "naga penjaga gua" in outline.outline_summary

    def test_valid_chapter_outline_creation_full(self, mock_logger):
        """Test creating ChapterOutlineOutput with all fields populated"""
        from Writer.Models import ChapterOutlineOutput

        outline_data = {
            "chapter_number": 2,
            "chapter_title": "Chapter 2: The Dragon's Challenge",
            "scenes": [
                "Rian prepares for the first challenge",
                "Bang Jaga explains the rules of the trial",
                "Rian faces the test of courage in the dark cave",
                "Bang Jaga reveals the true purpose of the trials"
            ],
            "characters_present": ["Rian", "Bang Jaga"],
            "outline_summary": "Rian undergoes trials set by Bang Jaga to prove his worthiness",
            "estimated_word_count": 2500,
            "setting": "Inside the mystical dragon cave",
            "main_conflict": "Rian must prove his courage and intentions to Bang Jaga"
        }

        outline = ChapterOutlineOutput(**outline_data)
        assert outline.chapter_number == 2
        assert outline.estimated_word_count == 2500
        assert outline.setting == "Inside the mystical dragon cave"
        assert "prove his courage" in outline.main_conflict

    def test_validation_minimum_requirements(self, mock_logger):
        """Test that validation errors are raised for minimum requirements"""
        from Writer.Models import ChapterOutlineOutput

        # Test missing required fields
        with pytest.raises(ValidationError) as exc_info:
            ChapterOutlineOutput(chapter_number=1)  # Missing required fields

        # Test invalid chapter number
        with pytest.raises(ValidationError) as exc_info:
            ChapterOutlineOutput(
                chapter_number=0,  # Should be >= 1
                chapter_title="Test",
                scenes=["Scene 1"],
                characters_present=["Character"],
                outline_summary="Summary"
            )

        # Test too few scenes (min 1)
        with pytest.raises(ValidationError) as exc_info:
            ChapterOutlineOutput(
                chapter_number=1,
                chapter_title="Test",
                scenes=[],  # Too few
                characters_present=["Character"],
                outline_summary="Summary"
            )

        # Test invalid estimated word count
        with pytest.raises(ValidationError) as exc_info:
            ChapterOutlineOutput(
                chapter_number=1,
                chapter_title="Test",
                scenes=["Scene 1", "Scene 2"],
                characters_present=["Character"],
                outline_summary="Summary",
                estimated_word_count=0  # Should be > 0
            )

    def test_integration_with_safe_generate_pydantic(self, mock_logger):
        """Test ChapterOutlineOutput integration with SafeGeneratePydantic"""
        from Writer.Models import ChapterOutlineOutput
        from Writer.Interface.Wrapper import Interface

        # Create mock interface
        interface = Interface(Models=[])

        # Mock SafeGeneratePydantic to return ChapterOutlineOutput
        mock_outline = ChapterOutlineOutput(
            chapter_number=1,
            chapter_title="Bab 1: Pertemuan Pertama",
            scenes=[
                "Rian discovers ancient cave entrance hidden in forest",
                "First tense meeting with Bang Jaga the dragon guardian",
                "Bang Jaga explains the trials that await brave adventurers"
            ],
            characters_present=["Rian", "Bang Jaga"],
            outline_summary="Pertemuan awal yang menentukan antara petualang dan naga penjaga gua"
        )

        with patch.object(interface, 'SafeGeneratePydantic') as mock_generate:
            mock_generate.return_value = (
                [{"role": "user", "content": "test"}],
                mock_outline,
                {'prompt_tokens': 50, 'completion_tokens': 100}
            )

            # Simulate the call from GeneratePerChapterOutline
            messages, result, tokens = interface.SafeGeneratePydantic(
                mock_logger(),
                [{"role": "user", "content": "test"}],
                "test_model",
                ChapterOutlineOutput
            )

            assert isinstance(result, ChapterOutlineOutput)
            assert result.chapter_number == 1
            assert len(result.scenes) == 3

    def test_format_instruction_building(self, mock_logger):
        """Test that format instructions are built correctly for ChapterOutlineOutput"""
        from Writer.Models import ChapterOutlineOutput
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])
        schema = ChapterOutlineOutput.model_json_schema()
        instruction = interface._build_format_instruction(schema)

        # Should contain proper field descriptions
        assert "chapter_number (integer, Required)" in instruction
        assert "chapter_title (string, Required)" in instruction
        assert "scenes (array of objects, Required)" in instruction
        assert "outline_summary (string, Required)" in instruction

        # Should contain examples for arrays
        assert 'Example: ["String 1", "String 2"]' in instruction

        # Should not contain ChapterOutput specific fields
        assert "text (string" not in instruction
        assert "The full chapter text content" not in instruction
        assert "Total word count of the chapter" not in instruction

    def test_invalid_chapter_title_too_short(self, mock_logger):
        """Test validation when chapter title is too short"""
        from Writer.Models import ChapterOutlineOutput

        with pytest.raises(ValidationError) as exc_info:
            ChapterOutlineOutput(
                chapter_number=1,
                chapter_title="B1",  # Too short (min 5)
                scenes=["Scene 1", "Scene 2"],
                characters_present=["Character"],
                outline_summary="Valid summary with enough characters"
            )
        assert "at least 5 characters" in str(exc_info.value)

    def test_invalid_outline_summary_too_short(self, mock_logger):
        """Test validation when outline summary is too short"""
        from Writer.Models import ChapterOutlineOutput

        with pytest.raises(ValidationError) as exc_info:
            ChapterOutlineOutput(
                chapter_number=1,
                chapter_title="Valid Chapter Title",
                scenes=["Scene 1", "Scene 2"],
                characters_present=["Character"],
                outline_summary="Too short"  # Too short (min 20)
            )
        assert "at least 20 characters" in str(exc_info.value)