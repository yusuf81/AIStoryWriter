"""
TDD tests for PDFGenerator internationalization support.

Tests that PDFGenerator correctly handles both English and Indonesian sections.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestPDFGeneratorI18n:
    """TDD tests for PDFGenerator internationalization support"""

    def test_pdf_generator_handles_indonesian_metadata(self):
        """Test that PDFGenerator filters out Indonesian metadata sections"""
        from Writer.PDFGenerator import extract_story_content

        # Content with Indonesian metadata
        content = """---
frontmatter: data
---

# Cerita Saya

## Ringkasan
Ini adalah ringkasan cerita dalam bahasa Indonesia

## Label
fantasi, petualangan, legenda

---

## Bab 1: Awal Petualangan
Puluhan tahun yang lalu, di sebuah kerajaan yang jauh...
"""

        result = extract_story_content(content)

        # Should include main title
        assert "# Cerita Saya" in result

        # Should include chapter content
        assert "## Bab 1" in result
        assert "Awal Petualangan" in result
        assert "Puluhan tahun yang lalu" in result

        # Should NOT include Indonesian metadata sections or content
        assert "## Ringkasan" not in result
        assert "Ini adalah ringkasan cerita" not in result
        assert "## Label" not in result
        assert "fantasi, petualangan, legenda" not in result

        # Should include metadata separator
        assert "---" in result

    def test_pdf_generator_handles_mixed_metadata(self):
        """Test that PDFGenerator handles mixed English/Indonesian metadata"""
        from Writer.PDFGenerator import extract_story_content

        content = """# Mixed Story

## Summary
English summary

## Ringkasan
Ringkasan dalam bahasa Indonesia

## Tags
english, tag

## Label
label, indonesia

---
Chapter content
"""

        result = extract_story_content(content)

        # Should include title and chapter
        assert "# Mixed Story" in result
        assert "Chapter content" in result

        # Should NOT include any metadata (both languages)
        assert "## Summary" not in result
        assert "English summary" not in result
        assert "## Ringkasan" not in result
        assert "Ringkasan dalam bahasa Indonesia" not in result
        assert "## Tags" not in result
        assert "english, tag" not in result
        assert "## Label" not in result
        assert "label, indonesia" not in result

    def test_pdf_generator_indonesian_whitespace_tolerance(self):
        """Test that PDFGenerator handles extra spaces in Indonesian sections"""
        from Writer.PDFGenerator import extract_story_content

        content = """# Test Story

##   Ringkasan   # Extra spaces
Summary with spaces

##    Label    # Extra spaces
Tags with spaces

---
Content here
"""

        result = extract_story_content(content)

        # Should include title and content
        assert "# Test Story" in result
        assert "Content here" in result

        # Should NOT filter metadata with extra spaces (thanks to FieldConstants)
        assert "##   Ringkasan" not in result
        assert "Summary with spaces" not in result
        assert "##    Label" not in result
        assert "Tags with spaces" not in result

    def test_pdf_generator_mixed_content_processing(self):
        """Test complete mixed English/Indonesian content processing"""
        from Writer.PDFGenerator import extract_story_content

        mixed_content = """---
yaml: frontmatter
---

# The Legend of Mount Bromo

## Ringkasan
Sebuah legenda tentang Dewa Bromo dan Dewi Semuru

## Summary
An English summary of the same legend

## Label
legenda, mitologi, jawa

## Tags
legend, mythology, java

---

## Bab 1: Awal Mula
Di puncak Gunung Bromo yang agung...

## Chapter 2: The English Chapter
Meanwhile, in the English version...

# Story Outline
Story outline content that crosses languages

# Generation Statistics
Words: 1000
Chapters: 2
"""

        result = extract_story_content(mixed_content)

        # Should include main title
        assert "# The Legend of Mount Bromo" in result

        # Should include both language chapters
        assert "## Bab 1" in result
        assert "Awal Mula" in result
        assert "## Chapter 2" in result
        assert "The English Chapter" in result

        # Should include story outline and generation statistics (these are not metadata)
        assert "# Story Outline" in result
        assert "Story outline content" in result
        assert "# Generation Statistics" in result
        assert "Words: 1000" in result

        # Should filter ALL metadata sections (both languages)
        assert "## Ringkasan" not in result
        assert "Sebuah legenda" not in result
        assert "## Summary" not in result
        assert "An English summary" not in result
        assert "## Label" not in result
        assert "legenda, mitologi" not in result
        assert "## Tags" not in result
        assert "legend, mythology" not in result
