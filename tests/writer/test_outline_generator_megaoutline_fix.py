"""
Tests for MegaOutline fallback fix in OutlineGenerator.py
Ensuring full scene content is extracted instead of just summary
"""

import pytest
from unittest.mock import Mock
from Writer.Models import ChapterOutlineOutput, EnhancedSceneOutline
from Writer.OutlineGenerator import GeneratePerChapterOutline


class TestMegaOutlineFix:
    """Test that chapter outline extraction returns full scenes content to avoid MegaOutline fallback"""

    def test_extract_full_scenes_content_from_enhanced_scenes(self):
        """Test that full EnhancedSceneOutline content is extracted, not just summary"""

        # Create mock interface and logger
        mock_interface = Mock()
        mock_logger = Mock()
        mock_logger.Log = Mock()  # Add the Log method

        # Create ChapterOutlineOutput with enhanced scenes
        enhanced_scene = EnhancedSceneOutline(
            title="Opening Scene",
            characters_and_setting="Alex, Sarah - dimana kafe yang nyaman dengan aroma kopi yang memabukkan",
            conflict_and_tone="Alex gugup mengakui perasaannya pada Sarah",
            key_events="Alex mengambil napas dalam-dasar, mati-matian berusaha mengumpulkan keberanian untuk mengakui perasaannya pada Sarah yang telah lama menjadi sahabatnya",
            literary_devices="metafora aroma kopi sebagai lambang ketertarikan, dialog yang terputus-putus menunjukkan ketegangan",
            resolution="Alex akhirnya berkata 'Aku suka kamu', Sarah tersenyum hangat"
        )

        chapter_outline = ChapterOutlineOutput(
            chapter_number=1,
            chapter_title="Pengakuan di Kafe",
            scenes=[enhanced_scene],
            outline_summary="Alex mengakui perasaannya pada Sarah di kafe"  # This is only 40 words
        )

        # Mock the SafeGeneratePydantic to return our test object
        mock_interface.SafeGeneratePydantic.return_value = ([], chapter_outline, None)

        # Call the function
        summary_text, chapter_title = GeneratePerChapterOutline(
            mock_interface,
            mock_logger,
            _Chapter=1,
            _TotalChapters=3,
            _Outline="Test outline"
        )

        # Verify that full scene content is extracted, not just summary
        assert "Opening Scene" in summary_text
        assert "Characters & Setting: Alex, Sarah" in summary_text
        assert "Conflict & Tone: Alex gugup" in summary_text
        assert "Key Events: Alex mengambil napas dalam-dasar" in summary_text
        assert "Literary Devices: metafora aroma kopi" in summary_text
        assert "Resolution: Alex akhirnya berkata 'Aku suka kamu'" in summary_text

        # Verify it's longer than the 40-word summary
        assert len(summary_text.split()) > 50  # Should be 70+ words, not just 40

    def test_extract_string_scenes_fallback(self):
        """Test that string scenes are handled correctly"""

        # Create mock interface and logger
        mock_interface = Mock()
        mock_logger = Mock()
        mock_logger.Log = Mock()  # Add the Log method

        # Create ChapterOutlineOutput with string scenes
        chapter_outline = ChapterOutlineOutput(
            chapter_number=1,
            chapter_title="Chapter One",
            scenes=[
                "Scene pertama: Alex dan Sarah bertemu di kafe lama yang telah menjadi saksi berbagai kenangan mereka selama bertahun-tahun."
                " Langit senja yang kemerahan memasuki jendela kaca, menciptakan bayangan panjang di lantai kayu yang sudah usang."
            ],
            outline_summary="This is a longer summary that meets the 20 character minimum requirement for validation."  # Fix validation error
        )

        # Mock the SafeGeneratePydantic to return our test object
        mock_interface.SafeGeneratePydantic.return_value = ([], chapter_outline, None)

        # Call the function
        summary_text, chapter_title = GeneratePerChapterOutline(
            mock_interface,
            mock_logger,
            _Chapter=1,
            _TotalChapters=3,
            _Outline="Test outline"
        )

        # Verify that the full string scene is used, not the summary
        assert "Scene pertama: Alex dan Sarah bertemu di kafe lama" in summary_text
        assert "Langit senja yang kemerahan memasuki jendela kaca" in summary_text
        assert len(summary_text.split()) > 30  # Should be longer than the summary

    def test_multiple_scenes_extraction(self):
        """Test that multiple scenes are combined properly"""

        # Create mock interface and logger
        mock_interface = Mock()
        mock_logger = Mock()
        mock_logger.Log = Mock()  # Add the Log method

        # Create ChapterOutlineOutput with multiple enhanced scenes
        scene1 = EnhancedSceneOutline(
            title="Scene 1",
            characters_and_setting="Alex berjalan sendirian",
            key_events="Alex memikirkan Sarah",
            resolution="Alex memutuskan untuk mengakui perasaannya"
        )

        scene2 = EnhancedSceneOutline(
            title="Scene 2",
            characters_and_setting="Alex bertemu Sarah di kafe",
            key_events="Alex mengakui perasaannya",
            resolution="Sarah menerima perasaan Alex"
        )

        chapter_outline = ChapterOutlineOutput(
            chapter_number=1,
            chapter_title="Chapter One",
            scenes=[scene1, scene2],
            outline_summary="Alex finally confesses to Sarah after gathering his courage"
        )

        # Mock the SafeGeneratePydantic to return our test object
        mock_interface.SafeGeneratePydantic.return_value = ([], chapter_outline, None)

        # Call the function
        summary_text, chapter_title = GeneratePerChapterOutline(
            mock_interface,
            mock_logger,
            _Chapter=1,
            _TotalChapters=3,
            _Outline="Test outline"
        )

        # Verify that both scenes are included
        assert "Scene: Scene 1" in summary_text
        assert "Scene: Scene 2" in summary_text
        assert "Alex berjalan sendirian" in summary_text
        assert "Alex bertemu Sarah di kafe" in summary_text

        # Should be longer than the brief summary
        assert len(summary_text.split()) > 30