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
            chapter_number=1,
            chapter_title=None
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
                chapter_number=1,
                chapter_title=None
            )

        assert "at least 100 characters" in str(exc_info.value)

    def test_invalid_text_with_placeholder(self):
        """Test that text containing TODO/FIXME placeholders fails validation

        Note: Ellipsis (...) is now allowed as valid punctuation
        """
        from Writer.Models import ChapterOutput

        chapter_text = "Alice walked through the forest TODO add more content here. Her blue eyes scanned the area for any signs of the artifact."

        with pytest.raises(ValidationError) as exc_info:
            ChapterOutput(
                text=chapter_text,
                word_count=len(chapter_text.split()),
                scenes=[],
                characters_present=["Alice"],
                chapter_number=1,
                chapter_title=None
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
                chapter_number=1,
                chapter_title=None
            )

        assert "greater than 0" in str(exc_info.value)

    def test_invalid_word_count_mismatch(self):
        """Test that word_count mismatching actual text fails validation"""
        from Writer.Models import ChapterOutput

        chapter_text = "Alice walked into the forest. Her blue eyes searched for danger. She needed to find the ancient artifact before the Dark Lord discovered its location. The fate of the kingdom rested on her shoulders."

        with pytest.raises(ValidationError) as exc_info:
            ChapterOutput(
                text=chapter_text,
                word_count=150,  # Outside ±100 tolerance (actual: 34)
                scenes=[],
                characters_present=["Alice"],
                chapter_number=1,
                chapter_title=None
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
                chapter_number=0,
                chapter_title=None
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


class TestPlaceholderValidationFix:
    """Test that ellipsis is allowed in content (not treated as placeholder)"""

    def test_chapter_allows_ellipsis_in_dialogue(self):
        """GREEN: Chapter text with ellipsis in dialogue is valid"""
        from Writer.Models import ChapterOutput

        chapter_text = '"I don\'t know..." she whispered, her voice trailing off into the darkness. The room fell silent. Only the sound of her heartbeat echoed in the stillness of the night.'

        chapter = ChapterOutput(
            text=chapter_text,
            word_count=len(chapter_text.split()),
            scenes=[],
            characters_present=["she"],
            chapter_number=1,
            chapter_title=None
        )
        assert chapter.text == chapter_text
        assert "..." in chapter.text

    def test_chapter_allows_ellipsis_for_suspense(self):
        """GREEN: Ellipsis used for suspense is valid"""
        from Writer.Models import ChapterOutput

        chapter_text = 'Aria melangkah hati-hati di lorong gua yang gelap dan lembap.... Suara aneh bergema dari kedalaman yang tak terjangkau oleh cahaya obor.'

        chapter = ChapterOutput(
            text=chapter_text,
            word_count=len(chapter_text.split()),
            scenes=[],
            characters_present=["Aria"],
            chapter_number=1,
            chapter_title=None
        )
        assert "..." in chapter.text  # Ellipsis should be preserved
        assert chapter.chapter_number == 1

    def test_chapter_still_rejects_todo_placeholder(self):
        """Validator still rejects actual placeholders like TODO"""
        from Writer.Models import ChapterOutput

        chapter_text = 'Valid content here TODO add more details later. This is long enough to pass minimum length requirement for validation testing purposes.'

        with pytest.raises(ValidationError) as exc_info:
            ChapterOutput(
                text=chapter_text,
                word_count=len(chapter_text.split()),
                scenes=[],
                characters_present=[],
                chapter_number=1,
                chapter_title=None
            )

        assert "placeholder text" in str(exc_info.value).lower()
        assert "TODO" in str(exc_info.value)

    def test_chapter_still_rejects_fixme_placeholder(self):
        """Validator still rejects FIXME placeholder"""
        from Writer.Models import ChapterOutput

        chapter_text = 'Valid content here FIXME need to revise this section later. This is long enough to pass minimum length requirement for validation testing purposes.'

        with pytest.raises(ValidationError) as exc_info:
            ChapterOutput(
                text=chapter_text,
                word_count=len(chapter_text.split()),
                scenes=[],
                characters_present=[],
                chapter_number=1,
                chapter_title=None
            )

        assert "placeholder text" in str(exc_info.value).lower()
        assert "FIXME" in str(exc_info.value)

    def test_chapter_still_rejects_tbd_placeholder(self):
        """Validator still rejects TBD placeholder"""
        from Writer.Models import ChapterOutput

        chapter_text = 'Valid content here TBD complete this part later. This is long enough to pass minimum length requirement for validation testing purposes.'

        with pytest.raises(ValidationError) as exc_info:
            ChapterOutput(
                text=chapter_text,
                word_count=len(chapter_text.split()),
                scenes=[],
                characters_present=[],
                chapter_number=1,
                chapter_title=None
            )

        assert "placeholder text" in str(exc_info.value).lower()
        assert "TBD" in str(exc_info.value)

    def test_reasoning_allows_ellipsis(self):
        """GREEN: ReasoningOutput allows ellipsis in reasoning text"""
        from Writer.Models import ReasoningOutput

        reasoning_text = "The character's motivation seems unclear... further development needed in later chapters."

        reasoning = ReasoningOutput(reasoning=reasoning_text)
        assert reasoning.reasoning == reasoning_text
        assert "..." in reasoning.reasoning

    def test_reasoning_still_rejects_na_placeholder(self):
        """ReasoningOutput still rejects N/A placeholder"""
        from Writer.Models import ReasoningOutput

        with pytest.raises(ValidationError) as exc_info:
            ReasoningOutput(reasoning="This is not applicable, so N/A for now.")

        assert "placeholder text" in str(exc_info.value).lower()


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
            character_details=None,
            setting={
                "time": "Medieval era",
                "location": "Medieval kingdom of Eldoria",
                "culture": "Feudal society with knights and magic",
                "mood": "Epic fantasy with mysterious undertones"
            },
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
            genre=None,
            theme=None,
            chapters=["Chapter 1: The beginning of an adventure where our hero discovers their destiny."],
            character_list=[],
            character_details=None,
            setting=None,
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
                genre=None,
                theme=None,
                chapters=["Chapter 1: Some content"],
                character_list=[],
                character_details=None,
                setting=None,
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
                genre=None,
                theme=None,
                chapters=["Chapter 1: Some content"],
                character_list=[],
                character_details=None,
                setting=None,
                target_chapter_count=1
            )

    def test_invalid_empty_chapters(self):
        """Test that empty chapters list fails validation"""
        from Writer.Models import OutlineOutput

        with pytest.raises(ValidationError):
            OutlineOutput(
                title="Test Story",
                genre=None,
                theme=None,
                chapters=[],
                character_list=[],
                character_details=None,
                setting=None,
                target_chapter_count=1
            )

    def test_invalid_short_chapter(self):
        """Test that chapter outline too short fails validation"""
        from Writer.Models import OutlineOutput

        with pytest.raises(ValidationError) as exc_info:
            OutlineOutput(
                title="Test Story",
                genre=None,
                theme=None,
                chapters=["Short"],
                character_list=[],
                character_details=None,
                setting=None,
                target_chapter_count=1
            )

        assert "is too short" in str(exc_info.value)

    def test_invalid_character_name(self):
        """Test that character names too short fail validation"""
        from Writer.Models import OutlineOutput

        with pytest.raises(ValidationError):
            OutlineOutput(
                title="Test Story",
                genre=None,
                theme=None,
                chapters=["Chapter 1: Valid chapter outline"],
                character_list=["A"],
                character_details=None,
                setting=None,
                target_chapter_count=1
            )

    def test_invalid_target_chapter_count(self):
        """Test that invalid chapter counts fail validation"""
        from Writer.Models import OutlineOutput

        # Test 0 chapters
        with pytest.raises(ValidationError):
            OutlineOutput(
                title="Test Story",
                genre=None,
                theme=None,
                chapters=["Chapter 1: Content"],
                character_list=[],
                character_details=None,
                setting=None,
                target_chapter_count=0
            )

        # Test too many chapters
        with pytest.raises(ValidationError):
            OutlineOutput(
                title="Test Story",
                genre=None,
                theme=None,
                chapters=["Chapter 1: Content"],
                character_list=[],
                character_details=None,
                setting=None,
                target_chapter_count=101
            )

    def test_outline_output_with_dict_setting(self):
        """GREEN: Test that OutlineOutput accepts Dict[str, str] for setting field"""
        from Writer.Models import OutlineOutput

        # This should PASS after updating model (GREEN phase)
        structured_setting = {
            "time": "Saat ini",
            "location": "Hutan yang dipenuhi misteri di pinggiran desa Rian.",
            "culture": "Modern dengan sentuhan legenda kuno.",
            "mood": "Misterius dan menantang."
        }

        # Should pass after model change to accept Dict[str, str]
        outline = OutlineOutput(
            title="Gua Harta Karun Naga",
            genre="Fantasi Petualangan",
            theme=None,
            chapters=[
                "Chapter 1: Rian, seorang petualang berani dari desa kecil di pinggiran hutan, mendengar legenda tentang gua yang dipenuhi harta karun dan dijaga oleh naga kecil. Dengan semangat petualangan, ia memutuskan untuk mencari gua tersebut.",
                "Chapter 2: Setelah menemukan gua, Rian menghadapi Naga Kecil yang menjaga harta karun. Terjadi konflik yang kemudian berubah menjadi persahabatan."
            ],
            character_list=["Rian", "Naga Kecil"],
            character_details=None,
            setting=structured_setting,  # Dict should now be accepted
            target_chapter_count=2
        )

        # Verify dict structure is preserved
        assert isinstance(outline.setting, dict)
        assert "time" in outline.setting
        assert "location" in outline.setting
        assert "culture" in outline.setting
        assert "mood" in outline.setting
        assert outline.setting["time"] == "Saat ini"
        assert outline.setting["location"] == "Hutan yang dipenuhi misteri di pinggiran desa Rian."

    def test_outline_output_with_none_setting(self):
        """Test that OutlineOutput handles None setting correctly"""
        from Writer.Models import OutlineOutput

        # Should work fine with None
        outline = OutlineOutput(
            title="Test Story",
            genre=None,
            theme=None,
            chapters=["Chapter 1: This is a long enough chapter outline that meets the minimum length requirement."],
            character_list=[],
            character_details=None,
            setting=None,
            target_chapter_count=1
        )

        assert outline.setting is None

    def test_outline_output_with_string_setting(self):
        """GREEN: Test that string setting fails after model change (as expected)"""
        from Writer.Models import OutlineOutput
        from pydantic import ValidationError
        import pytest

        # String setting should now fail after model change to expect dict
        with pytest.raises(ValidationError) as exc_info:
            OutlineOutput(
                title="Test Story",
                genre=None,
                theme=None,
                chapters=["Chapter 1: This is a long enough chapter outline that meets the minimum length requirement."],
                character_list=[],
                character_details=None,
                setting="A mystical forest setting in ancient times",  # type: ignore[arg-type]
                target_chapter_count=1
            )

        # Should fail expecting dict
        error_str = str(exc_info.value)
        assert "Input should be a valid dictionary" in error_str
        assert "setting" in error_str


