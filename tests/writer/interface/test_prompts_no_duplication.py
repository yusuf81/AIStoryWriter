"""Test prompts have NO hardcoded format instructions (prevents duplication).

SafeGeneratePydantic automatically appends format instructions from
_build_format_instruction(). Prompts must NOT include their own format
instructions, otherwise they get sent twice (duplication bug).
"""
import pytest


class TestPromptsNoDuplication:
    """Ensure prompts don't duplicate SafeGeneratePydantic's format instructions."""

    def test_generate_story_elements_no_format_english(self, english_language_config):
        """GENERATE_STORY_ELEMENTS has no hardcoded format instruction (EN)."""
        from Writer import Prompts

        prompt = Prompts.GENERATE_STORY_ELEMENTS

        # Assert NO format instruction artifacts
        assert '=== JSON SCHEMA' not in prompt
        assert 'Required fields:' not in prompt
        assert 'Example format:' not in prompt

        # Verify it's still valid
        assert 'story elements' in prompt.lower() or 'elements' in prompt.lower()
        assert '{_OutlinePrompt}' in prompt or 'PROMPT' in prompt

    def test_generate_story_elements_no_format_indonesian(self, indonesian_language_config):
        """GENERATE_STORY_ELEMENTS has no hardcoded format instruction (ID)."""
        from Writer import Prompts_id

        prompt = Prompts_id.GENERATE_STORY_ELEMENTS

        assert '=== SKEMA JSON' not in prompt
        assert 'Field wajib:' not in prompt
        assert 'Format contoh:' not in prompt
        assert 'elemen cerita' in prompt.lower() or 'story elements' in prompt.lower() or 'elements' in prompt.lower()

    def test_initial_outline_no_format_english(self, english_language_config):
        """INITIAL_OUTLINE_PROMPT has no hardcoded format instruction."""
        from Writer import Prompts

        prompt = Prompts.INITIAL_OUTLINE_PROMPT

        assert '=== JSON SCHEMA' not in prompt
        assert 'JSON OUTPUT FORMAT' not in prompt
        assert 'outline' in prompt.lower()

    def test_chapter_generation_no_format_english(self, english_language_config):
        """CHAPTER_GENERATION_PROMPT has no hardcoded format instruction."""
        from Writer import Prompts

        prompt = Prompts.CHAPTER_GENERATION_PROMPT

        assert 'JSON OUTPUT FORMAT' not in prompt
        assert 'chapter' in prompt.lower()

    def test_chapter_outline_no_format_english(self, english_language_config):
        """CHAPTER_OUTLINE_PROMPT has no hardcoded format instruction."""
        from Writer import Prompts

        prompt = Prompts.CHAPTER_OUTLINE_PROMPT

        assert 'JSON OUTPUT FORMAT' not in prompt
        assert 'outline' in prompt.lower()
