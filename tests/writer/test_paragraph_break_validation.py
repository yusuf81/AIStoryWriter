"""
Unit tests for paragraph break validation.

Tests the validate_paragraph_breaks function that ensures chapters have
sufficient paragraph breaks to avoid wall-of-text formatting.
"""


class TestValidateParagraphBreaks:
    """Test suite for paragraph break validation function."""

    def test_validate_paragraph_breaks_sufficient(self):
        """Test that text with adequate paragraph breaks passes validation."""
        # Arrange
        from Writer.Chapter.ParagraphValidator import validate_paragraph_breaks

        # 3000 chars with 10 breaks (exceeds minimum of 6)
        text_with_breaks = ("Paragraph 1 text here.\n\nParagraph 2 text here.\n\n" * 5) + ("A" * 2000)

        # Act
        is_valid, feedback = validate_paragraph_breaks(text_with_breaks, 1)

        # Assert
        assert is_valid is True
        assert feedback == ""

    def test_validate_paragraph_breaks_wall_of_text(self):
        """Test that text with 0-1 breaks fails validation."""
        # Arrange
        from Writer.Chapter.ParagraphValidator import validate_paragraph_breaks

        wall_of_text = "A" * 3000  # 3000 chars, no breaks

        # Act
        is_valid, feedback = validate_paragraph_breaks(wall_of_text, 1)

        # Assert
        assert is_valid is False
        assert "terlalu sedikit pemisah paragraf" in feedback
        assert "0" in feedback  # Current break count
        # Expected: max(3, 3000//500) = 6 breaks
        assert "6" in feedback or "minimal 6" in feedback

    def test_validate_paragraph_breaks_calculates_minimum(self):
        """Test that minimum breaks calculation is correct (1 per 500 chars)."""
        # Arrange
        from Writer.Chapter.ParagraphValidator import validate_paragraph_breaks

        # 5000 chars should need max(3, 5000//500) = 10 breaks
        # Provide exactly 8 breaks (just below threshold of 10)
        text_with_8_breaks = ("Short.\n\n" * 8) + ("A" * 4936)

        # Act
        is_valid, feedback = validate_paragraph_breaks(text_with_8_breaks, 1)

        # Assert
        assert is_valid is False
        assert "8" in feedback  # Current count
        assert "10" in feedback or "minimal 10" in feedback  # Expected

    def test_validate_paragraph_breaks_returns_feedback(self):
        """Test that feedback message includes count and target."""
        # Arrange
        from Writer.Chapter.ParagraphValidator import validate_paragraph_breaks

        wall_of_text = "B" * 2000  # Needs max(3, 2000//500) = 4 breaks

        # Act
        is_valid, feedback = validate_paragraph_breaks(wall_of_text, 1)

        # Assert
        assert is_valid is False
        assert "0 paragraf" in feedback or "0" in feedback
        assert "2000 karakter" in feedback or "2000" in feedback
        assert "minimal 4" in feedback or "4 paragraf" in feedback
        assert "baris kosong" in feedback

    def test_validate_paragraph_breaks_short_text(self):
        """Test that short text (<500 chars) still needs minimum 3 breaks."""
        # Arrange
        from Writer.Chapter.ParagraphValidator import validate_paragraph_breaks

        short_text = "A" * 400  # Only 400 chars, but still needs 3 breaks minimum

        # Act
        is_valid, feedback = validate_paragraph_breaks(short_text, 1)

        # Assert
        assert is_valid is False
        assert "minimal 3" in feedback

    def test_validate_paragraph_breaks_edge_cases(self):
        """Test edge cases: exactly at threshold."""
        # Arrange
        from Writer.Chapter.ParagraphValidator import validate_paragraph_breaks

        # 1500 chars needs max(3, 1500//500) = 3 breaks
        # Provide exactly 3 breaks
        text_exactly_3 = "Para 1.\n\nPara 2.\n\nPara 3.\n\n" + ("A" * 1450)

        # Act
        is_valid, feedback = validate_paragraph_breaks(text_exactly_3, 1)

        # Assert
        assert is_valid is True  # Exactly at threshold should pass
        assert feedback == ""
