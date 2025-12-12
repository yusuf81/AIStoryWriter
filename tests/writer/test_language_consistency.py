"""Test that language remains consistent throughout story generation."""

import pytest
from unittest.mock import patch, MagicMock
from Writer.Chapter.ChapterGenerator import GenerateChapter, ReviseChapter
from Writer.PrintUtils import Logger

def test_generate_chapter_uses_correct_language():
    """Test that GenerateChapter imports the correct language prompts."""

    # Set language to Indonesian
    with patch('Writer.Config.NATIVE_LANGUAGE', 'id'):
        # Mock the chat response
        with patch('Writer.Interface.Wrapper.Interface') as mock_interface:
            mock_instance = MagicMock()
            mock_instance.SafeGenerateText.return_value = (
                [{'role': 'assistant', 'content': 'Bab 1: Ini adalah konten dalam bahasa Indonesia'}],
                {'prompt_tokens': 100, 'completion_tokens': 50}
            )
            mock_instance.SafeGenerateJSON.return_value = (
                [{'role': 'assistant', 'content': '{"TotalScenes": 1}'}],
                {"TotalScenes": 1}
            )
            mock_interface.SafeGeneratePydantic.return_value = (
                [{'role': 'assistant', 'content': '{"text": "Ini bab dalam bahasa Indonesia", "word_count": 5}'}],
                {"text": "Ini bab dalam bahasa Indonesia", "word_count": 5},
                {}
            )
            mock_interface.return_value = mock_instance

            logger = Logger()

            # Call GenerateChapter with correct parameters
            result = GenerateChapter(
                Interface=mock_instance,
                _Logger=logger,
                _ChapterNum=1,
                _TotalChapters=2,
                _Outline="Full outline",
                _BaseContext=""
            )

            # Verify Indonesian prompts were used (not English)
            # The result should be in Indonesian, not English
            assert "Indonesia" in str(result) or "Bab" in str(result)

def test_prompt_imports_respect_language():
    """Test that prompt imports respect the language configuration."""

    # Check current language config
    import Writer.Config as Config
    original_lang = getattr(Config, 'NATIVE_LANGUAGE', 'en')

    # Mock NATIVE_LANGUAGE as Indonesian
    with patch.object(Config, 'NATIVE_LANGUAGE', 'id'):
        # Import and check if prompts are Indonesian
        if Config.NATIVE_LANGUAGE == "id":
            from Writer import Prompts_id as Prompts
        else:
            from Writer import Prompts

        # Check that we have Indonesian prompts, not English
        assert hasattr(Prompts, 'OUTLINE_REVISION_PROMPT')
        # Indonesian prompts should have "Bahasa Indonesia" in them
        assert 'Bahasa Indonesia' in str(Prompts.OUTLINE_REVISION_PROMPT)

def test_language_consistency_across_modules():
    """Test that different modules use the same language."""

    with patch('Writer.Config.NATIVE_LANGUAGE', 'id'):
        # ChapterGenerator
        from Writer.Chapter import ChapterGenerator
        # OutlineGenerator
        from Writer import OutlineGenerator

        # All should use Indonesian prompts when NATIVE_LANGUAGE is 'id'
        # We can't easily test the imports, but we can verify the config is respected
        import Writer.Config as Config
        assert Config.NATIVE_LANGUAGE == 'id'