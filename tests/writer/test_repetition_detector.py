"""
Tests for RepetitionDetector module following TDD London School

Phase: RED - These tests will fail initially because:
1. Writer.Config doesn't have repetition settings yet
2. Writer.RepetitionDetector module doesn't exist yet
"""
from Writer.RepetitionDetector import RepetitionDetector
import Writer.Config


class TestRepetitionDetector:
    """Test repetition detection algorithms"""

    def test_detect_character_explosion_positive(self):
        """Detect when character repeats excessively"""
        text = "Hello aaaaaaaaaaaaa world"

        detected, message = RepetitionDetector.detect_character_explosion(text, threshold=10)

        assert detected is True
        assert "'a'" in message
        assert "repeated" in message

    def test_detect_character_explosion_negative(self):
        """No false positive for normal text"""
        text = "This is a normal sentence without issues."

        detected, message = RepetitionDetector.detect_character_explosion(text, threshold=10)

        assert detected is False
        assert message == ""

    def test_detect_ngram_loop_positive(self):
        """Detect phrase repetition"""
        text = "The cat sat. The cat sat. The cat sat."

        detected, message = RepetitionDetector.detect_ngram_loop(text, ngram_size=3, threshold=2)

        assert detected is True
        assert "repeated" in message

    def test_detect_ngram_loop_negative(self):
        """No false positive for varied text"""
        text = "The cat sat. The dog ran. The bird flew."

        detected, message = RepetitionDetector.detect_ngram_loop(text, ngram_size=3, threshold=2)

        assert detected is False

    def test_detect_phrase_repetition_positive(self):
        """Detect long phrase repetition"""
        phrase = "This is a longer phrase that gets repeated"
        text = f"{phrase}. {phrase}. {phrase}."

        detected, message = RepetitionDetector.detect_phrase_repetition(text, min_phrase_length=20, threshold=2)

        assert detected is True

    def test_analyze_comprehensive(self):
        """Comprehensive analysis returns all fields"""
        text = "Normal text without issues"

        result = RepetitionDetector.analyze(text)

        assert "has_repetition" in result
        assert "character_explosion" in result
        assert "ngram_loop" in result
        assert "diagnostics" in result
        assert "should_retry" in result
        assert isinstance(result["unique_char_ratio"], float)

    def test_analyze_with_character_explosion(self):
        """Analysis detects character explosion"""
        text = "aaaaaaaaaaaaaaaaaaaaaa"

        result = RepetitionDetector.analyze(text)

        assert result["has_repetition"] is True
        assert result["character_explosion"] is True
        assert result["should_retry"] is True


class TestRepetitionConfig:
    """Test Config.py repetition settings exist"""

    def test_config_has_repetition_settings(self):
        """Config should have all repetition control settings"""
        assert hasattr(Writer.Config, 'OLLAMA_REPEAT_PENALTY')
        assert hasattr(Writer.Config, 'OPENROUTER_FREQUENCY_PENALTY')
        assert hasattr(Writer.Config, 'MAX_CONSECUTIVE_CHARS')
        assert hasattr(Writer.Config, 'MAX_REPETITION_RETRIES')

    def test_config_values_in_valid_range(self):
        """Config values should be in documented ranges"""
        assert Writer.Config.OLLAMA_REPEAT_PENALTY >= 1.0
        assert -2 <= Writer.Config.OPENROUTER_FREQUENCY_PENALTY <= 2
        assert Writer.Config.MAX_CONSECUTIVE_CHARS >= 5
