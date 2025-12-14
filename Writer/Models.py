# Writer/Models.py - Pydantic data models for structured output
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict
from datetime import datetime
import Writer.Config as Config


class BaseContext(BaseModel):
    """
    Structured output for extracting important base context from prompts.
    Captures key story elements that should be preserved throughout the story.
    """
    context: str = Field(min_length=10, description="Important base context extracted from the story prompt")

    @field_validator('context')
    @classmethod
    def validate_context(cls, v):
        """Validate context has meaningful content"""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Base context must be at least 10 characters long")

        # Check for empty placeholders
        if not any(c.isalnum() for c in v):
            raise ValueError("Base context must contain meaningful text")

        return v


class ChapterOutput(BaseModel):
    """
    Structured output for a generated chapter.
    Provides validation and type safety for chapter generation.
    """
    text: str = Field(min_length=100, description="The full chapter text content")
    word_count: int = Field(gt=0, description="Total word count of the chapter")
    scenes: List[str] = Field(default_factory=list, description="List of scene descriptions in the chapter")
    characters_present: List[str] = Field(default_factory=list, description="Characters appearing in this chapter")
    chapter_number: int = Field(ge=1, description="Chapter number in the story")
    chapter_title: Optional[str] = Field(None, max_length=100, description="Optional chapter title")

    @field_validator('text')
    @classmethod
    def validate_content(cls, v):
        """Validate chapter text quality"""
        v = v.strip()
        if len(v) < 100:
            raise ValueError("Chapter text must be at least 100 characters long")

        # Check for incomplete or placeholder content
        placeholder_indicators = ["TODO", "FIXME", "...", "TBD", "[PLACEHOLDER]"]
        for indicator in placeholder_indicators:
            if indicator in v.upper():
                raise ValueError(f"Chapter contains placeholder text: {indicator}")

        return v

    @field_validator('word_count')
    @classmethod
    def validate_word_count_consistency(cls, v, info):
        """Ensure word count matches actual text"""
        if 'text' in info.data:
            actual_word_count = len(info.data['text'].split())
            tolerance = getattr(Config, 'PYDANTIC_WORD_COUNT_TOLERANCE', 50)
            if abs(v - actual_word_count) > tolerance:
                raise ValueError(f"Word count {v} doesn't match actual word count {actual_word_count} (tolerance: ±{tolerance})")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChapterOutlineOutput(BaseModel):
    """
    Structured output for chapter outline generation.
    Specifically designed for outline data structure without requiring full chapter text.
    """
    chapter_number: int = Field(ge=1, description="Chapter number in the story")
    chapter_title: str = Field(min_length=5, description="Chapter title")

    # Scene structure matching CHAPTER_OUTLINE_PROMPT expectations
    scenes: List[str] = Field(description="Scene descriptions from outline")
    characters_present: List[str] = Field(default_factory=list, description="Characters appearing in this chapter")

    # Outline-specific fields (no minimum length like ChapterOutput.text)
    outline_summary: str = Field(min_length=20, description="Brief summary of chapter outline")
    estimated_word_count: Optional[int] = Field(None, gt=0, description="Estimated chapter word count")

    # Metadata for pipeline workflow
    setting: Optional[str] = Field(None, description="Primary setting for this chapter")
    main_conflict: Optional[str] = Field(None, description="Main conflict in this chapter")

    @field_validator('scenes')
    @classmethod
    def validate_scenes(cls, v):
        """Ensure each scene has meaningful content"""
        if len(v) < 3:
            raise ValueError("Chapter must have at least 3 scenes")

        for i, scene in enumerate(v):
            if len(scene.strip()) < 10:
                raise ValueError(f"Scene {i+1} description is too short (minimum 10 characters)")

        return v

    @field_validator('characters_present')
    @classmethod
    def validate_characters(cls, v):
        """Ensure character names are properly formatted"""
        for character in v:
            if len(character.strip()) < 2:
                raise ValueError("Character names must be at least 2 characters long")
        return v


class OutlineOutput(BaseModel):
    """
    Structured output for story outline.
    Provides validation for outline generation results.
    """
    title: str = Field(min_length=5, max_length=200, description="Story title")
    genre: Optional[str] = Field(None, description="Story genre")
    theme: Optional[str] = Field(None, description="Central theme of the story")
    chapters: List[str] = Field(min_length=1, description="List of chapter outlines")
    character_list: List[str] = Field(default_factory=list, description="List of main characters")
    setting: Optional[str] = Field(None, description="Story setting description")
    target_chapter_count: int = Field(gt=0, le=100, description="Target number of chapters")

    @field_validator('chapters')
    @classmethod
    def validate_chapters(cls, v):
        """Ensure each chapter has meaningful content"""
        if not v:
            raise ValueError("Must have at least one chapter")

        for i, chapter in enumerate(v):
            if len(chapter.strip()) < 20:
                raise ValueError(f"Chapter {i+1} outline is too short")

        return v

    @field_validator('character_list')
    @classmethod
    def validate_characters(cls, v):
        """Ensure character names are properly formatted"""
        for character in v:
            if len(character.strip()) < 2:
                raise ValueError("Character names must be at least 2 characters long")
        return v


