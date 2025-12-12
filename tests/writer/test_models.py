# tests/writer/test_models.py
import os
import pytest
from datetime import datetime
from pydantic import ValidationError

# Import the module we're testing
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class TestChapterOutput:
    """Test suite for ChapterOutput following TDD London School approach"""

    def test_valid_chapter_output_creation(self):
        """Test creating a valid ChapterOutput"""
        from Writer.Models import ChapterOutput

        chapter_text = "Alice walked into the dark forest, her blue eyes scanning the shadows. She knew the artifact was somewhere near, hidden in the ancient ruins. For years she had trained for this moment, learning the ancient magic that would help her defeat the darkness."

        chapter = ChapterOutput(
            text=chapter_text,
            word_count=len(chapter_text.split()),
            scenes=["Alice enters the forest", "Alice looks for the artifact"],
            characters_present=["Alice"],
            chapter_number=1,
            chapter_title="The Quest Begins"
        )

        assert chapter.text == chapter_text
        assert chapter.word_count == len(chapter_text.split())
        assert chapter.chapter_number == 1
        assert chapter.chapter_title == "The Quest Begins"
        assert "Alice" in chapter.characters_present
        assert len(chapter.scenes) == 2

    def test_minimum_valid_chapter_output(self):
        """Test creating ChapterOutput with minimum required fields"""
        from Writer.Models import ChapterOutput

        chapter_text = "This is a test chapter with sufficient text to meet the minimum requirement for length. It needs to be at least one hundred characters long to pass validation, so I'm adding more detail here to ensure it meets the criteria for testing purposes."

        chapter = ChapterOutput(
            text=chapter_text,
            word_count=len(chapter_text.split()),
            scenes=[],
            characters_present=[],
            chapter_number=1
        )

        assert chapter.text == chapter_text
        assert chapter.word_count == len(chapter_text.split())
        assert chapter.chapter_number == 1
        assert chapter.scenes == []
        assert chapter.characters_present == []

    def test_invalid_text_too_short(self):
        """Test that text shorter than 100 characters fails validation"""
        from Writer.Models import ChapterOutput

        with pytest.raises(ValidationError) as exc_info:
            ChapterOutput(
                text="Too short",
                word_count=2,
                scenes=[],
                characters_present=[],
                chapter_number=1
            )

        assert "at least 100 characters" in str(exc_info.value)

    def test_invalid_text_with_placeholder(self):
        """Test that text containing placeholders fails validation"""
        from Writer.Models import ChapterOutput

        chapter_text = "Alice walked through the forest TODO add more content here. Her blue eyes scanned the area for any signs of the artifact."

        with pytest.raises(ValidationError) as exc_info:
            ChapterOutput(
                text=chapter_text,
                word_count=len(chapter_text.split()),
                scenes=[],
                characters_present=["Alice"],
                chapter_number=1
            )

        assert "placeholder text" in str(exc_info.value).lower()
        assert "TODO" in str(exc_info.value)

    def test_invalid_word_count_too_low(self):
        """Test that word_count less than or equal to 0 fails validation"""
        from Writer.Models import ChapterOutput

        with pytest.raises(ValidationError) as exc_info:
            ChapterOutput(
                text="Some valid chapter text that meets the minimum requirements.",
                word_count=0,
                scenes=[],
                characters_present=[],
                chapter_number=1
            )

        assert "greater than 0" in str(exc_info.value)

    def test_invalid_word_count_mismatch(self):
        """Test that word_count mismatching actual text fails validation"""
        from Writer.Models import ChapterOutput

        chapter_text = "Alice walked into the forest. Her blue eyes searched for danger. She needed to find the ancient artifact before the Dark Lord discovered its location. The fate of the kingdom rested on her shoulders."

        with pytest.raises(ValidationError) as exc_info:
            ChapterOutput(
                text=chapter_text,
                word_count=100,  # Wrong word count
                scenes=[],
                characters_present=["Alice"],
                chapter_number=1
            )

        assert "doesn't match actual word count" in str(exc_info.value)

    def test_invalid_chapter_number(self):
        """Test that invalid chapter numbers fail validation"""
        from Writer.Models import ChapterOutput

        chapter_text = "This is a valid chapter text that meets all the requirements for minimum length and content quality."

        # Test chapter number less than 1
        with pytest.raises(ValidationError):
            ChapterOutput(
                text=chapter_text,
                word_count=len(chapter_text.split()),
                scenes=[],
                characters_present=[],
                chapter_number=0
            )

    def test_chapter_title_too_long(self):
        """Test that chapter title exceeds maximum length fails validation"""
        from Writer.Models import ChapterOutput

        chapter_text = "Alice's journey continues as she explores the ancient ruins, her blue eyes searching for clues about the artifact's location. The darkness seemed to deepen with every step she took."

        long_title = "A" * 101  # 101 characters

        with pytest.raises(ValidationError):
            ChapterOutput(
                text=chapter_text,
                word_count=len(chapter_text.split()),
                scenes=["Exploring ruins"],
                characters_present=["Alice"],
                chapter_number=1,
                chapter_title=long_title
            )


