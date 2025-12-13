"""
New Pydantic Models TDD Tests - London School Approach
Tests for 5 new models: Evaluation (outline/chapter), StoryInfo, SceneValidation, Review
"""
import pytest
from pydantic import ValidationError
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestEvaluationModels:
    """Test evaluation models - using DRY base class pattern"""

    def test_evaluation_output_base_exists(self):
        """Verify EvaluationOutputBase base class exists (DRY principle)"""
        from Writer.Models import EvaluationOutputBase

        # Should be able to instantiate the base class
        eval_data = {
            "score": 8,
            "strengths": "Good plot structure and pacing",
            "weaknesses": "Needs more character depth",
            "recommendations": "Add character backstories and motivations"
        }
        eval_obj = EvaluationOutputBase(**eval_data)
        assert eval_obj.score == 8
        assert eval_obj.strengths == "Good plot structure and pacing"

    def test_outline_evaluation_output_validates_score_range(self):
        """RED: Test OutlineEvaluationOutput validates score 0-10"""
        from Writer.Models import OutlineEvaluationOutput

        # Arrange - valid data
        eval_data = {
            "score": 8,
            "strengths": "Good plot structure and pacing",
            "weaknesses": "Needs more character depth",
            "recommendations": "Add character backstories and motivations"
        }

        # Act
        eval_obj = OutlineEvaluationOutput(**eval_data)

        # Assert
        assert eval_obj.score == 8
        assert len(eval_obj.strengths) >= 10

        # Test validation: score must be 0-10
        with pytest.raises(ValidationError):
            OutlineEvaluationOutput(**{**eval_data, "score": 11})  # Invalid score > 10

        with pytest.raises(ValidationError):
            OutlineEvaluationOutput(**{**eval_data, "score": -1})  # Invalid score < 0

    def test_outline_evaluation_output_validates_min_length(self):
        """Test OutlineEvaluationOutput validates minimum field lengths"""
        from Writer.Models import OutlineEvaluationOutput

        # Too short strengths (< 10 chars)
        with pytest.raises(ValidationError):
            OutlineEvaluationOutput(
                score=8,
                strengths="Too short",  # Only 9 chars
                weaknesses="Valid weakness text",
                recommendations="Valid recommendations"
            )

    def test_chapter_evaluation_output_same_structure_as_outline(self):
        """Verify DRY: ChapterEvaluationOutput shares same base"""
        from Writer.Models import OutlineEvaluationOutput, ChapterEvaluationOutput

        # Both should have same fields from base class
        outline_fields = set(OutlineEvaluationOutput.model_fields.keys())
        chapter_fields = set(ChapterEvaluationOutput.model_fields.keys())
        assert outline_fields == chapter_fields, "Both models should inherit same fields from base"

    def test_chapter_evaluation_output_validates_correctly(self):
        """Test ChapterEvaluationOutput validates like OutlineEvaluationOutput"""
        from Writer.Models import ChapterEvaluationOutput

        eval_data = {
            "score": 7,
            "strengths": "Strong character development",
            "weaknesses": "Pacing could be improved",
            "recommendations": "Add more action scenes to increase pacing"
        }

        eval_obj = ChapterEvaluationOutput(**eval_data)
        assert eval_obj.score == 7
        assert eval_obj.strengths == "Strong character development"


class TestStoryInfoModel:
    """Test StoryInfoOutput model"""

    def test_story_info_output_structure(self):
        """RED: Test StoryInfoOutput has correct fields"""
        from Writer.Models import StoryInfoOutput

        info_data = {
            "title": "The Hero's Journey",
            "genre": "Fantasy Adventure",
            "summary": "A young hero must embark on a quest to save the kingdom from darkness",
            "themes": ["courage", "good vs evil", "coming of age"],
            "characters": ["Hero", "Mentor", "Villain"]
        }

        info_obj = StoryInfoOutput(**info_data)
        assert info_obj.title == "The Hero's Journey"
        assert info_obj.genre == "Fantasy Adventure"
        assert len(info_obj.summary) >= 20
        assert len(info_obj.themes) == 3
        assert "Hero" in info_obj.characters

    def test_story_info_output_validates_min_lengths(self):
        """Test StoryInfoOutput validates minimum lengths"""
        from Writer.Models import StoryInfoOutput

        # Empty title should fail
        with pytest.raises(ValidationError):
            StoryInfoOutput(
                title="",  # Too short
                genre="Fantasy",
                summary="A story about heroes and villains in a fantasy world",
                themes=["courage"],
                characters=["Hero"]
            )

        # Too short summary (< 20 chars) should fail
        with pytest.raises(ValidationError):
            StoryInfoOutput(
                title="Test Title",
                genre="Fantasy",
                summary="Too short",  # Only 9 chars
                themes=["courage"],
                characters=["Hero"]
            )