class StoryElements(BaseModel):
    """
    Structured output for story elements extraction.
    """
    characters: Dict[str, str] = Field(default_factory=dict, description="Character names and their descriptions")
    locations: Dict[str, str] = Field(default_factory=dict, description="Locations and their descriptions")
    themes: List[str] = Field(default_factory=list, description="Main themes of the story")
    conflict: Optional[str] = Field(None, description="Central conflict of the story")
    resolution: Optional[str] = Field(None, description="Story resolution or ending direction")


class ChapterGenerationRequest(BaseModel):
    """
    Request model for chapter generation.
    Ensures all required context is provided.
    """
    chapter_number: int = Field(ge=1, description="Chapter number to generate")
    previous_chapter_summary: Optional[str] = Field(None, description="Summary of previous chapter")
    story_context: str = Field(min_length=10, description="Overall story context and elements")
    chapter_outline: str = Field(min_length=10, description="Specific outline for this chapter")
    word_count_target: int = Field(gt=0, le=10000, description="Target word count for this chapter")


class GenerationStats(BaseModel):
    """
    Statistics about the generation process.
    """
    tokens_used: int = Field(ge=0, description="Total tokens consumed")
    generation_time: float = Field(ge=0, description="Time taken to generate in seconds")
    retry_count: int = Field(ge=0, description="Number of retries attempted")
    model_used: str = Field(description="Which model was used for generation")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QualityMetrics(BaseModel):
    """
    Quality assessment metrics for generated content.
    """
    coherence_score: float = Field(ge=0, le=1, description="Text coherence rating")
    relevance_score: float = Field(ge=0, le=1, description="Relevance to prompt rating")
    completeness_score: float = Field(ge=0, le=1, description="Completeness of content")
    feedback: Optional[str] = Field(None, description="Qualitative feedback")
    revision_count: int = Field(default=0, ge=0, description="Number of revisions made")

    @field_validator('coherence_score', 'relevance_score', 'completeness_score')
    @classmethod
    def validate_scores(cls, v):
        """Ensure scores are reasonable"""
        if v < 0 or v > 1:
            raise ValueError("Scores must be between 0 and 1")
        return v


class SceneOutline(BaseModel):
    """
    Structure for scene-level chapter outlines.
    """
    scene_number: int = Field(ge=1, description="Scene number within chapter")
    setting: str = Field(min_length=1, description="Where the scene takes place")
    characters_present: List[str] = Field(description="Characters in this scene")
    action: str = Field(min_length=10, description="What happens in the scene")
    purpose: str = Field(min_length=5, description="Purpose of this scene in the story")
    estimated_word_count: int = Field(gt=0, description="Target words for this scene")

    @field_validator('setting')
    @classmethod
    def validate_setting(cls, v):
        """Ensure setting is not empty"""
        if not v.strip():
            raise ValueError("Setting cannot be empty")
        return v


class ChapterWithScenes(ChapterOutput):
    """
    Extended chapter model that includes scene-level structure.
    """
    scene_details: List[SceneOutline] = Field(description="Detailed scene breakdowns")  # Renamed to avoid conflict
    scene_transitions: List[str] = Field(default_factory=list, description="Transitions between scenes")