class TestOutlineOutput:
    """Test suite for OutlineOutput following TDD London School approach"""

    def test_valid_outline_output_creation(self):
        """Test creating a valid OutlineOutput"""
        from Writer.Models import OutlineOutput

        outline = OutlineOutput(
            title="The Knight's Quest",
            genre="Fantasy",
            theme="Courage vs. Darkness",
            chapters=[
                "Chapter 1: Alice receives her quest to find the ancient artifact",
                "Chapter 2: Alice enters the Dark Forest, facing dangerous creatures",
                "Chapter 3: Alice discovers the hidden temple where the artifact is located"
            ],
            character_list=["Alice", "Merlin", "Dark Lord"],
            setting="Medieval kingdom of Eldoria",
            target_chapter_count=10
        )

        assert outline.title == "The Knight's Quest"
        assert outline.genre == "Fantasy"
        assert outline.theme == "Courage vs. Darkness"
        assert len(outline.chapters) == 3
        assert outline.target_chapter_count == 10
        assert "Alice" in outline.character_list

    def test_minimum_valid_outline_output(self):
        """Test creating OutlineOutput with minimum required fields"""
        from Writer.Models import OutlineOutput

        outline = OutlineOutput(
            title="Test Story",
            chapters=["Chapter 1: The beginning of an adventure where our hero discovers their destiny."],
            target_chapter_count=1
        )

        assert outline.title == "Test Story"
        assert len(outline.chapters) == 1
        assert outline.target_chapter_count == 1
        assert outline.genre is None
        assert outline.character_list == []

    def test_invalid_title_too_short(self):
        """Test that title shorter than 5 characters fails validation"""
        from Writer.Models import OutlineOutput

        with pytest.raises(ValidationError) as exc_info:
            OutlineOutput(
                title="T",
                chapters=["Chapter 1: Some content"],
                target_chapter_count=1
            )

        assert "at least 5 characters" in str(exc_info.value)

    def test_invalid_title_too_long(self):
        """Test that title longer than 200 characters fails validation"""
        from Writer.Models import OutlineOutput

        long_title = "A" * 201  # 201 characters

        with pytest.raises(ValidationError):
            OutlineOutput(
                title=long_title,
                chapters=["Chapter 1: Some content"],
                target_chapter_count=1
            )

    def test_invalid_empty_chapters(self):
        """Test that empty chapters list fails validation"""
        from Writer.Models import OutlineOutput

        with pytest.raises(ValidationError):
            OutlineOutput(
                title="Test Story",
                chapters=[],
                target_chapter_count=1
            )

    def test_invalid_short_chapter(self):
        """Test that chapter outline too short fails validation"""
        from Writer.Models import OutlineOutput

        with pytest.raises(ValidationError) as exc_info:
            OutlineOutput(
                title="Test Story",
                chapters=["Short"],
                target_chapter_count=1
            )

        assert "is too short" in str(exc_info.value)

    def test_invalid_character_name(self):
        """Test that character names too short fail validation"""
        from Writer.Models import OutlineOutput

        with pytest.raises(ValidationError):
            OutlineOutput(
                title="Test Story",
                chapters=["Chapter 1: Valid chapter outline"],
                character_list=["A"],
                target_chapter_count=1
            )

    def test_invalid_target_chapter_count(self):
        """Test that invalid chapter counts fail validation"""
        from Writer.Models import OutlineOutput

        # Test 0 chapters
        with pytest.raises(ValidationError):
            OutlineOutput(
                title="Test Story",
                chapters=["Chapter 1: Content"],
                target_chapter_count=0
            )

        # Test too many chapters
        with pytest.raises(ValidationError):
            OutlineOutput(
                title="Test Story",
                chapters=["Chapter 1: Content"],
                target_chapter_count=101
            )


