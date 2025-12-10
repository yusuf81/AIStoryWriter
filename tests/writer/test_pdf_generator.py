import pytest
from pytest_mock import MockerFixture
import sys
import os
import tempfile
import types
from unittest.mock import mock_open, patch

import Writer.Config
from Writer.PDFGenerator import GeneratePDF, extract_story_content


# Mock ActivePrompts for the Test Module
@pytest.fixture(autouse=True)
def mock_active_prompts_for_pdf_generator(mocker: MockerFixture):
    mock_prompts = types.ModuleType("Writer.Prompts")
    mocker.patch.dict(sys.modules, {"Writer.Prompts": mock_prompts})
    yield


class MockLogger:
    """Mock logger for testing"""
    def __init__(self):
        self.logs = []
        self.log_levels = []

    def Log(self, msg, lvl):
        self.logs.append(msg)
        self.log_levels.append(lvl)

    def SaveLangchain(self, s, m):
        pass


@pytest.fixture
def mock_logger():
    return MockLogger()


@pytest.fixture
def mock_interface():
    """Mock interface - not used in PDF generation but needed for signature"""
    import types
    mock = types.ModuleType("MockInterface")
    return mock


@pytest.fixture
def sample_markdown_content():
    """Sample markdown content with YAML and metadata"""
    return """---
title: "Test Story"
summary: "A test story for PDF generation"
tags: "test, pdf, story"
---
# The Great Adventure

## Summary
This is a summary section that should be excluded from PDF.

## Tags
test, pdf, story

---

## Chapter 1
Once upon a time, in a land far away, there lived a brave knight.

The knight ventured into the dark forest, searching for the legendary treasure.

### Finding the Map
After many days of searching, the knight found an ancient map hidden in an old tree.

The map showed the way to the hidden treasure deep within the mountain.

---

## Chapter 2
The knight followed the map through valleys and over mountains.

At last, the knight reached the entrance to the treasure cave.

### Facing the Dragon
Inside the cave, a fearsome dragon guarded the treasure.

The knight bravely faced the dragon and defeated it in combat.

With the dragon defeated, the knight claimed the treasure and returned home a hero.
---"""


class TestExtractStoryContent:
    """Test the extract_story_content function"""

    def test_extracts_title_and_chapters_only(self, sample_markdown_content):
        """Test that only title and chapters are extracted"""
        result = extract_story_content(sample_markdown_content)

        # Should contain title
        assert "# The Great Adventure" in result

        # Should contain chapters
        assert "## Chapter 1" in result
        assert "Once upon a time" in result
        assert "## Chapter 2" in result
        assert "The knight followed the map" in result

        # Should contain multiple story separators (OK to keep them)
        # It just shouldn't contain YAML front matter with title/key pairs
        assert 'title: "Test Story"' not in result
        assert 'summary: "A test story for PDF generation"' not in result

        # Should NOT contain metadata sections
        assert "## Summary" not in result
        assert "This is a summary section" not in result
        assert "## Tags" not in result
        assert "test, pdf, story" not in result

        # Should NOT contain technical sections
        assert "# Story Outline" not in result
        assert "# Generation Statistics" not in result

    def test_handles_content_without_yaml(self):
        """Test handling of markdown without YAML front matter"""
        content = """# Simple Story

## Chapter 1
A simple beginning.

## Chapter 2
The continuation."""

        result = extract_story_content(content)

        assert "# Simple Story" in result
        assert "## Chapter 1" in result
        assert "A simple beginning" in result
        assert "## Chapter 2" in result

    def test_multiple_story_separators(self):
        """Test handling of multiple story separators"""
        content = """# Complex Story

---

## Chapter 1
Content here.

---

### Section Within Chapter
More content.

---

## Chapter 2
New chapter."""

        result = extract_story_content(content)

        assert "# Complex Story" in result
        assert "## Chapter 1" in result
        assert "### Section Within Chapter" in result
        assert "## Chapter 2" in result


