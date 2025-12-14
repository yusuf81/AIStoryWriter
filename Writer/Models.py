# Writer/Models.py - Pydantic data models for structured output
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Union
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

    # Scene structure supporting both strings and enhanced scene objects
    scenes: List[Union[str, 'EnhancedSceneOutline']] = Field(description="Scene descriptions or structured scene data")
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
        if len(v) < 1:  # Allow flexible scene count when using structured scenes
            raise ValueError("Chapter must have at least 1 scene")

        for i, scene in enumerate(v):
            if isinstance(scene, str):
                # String scene validation
                if len(scene.strip()) < 10:
                    raise ValueError(f"Scene {i+1} description is too short (minimum 10 characters)")
            elif not isinstance(scene, str):
                # Enhanced scene validation - check if it has meaningful content
                meaningful_fields = [
                    field for field in [scene.title, scene.characters_and_setting,
                                        scene.conflict_and_tone, scene.key_events,
                                        scene.literary_devices, scene.resolution]
                    if field and field.strip()
                ]
                if not meaningful_fields:
                    raise ValueError(f"Enhanced scene {i+1} must have at least one meaningful field")

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
    character_details: Optional[Dict[str, str]] = Field(None, description="Extracted character descriptions from chapters")
    setting: Optional[Dict[str, str]] = Field(None, description="Story setting details with time, location, culture, mood")
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


class CharacterDetail(BaseModel):
    """
    Detailed character information to match prompt structure.
    Supports both English and Indonesian character formats.
    """
    name: str = Field(min_length=2, max_length=100, description="Character name")
    physical_description: Optional[str] = Field(None, description="Physical appearance and characteristics")
    personality: Optional[str] = Field(None, description="Personality traits and behavioral patterns")
    background: Optional[str] = Field(None, description="Character history and background story")
    motivation: Optional[str] = Field(None, description="Character motivation, goals, or role in story")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Ensure character name is meaningful"""
        if len(v.strip()) < 2:
            raise ValueError("Character name must be at least 2 characters long")
        return v.strip()


class StoryElements(BaseModel):
    """
    Structured output for story elements extraction.
    Enhanced to capture all fields requested by GENERATE_STORY_ELEMENTS prompt.
    """
    # New required fields from prompt analysis
    title: str = Field(min_length=5, max_length=200, description="Story title")
    genre: str = Field(min_length=2, description="Story genre category")
    themes: List[str] = Field(min_length=1, description="Central themes of the story")
    characters: Dict[str, List[CharacterDetail]] = Field(default_factory=dict, description="Character lists by type with detailed information")

    # Optional fields for enhanced story structure
    pacing: Optional[str] = Field(None, description="Story pacing speed (e.g., slow, moderate, fast)")
    style: Optional[str] = Field(None, description="Language style description")
    plot_structure: Optional[Dict[str, str]] = Field(None, description="Plot elements (exposition, rising action, climax, falling_action, resolution)")
    settings: Dict[str, Dict[str, str]] = Field(default_factory=dict, description="Setting details with time, location, culture, mood")
    conflict: Optional[str] = Field(None, description="Central conflict of the story")
    symbolism: Optional[List[Dict[str, str]]] = Field(None, description="Symbols and their meanings")
    resolution: Optional[str] = Field(None, description="Story resolution or ending direction")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate title has meaningful content"""
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Title must be at least 5 characters long")
        if len(v) > 200:
            raise ValueError("Title must be at most 200 characters long")
        return v

    @field_validator('genre')
    @classmethod
    def validate_genre(cls, v):
        """Validate genre has meaningful content"""
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Genre must be at least 2 characters long")
        return v

    @field_validator('themes')
    @classmethod
    def validate_themes(cls, v):
        """Ensure themes list has meaningful content"""
        if not v:
            raise ValueError("Must have at least 1 theme")
        for theme in v:
            if not theme.strip():
                raise ValueError("Theme cannot be empty")
        return v

    @field_validator('characters')
    @classmethod
    def validate_characters(cls, v):
        """Ensure character lists are properly formatted"""
        for character_type, character_list in v.items():
            if not character_list:
                raise ValueError(f"Character list for {character_type} cannot be empty")
            for i, character in enumerate(character_list):
                if not character.name.strip():
                    raise ValueError(f"Character name cannot be empty in {character_type}[{i}]")
        return v

    @field_validator('plot_structure')
    @classmethod
    def validate_plot_structure(cls, v):
        """Validate plot structure has meaningful values if provided"""
        if v is not None:
            for key, value in v.items():
                if not value.strip():
                    raise ValueError(f"Plot structure element '{key}' cannot be empty")
        return v

    @field_validator('settings')
    @classmethod
    def validate_settings(cls, v):
        """Validate settings have proper structure if provided"""
        if v is not None:
            for setting_name, setting_details in v.items():
                if not isinstance(setting_details, dict):
                    raise ValueError(f"Setting '{setting_name}' must be a dictionary")
                for detail_key, detail_value in setting_details.items():
                    if not isinstance(detail_value, str) or not detail_value.strip():
                        raise ValueError(f"Setting detail '{detail_key}' for '{setting_name}' must be non-empty string")
        return v

    @field_validator('symbolism')
    @classmethod
    def validate_symbolism(cls, v):
        """Validate symbolism entries if provided"""
        if v is not None:
            for symbol_entry in v:
                if not isinstance(symbol_entry, dict):
                    raise ValueError("Each symbolism entry must be a dictionary")
                if 'symbol' not in symbol_entry or 'meaning' not in symbol_entry:
                    raise ValueError("Symbolism entries must have 'symbol' and 'meaning' fields")
                if not symbol_entry['symbol'].strip() or not symbol_entry['meaning'].strip():
                    raise ValueError("Symbol and meaning cannot be empty")
        return v


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