class TestStoryElements:
    """Test suite for StoryElements following TDD London School approach"""

    def test_valid_story_elements_creation(self):
        """Test creating valid StoryElements"""
        from Writer.Models import StoryElements

        elements = StoryElements(
            characters={
                "Alice": "A brave knight with blue eyes, searching for the ancient artifact",
                "Merlin": "A wise old wizard who guides Alice on her quest"
            },
            locations={
                "Dark Forest": "A dangerous forest filled with magical creatures",
                "Eldoria": "The peaceful kingdom where Alice lives"
            },
            themes=["courage", "friendship", "good vs evil"],
            conflict="Alice must find the artifact before the Dark Lord does",
            resolution="Alice defeats the Dark Lord and restores peace to Eldoria"
        )

        assert "Alice" in elements.characters
        assert elements.characters["Alice"] == "A brave knight with blue eyes, searching for the ancient artifact"
        assert len(elements.themes) == 3
        assert elements.conflict == "Alice must find the artifact before the Dark Lord does"

    def test_minimum_valid_story_elements(self):
        """Test creating StoryElements with minimum required fields"""
        from Writer.Models import StoryElements

        elements = StoryElements()

        assert elements.characters == {}
        assert elements.locations == {}
        assert elements.themes == []
        assert elements.conflict is None
        assert elements.resolution is None


class TestGenerationStats:
    """Test suite for GenerationStats following TDD London School approach"""

    def test_valid_generation_stats_creation(self):
        """Test creating valid GenerationStats"""
        from Writer.Models import GenerationStats

        stats = GenerationStats(
            tokens_used=1500,
            generation_time=5.2,
            retry_count=2,
            model_used="gpt-4"
        )

        assert stats.tokens_used == 1500
        assert stats.generation_time == 5.2
        assert stats.retry_count == 2
        assert stats.model_used == "gpt-4"
        assert isinstance(stats.timestamp, datetime)

    def test_invalid_negative_values(self):
        """Test that negative values fail validation"""
        from Writer.Models import GenerationStats

        # Test negative tokens
        with pytest.raises(ValidationError):
            GenerationStats(
                tokens_used=-1,
                generation_time=5.2,
                retry_count=0,
                model_used="gpt-4"
            )

        # Test negative time
        with pytest.raises(ValidationError):
            GenerationStats(
                tokens_used=100,
                generation_time=-1.0,
                retry_count=0,
                model_used="gpt-4"
            )


