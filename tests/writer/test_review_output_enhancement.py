#!/usr/bin/env python3
"""
TDD tests for ReviewOutput prompt enhancement.
Tests that the enhanced CRITIC prompts explicitly request structured feedback.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pydantic import ValidationError


class TestReviewOutputEnhancement:
    """Test ReviewOutput prompt enhancement following London School TDD"""

    def test_outline_critique_with_structured_request(self, mock_logger):
        """Test that CRITIC_OUTLINE_PROMPT includes structured format instructions"""
        from Writer.PromptsHelper import get_prompts

        # Get prompts based on the current language setting
        ActivePrompts = get_prompts()

        # Check that the outline critique prompt has structured format instructions
        critique_prompt = ActivePrompts.CRITIC_OUTLINE_PROMPT

        # Should contain explicit requests for structured feedback (language-agnostic)
        prompt_lower = critique_prompt.lower()
        has_format = ("structured format" in prompt_lower or
                     "format terstruktur" in prompt_lower)
        has_suggestions = ("specific suggestions" in prompt_lower or
                          "saran spesifik" in prompt_lower or
                          "suggestions" in prompt_lower or
                          "rekomendasi" in prompt_lower)
        has_rating = ("rating" in prompt_lower or
                     "peringkat" in prompt_lower or
                     "skor" in prompt_lower)
        has_feedback = ("feedback" in prompt_lower or
                       "umpan balik" in prompt_lower)

        assert has_format or has_suggestions, "Prompt should request structured format or specific suggestions"
        assert has_rating, "Prompt should request rating"
        assert has_feedback, "Prompt should request feedback"

    def test_chapter_critique_with_structured_request(self, mock_logger):
        """Test that CRITIC_CHAPTER_PROMPT includes structured format instructions"""
        from Writer.PromptsHelper import get_prompts

        # Get prompts based on the current language setting
        ActivePrompts = get_prompts()

        # Check that the chapter critique prompt has structured format instructions
        critique_prompt = ActivePrompts.CRITIC_CHAPTER_PROMPT

        # Should contain explicit requests for structured feedback (language-agnostic)
        prompt_lower = critique_prompt.lower()
        has_format = ("structured format" in prompt_lower or
                     "format terstruktur" in prompt_lower)
        has_suggestions = ("specific suggestions" in prompt_lower or
                          "saran spesifik" in prompt_lower or
                          "suggestions" in prompt_lower or
                          "rekomendasi" in prompt_lower)
        has_rating = ("rating" in prompt_lower or
                     "peringkat" in prompt_lower or
                     "skor" in prompt_lower)
        has_feedback = ("feedback" in prompt_lower or
                       "umpan balik" in prompt_lower)

        assert has_format or has_suggestions, "Prompt should request structured format or specific suggestions"
        assert has_rating, "Prompt should request rating"
        assert has_feedback, "Prompt should request feedback"

    def test_enhanced_critique_prompts_score_range(self, mock_logger):
        """Test that enhanced prompts specify 0-10 score range"""
        from Writer.PromptsHelper import get_prompts

        ActivePrompts = get_prompts()

        # Both prompts should specify the rating scale
        outline_prompt = ActivePrompts.CRITIC_OUTLINE_PROMPT
        chapter_prompt = ActivePrompts.CRITIC_CHAPTER_PROMPT

        # Should mention 0-10 range or similar
        assert "0-10" in outline_prompt or "0 to 10" in outline_prompt or "10" in outline_prompt
        assert "0-10" in chapter_prompt or "0 to 10" in chapter_prompt or "10" in chapter_prompt

    def test_llm_response_matches_structure(self, mock_logger):
        """Test that LLM can provide properly structured ReviewOutput response"""
        from Writer.Models import ReviewOutput
        from Writer.Interface.Wrapper import Interface

        # Create mock interface
        interface = Interface(Models=[])

        # Mock ReviewOutput response as LLM should provide
        mock_review = ReviewOutput(
            feedback="The outline shows good character development but needs more conflict.",
            suggestions=[
                "Add more tension between characters",
                "Clarify the main character's motivation",
                "Strengthen the climax scene"
            ],
            rating=7
        )

        with patch.object(interface, 'SafeGeneratePydantic') as mock_generate:
            mock_generate.return_value = (
                [{"role": "user", "content": "test"}],
                mock_review,
                {'prompt_tokens': 100, 'completion_tokens': 150}
            )

            # Simulate the call from GetFeedbackOnOutline
            messages, result, tokens = interface.SafeGeneratePydantic(
                mock_logger(),
                [{"role": "user", "content": "test"}],
                "test_model",
                ReviewOutput
            )

            assert isinstance(result, ReviewOutput)
            assert result.rating == 7
            assert len(result.suggestions) == 3
            assert "character development" in result.feedback

    def test_review_output_validation_still_works(self, mock_logger):
        """Test that ReviewOutput validation still works as expected"""
        from Writer.Models import ReviewOutput

        # Test valid ReviewOutput
        valid_review = ReviewOutput(
            feedback="Great story with strong characters",
            suggestions=["Add more description", "Check pacing"],
            rating=8
        )
        assert valid_review.rating == 8
        assert len(valid_review.suggestions) == 2

        # Test rating boundary validation
        with pytest.raises(ValidationError) as exc_info:
            ReviewOutput(
                feedback="Valid feedback",
                suggestions=["Good suggestion"],
                rating=11  # Too high
            )
        assert "less than or equal to 10" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            ReviewOutput(
                feedback="Valid feedback",
                suggestions=["Good suggestion"],
                rating=-1  # Too low
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_minimum_feedback_length_enforced(self, mock_logger):
        """Test that feedback minimum length is still enforced"""
        from Writer.Models import ReviewOutput

        # Test feedback too short
        with pytest.raises(ValidationError) as exc_info:
            ReviewOutput(
                feedback="Too",  # Too short (min 10)
                suggestions=["Good suggestion"],
                rating=5
            )
        assert "at least 10 characters" in str(exc_info.value)

        # Test feedback just long enough
        valid_review = ReviewOutput(
            feedback="This is exactly ten",
            suggestions=["Good suggestion"],
            rating=5
        )
        assert valid_review.feedback == "This is exactly ten"

    def test_suggestions_list_validation(self, mock_logger):
        """Test that suggestions field works correctly"""
        from Writer.Models import ReviewOutput

        # Test with empty suggestions list (should be fine since it's optional)
        review_no_suggestions = ReviewOutput(
            feedback="Good feedback with analysis",
            suggestions=[],
            rating=6
        )
        assert len(review_no_suggestions.suggestions) == 0

        # Test with multiple suggestions
        review_multi_suggestions = ReviewOutput(
            feedback="Areas for improvement identified",
            suggestions=[
                "Strengthen character dialogue",
                "Add more setting details",
                "Improve story pacing",
                "Clarify story themes"
            ],
            rating=7
        )
        assert len(review_multi_suggestions.suggestions) == 4
        assert "Improve story pacing" in review_multi_suggestions.suggestions

    def test_critique_prompt_contains_actionable_requirements(self, mock_logger):
        """Test that enhanced prompts ask for actionable suggestions"""
        from Writer.PromptsHelper import get_prompts

        ActivePrompts = get_prompts()

        outline_prompt = ActivePrompts.CRITIC_OUTLINE_PROMPT
        chapter_prompt = ActivePrompts.CRITIC_CHAPTER_PROMPT

        # Should ask for actionable/recommendation-style suggestions (language-agnostic)
        outline_has_actionable = (
            "actionable" in outline_prompt.lower() or
            "recommendations" in outline_prompt.lower() or
            "specific suggestions" in outline_prompt.lower() or
            "saran spesifik" in outline_prompt.lower() or
            "rekomendasi" in outline_prompt.lower() or
            "dapat ditindaklanjuti" in outline_prompt.lower()
        )

        chapter_has_actionable = (
            "actionable" in chapter_prompt.lower() or
            "recommendations" in chapter_prompt.lower() or
            "specific suggestions" in chapter_prompt.lower() or
            "saran spesifik" in chapter_prompt.lower() or
            "rekomendasi" in chapter_prompt.lower() or
            "dapat ditindaklanjuti" in chapter_prompt.lower()
        )

        assert outline_has_actionable and chapter_has_actionable