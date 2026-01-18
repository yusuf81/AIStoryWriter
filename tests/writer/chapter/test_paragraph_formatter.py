"""
Tests for ParagraphFormatter - Fallback paragraph formatting.

TDD London School: Tests written first (RED phase).

This module provides fallback paragraph formatting when LLM fails to add
adequate paragraph breaks after max retries.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TestRegexSentTokenize:
    """Test regex-based sentence tokenizer."""

    def test_basic_sentences_split(self):
        """Split basic sentences ending with period."""
        from Writer.Chapter.ParagraphFormatter import regex_sent_tokenize

        text = "This is sentence one. This is sentence two. This is sentence three."
        sentences = regex_sent_tokenize(text)

        assert len(sentences) == 3
        assert sentences[0] == "This is sentence one."
        assert sentences[1] == "This is sentence two."
        assert sentences[2] == "This is sentence three."

    def test_sentences_with_question_and_exclamation(self):
        """Split sentences with ? and ! marks."""
        from Writer.Chapter.ParagraphFormatter import regex_sent_tokenize

        text = "What is this? It is amazing! Yes it is."
        sentences = regex_sent_tokenize(text)

        assert len(sentences) == 3
        assert "What is this?" in sentences[0]
        assert "amazing!" in sentences[1]

    def test_dialogue_with_quotes(self):
        """Handle dialogue with quotes correctly."""
        from Writer.Chapter.ParagraphFormatter import regex_sent_tokenize

        text = '"Hello," she said. "How are you?" He smiled.'
        sentences = regex_sent_tokenize(text)

        # Should split into meaningful units
        assert len(sentences) >= 2

    def test_ellipsis_handling(self):
        """Handle ellipsis (...) without breaking mid-sentence."""
        from Writer.Chapter.ParagraphFormatter import regex_sent_tokenize

        text = "He paused... then continued. She nodded."
        sentences = regex_sent_tokenize(text)

        # Ellipsis should not cause extra splits
        assert len(sentences) <= 3

    def test_indonesian_sentences(self):
        """Handle Indonesian sentences correctly."""
        from Writer.Chapter.ParagraphFormatter import regex_sent_tokenize

        text = "Ini kalimat pertama. Ini kalimat kedua. Ini kalimat ketiga."
        sentences = regex_sent_tokenize(text)

        assert len(sentences) == 3

    def test_empty_text(self):
        """Handle empty text gracefully."""
        from Writer.Chapter.ParagraphFormatter import regex_sent_tokenize

        sentences = regex_sent_tokenize("")
        assert sentences == []

    def test_single_sentence(self):
        """Handle single sentence without period at end."""
        from Writer.Chapter.ParagraphFormatter import regex_sent_tokenize

        text = "This is a single sentence without ending period"
        sentences = regex_sent_tokenize(text)

        assert len(sentences) == 1
        assert sentences[0] == text


class TestAutoFormatParagraphs:
    """Test heuristic-based auto paragraph formatting."""

    def test_splits_at_dialogue_boundary(self):
        """Should start new paragraph before dialogue."""
        from Writer.Chapter.ParagraphFormatter import auto_format_paragraphs

        text = (
            "The room was quiet. Everyone waited. "
            '"I have an announcement," said the leader. '
            "The crowd gasped."
        )
        result = auto_format_paragraphs(text, target_words=50)

        # Should have paragraph break before dialogue
        assert '\n\n' in result
        paragraphs = result.split('\n\n')
        # At least one paragraph should start with dialogue
        assert any(p.strip().startswith('"') for p in paragraphs)

    def test_splits_at_scene_indicator_english(self):
        """Should start new paragraph at scene indicators (English)."""
        from Writer.Chapter.ParagraphFormatter import auto_format_paragraphs

        text = (
            "John walked home. He was tired. "
            "Meanwhile, Mary was cooking dinner. She hummed a tune."
        )
        result = auto_format_paragraphs(text, target_words=100)

        assert '\n\n' in result
        paragraphs = result.split('\n\n')
        # "Meanwhile" should start a new paragraph
        assert any('Meanwhile' in p for p in paragraphs)

    def test_splits_at_scene_indicator_indonesian(self):
        """Should start new paragraph at scene indicators (Indonesian)."""
        from Writer.Chapter.ParagraphFormatter import auto_format_paragraphs

        text = (
            "Budi berjalan pulang. Dia sangat lelah. "
            "Sementara itu, Ani sedang memasak makan malam. Dia bersenandung."
        )
        result = auto_format_paragraphs(text, target_words=100)

        assert '\n\n' in result
        paragraphs = result.split('\n\n')
        # "Sementara itu" should start a new paragraph
        assert any('Sementara itu' in p for p in paragraphs)

    def test_splits_at_word_count_threshold(self):
        """Should split when word count threshold reached."""
        from Writer.Chapter.ParagraphFormatter import auto_format_paragraphs

        # Create text with ~300 words (should split into 2+ paragraphs at 150 threshold)
        text = "This is a test sentence. " * 60  # ~300 words
        result = auto_format_paragraphs(text, target_words=150)

        paragraphs = result.split('\n\n')
        assert len(paragraphs) >= 2

    def test_preserves_content(self):
        """Should not lose any content during formatting."""
        from Writer.Chapter.ParagraphFormatter import auto_format_paragraphs

        text = "First sentence here. Second sentence here. Third sentence here."
        result = auto_format_paragraphs(text, target_words=10)

        # All original content should be present
        assert "First sentence" in result
        assert "Second sentence" in result
        assert "Third sentence" in result

    def test_uses_config_target_words(self):
        """Should use PARAGRAPH_TARGET_WORDS from config."""
        from Writer.Chapter.ParagraphFormatter import auto_format_paragraphs
        import Writer.Config as Config

        # Verify config exists
        assert hasattr(Config, 'PARAGRAPH_TARGET_WORDS')

        text = "Test sentence. " * 100
        # Default should use config value
        result = auto_format_paragraphs(text)
        assert '\n\n' in result


class TestForceSplitParagraphs:
    """Test force split fallback (last resort)."""

    def test_splits_at_char_threshold(self):
        """Should split at character threshold."""
        from Writer.Chapter.ParagraphFormatter import force_split_paragraphs

        text = "This is a sentence. " * 50  # ~1000 chars
        result = force_split_paragraphs(text, max_chars=500)

        paragraphs = result.split('\n\n')
        assert len(paragraphs) >= 2

    def test_splits_at_sentence_boundary(self):
        """Should split at sentence boundary, not mid-word."""
        from Writer.Chapter.ParagraphFormatter import force_split_paragraphs

        text = "First sentence here. Second sentence here. Third sentence here."
        result = force_split_paragraphs(text, max_chars=30)

        paragraphs = result.split('\n\n')
        # Each paragraph should end with proper punctuation
        for para in paragraphs:
            if para.strip():
                assert para.strip()[-1] in '.!?'

    def test_preserves_content(self):
        """Should not lose any content during force split."""
        from Writer.Chapter.ParagraphFormatter import force_split_paragraphs

        text = "Word one. Word two. Word three."
        result = force_split_paragraphs(text, max_chars=15)

        assert "Word one" in result
        assert "Word two" in result
        assert "Word three" in result


class TestEnsureParagraphFormatting:
    """Test main fallback function."""

    def test_returns_unchanged_if_valid(self):
        """Should return text unchanged if already valid."""
        from Writer.Chapter.ParagraphFormatter import ensure_paragraph_formatting

        # Text with adequate breaks (3+ breaks for short text)
        text = "Para 1.\n\nPara 2.\n\nPara 3.\n\nPara 4."
        result, was_modified = ensure_paragraph_formatting(text, chapter_num=1)

        assert was_modified is False
        assert result == text

    def test_applies_heuristic_formatting(self):
        """Should apply heuristic formatting if validation fails."""
        from Writer.Chapter.ParagraphFormatter import ensure_paragraph_formatting

        # Wall of text without breaks (~1000 chars to trigger validation failure)
        text = "This is a sentence. " * 50
        result, was_modified = ensure_paragraph_formatting(text, chapter_num=1)

        assert was_modified is True
        assert '\n\n' in result

    def test_uses_force_split_as_last_resort(self):
        """Should use force split if heuristic doesn't produce enough breaks."""
        from Writer.Chapter.ParagraphFormatter import ensure_paragraph_formatting

        # Very long text that needs aggressive splitting
        text = "Word. " * 500  # ~3000 chars
        result, was_modified = ensure_paragraph_formatting(text, chapter_num=1)

        assert was_modified is True
        paragraphs = result.split('\n\n')
        assert len(paragraphs) >= 3  # Should have minimum breaks

    def test_respects_native_language(self):
        """Should work with both EN and ID languages."""
        from Writer.Chapter.ParagraphFormatter import ensure_paragraph_formatting

        text = "Kalimat satu. " * 50
        result_id, _ = ensure_paragraph_formatting(text, chapter_num=1, native_language="id")
        result_en, _ = ensure_paragraph_formatting(text, chapter_num=1, native_language="en")

        # Both should produce formatted output
        assert '\n\n' in result_id
        assert '\n\n' in result_en