class TestGeneratePDF:
    """Test the GeneratePDF function"""

    def test_successful_pdf_generation(self, mock_interface, mock_logger, sample_markdown_content, mocker):
        """Test successful PDF generation"""
        # Mock reportlab to avoid actual PDF generation in tests
        mocked_doc = mocker.MagicMock()
        mocker.patch('Writer.PDFGenerator.SimpleDocTemplate', return_value=mocked_doc)
        mocker.patch('Writer.PDFGenerator.os.makedirs')

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")

            success, message = GeneratePDF(
                mock_interface,
                mock_logger,
                sample_markdown_content,
                pdf_path,
                "Test Story"
            )

            assert success is True
            assert "successfully" in message.lower()
            assert any("generated PDF" in log for log in mock_logger.logs)

            # Verify SimpleDocTemplate was called
            mocked_doc.build.assert_called_once()

    def test_pdf_creation_failure(self, mock_interface, mock_logger, sample_markdown_content, mocker):
        """Test handling of PDF creation failure"""
        # Force an error in PDF generation
        mocker.patch('Writer.PDFGenerator.SimpleDocTemplate', side_effect=Exception("Test error"))

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")

            success, message = GeneratePDF(
                mock_interface,
                mock_logger,
                sample_markdown_content,
                pdf_path,
                "Test Story"
            )

            assert success is False
            assert "failed" in message.lower()
            assert "Test error" in message
            assert any("PDF generation failed" in log for log in mock_logger.logs)

    def test_directory_creation(self, mock_interface, mock_logger, sample_markdown_content, mocker):
        """Test that output directory is created if it doesn't exist"""
        mocked_doc = mocker.MagicMock()
        mocker.patch('Writer.PDFGenerator.SimpleDocTemplate', return_value=mocked_doc)

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "newdir", "test.pdf")

            # Mock os.makedirs to verify it's called
            mock_makedirs = mocker.patch('Writer.PDFGenerator.os.makedirs')

            GeneratePDF(
                mock_interface,
                mock_logger,
                sample_markdown_content,
                pdf_path,
                "Test Story"
            )

            mock_makedirs.assert_called_once_with(os.path.dirname(pdf_path), exist_ok=True)

    def test_chapter_formatting(self, mock_interface, mock_logger, mocker):
        """Test that chapters are formatted correctly"""
        mocked_doc = mocker.MagicMock()
        mocker.patch('Writer.PDFGenerator.SimpleDocTemplate', return_value=mocked_doc)
        mocker.patch('Writer.PDFGenerator.os.makedirs')

        content = """# Multi Chapter Story

---

## Chapter 1
Chapter one content.

### Section 1.1
Section content.

## Chapter 2
Chapter two content."""

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")

            GeneratePDF(
                mock_interface,
                mock_logger,
                content,
                pdf_path,
                "Multi Chapter Story"
            )

            # Verify build was called
            mocked_doc.build.assert_called_once()

            # Get the story argument from build call
            call_args = mocked_doc.build.call_args
            story = call_args[0][0]  # First positional argument to build

            # Should contain title and chapters
            story_text = ' '.join([str(item) for item in story])

            # Verify title formatting
            assert "Multi Chapter Story" in story_text

            # Verify chapter formatting
            assert "Chapter 1" in story_text
            assert "Chapter one content" in story_text
            assert "Chapter 2" in story_text
            assert "Chapter two content" in story_text


@pytest.mark.integration
class TestPDFGenerationIntegration:
    """Integration tests for PDF generation"""

    def test_full_flow_with_mock_dependencies(self, mock_interface, mock_logger, mocker):
        """Test the complete PDF generation flow with all dependencies mocked"""
        # Mock the entire reportlab module chain
        with patch('Writer.PDFGenerator.SimpleDocTemplate') as mock_doc, \
             patch('Writer.PDFGenerator.NumberedCanvas'), \
             patch('Writer.PDFGenerator.os.makedirs'):

            mock_doc.return_value.build = mocker.MagicMock()

            content = """# Integration Test

---

## Chapter 1
Test content for integration test."""

            with tempfile.TemporaryDirectory() as tmpdir:
                pdf_path = os.path.join(tmpdir, "integration_test.pdf")

                success, message = GeneratePDF(
                    mock_interface,
                    mock_logger,
                    content,
                    pdf_path,
                    "Integration Test"
                )

                assert success