class TestStoryElements:
    """Test suite for StoryElements following TDD London School approach"""

    def test_valid_story_elements_creation(self):
        """Test creating valid StoryElements"""
        from Writer.Models import StoryElements

        from Writer.Models import CharacterDetail

        alice_character = CharacterDetail(
            name="Alice",
            physical_description="A brave knight with blue eyes",
            background="Searching for the ancient artifact",
            personality="Determined and courageous",
            motivation="Find the artifact to save the kingdom"
        )

        merlin_character = CharacterDetail(
            name="Merlin",
            physical_description="A wise old wizard with long white beard",
            background="Ancient magical guardian of the realm",
            personality="Wise and mysterious",
            motivation="Guide Alice on her quest to defeat evil"
        )

        elements = StoryElements(
            title="Alice and the Ancient Artifact",
            genre="Fantasy Adventure",
            characters={
                "main_character": [alice_character],
                "mentor": [merlin_character]
            },
            settings={
                "Dark Forest": {
                    "location": "A dangerous forest filled with magical creatures",
                    "time": "Present day in story timeline",
                    "culture": "Magical, dangerous",
                    "mood": "Mysterious and threatening"
                },
                "Eldoria": {
                    "location": "The peaceful kingdom where Alice lives",
                    "time": "Present day in story timeline",
                    "culture": "Medieval fantasy kingdom",
                    "mood": "Peaceful and safe"
                }
            },
            themes=["courage", "friendship", "good vs evil"],
            pacing=None,
            style=None,
            plot_structure=None,
            conflict="Alice must find the artifact before the Dark Lord does",
            symbolism=None,
            resolution="Alice defeats the Dark Lord and restores peace to Eldoria"
        )

        assert "main_character" in elements.characters
        assert len(elements.characters["main_character"]) == 1
        assert elements.characters["main_character"][0].name == "Alice"
        assert "blue eyes" in (elements.characters["main_character"][0].physical_description or "")
        assert "mentor" in elements.characters
        assert elements.characters["mentor"][0].name == "Merlin"
        assert len(elements.themes) == 3
        assert elements.conflict == "Alice must find the artifact before the Dark Lord does"

    def test_minimum_valid_story_elements(self):
        """Test creating StoryElements with minimum required fields"""
        from Writer.Models import StoryElements

        elements = StoryElements(
            title="Test Story",
            genre="Test Genre",
            themes=["theme1"],
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        assert elements.title == "Test Story"
        assert elements.genre == "Test Genre"
        assert elements.themes == ["theme1"]
        assert elements.characters == {}
        assert elements.settings == {}
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
            completeness_score=0.0,
            feedback=None
        )
        assert metrics_min.coherence_score == 0.0

        # Test maximum scores
        metrics_max = QualityMetrics(
            coherence_score=1.0,
            relevance_score=1.0,
            completeness_score=1.0,
            feedback=None
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
                completeness_score=0.5,
                feedback=None
            )

        # Test score > 1
        with pytest.raises(ValidationError):
            QualityMetrics(
                coherence_score=0.5,
                relevance_score=1.1,
                completeness_score=0.5,
                feedback=None
            )

    def test_minimum_valid_metrics(self):
        """Test creating QualityMetrics with minimum required fields"""
        from Writer.Models import QualityMetrics

        metrics = QualityMetrics(
            coherence_score=0.5,
            relevance_score=0.5,
            completeness_score=0.5,
            feedback=None
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


class TestReviewOutputSuggestions:
    """Test ReviewOutput with structured suggestions from LLM"""

    def test_review_output_accepts_structured_suggestions_green(self):
        """GREEN: Test that ReviewOutput now accepts structured suggestions after implementation"""
        from Writer.Models import ReviewOutput
        from Writer.Models import EnhancedSuggestion

        # This should work now with our Union[str, EnhancedSuggestion] implementation
        review = ReviewOutput(
            feedback="Outline ini memiliki kekuatan dalam menggambarkan karakter dan setting yang menarik.",
            suggestions=[
                EnhancedSuggestion(
                    description="Tambahkan lebih banyak detail tentang tantangan yang dihadapi Rian dalam menemukan gua tersebut. Misalnya, apa saja rintangannya dan bagaimana ia mengatasinya?",
                    pacing="Perlu diperhatikan laju cerita agar tidak terlalu cepat melewati poin plot tertentu. Misalnya, tambahkan lebih banyak detail tentang hubungan antara Rian dengan Naga Kecil.",
                    flow="Pastikan setiap bab mengalir ke bab berikutnya dan memiliki struktur naratif yang konsisten di seluruh cerita.",
                    other_criteria=None
                ),
                "Saran sederhana tentang pengembangan karakter"
            ],
            rating=7
        )

        # Should validate successfully with structured suggestions
        assert review.feedback is not None
        assert review.suggestions is not None
        assert len(review.suggestions) == 2
        assert review.rating == 7

        # Check types - first should be EnhancedSuggestion, second should be string
        assert isinstance(review.suggestions[0], EnhancedSuggestion)
        assert isinstance(review.suggestions[1], str)

        # Check field mapping from Indonesian to English
        structured_suggestion = review.suggestions[0]
        assert structured_suggestion.description == "Tambahkan lebih banyak detail tentang tantangan yang dihadapi Rian dalam menemukan gua tersebut. Misalnya, apa saja rintangannya dan bagaimana ia mengatasinya?"
        assert structured_suggestion.pacing == "Perlu diperhatikan laju cerita agar tidak terlalu cepat melewati poin plot tertentu. Misalnya, tambahkan lebih banyak detail tentang hubungan antara Rian dengan Naga Kecil."
        assert structured_suggestion.flow == "Pastikan setiap bab mengalir ke bab berikutnya dan memiliki struktur naratif yang konsisten di seluruh cerita."

    def test_enhanced_suggestion_model_will_work_after_creation(self):
        """GREEN: Test that EnhancedSuggestion model will work after we create it"""
        # This tests the future state after we create EnhancedSuggestion

        # For now, just verify the structured data pattern
        structured_suggestion = {
            "detail": "Tambahkan lebih banyak detail tentang tantangan",
            "laju": "Perbaiki laju cerita di bab pertama",
            "alur": "Pastikan alur naratif konsisten"
        }

        # Verify the expected English field mappings
        expected_mapping = {
            "description": "detail",
            "pacing": "laju",
            "flow": "alur"
        }

        # This will be used in our future validator
        for english_field, indonesian_field in expected_mapping.items():
            assert indonesian_field in structured_suggestion
            assert structured_suggestion[indonesian_field] is not None


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
            'QualityMetrics', 'SceneOutline', 'ChapterWithScenes',
            'CharacterDetail', 'EnhancedSceneOutline'
        ]

        for model_name in expected_models:
            assert model_name in MODEL_REGISTRY, f"{model_name} not found in MODEL_REGISTRY"


