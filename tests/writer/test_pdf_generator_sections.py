"""
TDD tests for PDFGenerator.py fragile pattern refactoring.

Tests for replacing hardcoded string patterns with robust FieldConstants section detection.
Following TDD London School approach - tests written first (RED phase).
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestPDFGeneratorSectionDetection:
    """TDD tests for PDFGenerator section detection refactoring"""

    def test_extract_story_content_skips_metadata_sections(self):
        """Test that extract_story_content uses FieldConstants to skip metadata sections"""
        from Writer.PDFGenerator import extract_story_content
        from Writer.FieldConstants import is_metadata_section

        # Test content with metadata sections
        content = """---
frontmatter: here
---

# My Great Story

## Summary
This is a summary

## Tags
fantasy, adventure

---

## Chapter 1
Once upon a time...

## Chapter 2
The adventure continues...

"""

        result = extract_story_content(content)

        # Should include main title
        assert "# My Great Story" in result

        # Should include chapter content
        assert "## Chapter 1" in result
        assert "Once upon a time..." in result
        assert "## Chapter 2" in result
        assert "The adventure continues..." in result

        # Should NOT include metadata section headers
        assert "## Summary" not in result
        assert "This is a summary" not in result
        assert "## Tags" not in result
        assert "fantasy, adventure" not in result

        # Should include metadata separator
        assert "---" in result

    def test_extract_story_content_includes_story_outline(self):
        """Test that extract_story_content includes Story Outline section"""
        from Writer.PDFGenerator import extract_story_content
        from Writer.FieldConstants import is_story_outline_section

        content = """# My Story

# Story Outline
This is the story outline with plot points
and character development arcs.

---

## Chapter 1
The story begins...
"""

        result = extract_story_content(content)

        # Should include Story Outline section
        assert "# Story Outline" in result
        assert "This is the story outline" in result

    def test_extract_story_content_includes_generation_statistics(self):
        """Test that extract_story_content includes Generation Statistics section"""
        from Writer.PDFGenerator import extract_story_content
        from Writer.FieldConstants import is_generation_statistics_section

        content = """# My Story

# Generation Statistics
Words: 5000
Chapters: 3
Models: ollama://llama3

---

