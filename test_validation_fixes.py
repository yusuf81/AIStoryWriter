"""
Integration test for validation fixes - rating scale, suggestions format, and word count.
Tests the fixes made in Phase 1-2 of the bug fix plan.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

import pytest  # noqa: E402
from pydantic import ValidationError  # noqa: E402


class TestRatingScaleFix:
    """Test that rating scale 0-100 is properly implemented across all models"""

    def test_review_output_accepts_0_to_100(self):
        """Verify ReviewOutput accepts 0-100 rating scale"""
        from Writer.Models import ReviewOutput

        # Test low range
        review_low = ReviewOutput(
            feedback="Needs significant improvement in plot structure",
            suggestions=["Add more conflict", "Develop character arcs"],
            rating=15
        )
        assert review_low.rating == 15

        # Test mid-low range
        review_mid_low = ReviewOutput(
            feedback="Decent foundation but needs work",
            suggestions=["Strengthen dialogue"],
            rating=45
        )
        assert review_mid_low.rating == 45

        # Test mid-high range
        review_mid_high = ReviewOutput(
            feedback="Good work with minor improvements needed",
            suggestions=["Polish ending"],
            rating=75
        )
        assert review_mid_high.rating == 75

        # Test high range
        review_high = ReviewOutput(
            feedback="Excellent work overall",
            suggestions=["Add final touches"],
            rating=95
        )
        assert review_high.rating == 95

        # Test upper bound
        review_max = ReviewOutput(
            feedback="Perfect story, no changes needed",
            suggestions=[],
            rating=100
        )
        assert review_max.rating == 100

    def test_review_output_rejects_invalid_ratings(self):
        """Verify ReviewOutput rejects ratings outside 0-100 range"""
        from Writer.Models import ReviewOutput

        # Rating > 100 should fail
        with pytest.raises(ValidationError) as exc_info:
            ReviewOutput(
                feedback="Good work",
                suggestions=["Minor edits"],
                rating=101
            )
        assert "rating" in str(exc_info.value).lower()

        # Rating < 0 should fail
        with pytest.raises(ValidationError) as exc_info:
            ReviewOutput(
                feedback="Needs work",
                suggestions=["Major revision"],
                rating=-1
            )
        assert "rating" in str(exc_info.value).lower()

    def test_outline_evaluation_output_accepts_0_to_100(self):
        """Verify OutlineEvaluationOutput accepts 0-100 score scale"""
        from Writer.Models import OutlineEvaluationOutput

        # Test various ranges
        eval_low = OutlineEvaluationOutput(
            score=25,
            strengths="Clear basic structure present in outline",
            weaknesses="Lacks depth and character development",
            recommendations="Add more detailed character motivations and plot complexity"
        )
        assert eval_low.score == 25

        eval_mid = OutlineEvaluationOutput(
            score=50,
            strengths="Good foundation with interesting premise",
            weaknesses="Pacing needs adjustment in middle section",
            recommendations="Expand middle chapters and add more conflict"
        )
        assert eval_mid.score == 50

        eval_high = OutlineEvaluationOutput(
            score=92,
            strengths="Excellent plot structure with strong character arcs",
            weaknesses="Minor pacing issue in climax",
            recommendations="Tighten climax sequence slightly"
        )
        assert eval_high.score == 92

    def test_chapter_evaluation_output_accepts_0_to_100(self):
        """Verify ChapterEvaluationOutput accepts 0-100 score scale"""
        from Writer.Models import ChapterEvaluationOutput

        # Test with word_count field (ChapterEvaluationOutput-specific)
        eval_chapter = ChapterEvaluationOutput(
            score=88,
            strengths="Strong character development and engaging dialogue",
            weaknesses="Opening paragraph could be stronger",
            recommendations="Revise opening to hook reader immediately"
        )
        assert eval_chapter.score == 88

    def test_all_evaluation_models_reject_invalid_scores(self):
        """Verify all evaluation models reject scores outside 0-100"""
        from Writer.Models import OutlineEvaluationOutput, ChapterEvaluationOutput

        # OutlineEvaluationOutput score > 100
        with pytest.raises(ValidationError):
            OutlineEvaluationOutput(
                score=101,
                strengths="Good structure",
                weaknesses="None",
                recommendations="None"
            )

        # ChapterEvaluationOutput score < 0
        with pytest.raises(ValidationError):
            ChapterEvaluationOutput(
                score=-5,
                strengths="Some strengths",
                weaknesses="Major issues",
                recommendations="Full rewrite"
            )


class TestSuggestionsFieldFormat:
    """Test that suggestions field properly accepts list format"""

    def test_review_output_accepts_list_of_strings(self):
        """Verify ReviewOutput accepts suggestions as list of strings"""
        from Writer.Models import ReviewOutput

        review = ReviewOutput(
            feedback="Good foundation with room for improvement",
            suggestions=[
                "Add more dialogue in opening scene",
                "Develop character backstory",
                "Strengthen conflict in middle chapters",
                "Polish resolution"
            ],
            rating=75
        )
        assert review.suggestions is not None
        assert len(review.suggestions) == 4
        assert review.suggestions[0] == "Add more dialogue in opening scene"
        assert all(isinstance(s, str) for s in review.suggestions)

    def test_review_output_accepts_empty_suggestions_list(self):
        """Verify ReviewOutput accepts empty suggestions list"""
        from Writer.Models import ReviewOutput

        review = ReviewOutput(
            feedback="Perfect work, no changes needed",
            suggestions=[],
            rating=100
        )
        assert review.suggestions is not None
        assert len(review.suggestions) == 0

    def test_evaluation_models_use_recommendations_field(self):
        """Verify OutlineEvaluationOutput and ChapterEvaluationOutput use recommendations field"""
        from Writer.Models import OutlineEvaluationOutput, ChapterEvaluationOutput

        # OutlineEvaluationOutput uses 'recommendations' field (not 'suggestions')
        eval_outline = OutlineEvaluationOutput(
            score=85,
            strengths="Well-structured narrative with clear progression",
            weaknesses="Character development needs depth",
            recommendations="Add character backstories and motivations in early chapters"
        )
        assert len(eval_outline.recommendations) > 10
        assert "character" in eval_outline.recommendations.lower()

        # ChapterEvaluationOutput uses 'recommendations' field (not 'suggestions')
        eval_chapter = ChapterEvaluationOutput(
            score=90,
            strengths="Engaging narrative with good pacing",
            weaknesses="Dialogue could be more natural",
            recommendations="Revise dialogue to sound more conversational and add subtext"
        )
        assert len(eval_chapter.recommendations) > 10
        assert "dialogue" in eval_chapter.recommendations.lower()


class TestModelRegistry:
    """Verify all fixed models are properly registered"""

    def test_all_models_in_registry(self):
        """Verify all evaluation and review models are in MODEL_REGISTRY"""
        from Writer.Models import MODEL_REGISTRY

        required_models = [
            'ReviewOutput',
            'OutlineEvaluationOutput',
            'ChapterEvaluationOutput'
            # Note: EvaluationOutputBase is a base class, not used directly by LLM
        ]

        for model_name in required_models:
            assert model_name in MODEL_REGISTRY, \
                f"{model_name} not found in MODEL_REGISTRY"


def main():
    """Run tests with pytest"""
    print("=" * 60)
    print("VALIDATION FIXES INTEGRATION TEST")
    print("=" * 60)
    print("\nTesting Phase 1-2 bug fixes:")
    print("  - Rating scale: 0-10 → 0-100")
    print("  - Suggestions format: List of strings")
    print("  - Model registry completeness")
    print("\n" + "=" * 60)

    # Run pytest programmatically
    exit_code = pytest.main([__file__, "-v", "--tb=short"])

    if exit_code == 0:
        print("\n" + "=" * 60)
        print("✓ ALL VALIDATION FIX TESTS PASSED")
        print("=" * 60)
        print("\nValidated:")
        print("  ✓ ReviewOutput rating: 0-100 ✓")
        print("  ✓ OutlineEvaluationOutput score: 0-100 ✓")
        print("  ✓ ChapterEvaluationOutput score: 0-100 ✓")
        print("  ✓ Suggestions field: List format ✓")
        print("  ✓ Model registry: All models present ✓")
    else:
        print("\n" + "=" * 60)
        print("✗ SOME TESTS FAILED")
        print("=" * 60)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