class TestQualityMetrics:
    """Test suite for QualityMetrics following TDD London School approach"""

    def test_valid_quality_metrics_creation(self):
        """Test creating valid QualityMetrics"""
        from Writer.Models import QualityMetrics

        metrics = QualityMetrics(
            coherence_score=0.85,
            relevance_score=0.90,
            completeness_score=0.75,
            feedback="Good character development",
            revision_count=2
        )

        assert metrics.coherence_score == 0.85
        assert metrics.relevance_score == 0.90
        assert metrics.completeness_score == 0.75
        assert metrics.feedback == "Good character development"
        assert metrics.revision_count == 2

    def test_valid_score_bounds(self):
        """Test that scores within valid bounds pass"""
        from Writer.Models import QualityMetrics

        # Test minimum scores
        metrics_min = QualityMetrics(
            coherence_score=0.0,
            relevance_score=0.0,
            completeness_score=0.0
        )
        assert metrics_min.coherence_score == 0.0

        # Test maximum scores
        metrics_max = QualityMetrics(
            coherence_score=1.0,
            relevance_score=1.0,
            completeness_score=1.0
        )
        assert metrics_max.coherence_score == 1.0

    def test_invalid_scores(self):
        """Test that scores outside 0-1 range fail validation"""
        from Writer.Models import QualityMetrics

        # Test negative score
        with pytest.raises(ValidationError):
            QualityMetrics(
                coherence_score=-0.1,
                relevance_score=0.5,
                completeness_score=0.5
            )

        # Test score > 1
        with pytest.raises(ValidationError):
            QualityMetrics(
                coherence_score=0.5,
                relevance_score=1.1,
                completeness_score=0.5
            )

    def test_minimum_valid_metrics(self):
        """Test creating QualityMetrics with minimum required fields"""
        from Writer.Models import QualityMetrics

        metrics = QualityMetrics(
            coherence_score=0.5,
            relevance_score=0.5,
            completeness_score=0.5
        )

        assert metrics.feedback is None
        assert metrics.revision_count == 0


class TestSceneOutline:
    """Test suite for SceneOutline following TDD London School approach"""

    def test_valid_scene_outline(self):
        """Test creating valid SceneOutline"""
        from Writer.Models import SceneOutline

        scene = SceneOutline(
            scene_number=1,
            setting="The Dark Forest at midnight",
            characters_present=["Alice", "Bob"],
            action="Alice finds a glowing artifact hidden behind an ancient tree. Bob warns her about the curse.",
            purpose="Introduce the main quest and establish the relationship between Alice and Bob",
            estimated_word_count=150
        )

        assert scene.scene_number == 1
        assert "Dark Forest" in scene.setting
        assert "Alice" in scene.characters_present
        assert "artifact" in scene.action
        assert scene.estimated_word_count == 150

    def test_invalid_scene_number(self):
        """Test that invalid scene numbers fail validation"""
        from Writer.Models import SceneOutline

        with pytest.raises(ValidationError):
            SceneOutline(
                scene_number=0,
                setting="Forest",
                characters_present=["Alice"],
                action="Something happens",
                purpose="To advance plot",
                estimated_word_count=100
            )

    def test_invalid_empty_fields(self):
        """Test that empty required fields fail validation"""
        from Writer.Models import SceneOutline

        with pytest.raises(ValidationError):
            SceneOutline(
                scene_number=1,
                setting="",  # Empty setting
                characters_present=["Alice"],
                action="Action happens",
                purpose="Purpose",
                estimated_word_count=100
            )


class TestModelRegistry:
    """Test suite for model registry functionality"""

    def test_get_existing_model(self):
        """Test retrieving existing models from registry"""
        from Writer.Models import get_model, ChapterOutput

        chapter_model = get_model('ChapterOutput')
        assert chapter_model == ChapterOutput

        outline_model = get_model('OutlineOutput')
        assert outline_model.__name__ == 'OutlineOutput'

    def test_get_nonexistent_model(self):
        """Test that retrieving non-existent model raises error"""
        from Writer.Models import get_model

        with pytest.raises(KeyError) as exc_info:
            get_model('NonExistentModel')

        assert "'NonExistentModel' not found" in str(exc_info.value)
        assert "Available:" in str(exc_info.value)

    def test_all_models_in_registry(self):
        """Test that all expected models are in registry"""
        from Writer.Models import MODEL_REGISTRY

        expected_models = [
            'ChapterOutput', 'OutlineOutput', 'StoryElements',
            'ChapterGenerationRequest', 'GenerationStats',
            'QualityMetrics', 'SceneOutline', 'ChapterWithScenes'
        ]

        for model_name in expected_models:
            assert model_name in MODEL_REGISTRY, f"{model_name} not found in MODEL_REGISTRY"