class TestConfigIntegration:
    """Test that config values exist and are correct."""

    def test_paragraph_target_words_exists(self):
        """Config should have PARAGRAPH_TARGET_WORDS."""
        import Writer.Config as Config
        assert hasattr(Config, 'PARAGRAPH_TARGET_WORDS')
        assert Config.PARAGRAPH_TARGET_WORDS == 150

    def test_scene_indicators_en_exists(self):
        """Config should have PARAGRAPH_SCENE_INDICATORS_EN."""
        import Writer.Config as Config
        assert hasattr(Config, 'PARAGRAPH_SCENE_INDICATORS_EN')
        assert isinstance(Config.PARAGRAPH_SCENE_INDICATORS_EN, list)
        assert len(Config.PARAGRAPH_SCENE_INDICATORS_EN) > 0

    def test_scene_indicators_id_exists(self):
        """Config should have PARAGRAPH_SCENE_INDICATORS_ID."""
        import Writer.Config as Config
        assert hasattr(Config, 'PARAGRAPH_SCENE_INDICATORS_ID')
        assert isinstance(Config.PARAGRAPH_SCENE_INDICATORS_ID, list)
        assert len(Config.PARAGRAPH_SCENE_INDICATORS_ID) > 0

    def test_scene_indicators_symmetric(self):
        """EN and ID scene indicator lists should be same length."""
        import Writer.Config as Config
        assert len(Config.PARAGRAPH_SCENE_INDICATORS_EN) == len(Config.PARAGRAPH_SCENE_INDICATORS_ID), \
            "EN and ID scene indicator lists must be symmetric (same length)"