class SceneOutlineList(BaseModel):
    """Wrapper model for multiple SceneOutline objects following SceneListSchema pattern"""
    scenes: List[SceneOutline] = Field(description="List of scenes for chapter outline conversion")

    @field_validator('scenes')
    @classmethod
    def validate_scenes(cls, v):
        """Ensure at least one scene is provided"""
        if not v:
            raise ValueError("At least one scene must be provided")
        return v


class EnhancedSceneOutline(BaseModel):
    """
    Enhanced scene structure matching prompt expectations.
    Supports the detailed scene fields requested by Indonesian and English prompts.
    """
    title: Optional[str] = Field(None, max_length=200, description="Brief scene title")
    characters_and_setting: Optional[str] = Field(None, description="Characters present and setting details")
    conflict_and_tone: Optional[str] = Field(None, description="Scene conflict and emotional tone")
    key_events: Optional[str] = Field(None, description="Important plot points and events")
    literary_devices: Optional[str] = Field(None, description="Literary techniques used")
    resolution: Optional[str] = Field(None, description="Scene conclusion and lead-in")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate title content if provided"""
        if v is not None:
            v = v.strip()
            if len(v) > 200:
                raise ValueError("Scene title cannot exceed 200 characters")
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

class EnhancedSuggestion(BaseModel):
    """Structured suggestion with detailed criteria from critique prompts."""
    description: str = Field(description="Main suggestion detail (maps to Indonesian 'detail')")
    pacing: Optional[str] = Field(None, description="Pacing-related suggestion (maps to Indonesian 'laju')")
    flow: Optional[str] = Field(None, description="Flow/narrative suggestion (maps to Indonesian 'alur')")
    other_criteria: Optional[Dict[str, str]] = Field(None, description="Additional criteria from critique prompts")


class ReviewOutput(BaseModel):
    """Structured output for outline/chapter review feedback with flexible suggestion handling."""
    feedback: str = Field(min_length=10, description="Detailed feedback")
    suggestions: Optional[List[Union[str, 'EnhancedSuggestion']]] = Field(None, description="Specific suggestions for improvement (structured or simple)")
    rating: int = Field(ge=0, le=10, description="Quality rating 0-10")

    @field_validator('suggestions', mode='before')
    @classmethod
    def normalize_suggestions(cls, v):
        """Convert structured Indonesian suggestions to EnhancedSuggestion objects."""
        if isinstance(v, list):
            normalized = []
            for item in v:
                if isinstance(item, str):
                    # Keep string suggestions as-is
                    normalized.append(item)
                elif isinstance(item, dict):
                    # Map Indonesian fields to English EnhancedSuggestion
                    suggestion_data = {
                        'description': item.get('detail', ''),
                        'pacing': item.get('laju'),
                        'flow': item.get('alur'),
                        'other_criteria': {
                            k: v for k, v in item.items()
                            if k not in ['detail', 'laju', 'alur']
                        }
                    }
                    # Remove None values from other_criteria if empty
                    if not suggestion_data['other_criteria']:
                        suggestion_data.pop('other_criteria', None)
                    normalized.append(suggestion_data)
            return normalized
        return v

    @field_validator('suggestions')
    @classmethod
    def extract_suggestions_from_feedback(cls, v, info):
        """Extract suggestions from feedback if not provided separately"""
        if v is None and 'feedback' in info.data:
            feedback = info.data['feedback']
            # Try to extract suggestions embedded in feedback
            suggestions = []

            # Look for numbered lists
            import re
            numbered_suggestions = re.findall(r'(\d+[.)\s]+[^\n]+)', feedback)
            for suggestion in numbered_suggestions:
                # Clean up the suggestion
                clean_suggestion = re.sub(r'^\d+[.)\s]+', '', suggestion).strip()
                if clean_suggestion:
                    suggestions.append(clean_suggestion)

            # Look for bullet points
            bullet_suggestions = re.findall(r'[•\-\*]\s+([^\n]+)', feedback)
            for suggestion in bullet_suggestions:
                clean_suggestion = suggestion.strip()
                if clean_suggestion:
                    suggestions.append(clean_suggestion)

            # If no structured suggestions found, look for suggestion keywords
            if not suggestions:
                suggestion_patterns = [
                    r'(?:suggest|recommend|could|should|might)\s+([^.!?]*[.!?])',
                    r'(?:consider|try|add|include|use)[^.!?]*[.!?]',
                    r'(?:improve|enhance|better)[^.!?]*[.!?]'
                ]

                for pattern in suggestion_patterns:
                    matches = re.findall(pattern, feedback, re.IGNORECASE)
                    for match in matches:
                        clean_suggestion = match.strip()
                        if clean_suggestion and len(clean_suggestion) > 10:
                            suggestions.append(clean_suggestion)

            return suggestions if suggestions else None

        return v

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
    'CharacterDetail': CharacterDetail,
    'EnhancedSceneOutline': EnhancedSceneOutline,
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