## Chapter 1
Content here...
"""

        result = extract_story_content(content)

        # Should include Generation Statistics section
        assert "# Generation Statistics" in result
        assert "Words: 5000" in result

    def test_generate_pdf_uses_field_constants_for_sections(self):
        """Test that GeneratePDF uses FieldConstants for section detection"""
        # This is an integration test - we'll test the internal functions
        # that should be refactored to use FieldConstants
        from Writer.FieldConstants import (
            is_story_outline_section,
            is_generation_statistics_section,
            is_metadata_section
        )

        # Test the section detection functions work correctly
        assert is_story_outline_section("# Story Outline")
        assert is_story_outline_section("# Story Outline content")
        assert not is_story_outline_section("# Chapter 1")

        assert is_generation_statistics_section("# Generation Statistics")
        assert is_generation_statistics_section("# Generation Statistics here")
        assert not is_generation_statistics_section("# Chapter 1")

        assert is_metadata_section("## Summary")
        assert is_metadata_section("## Tags")
        assert not is_metadata_section("## Chapter 1")

    def test_metadata_section_rejection_in_chapter_detection(self):
        """Test that metadata sections are not detected as chapters"""
        from Writer.FieldConstants import is_metadata_section

        # These should be detected as metadata, not chapters
        assert is_metadata_section("## Summary")
        assert is_metadata_section("## Summary content here")
        assert is_metadata_section("## Tags")
        assert is_metadata_section("## Tags: fantasy, sci-fi")

        # These should NOT be detected as metadata
        assert not is_metadata_section("## Chapter 1")
        assert not is_metadata_section("## Character Development")
        assert not is_metadata_section("## Plot Points")

    def test_whitespacing_handling_in_section_detection(self):
        """Test that section detection handles whitespace correctly"""
        from Writer.FieldConstants import (
            is_story_outline_section,
            is_generation_statistics_section,
            is_metadata_section
        )

        # Test extra spaces handling
        assert is_story_outline_section("#   Story Outline")
        assert is_generation_statistics_section("#    Generation Statistics")
        assert is_metadata_section("##   Summary")
        assert is_metadata_section("##    Tags")

        # Test that it still rejects incorrect sections
        assert not is_story_outline_section("#   Story Summary")
        assert not is_generation_statistics_section("#    Generation Data")

    @pytest.mark.parametrize("section_line", [
        "# Story Outline",
        "# Story Outline with content",
        "#   Story Outline",  # Extra spaces
        "#    Story Outline content",  # More spaces
    ])
    def test_story_outline_detection_patterns(self, section_line):
        """Test various Story Outline section patterns"""
        from Writer.FieldConstants import is_story_outline_section

        assert is_story_outline_section(section_line), f"Should detect '{section_line}' as Story Outline"

    @pytest.mark.parametrize("section_line", [
        "# Generation Statistics",
        "# Generation Statistics with data",
        "#   Generation Statistics",  # Extra spaces
        "#    Generation Statistics content",  # More spaces
    ])
    def test_generation_statistics_detection_patterns(self, section_line):
        """Test various Generation Statistics section patterns"""
        from Writer.FieldConstants import is_generation_statistics_section

        assert is_generation_statistics_section(section_line), f"Should detect '{section_line}' as Generation Statistics"

    @pytest.mark.parametrize("section_line", [
        "## Summary",
        "## Summary content",
        "##   Summary",  # Extra spaces
        "##    Summary content",  # More spaces
        "## Tags",
        "## Tags: fantasy",
        "##   Tags",  # Extra spaces
        "##    Tags content",  # More spaces
    ])
    def test_metadata_section_detection_patterns(self, section_line):
        """Test various metadata section patterns"""
        from Writer.FieldConstants import is_metadata_section

        assert is_metadata_section(section_line), f"Should detect '{section_line}' as metadata section"

    @pytest.mark.parametrize("non_section_line", [
        "# Chapter 1",
        "## Chapter 1",
        "# Character List",
        "## Settings",
        "Random text line",
        "",
        "# Outline",  # Missing "Story" prefix
        "## Tagline",  # Singular, not "Tags"
        "# Statistics Generation",  # Wrong word order
    ])
    def test_non_section_section_rejection(self, non_section_line):
        """Test that non-section lines are correctly rejected"""
        from Writer.FieldConstants import (
            is_story_outline_section,
            is_generation_statistics_section,
            is_metadata_section
        )

        # None of these should be detected as special sections
        assert not is_story_outline_section(non_section_line), f"Should not detect '{non_section_line}' as Story Outline"
        assert not is_generation_statistics_section(non_section_line), f"Should not detect '{non_section_line}' as Generation Statistics"
        assert not is_metadata_section(non_section_line), f"Should not detect '{non_section_line}' as metadata"

    def test_pdf_generator_import_compatibility(self):
        """Test that PDFGenerator can import and use FieldConstants"""
        from Writer.FieldConstants import (
            is_story_outline_section,
            is_generation_statistics_section,
            is_metadata_section,
            STORY_OUTLINE,
            GENERATION_STATISTICS,
            METADATA_SECTIONS
        )

        # Test that constants are available
        assert STORY_OUTLINE == "# Story Outline"
        assert GENERATION_STATISTICS == "# Generation Statistics"
        assert isinstance(METADATA_SECTIONS, list)
        assert "## Summary" in METADATA_SECTIONS
        assert "## Tags" in METADATA_SECTIONS

        # Test that functions work
        assert callable(is_story_outline_section)
        assert callable(is_generation_statistics_section)
        assert callable(is_metadata_section)