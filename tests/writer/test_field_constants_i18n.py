"""
TDD tests for FieldConstants internationalization support.

Tests that FieldConstants handles both English and Indonesian section patterns.
Following TDD London School approach.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestFieldConstantsInternationalization:
    """TDD tests for internationalization support in FieldConstants"""

    def test_indonesian_metadata_section_detection(self):
        """Test that Indonesian metadata sections are detected correctly"""
        from Writer.FieldConstants import is_metadata_section, METADATA_SECTIONS

        # Test Indonesian metadata sections
        assert is_metadata_section("## Ringkasan"), "Should detect Indonesian 'Ringkasan'"
        assert is_metadata_section("## Ringkasan content"), "Should detect Ringkasan with content"
        assert is_metadata_section("## Label"), "Should detect Indonesian 'Label'"
        assert is_metadata_section("## Label: fantasi, petualangan"), "Should detect Label with content"

        # Verify the constants include Indonesian versions
        assert "## Ringkasan" in METADATA_SECTIONS, "METADATA_SECTIONS should include Indonesian Ringkasan"
        assert "## Label" in METADATA_SECTIONS, "METADATA_SECTIONS should include Indonesian Label"

        # Should still detect English sections
        assert is_metadata_section("## Summary"), "Should still detect English 'Summary'"
        assert is_metadata_section("## Tags"), "Should still detect English 'Tags'"

    def test_indonesian_whitespace_handling(self):
        """Test that Indonesian sections handle extra spaces properly"""
        from Writer.FieldConstants import is_metadata_section

        # Test Indonesian sections with extra spaces
        assert is_metadata_section("##   Ringkasan"), "Should handle extra spaces in Indonesian Ringkasan"
        assert is_metadata_section("##    Label"), "Should handle extra spaces in Indonesian Label"

    @pytest.mark.parametrize("ind_section", [
        "## Ringkasan",
        "## Ringkasan content here",
        "## Label",
        "## Label: genre tags",
        "##   Ringkasan",  # Extra spaces
        "##    Label content",  # Extra spaces
    ])
    def test_indonesian_metadata_section_patterns(self, ind_section):
        """Test various Indonesian metadata section patterns"""
        from Writer.FieldConstants import is_metadata_section

        assert is_metadata_section(ind_section), f"Should detect Indonesian section: '{ind_section}'"

    @pytest.mark.parametrize("outline_line,expected", [
        ("# Story Outline", True),       # English pattern should work
        ("# Ringkasan Cerita", False),   # Indonesian doesn't use this format
        ("# Outline Cerita", False),     # Indonesian doesn't use this format
        ("# Garis Besar", False),        # Indonesian doesn't use this format
        ("# Summary", False),           # Summary is metadata, not outline
        ("# Label", False),             # Label is metadata, not outline
    ])
    def test_story_outline_detection_i18n(self, outline_line, expected):
        """Test story outline section detection with internationalization"""
        from Writer.FieldConstants import is_story_outline_section

        result = is_story_outline_section(outline_line)

        if expected:
            assert result, f"Should detect story outline: '{outline_line}'"
        else:
            assert not result, f"Should not detect as story outline: '{outline_line}'"

    def test_mixed_language_compatibility(self):
        """Test that mixed English/Indonesian content works correctly"""
        from Writer.FieldConstants import is_metadata_section

        # Content with mixed sections - should detect both
        english_line = "## Summary"
        indonesian_line = "## Ringkasan"
        tag_line = "## Tags"
        label_line = "## Label"

        assert is_metadata_section(english_line), "English summary should be detected"
        assert is_metadata_section(indonesian_line), "Indonesian ringkasan should be detected"
        assert is_metadata_section(tag_line), "English tags should be detected"
        assert is_metadata_section(label_line), "Indonesian label should be detected"

    def test_pdf_generator_i18n_compatibility(self):
        """Test that PDFGenerator can handle Indonesian sections"""
        from Writer.FieldConstants import METADATA_SECTIONS

        # Verify METADATA_SECTIONS includes both languages
        expected_sections = ["## Summary", "## Tags", "## Ringkasan", "## Label"]

        for section in expected_sections:
            assert section in METADATA_SECTIONS, f"METADATA_SECTIONS should include {section}"

        # Verify we have both English and Indonesian
        assert "## Summary" in METADATA_SECTIONS, "Should include English Summary"
        assert "## Ringkasan" in METADATA_SECTIONS, "Should include Indonesian Ringkasan"
        assert "## Tags" in METADATA_SECTIONS, "Should include English Tags"
        assert "## Label" in METADATA_SECTIONS, "Should include Indonesian Label"

    def test_constants_documentation(self):
        """Test that constants are properly documented with i18n support"""
        from Writer.FieldConstants import METADATA_SECTIONS

        # Should have 4 sections total (2 English + 2 Indonesian)
        assert len(METADATA_SECTIONS) >= 4, "Should have at least 4 metadata sections"

        # Should contain both language variants
        eng_sections = [s for s in METADATA_SECTIONS if s.startswith("## ") and
                        any(word in s.lower() for word in ["summary", "tags"])]
        ind_sections = [s for s in METADATA_SECTIONS if s.startswith("## ") and
                        any(word in s.lower() for word in ["ringkasan", "label"])]

        assert len(eng_sections) >= 2, "Should have at least English sections"
        assert len(ind_sections) >= 2, "Should have at least Indonesian sections"