class TestModelMethods:
    """Test new Pydantic model methods for structured extraction"""

    def test_story_elements_to_prompt_string(self):
        """RED: Generate prompt string from Pydantic object directly"""
        from Writer.Models import StoryElements, CharacterDetail

        hero = CharacterDetail(
            name="Luna",
            physical_description="Brave warrior princess",
            background="Raised in magical kingdom",
            personality="Determined and kind",
            motivation=None
        )

        story_elements = StoryElements(
            title="Luna's Quest",
            genre="Fantasy Adventure",
            themes=["courage", "magic", "friendship"],
            characters={"main": [hero]},
            settings={
                "Crystal Kingdom": {
                    "location": "Floating islands in the sky",
                    "mood": "Enchanted, peaceful",
                    "culture": "Magical society",
                    "time": "Age of wonders"
                }
            },
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        # This should FAIL before implementation - to_prompt_string method doesn't exist yet
        prompt_string = story_elements.to_prompt_string()

        # Validate prompt string structure
        assert "Title: Luna's Quest" in prompt_string
        assert "Genre: Fantasy Adventure" in prompt_string
        assert "Themes: courage, magic, friendship" in prompt_string
        assert "Characters:" in prompt_string
        assert "- Luna: Brave warrior princess" in prompt_string
        assert "Settings:" in prompt_string
        assert "- Crystal Kingdom:" in prompt_string
        assert "  - location: Floating islands in the sky" in prompt_string

    def test_story_elements_minimal_to_prompt_string(self):
        """RED: Prompt string with minimal story elements"""
        from Writer.Models import StoryElements

        story_elements = StoryElements(
            title="Minimal Story",
            genre="Test",
            themes=["minimal"],  # Required field
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        # This should FAIL before implementation
        prompt_string = story_elements.to_prompt_string()

        # Should handle minimal elements gracefully
        assert "Title: Minimal Story" in prompt_string
        assert "Genre: Test" in prompt_string
        assert "Themes: minimal" in prompt_string  # Has themes
        assert "Characters:" not in prompt_string  # No characters
        assert "Settings:" not in prompt_string    # No settings

    def test_outline_output_to_prompt_string(self):
        """RED: Generate outline prompt from OutlineOutput"""
        from Writer.Models import OutlineOutput

        outline = OutlineOutput(
            title="The Dragon's Treasure",
            genre=None,
            theme=None,
            chapters=[
                "Chapter 1: Young hero discovers ancient map leading to dragon's lair",
                "Chapter 2: Hero assembles fellowship of brave adventurers",
                "Chapter 3: Journey through dangerous forests and mountains",
                "Chapter 4: Confrontation with the ancient dragon",
                "Chapter 5: Hero chooses wisdom over wealth, earning dragon's respect"
            ],
            character_list=[],
            character_details=None,
            setting=None,
            target_chapter_count=5
        )

        # This should FAIL before implementation - to_prompt_string method doesn't exist yet
        prompt_string = outline.to_prompt_string()

        # Validate prompt string structure
        assert "The Dragon's Treasure" in prompt_string
        assert "Chapter 1: Young hero discovers ancient map" in prompt_string
        assert "Chapter 2: Hero assembles fellowship" in prompt_string
        assert "Chapter 3: Journey through dangerous forests" in prompt_string
        assert "Chapter 4: Confrontation with the ancient dragon" in prompt_string
        assert "Chapter 5: Hero chooses wisdom" in prompt_string

    def test_outline_output_extract_lorebook_entries(self):
        """RED: Extract plot points from OutlineOutput"""
        from Writer.Models import OutlineOutput

        outline = OutlineOutput(
            title="Space Odyssey",
            genre=None,
            theme=None,
            chapters=[
                "Chapter 1: Captain receives mysterious distress signal from outer space",
                "Chapter 2: Crew investigates abandoned space station",
                "Chapter 3: Discovery of alien artifact with strange powers",
                "Chapter 4: Space pirates attack seeking the artifact"
            ],
            character_list=[],
            character_details=None,
            setting=None,
            target_chapter_count=4
        )

        # This should FAIL before implementation - extract_lorebook_entries method doesn't exist yet
        entries = outline.extract_lorebook_entries()

        # Validate plot point entries
        assert len(entries) == 4

        # Check individual entries
        for i, entry in enumerate(entries):
            assert entry["type"] == "plot_point"
            assert entry["name"] == f"chapter_{i+1}"
            assert entry["metadata"]["source"] == "outline"
            assert entry["metadata"]["chapter"] == i + 1

        # Check specific content
        assert "distress signal" in entries[0]["content"]
        assert "abandoned space station" in entries[1]["content"]
        assert "alien artifact" in entries[2]["content"]
        assert "Space pirates" in entries[3]["content"]

    def test_outline_output_extract_lorebook_entries_filter_short_chapters(self):
        """RED: Filter out very short chapter outlines"""
        from Writer.Models import OutlineOutput

        outline = OutlineOutput(
            title="Mixed Quality Outline",
            genre=None,
            theme=None,
            chapters=[
                "Chapter 1: Detailed description of hero's background and motivations for the quest ahead.",  # Long enough
                "Chapter 2: Very short chapter that meets minimum length requirement.",  # Minimum length (20 chars)
                "Chapter 3: Hero meets mysterious stranger who provides crucial information and warnings about dangers.",  # Long enough
                "Chapter 4: Another short chapter that meets minimum length requirement.",  # Minimum length (20 chars)
                "Chapter 5: Epic confrontation where hero faces ultimate challenge and makes difficult choice."  # Long enough
            ],
            character_list=[],
            character_details=None,
            setting=None,
            target_chapter_count=5
        )

        # This should FAIL before implementation
        entries = outline.extract_lorebook_entries()

        # Should include chapters 1, 3, and 5 (longer), chapters 2 and 4 are exactly 20 chars (will be included)
        # So all 5 chapters will be included since they meet minimum length
        assert len(entries) == 5
        assert entries[0]["metadata"]["chapter"] == 1
        assert entries[1]["metadata"]["chapter"] == 2
        assert entries[2]["metadata"]["chapter"] == 3
        assert entries[3]["metadata"]["chapter"] == 4
        assert entries[4]["metadata"]["chapter"] == 5


class TestMetadataFlattening:
    """TDD London School: Test metadata flattening for ChromaDB compatibility"""

    def test_flatten_simple_nested_dict(self):
        """RED: Flatten simple nested dictionary"""
        from Writer.Models import _flatten_metadata

        metadata = {
            "type": "location",
            "details": {"time": "2024", "mood": "dark"}
        }

        result = _flatten_metadata(metadata)

        expected = {
            "type": "location",
            "details_time": "2024",
            "details_mood": "dark"
        }

        assert result == expected

    def test_flatten_preserves_primitives(self):
        """RED: Preserve primitive types"""
        from Writer.Models import _flatten_metadata

        metadata = {
            "string": "test",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "none_value": None,
            "nested": {"nested_int": 100}
        }

        result = _flatten_metadata(metadata)

        expected = {
            "string": "test",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "none_value": None,
            "nested_nested_int": 100
        }

        assert result == expected

    def test_flatten_handles_complex_types(self):
        """RED: Convert complex types to strings"""
        from Writer.Models import _flatten_metadata

        metadata = {
            "list": [1, 2, 3],
            "tuple": ("a", "b"),
            "object": object()
        }

        result = _flatten_metadata(metadata)

        # All non-primitive/non-dict types should be converted to strings
        assert isinstance(result["list"], str)
        assert isinstance(result["tuple"], str)
        assert isinstance(result["object"], str)

    def test_flatten_empty_and_edge_cases(self):
        """RED: Handle empty dictionaries and edge cases"""
        from Writer.Models import _flatten_metadata

        # Empty dictionary
        assert _flatten_metadata({}) == {}

        # Empty nested dictionaries
        metadata = {"empty": {}, "nested": {"empty": {}}}
        result = _flatten_metadata(metadata)
        assert result == {"empty": {}, "nested_empty": {}}
