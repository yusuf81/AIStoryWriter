"""
TDD tests for PDFGenerator.py fragile pattern detection.

These tests verify that PDFGenerator now uses robust FieldConstants
instead of fragile string patterns.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestPDFGeneratorFragilePatterns:
    """TDD tests to verify PDFGenerator uses FieldConstants correctly"""

    def test_pdf_generator_uses_hardcoded_summary_pattern(self):
        """Test that PDFGenerator correctly processes Summary sections"""
        from Writer.PDFGenerator import extract_story_content

        content = """
# Test Story

## Summary
This is summary content

## Tags
fantasy, sci-fi

---
Chapter content
"""

        result = extract_story_content(content)
        # Should filter out summary and tags
        assert "## Summary" not in result, "Should filter Summary"
        assert "This is summary content" not in result

    def test_pdf_generator_uses_hardcoded_tags_pattern(self):
        """Test that PDFGenerator correctly processes Tags sections"""
        from Writer.PDFGenerator import extract_story_content

        content = """
# Test Story

## Tags
fantasy, sci-fi

---
Chapter content
"""

        result = extract_story_content(content)
        # Should filter out tags
        assert "## Tags" not in result, "Should filter Tags"
        assert "fantasy, sci-fi" not in result

    def test_pdf_generator_uses_hardcoded_story_outline_pattern(self):
        """Test that PDFGenerator correctly includes Story Outline sections"""
        from Writer.PDFGenerator import extract_story_content

        content = """
# Test Story

# Story Outline
Outline content here

---
Chapter content
"""

        result = extract_story_content(content)
        # Should include story outline
        assert "# Story Outline" in result, "Should include Story Outline"
        assert "Outline content here" in result

    def test_pdf_generator_uses_hardcoded_generation_statistics_pattern(self):
        """Test that PDFGenerator correctly includes Generation Statistics sections"""
        from Writer.PDFGenerator import extract_story_content

        content = """
# Test Story

# Generation Statistics
Words: 5000

---
Chapter content
"""

        result = extract_story_content(content)
        # Should include generation statistics
        assert "# Generation Statistics" in result, "Should include Generation Statistics"
        assert "Words: 5000" in result

    def test_field_constants_are_available_for_pdf_generation(self):
        """Test that FieldConstants functions are properly available for PDF generation"""
        from Writer.FieldConstants import (
            is_metadata_section,
            is_story_outline_section,
            is_generation_statistics_section
        )

        # Test that functions are callable and work correctly
        assert callable(is_metadata_section), "is_metadata_section should be callable"
        assert callable(is_story_outline_section), "is_story_outline_section should be callable"
        assert callable(is_generation_statistics_section), "is_generation_statistics_section should be callable"

        # Test basic functionality
        assert is_metadata_section("## Summary"), "Should detect Summary"
        assert is_metadata_section("## Tags"), "Should detect Tags"
        assert is_story_outline_section("# Story Outline"), "Should detect Story Outline"
        assert is_generation_statistics_section("# Generation Statistics"), "Should detect Generation Statistics"

    def test_current_robust_pattern_implementation(self):
        """Test that current implementation now handles extra spaces correctly"""
        from Writer.PDFGenerator import extract_story_content

        # Test content with extra spaces - should now be handled correctly
        content_with_extra_spaces = """# Test Story

##   Summary   # Extra spaces
Summary with spaces

##  Tags    # Extra spaces
Tags with spaces

---
Content
"""

        result = extract_story_content(content_with_extra_spaces)

        # Robust implementation should now handle extra spaces
        assert "##  Summary" not in result, "Should handle extra spaces properly"
        assert "Summary with spaces" not in result, "Should filter content with extra spaces"
        assert "##  Tags" not in result, "Should handle extra spaces properly"
        assert "Tags with spaces" not in result, "Should filter content with extra spaces"
