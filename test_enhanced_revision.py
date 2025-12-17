"""
Enhanced chapter revision system with quality scoring and best version selection.

This module extends the current system to:
1. Track quality scores for each iteration
2. Store all versions with their scores
3. Return the best version instead of just the last one
"""

from dataclasses import dataclass
from typing import List, Optional
from Writer.Models import ChapterOutput


@dataclass
class ChapterVersion:
    """Container for tracking chapter generation attempts"""
    iteration: int
    chapter_content: str
    did_follow_outline: bool
    quality_score: Optional[float] = None
    suggestions: str = ""
    word_count: int = 0

    def __post_init__(self):
        """Calculate word count if not provided"""
        if self.word_count == 0:
            self.word_count = len(self.chapter_content.split())


class ChapterRevisionTracker:
    """
    Enhanced version of ChapterGenerator that tracks quality and selects best version.

    Instead of always returning the last attempt, this returns the best version
    based on multiple quality metrics.
    """

    def __init__(self, max_revisions: int = 3):
        self.max_revisions = max_revisions
        self.versions: List[ChapterVersion] = []

    def add_version(self, iteration: int, content: str, did_follow_outline: bool,
                   suggestions: str = "", quality_score: Optional[float] = None):
        """Add a new version to track"""
        version = ChapterVersion(
            iteration=iteration,
            chapter_content=content,
            did_follow_outline=did_follow_outline,
            suggestions=suggestions,
            quality_score=quality_score
        )
        self.versions.append(version)

    def get_best_version(self) -> Optional[ChapterVersion]:
        """
        Get the best version based on priority criteria:

        Priority 1: DidFollowOutline = true (any score)
        Priority 2: Highest QualityScore
        Priority 3: Lowest iteration (earlier success)
        """
        if not self.versions:
            return None

        # Filter by outline compliance first
        outline_compliant = [v for v in self.versions if v.did_follow_outline]

        if outline_compliant:
            # Among outline-compliant versions, pick highest score
            best_scoring = outline_compliant
            # Could extend with actual scores here
            best_scoring.sort(key=lambda x: x.iteration)  # Earlier preference
            return best_scoring[0]
        else:
            # If none are outline-compliant, pick by secondary criteria
            # Could implement scoring here in future
            return max(self.versions, key=lambda x: (x.word_count, -x.iteration))

    def get_quality_score(self, content: str, outline: str) -> float:
        """
        Generate quality score using LLM evaluation.

        Returns:
            float: Quality score 0-100
        """
        # This would need to be implemented with actual LLM call
        # For now, returns a placeholder score based on content length
        base_score = min(len(content.split()) / 10, 50)  # Basic length scoring

        # Future: Add actual LLM evaluation for:
        # - Outline adherence score (0-40)
        # - Content quality score (0-30)
        # - Character consistency score (0-20)
        # - Plot coherence score (0-10)

        return base_score


# Enhanced SummaryComparisonSchema with scoring
class EnhancedSummaryComparisonSchema(BaseModel):
    """Extended version with quality scoring"""
    Suggestions: str
    DidFollowOutline: bool
    QualityScore: Optional[float] = Field(default=None, ge=0, le=100,
                                         description="Quality score 0-100")

    @field_validator('QualityScore')
    @classmethod
    def validate_score(cls, v):
        """Validate quality score within valid range"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Quality score must be between 0 and 100")
        return v


# Integration concept for ChapterGenerator
def enhanced_revision_loop(current_logic):
    """
    Enhanced revision logic that could replace current ChapterGenerator loops.

    Usage:
        tracker = ChapterRevisionTracker(max_revisions=3)

        for iteration in range(1, max_revisions + 1):
            # Generate chapter
            content = generate_chapter()

            # Check quality (could add quality scoring here)
            did_follow, suggestions = LLMSummaryCheck(...)

            # Calculate quality score (new feature)
            quality_score = tracker.get_quality_score(content, outline) if not did_follow else 85.0

            # Track this version
            tracker.add_version(iteration, content, did_follow, suggestions, quality_score)

            if did_follow:
                break

        # Return BEST version, not just last
        return tracker.get_best_version().chapter_content
    """