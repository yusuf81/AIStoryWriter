"""
Tests for CHAPTER_GENERATION_PROMPT (Phase 6 update).

Phase 6: Format instructions removed from prompts because SafeGeneratePydantic
automatically adds them via _build_format_instruction().

This prevents duplication and ensures language-aware format instructions.
"""


class TestChapterExtractionPromptFormat:
    """Test that CHAPTER_GENERATION_PROMPT has NO hardcoded format instructions."""

    def test_english_prompt_has_json_format_section(self):
        """Test that English prompt has NO hardcoded format instructions"""
        # Arrange
        import Writer.Prompts as Prompts

        # Act
        prompt = Prompts.CHAPTER_GENERATION_PROMPT

        # Assert - Should NOT have format instructions (added by SafeGeneratePydantic)
        assert 'JSON OUTPUT FORMAT' not in prompt, "Format instructions should not be hardcoded"
        assert '{{' not in prompt or 'Example format:' not in prompt, "Should not have JSON examples"
        # Should still have core task
        assert 'extract' in prompt.lower() or 'chapter' in prompt.lower(), "Prompt should describe task"

    def test_indonesian_prompt_has_json_format_section(self):
        """Test that Indonesian prompt has NO hardcoded format instructions"""
        # Arrange
        import Writer.Prompts_id as Prompts_id

        # Act
        prompt = Prompts_id.CHAPTER_GENERATION_PROMPT

        # Assert - Should NOT have format instructions (added by SafeGeneratePydantic)
        assert 'FORMAT JSON' not in prompt, "Format instructions should not be hardcoded"
        assert '{{' not in prompt or 'Format contoh:' not in prompt, "Should not have JSON examples"
        # Should still have core task
        assert 'ekstrak' in prompt.lower() or 'bab' in prompt.lower(), "Prompt should describe task"


class TestChapterExtractionGeneration:
    """Test that chapter extraction uses SafeGeneratePydantic correctly."""

    def test_chapter_extraction_uses_pydantic_model(self, mock_interface, mock_logger):
        """Test that SafeGeneratePydantic is called with ChapterOutput model"""
        # Arrange
        from Writer.Chapter.ChapterGenerator import GenerateChapter
        from Writer.Models import ChapterOutput

        mock_int = mock_interface()
        mock_log = mock_logger()

        # Create valid ChapterOutput for extraction
        extracted_outline = ChapterOutput(
            text="Chapter 1 outline: Hero begins epic journey in the bustling village market, meets wise mentor under ancient oak tree, receives mysterious quest to find legendary artifact hidden in distant mountains across dangerous wilderness",
            word_count=30,
            chapter_number=1,
            chapter_title="The Beginning"
        )

        # Mock SafeGeneratePydantic for chapter extraction (first call in GenerateChapter)
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant'}],
            extracted_outline,
            {'prompt_tokens': 100}
        )

        # Mock SafeGenerateJSON for chapter summary (to avoid needing full mock chain)
        mock_int.SafeGenerateJSON.return_value = (
            [{'role': 'assistant'}],
            {'summary': 'Test summary', 'key_points': ['point 1'], 'setting': 'village'},
            {'prompt_tokens': 50}
        )

        # Act
        try:
            GenerateChapter(
                mock_int, mock_log, 1, 5,
                "Full outline text",
                _Chapters=[]
            )
        except (AttributeError, KeyError, IndexError):
            # Expected - we're only testing the first call, not the full generation
            pass

        # Assert - Verify ChapterOutput was used in first SafeGeneratePydantic call
        assert mock_int.SafeGeneratePydantic.called
        first_call_args = mock_int.SafeGeneratePydantic.call_args_list[0][0]
        assert first_call_args[3] == ChapterOutput

    def test_chapter_output_validates_required_fields(self):
        """Test that ChapterOutput model validates required fields"""
        # Arrange
        from Writer.Models import ChapterOutput
        import pytest

        # Act & Assert - Missing required fields should raise ValidationError
        with pytest.raises(Exception):  # Pydantic ValidationError
            ChapterOutput(  # type: ignore[call-arg]
                # Missing text, word_count, chapter_number
                chapter_title="Title Only"
            )

    def test_chapter_output_accepts_extraction_format(self):
        """Test that ChapterOutput accepts extraction-style content"""
        # Arrange
        from Writer.Models import ChapterOutput

        # Act - Create with extraction-style data (outline text, not full chapter)
        chapter = ChapterOutput(
            text="Chapter 3 outline: Hero discovers ancient temple hidden in forbidden forest, encounters mysterious guardian spirit protecting sacred artifacts, learns ancient prophecy about destiny and must make difficult choice about future path",
            word_count=30,
            chapter_number=3,
            chapter_title="The Discovery"
        )

        # Assert
        assert chapter.chapter_number == 3
        assert "ancient temple" in chapter.text
        assert chapter.word_count == 30

    def test_chapter_output_validates_text_length(self):
        """Test that ChapterOutput validates minimum text length"""
        # Arrange
        from Writer.Models import ChapterOutput
        import pytest

        # Act & Assert - Too short text should raise ValidationError
        with pytest.raises(Exception):  # Pydantic ValidationError
            ChapterOutput(  # type: ignore[call-arg]
                text="Short",  # Too short - needs 100+ chars
                word_count=1,
                chapter_number=1
            )
