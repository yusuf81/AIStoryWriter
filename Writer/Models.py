# Writer/Models.py - Pydantic data models for structured output
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import Writer.Config as Config


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
    scenes: List[SceneOutline] = Field(description="Detailed scene breakdowns")
    scene_transitions: List[str] = Field(default_factory=list, description="Transitions between scenes")


# Registry of all available models for dynamic loading
MODEL_REGISTRY = {
    'ChapterOutput': ChapterOutput,
    'OutlineOutput': OutlineOutput,
    'StoryElements': StoryElements,
    'ChapterGenerationRequest': ChapterGenerationRequest,
    'GenerationStats': GenerationStats,
    'QualityMetrics': QualityMetrics,
    'SceneOutline': SceneOutline,
    'ChapterWithScenes': ChapterWithScenes,
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