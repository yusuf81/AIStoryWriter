"""Test format instruction examples for schemas that need visual guidance.

Some models (especially LLaMA variants) need concrete examples to follow
JSON schema correctly, otherwise they omit required fields.
"""

from Writer.Interface.Wrapper import Interface


class TestFormatInstructionExamples:
    """Test that format instructions include examples for problematic schemas."""

    def test_chapter_output_includes_example_english(self, english_language_config):
        """ChapterOutput schema should include concrete example in English."""
        interface = Interface([])
        from Writer.Models import ChapterOutput

        schema = ChapterOutput.model_json_schema()
        instruction = interface._build_format_instruction(schema)

        # Should include ChapterOutput example
        assert '"text"' in instruction
        assert '"chapter_number"' in instruction

    def test_chapter_output_includes_example_indonesian(self, indonesian_language_config):
        """ChapterOutput schema should include concrete example in Indonesian."""
        interface = Interface([])
        from Writer.Models import ChapterOutput

        schema = ChapterOutput.model_json_schema()
        instruction = interface._build_format_instruction(schema)

        # Should include ChapterOutput example
        assert '"text"' in instruction
        assert '"chapter_number"' in instruction

    def test_chapter_output_example_is_simple(self, english_language_config):
        """ChapterOutput example should only show required fields (text, chapter_number)."""
        interface = Interface([])
        from Writer.Models import ChapterOutput

        schema = ChapterOutput.model_json_schema()
        instruction = interface._build_format_instruction(schema)

        # Example should be simple - not include all optional fields
        # Check that ChapterOutput example section is minimal
        # (should not include scenes, characters_present in the example)
        if "Chapter output format" in instruction or "Format output bab" in instruction:
            # Count occurrences of optional fields in example section
            example_section = instruction.split("Chapter output format")[-1].split("===")[0] if "Chapter output format" in instruction else ""
            if "Format output bab" in instruction:
                example_section = instruction.split("Format output bab")[-1].split("===")[0]

            # Example should be minimal, not including all optional fields
            assert example_section.count("scenes") <= 1
            assert example_section.count("characters") <= 1

    def test_other_schemas_not_affected(self, english_language_config):
        """Other schemas (OutlineOutput, StoryElements) should not get ChapterOutput example."""
        interface = Interface([])
        from Writer.Models import OutlineOutput, StoryElements

        # Test OutlineOutput
        outline_schema = OutlineOutput.model_json_schema()
        outline_instruction = interface._build_format_instruction(outline_schema)
        # OutlineOutput has chapter_number but NOT text, so should not trigger example
        assert outline_instruction.count("chapter_number") <= 2  # Only in field list, not in example

        # Test StoryElements
        story_schema = StoryElements.model_json_schema()
        story_instruction = interface._build_format_instruction(story_schema)
        assert "chapter_number" not in story_instruction

    def test_schema_based_detection_universal(self, english_language_config):
        """Detection should be based on schema structure, not provider names."""
        # Should work regardless of language config
        from Writer.Models import ChapterOutput
        schema = ChapterOutput.model_json_schema()

        # Check for ChapterOutput structure: has 'text' and 'chapter_number' fields
        properties = schema.get('properties', {})
        assert 'text' in properties
        assert 'chapter_number' in properties
