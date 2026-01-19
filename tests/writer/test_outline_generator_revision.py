"""
Tests for OutlineGenerator revision content loss protection.

TDD London School: Tests written first (RED phase).

When LLM returns truncated chapters (only titles, losing content),
the revision should keep the original outline instead.
"""

from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestReviseOutlineContentProtection:
    """Test that ReviseOutline protects against content loss."""

    def test_keeps_original_when_revision_loses_content(self):
        """Should keep original outline when revision loses >50% content."""
        from Writer.OutlineGenerator import ReviseOutline

        # Original outline with full content
        original_outline = """Emas & Sisik Zamrud

**Bab 1: Debu Kejayaan** Arion Thorne, si Pemburu Legenda yang mulai merasa bosan
dengan kejayaannya sendiri, tiba di kaki Gunung Cinder. Setelah bertahun-tahun
mengejar rumor tentang Gua Mata Naga, rumah perhiasan Raja Eldrin yang hilang.

**Bab 2: Napas Api Kecil** Di dalam kegelapan lembap Gua Mata Naga, Arion
menghadapi penghuninya: Fizzwick, seekor naga muda berwarna zamrud."""

        # Mock interface
        mock_interface = MagicMock()
        mock_logger = MagicMock()

        # Mock LLM returns truncated chapters (only titles)
        mock_outline_obj = MagicMock()
        mock_outline_obj.title = "Emas & Sisik Zamrud"
        mock_outline_obj.chapters = [
            "Bab 1: Debu Kejayaan",  # Only title, no content!
            "Bab 2: Napas Api Kecil"  # Only title, no content!
        ]
        mock_interface.SafeGeneratePydantic.return_value = ([], mock_outline_obj, None)
        mock_interface.BuildUserQuery.return_value = {"role": "user", "content": "test"}

        with patch('Writer.OutlineGenerator.Writer.Config') as mock_config:
            mock_config.INITIAL_OUTLINE_WRITER_MODEL = "test-model"
            mock_config.OUTLINE_MAX_REVISIONS = 3
            mock_config.OUTLINE_REVISION_MIN_RETENTION = 0.5  # 50% minimum

            result_outline, _ = ReviseOutline(
                mock_interface,
                mock_logger,
                original_outline,
                "Some feedback",
                [],
                _Iteration=1
            )

        # Should keep original because revision lost too much content
        assert result_outline == original_outline

    def test_accepts_revision_when_content_retained(self):
        """Should accept revision when content is retained (>50%)."""
        from Writer.OutlineGenerator import ReviseOutline

        # Original outline
        original_outline = """Emas & Sisik Zamrud

**Bab 1: Debu Kejayaan** Arion Thorne tiba di Gunung Cinder.

**Bab 2: Napas Api** Arion bertemu Fizzwick."""

        # Mock interface
        mock_interface = MagicMock()
        mock_logger = MagicMock()

        # Mock LLM returns good revision (similar or more content)
        mock_outline_obj = MagicMock()
        mock_outline_obj.title = "Emas & Sisik Zamrud"
        mock_outline_obj.chapters = [
            "**Bab 1: Debu Kejayaan** Arion Thorne, pemburu legenda, tiba di Gunung Cinder dengan penuh semangat.",
            "**Bab 2: Napas Api** Arion bertemu Fizzwick si naga zamrud yang lucu."
        ]
        mock_interface.SafeGeneratePydantic.return_value = ([], mock_outline_obj, None)
        mock_interface.BuildUserQuery.return_value = {"role": "user", "content": "test"}

        with patch('Writer.OutlineGenerator.Writer.Config') as mock_config:
            mock_config.INITIAL_OUTLINE_WRITER_MODEL = "test-model"
            mock_config.OUTLINE_MAX_REVISIONS = 3
            mock_config.OUTLINE_REVISION_MIN_RETENTION = 0.5

            result_outline, _ = ReviseOutline(
                mock_interface,
                mock_logger,
                original_outline,
                "Some feedback",
                [],
                _Iteration=1
            )

        # Should accept new revision (content retained)
        assert result_outline != original_outline
        assert "pemburu legenda" in result_outline

    def test_logs_warning_when_revision_rejected(self):
        """Should log warning when revision is rejected due to content loss."""
        from Writer.OutlineGenerator import ReviseOutline

        original_outline = "Full outline with lots of content about characters and plot."

        mock_interface = MagicMock()
        mock_logger = MagicMock()

        # Truncated revision
        mock_outline_obj = MagicMock()
        mock_outline_obj.title = "Title"
        mock_outline_obj.chapters = ["Ch1", "Ch2"]  # Very short
        mock_interface.SafeGeneratePydantic.return_value = ([], mock_outline_obj, None)
        mock_interface.BuildUserQuery.return_value = {"role": "user", "content": "test"}

        with patch('Writer.OutlineGenerator.Writer.Config') as mock_config:
            mock_config.INITIAL_OUTLINE_WRITER_MODEL = "test-model"
            mock_config.OUTLINE_MAX_REVISIONS = 3
            mock_config.OUTLINE_REVISION_MIN_RETENTION = 0.5

            ReviseOutline(
                mock_interface,
                mock_logger,
                original_outline,
                "Feedback",
                [],
                _Iteration=1
            )

        # Should log warning about content loss
        log_calls = [str(call) for call in mock_logger.Log.call_args_list]
        assert any("content loss" in call.lower() or "rejected" in call.lower()
                   for call in log_calls)

    def test_uses_config_retention_threshold(self):
        """Should use OUTLINE_REVISION_MIN_RETENTION from config."""
        from Writer.OutlineGenerator import ReviseOutline

        original_outline = "A" * 100  # 100 chars

        mock_interface = MagicMock()
        mock_logger = MagicMock()

        # Revision with 70 chars (70% of original)
        mock_outline_obj = MagicMock()
        mock_outline_obj.title = "Title"
        mock_outline_obj.chapters = ["A" * 60]  # title(5) + chapters(60) = ~65 chars
        mock_interface.SafeGeneratePydantic.return_value = ([], mock_outline_obj, None)
        mock_interface.BuildUserQuery.return_value = {"role": "user", "content": "test"}

        # Test with 80% threshold - should reject (70% < 80%)
        with patch('Writer.OutlineGenerator.Writer.Config') as mock_config:
            mock_config.INITIAL_OUTLINE_WRITER_MODEL = "test-model"
            mock_config.OUTLINE_MAX_REVISIONS = 3
            mock_config.OUTLINE_REVISION_MIN_RETENTION = 0.8  # 80% threshold

            result, _ = ReviseOutline(
                mock_interface, mock_logger, original_outline,
                "Feedback", [], _Iteration=1
            )

        # Should keep original (70% < 80% threshold)
        assert result == original_outline