class TitleOutput(BaseModel):
    """
    Structured output for a chapter title.
    Simple model for title generation responses.
    """
    title: str = Field(min_length=1, max_length=100, description="The chapter title")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate title content"""
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")

        # Remove surrounding quotes if present
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1].strip()

        # Check for placeholder indicators
        placeholder_indicators = ["TODO", "FIXME", "TBD", "[PLACEHOLDER]"]
        for indicator in placeholder_indicators:
            if indicator in v.upper():
                raise ValueError(f"Title contains placeholder text: {indicator}")

        return v


class ReasoningOutput(BaseModel):
    """
    Structured output for reasoning chain responses.
    Provides validation for AI-generated reasoning content.
    """
    reasoning: str = Field(min_length=10, max_length=2000, description="The reasoning text generated by the AI")

    @field_validator('reasoning')
    @classmethod
    def validate_reasoning(cls, v):
        """Validate reasoning has meaningful content"""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Reasoning must be at least 10 characters long")

        # Check for empty placeholders or minimal content
        placeholder_indicators = ["TODO", "FIXME", "...", "TBD", "[PLACEHOLDER]", "Not applicable", "N/A"]
        if any(indicator.lower() in v.lower() for indicator in placeholder_indicators):
            raise ValueError("Reasoning contains placeholder text")

        # Ensure it contains some actual content
        if not any(c.isalnum() for c in v):
            raise ValueError("Reasoning must contain meaningful text")

        return v

# ==============================================================================
# Evaluation Models (DRY base class pattern)
# ==============================================================================

class EvaluationOutputBase(BaseModel):
    """
    BASE CLASS for evaluation outputs - DRY principle.
    Used by both OutlineEvaluationOutput and ChapterEvaluationOutput.
    """
    score: int = Field(ge=0, le=10, description="Evaluation score 0-10")
    strengths: str = Field(min_length=10, description="What works well")
    weaknesses: str = Field(min_length=10, description="What needs improvement")
    recommendations: str = Field(min_length=10, description="Specific recommendations")

    @field_validator('strengths', 'weaknesses', 'recommendations')
    @classmethod
    def validate_min_content(cls, v):
        """Shared validator for all feedback fields"""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Feedback must be at least 10 characters")
        return v


class OutlineEvaluationOutput(EvaluationOutputBase):
    """
    Evaluation output for outlines.
    Inherits all fields from EvaluationOutputBase (DRY).
    """
    pass  # All fields inherited from base class


class ChapterEvaluationOutput(EvaluationOutputBase):
    """
    Evaluation output for chapters.
    Inherits all fields from EvaluationOutputBase (DRY).
    """
    pass  # All fields inherited from base class


# ==============================================================================
# Story Metadata Models
# ==============================================================================

class StoryInfoOutput(BaseModel):
    """Structured output for story metadata extraction."""
    title: str = Field(min_length=1, description="Story title")
    genre: str = Field(min_length=1, description="Story genre")
    summary: str = Field(min_length=20, description="Story summary")
    themes: List[str] = Field(description="Main themes")
    characters: List[str] = Field(description="Main characters")

    @field_validator('summary')
    @classmethod
    def validate_summary(cls, v):
        """Validate summary has meaningful content"""
        v = v.strip()
        if len(v) < 20:
            raise ValueError("Summary must be at least 20 characters")
        return v


# ==============================================================================
# Scene Validation Models
# ==============================================================================

class SceneValidationOutput(BaseModel):
    """Structured output for scene validation results."""
    is_valid: bool = Field(description="Whether scene structure is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors found")
    scene_count: int = Field(ge=0, description="Number of scenes detected")


# ==============================================================================
# Review Models
# ==============================================================================

class ReviewOutput(BaseModel):
    """Structured output for outline/chapter review feedback."""
    feedback: str = Field(min_length=10, description="Detailed feedback")
    suggestions: List[str] = Field(description="Specific suggestions for improvement")
    rating: int = Field(ge=0, le=10, description="Quality rating 0-10")

    @field_validator('feedback')
    @classmethod
    def validate_feedback(cls, v):
        """Validate feedback has meaningful content"""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Feedback must be at least 10 characters")
        return v


# Registry of all available models for dynamic loading
MODEL_REGISTRY = {
    'BaseContext': BaseContext,
    'ChapterOutput': ChapterOutput,
    'ChapterOutlineOutput': ChapterOutlineOutput,
    'OutlineOutput': OutlineOutput,
    'StoryElements': StoryElements,
    'ChapterGenerationRequest': ChapterGenerationRequest,
    'GenerationStats': GenerationStats,
    'QualityMetrics': QualityMetrics,
    'SceneOutline': SceneOutline,
    'ChapterWithScenes': ChapterWithScenes,
    'TitleOutput': TitleOutput,
    'ReasoningOutput': ReasoningOutput,
    # New models for SafeGenerateJSON -> SafeGeneratePydantic migration
    'OutlineEvaluationOutput': OutlineEvaluationOutput,
    'ChapterEvaluationOutput': ChapterEvaluationOutput,
    'StoryInfoOutput': StoryInfoOutput,
    'SceneValidationOutput': SceneValidationOutput,
    'ReviewOutput': ReviewOutput,
}


def get_model(model_name: str) -> type:
    """
    Get a Pydantic model by name from the registry.

    Args:
        model_name (str): Name of the model to retrieve

    Returns:
        type: The Pydantic model class

    Raises:
        KeyError: If model_name is not found in registry
    """
    if model_name not in MODEL_REGISTRY:
        available = ', '.join(MODEL_REGISTRY.keys())
        raise KeyError(f"Model '{model_name}' not found. Available: {available}")
    return MODEL_REGISTRY[model_name]