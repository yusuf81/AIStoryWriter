"""
TDD tests for normalize_suggestions bilingual bug fix.

Following London School TDD: RED -> GREEN -> REFACTOR

Problem: normalize_suggestions field_validator only supports Indonesian fields
and doesn't exclude English fields from other_criteria, causing nested structures
when Gemini returns English format.
"""
import pytest
from pydantic import ValidationError

from Writer.Models import ReviewOutput, EnhancedSuggestion


class TestNormalizeSuggestionsBilingualSupport:
    """RED tests - will FAIL before fix, PASS after fix"""

    # --- Fixtures ---

    @pytest.fixture
    def gemini_english_suggestion(self):
        """Gemini-format English suggestion with other_criteria"""
        return {
            'description': 'Perkuat koneksi emosional antara teror anak-anak dan teror Jaka',
            'pacing': 'Percepat transisi antar adegan',
            'flow': 'Memperkuat kontinuitas plot antara adegan 1 dan 2'
        }

    @pytest.fixture
    def gemini_english_suggestion_with_other_criteria(self):
        """Gemini-format English suggestion with other_criteria dict"""
        return {
            'description': 'Perjelas perbedaan antara rambut yang menjulur di jendela Jaka',
            'other_criteria': {
                'visual_consistency': 'Pastikan deskripsi rambut yang basah kuyup di jendela Jaka dikaitkan dengan aura dingin'
            }
        }

    @pytest.fixture
    def indonesian_suggestion(self):
        """Indonesian-format suggestion with detail, laju, alur"""
        return {
            'detail': 'Tambahkan lebih banyak detail tentang tantangan',
            'laju': 'Perbaiki laju cerita di bab pertama',
            'alur': 'Pastikan alur naratif konsisten'
        }

    @pytest.fixture
    def mixed_language_suggestion(self):
        """Mixed Indonesian and English fields"""
        return {
            'description': 'Test dengan English field',
            'laju': 'Tapi Indonesian field juga',
            'alur': 'Campuran bahasa'
        }

    @pytest.fixture
    def suggestion_with_empty_other_criteria(self):
        """Suggestion with empty other_criteria that should be removed"""
        return {
            'description': 'Test suggestion',
            'other_criteria': {}
        }

    @pytest.fixture
    def suggestion_with_none_optional_fields(self):
        """Suggestion with None values in optional fields"""
        return {
            'description': 'Test suggestion',
            'pacing': None,
            'flow': None
        }

    # --- RED Tests (should FAIL before fix) ---

    def test_english_format_description_preserved(self, gemini_english_suggestion):
        """RED: English 'description' field should be preserved and mapped correctly"""
        review = ReviewOutput(
            feedback='Test feedback with enough length for validation',
            suggestions=[gemini_english_suggestion],
            rating=85
        )

        assert review.suggestions is not None
        assert isinstance(review.suggestions[0], EnhancedSuggestion)
        assert review.suggestions[0].description == 'Perkuat koneksi emosional antara teror anak-anak dan teror Jaka'

    def test_english_format_optional_fields_preserved(self, gemini_english_suggestion):
        """RED: English 'pacing' and 'flow' fields should be preserved"""
        review = ReviewOutput(
            feedback='Test feedback with enough length for validation',
            suggestions=[gemini_english_suggestion],
            rating=85
        )

        assert review.suggestions is not None
        assert review.suggestions[0].pacing == 'Percepat transisi antar adegan'  # type: ignore[arg-type]
        assert review.suggestions[0].flow == 'Memperkuat kontinuitas plot antara adegan 1 dan 2'  # type: ignore[arg-type]

    def test_english_format_with_other_criteria_not_nested(self, gemini_english_suggestion_with_other_criteria):
        """RED: other_criteria should NOT be nested when input has English format"""
        review = ReviewOutput(
            feedback='Test feedback with enough length for validation',
            suggestions=[gemini_english_suggestion_with_other_criteria],
            rating=85
        )

        # other_criteria should be a flat dict, NOT nested
        assert review.suggestions is not None
        other_criteria = review.suggestions[0].other_criteria  # type: ignore[arg-type]
        assert other_criteria is not None
        assert 'visual_consistency' in other_criteria
        assert 'other_criteria' not in other_criteria  # Should NOT be nested
        assert isinstance(other_criteria['visual_consistency'], str)

    def test_indonesian_format_normalized_correctly(self, indonesian_suggestion):
        """RED: Indonesian fields should still work and be mapped to English"""
        review = ReviewOutput(
            feedback='Test feedback with enough length for validation',
            suggestions=[indonesian_suggestion],
            rating=85
        )

        assert review.suggestions is not None
        assert review.suggestions[0].description == 'Tambahkan lebih banyak detail tentang tantangan'  # type: ignore[arg-type]
        assert review.suggestions[0].pacing == 'Perbaiki laju cerita di bab pertama'  # type: ignore[arg-type]
        assert review.suggestions[0].flow == 'Pastikan alur naratif konsisten'  # type: ignore[arg-type]

    def test_mixed_language_fields_english_takes_priority(self, mixed_language_suggestion):
        """RED: When both English and Indonesian present, English should take priority"""
        review = ReviewOutput(
            feedback='Test feedback with enough length for validation',
            suggestions=[mixed_language_suggestion],
            rating=85
        )

        # English 'description' should take priority over Indonesian 'detail'
        assert review.suggestions is not None
        assert review.suggestions[0].description == 'Test dengan English field'  # type: ignore[arg-type]
        # Indonesian fields preserved
        assert review.suggestions[0].pacing == 'Tapi Indonesian field juga'  # type: ignore[arg-type]
        assert review.suggestions[0].flow == 'Campuran bahasa'  # type: ignore[arg-type]

    def test_empty_other_criteria_removed(self, suggestion_with_empty_other_criteria):
        """RED: Empty other_criteria dict should be removed (set to None)"""
        review = ReviewOutput(
            feedback='Test feedback with enough length for validation',
            suggestions=[suggestion_with_empty_other_criteria],
            rating=85
        )

        # Empty other_criteria should be removed (None)
        assert review.suggestions is not None
        assert review.suggestions[0].other_criteria is None  # type: ignore[arg-type]

    def test_none_optional_fields_removed(self, suggestion_with_none_optional_fields):
        """RED: Optional fields with None values should be removed"""
        review = ReviewOutput(
            feedback='Test feedback with enough length for validation',
            suggestions=[suggestion_with_none_optional_fields],
            rating=85
        )

        # Optional fields with None should not be present in the model
        assert review.suggestions is not None
        assert review.suggestions[0].pacing is None  # type: ignore[arg-type]
        assert review.suggestions[0].flow is None  # type: ignore[arg-type]

    def test_string_suggestions_preserved_as_strings(self):
        """RED: Plain string suggestions should be preserved as-is"""
        review = ReviewOutput(
            feedback='Test feedback with enough length for validation',
            suggestions=['Saran pertama', 'Saran kedua'],
            rating=85
        )

        assert review.suggestions is not None
        assert len(review.suggestions) == 2  # type: ignore[arg-type]
        assert review.suggestions[0] == 'Saran pertama'
        assert review.suggestions[1] == 'Saran kedua'
        assert all(isinstance(s, str) for s in review.suggestions)  # type: ignore[arg-type]

    def test_mixed_string_and_structured_suggestions(self):
        """RED: Mix of string and structured suggestions should work"""
        review = ReviewOutput(
            feedback='Test feedback with enough length for validation',
            suggestions=[
                'Saran sederhana',
                {'description': 'Saran terstruktur'}  # type: ignore[arg-type]
            ],
            rating=85
        )

        assert review.suggestions is not None
        assert len(review.suggestions) == 2  # type: ignore[arg-type]
        assert review.suggestions[0] == 'Saran sederhana'  # First is string
        assert isinstance(review.suggestions[1], EnhancedSuggestion)  # Second is EnhancedSuggestion
        assert review.suggestions[1].description == 'Saran terstruktur'  # type: ignore[arg-type]

    def test_gemini_actual_format_validates(self, gemini_english_suggestion_with_other_criteria):
        """RED: Actual Gemini format from log should validate correctly"""
        # This is the exact format from Gemini that caused the bug
        gemini_format = [
            {
                'description': 'Perkuat koneksi emosional antara teror anak-anak (Bimo dkk) dan teror Jaka',
                'flow': 'Memperkuat transisi antar adegan'
            },
            {
                'description': 'Perjelas perbedaan antara rambut yang menjulur di jendela Jaka',
                'other_criteria': {
                    'visual_consistency': 'Pastikan deskripsi rambut yang basah kuyup'
                }
            }
        ]

        review = ReviewOutput(
            feedback='Test feedback with enough length for validation',
            suggestions=gemini_format,  # type: ignore[arg-type]
            rating=95
        )

        assert review.suggestions is not None
        assert review.rating == 95
        assert len(review.suggestions) == 2  # type: ignore[arg-type]
        assert review.suggestions[0].flow == 'Memperkuat transisi antar adegan'  # type: ignore[arg-type]
        assert review.suggestions[1].other_criteria is not None  # type: ignore[arg-type]
        assert 'visual_consistency' in review.suggestions[1].other_criteria  # type: ignore[arg-type]

    def test_no_nested_description_in_other_criteria(self, gemini_english_suggestion_with_other_criteria):
        """RED: description should NOT appear in other_criteria (was in bug)"""
        review = ReviewOutput(
            feedback='Test feedback with enough length for validation',
            suggestions=[gemini_english_suggestion_with_other_criteria],
            rating=85
        )

        assert review.suggestions is not None
        other_criteria = review.suggestions[0].other_criteria  # type: ignore[arg-type]
        if other_criteria:
            # The bug caused 'description' to be in other_criteria
            assert 'description' not in other_criteria, 'BUG: description should not be in other_criteria'

    def test_no_nested_other_criteria_key(self, gemini_english_suggestion_with_other_criteria):
        """RED: other_criteria should NOT contain key 'other_criteria' (was in bug)"""
        review = ReviewOutput(
            feedback='Test feedback with enough length for validation',
            suggestions=[gemini_english_suggestion_with_other_criteria],
            rating=85
        )

        assert review.suggestions is not None
        other_criteria = review.suggestions[0].other_criteria  # type: ignore[arg-type]
        if other_criteria:
            # The bug caused nested: other_criteria: {'other_criteria': {...}}
            assert 'other_criteria' not in other_criteria, 'BUG: other_criteria should not be nested'