class TestSceneValidationModel:
    """Test SceneValidationOutput model"""

    def test_scene_validation_output_structure(self):
        """RED: Test SceneValidationOutput has correct fields"""
        from Writer.Models import SceneValidationOutput

        validation_data = {
            "is_valid": True,
            "errors": [],
            "scene_count": 5
        }

        validation_obj = SceneValidationOutput(**validation_data)
        assert validation_obj.is_valid is True
        assert len(validation_obj.errors) == 0
        assert validation_obj.scene_count == 5

    def test_scene_validation_output_with_errors(self):
        """Test SceneValidationOutput can store validation errors"""
        from Writer.Models import SceneValidationOutput

        validation_data = {
            "is_valid": False,
            "errors": ["Scene 2 is missing location", "Scene 3 has no dialogue"],
            "scene_count": 3
        }

        validation_obj = SceneValidationOutput(**validation_data)
        assert validation_obj.is_valid is False
        assert len(validation_obj.errors) == 2
        assert "Scene 2 is missing location" in validation_obj.errors

    def test_scene_validation_output_validates_scene_count_ge_zero(self):
        """Test SceneValidationOutput validates scene_count >= 0"""
        from Writer.Models import SceneValidationOutput

        # Negative scene count should fail
        with pytest.raises(ValidationError):
            SceneValidationOutput(
                is_valid=True,
                errors=[],
                scene_count=-1  # Invalid negative count
            )


class TestReviewModel:
    """Test ReviewOutput model"""

    def test_review_output_structure(self):
        """RED: Test ReviewOutput has correct fields"""
        from Writer.Models import ReviewOutput

        review_data = {
            "feedback": "The outline is well-structured with clear progression",
            "suggestions": [
                "Add more character backstory",
                "Increase tension in middle chapters",
                "Strengthen the climax"
            ],
            "rating": 8
        }

        review_obj = ReviewOutput(**review_data)
        assert len(review_obj.feedback) >= 10
        assert len(review_obj.suggestions) == 3
        assert review_obj.rating == 8

    def test_review_output_validates_rating_range(self):
        """Test ReviewOutput validates rating 0-10"""
        from Writer.Models import ReviewOutput

        # Rating > 10 should fail
        with pytest.raises(ValidationError):
            ReviewOutput(
                feedback="Good story structure overall",
                suggestions=["Add more details"],
                rating=11  # Invalid rating > 10
            )

        # Rating < 0 should fail
        with pytest.raises(ValidationError):
            ReviewOutput(
                feedback="Needs significant improvement",
                suggestions=["Revise entire plot"],
                rating=-1  # Invalid rating < 0
            )

    def test_review_output_validates_min_feedback_length(self):
        """Test ReviewOutput validates feedback minimum length"""
        from Writer.Models import ReviewOutput

        # Too short feedback (< 10 chars) should fail
        with pytest.raises(ValidationError):
            ReviewOutput(
                feedback="Too short",  # Only 9 chars
                suggestions=["Add more"],
                rating=5
            )


class TestModelRegistry:
    """Test that all new models are registered"""

    def test_all_new_models_in_registry(self):
        """Verify all 5 new models (+ base) are in MODEL_REGISTRY"""
        from Writer.Models import MODEL_REGISTRY

        # Check all required models are registered
        required_models = [
            'OutlineEvaluationOutput',
            'ChapterEvaluationOutput',
            'StoryInfoOutput',
            'SceneValidationOutput',
            'ReviewOutput'
        ]

        for model_name in required_models:
            assert model_name in MODEL_REGISTRY, f"{model_name} not found in MODEL_REGISTRY"
