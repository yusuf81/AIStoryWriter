"""
Tests for JSON repair with extra keys merge in SafeGeneratePydantic.

TDD London School: Tests written first (RED phase) to document expected behavior.

Problem: When LLM produces JSON with unescaped quotes, json_repair.loads()
parses it as valid JSON but with incorrect keys. Example:

Input from LLM:
{"text": "...pekat... "Jangan pernah menyerah," gumamnya... hadapannya..."}

Parsed by json_repair (incorrect semantics):
{
    "text": "...pekat...",
    "Jangan pernah menyerah,": "gumamnya...",
    "hadapannya": "..."
}

Expected behavior: Merge extra keys back into the 'text' field using Pydantic schema.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TestJSONRepairExtraKeysMerge:
    """
    Test schema-aware JSON repair that merges extra keys back to text field.
    """

    @pytest.fixture
    def mock_logger(self):
        """Factory for creating mock Logger"""
        logger = MagicMock(name='mock_logger')
        logger.Log = MagicMock()
        return logger

    def test_extra_keys_merged_into_text_field(self, mock_logger):
        """
        RED: Test fails because SafeGeneratePydantic doesn't merge extra keys

        Expected: When JSONResponse has keys not in Pydantic schema,
        and schema has 'text' field, merge extra keys back into text.

        Scenario: Model produces broken JSON due to unescaped quotes
        {"text": "Kabut", "Jangan menyerah,": "gumam", "hadapannya": "tugas"}

        After merge, text should be:
        "Kabut \"Jangan menyerah,\" gumam hadapannya tugas"
        """
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])

        # Mock SafeGenerateJSON to return broken JSON (as parsed by json_repair)
        broken_json_response = {
            "text": "Kabut itu terasa begitu pekat",  # Truncated at unescaped quote
            "Jangan pernah menyerah,": "gumamnya pelan",  # Extra key from broken quote
            "hadapannya": "mencapai puncak gunung",  # Another extra key
            "chapter_number": 1,
            "chapter_title": "Pendakian"
        }

        with patch.object(interface, 'SafeGenerateJSON') as mock_json:
            mock_json.return_value = (
                [{"role": "user", "content": "test"}, {"role": "assistant", "content": "{}"}],
                broken_json_response,
                {"prompt_tokens": 100, "completion_tokens": 50}
            )

            # Call SafeGeneratePydantic
            messages, result, usage = interface.SafeGeneratePydantic(
                _Logger=mock_logger,
                _Messages=[{"role": "user", "content": "test"}],
                _Model="ollama://test",
                _PydanticModel=ChapterOutput,
                _SeedOverride=42
            )

            # The text field should contain merged content
            assert hasattr(result, 'text'), "Result should have text field"
            merged_text = result.text

            # Check that original text is preserved
            assert "Kabut itu terasa begitu pekat" in merged_text, \
                f"Original text should be in merged result, got: {merged_text[:100]}"

            # Check that extra keys are merged back
            assert "Jangan pernah menyerah" in merged_text, \
                f"Extra key 'Jangan pernah menyerah' should be merged into text, got: {merged_text[:100]}"
            assert "gumamnya pelan" in merged_text, \
                f"Extra value 'gumamnya pelan' should be in merged text, got: {merged_text[:100]}"

    def test_no_merge_when_no_extra_keys(self, mock_logger):
        """
        RED: Test that normal JSON (no extra keys) is not modified

        Expected: When JSONResponse only has expected schema keys,
        no merging should occur.
        """
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])

        # Normal JSON response with all expected keys
        normal_json_response = {
            "text": "A" * 150,  # Valid text (min 100 chars)
            "chapter_number": 1,
            "chapter_title": "Chapter One"
        }

        with patch.object(interface, 'SafeGenerateJSON') as mock_json:
            mock_json.return_value = (
                [{"role": "user", "content": "test"}, {"role": "assistant", "content": "{}"}],
                normal_json_response,
                {"prompt_tokens": 100, "completion_tokens": 50}
            )

            messages, result, usage = interface.SafeGeneratePydantic(
                _Logger=mock_logger,
                _Messages=[{"role": "user", "content": "test"}],
                _Model="ollama://test",
                _PydanticModel=ChapterOutput,
                _SeedOverride=42
            )

            # Text should be exactly as provided (no modifications)
            assert result.text == "A" * 150, \
                f"Text should not be modified when no extra keys, got: {result.text[:50]}"

    def test_no_merge_when_no_text_field_in_schema(self, mock_logger):
        """
        RED: Test that merge only happens when Pydantic schema has 'text' field

        Expected: For schemas without 'text' field, extra keys are ignored
        (Pydantic default behavior) and no merge attempt is made.
        """
        from Writer.Interface.Wrapper import Interface
        from pydantic import BaseModel

        # Create a Pydantic model WITHOUT 'text' field
        class NoTextModel(BaseModel):
            name: str
            value: int

        interface = Interface(Models=[])

        # JSON with extra keys but no 'text' field to merge into
        json_response = {
            "name": "test",
            "value": 42,
            "extra_key": "will be ignored by Pydantic"
        }

        with patch.object(interface, 'SafeGenerateJSON') as mock_json:
            mock_json.return_value = (
                [{"role": "user", "content": "test"}, {"role": "assistant", "content": "{}"}],
                json_response,
                {"prompt_tokens": 100, "completion_tokens": 50}
            )

            # Should succeed - Pydantic ignores extra keys by default
            messages, result, usage = interface.SafeGeneratePydantic(
                _Logger=mock_logger,
                _Messages=[{"role": "user", "content": "test"}],
                _Model="ollama://test",
                _PydanticModel=NoTextModel,
                _SeedOverride=42
            )

            # Verify result has expected fields
            assert result.name == "test"
            assert result.value == 42
            # Verify extra_key is NOT in result (not merged anywhere)
            assert not hasattr(result, 'extra_key')

    def test_merged_text_meets_minimum_length(self, mock_logger):
        """
        RED: Test that merged text satisfies min_length constraint

        Expected: After merging extra keys, the text field should be long enough
        to pass Pydantic validation (min_length=100 for ChapterOutput).
        """
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        interface = Interface(Models=[])

        # Broken JSON where original text is too short, but merged would be long enough
        broken_json_response = {
            "text": "Kabut itu terasa begitu pekat",  # Only 29 chars
            "Jangan pernah menyerah,": "gumamnya pelan kalimat terakhir yang ia dengar",
            "hadapannya": "mencapai puncak gunung ini dan mendapatkan kembali",
            "chapter_number": 1,
            "chapter_title": "Pendakian"
        }

        with patch.object(interface, 'SafeGenerateJSON') as mock_json:
            mock_json.return_value = (
                [{"role": "user", "content": "test"}, {"role": "assistant", "content": "{}"}],
                broken_json_response,
                {"prompt_tokens": 100, "completion_tokens": 50}
            )

            messages, result, usage = interface.SafeGeneratePydantic(
                _Logger=mock_logger,
                _Messages=[{"role": "user", "content": "test"}],
                _Model="ollama://test",
                _PydanticModel=ChapterOutput,
                _SeedOverride=42
            )

            # Merged text should be >= 100 chars (ChapterOutput min_length)
            assert len(result.text) >= 100, \
                f"Merged text should be >= 100 chars, got {len(result.text)}"