class TestNormalizeSuggestionsRegression:
    """Regression tests - ensure existing features still work

    These tests should PASS both before and after the fix.
    """

    def test_existing_indonesian_integration_test_still_works(self):
        """Ensure existing Indonesian format integration still works"""
        # From test_models.py existing test
        review = ReviewOutput(
            feedback='Outline ini memiliki kekuatan...',
            suggestions=[
                EnhancedSuggestion(
                    description='Tambahkan lebih banyak detail...',
                    pacing='Perlu diperhatikan laju cerita...',
                    flow='Pastikan setiap bab mengalir...',
                    other_criteria=None
                ),
                'Saran sederhana tentang pengembangan karakter'
            ],
            rating=7
        )

        # Checks types - first should be EnhancedSuggestion, second should be string
        assert review.suggestions is not None
        assert isinstance(review.suggestions[0], EnhancedSuggestion)
        assert isinstance(review.suggestions[1], str)
        assert review.suggestions[0].description == 'Tambahkan lebih banyak detail...'

    def test_empty_suggestions_list(self):
        """Empty suggestions list should work"""
        review = ReviewOutput(
            feedback='Test feedback with enough length for validation',
            suggestions=[],
            rating=85
        )

        assert review.suggestions is not None
        assert review.suggestions == []

    def test_none_suggestions(self):
        """None suggestions should remain None"""
        review = ReviewOutput(
            feedback='Test feedback with enough length for validation',
            suggestions=None,
            rating=85
        )

        assert review.suggestions is None

    def test_min_feedback_validation(self):
        """Minimum feedback length validation should still work"""
        with pytest.raises(ValidationError) as exc_info:
            ReviewOutput(
                feedback='Short',  # Too short (min 10)
                suggestions=None,
                rating=85
            )

        assert 'min_length' in str(exc_info.value).lower() or 'at least 10' in str(exc_info.value).lower()

    def test_rating_range_validation(self):
        """Rating range validation should still work"""
        with pytest.raises(ValidationError):
            ReviewOutput(
                feedback='Test feedback with enough length for validation',
                suggestions=None,
                rating=150  # Should be 0-100
            )
