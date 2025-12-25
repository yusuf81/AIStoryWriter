"""
TDD Tests for Enhanced StoryElements Model - London School Approach
Tests for CharacterDetail model and enhanced StoryElements to fix prompt-model conflicts
"""
from pydantic import ValidationError
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestCharacterDetailModel:
    """TDD tests for CharacterDetail Pydantic model following London School approach"""

    def test_character_detail_minimal_creation(self):
        """
        RED TEST: CharacterDetail can be created with minimal required fields

        This test will FAIL initially because CharacterDetail model doesn't exist yet.
        After implementation, this test will PASS because CharacterDetail will be created.
        """
        from Writer.Models import CharacterDetail

        # Should be able to create with just name (required field)
        character = CharacterDetail(
            name="Rian",
            physical_description=None,
            personality=None,
            background=None,
            motivation=None
        )

        assert character.name == "Rian"
        assert character.physical_description is None
        assert character.personality is None
        assert character.background is None
        assert character.motivation is None

    def test_character_detail_full_creation(self):
        """
        RED TEST: CharacterDetail can be created with all fields

        This test will FAIL initially because CharacterDetail model doesn't exist yet.
        After implementation, this test will PASS with complete character data.
        """
        from Writer.Models import CharacterDetail

        character = CharacterDetail(
            name="Rian",
            physical_description="Tinggi, berotot, dengan rambut cokelat yang acak-acakan",
            personality="Berani dan penuh semangat petualangan",
            background="Seorang petualang yang telah menjelajahi banyak tempat di hutan",
            motivation="Mencari kekayaan dan pengalaman baru"
        )

        assert character.name == "Rian"
        assert "Tinggi" in (character.physical_description or "")
        assert "Berani" in (character.personality or "")
        assert "petualang" in (character.background or "")
        assert "kekayaan" in (character.motivation or "")

    def test_character_detail_validation(self):
        """
        RED TEST: CharacterDetail validates required name field

        This test will FAIL initially because CharacterDetail model doesn't exist yet.
        After implementation, this test will PASS with proper validation.
        """
        from Writer.Models import CharacterDetail

        # Empty name should fail validation
        with pytest.raises(ValidationError) as exc_info:
            CharacterDetail(
                name="",
                physical_description=None,
                personality=None,
                background=None,
                motivation=None
            )

        assert "name" in str(exc_info.value)

    def test_character_detail_indonesian_fields(self):
        """
        RED TEST: CharacterDetail supports Indonesian character structure

        This test will FAIL initially because CharacterDetail model doesn't exist yet.
        After implementation, this test will PASS with Indonesian character data.
        """
        from Writer.Models import CharacterDetail

        character = CharacterDetail(
            name="Naga Kecil",
            physical_description="Berwarna hijau dengan sayap yang kecil, memiliki cakar tajam",
            personality="Cerdas dan bijaksana, tetapi juga sedikit curiga terhadap orang asing",
            background="Menjaga harta karun di gua selama berabad-abad",
            motivation="Menjaga harta karun yang menguji ketulusan Rian"
        )

        assert character.name == "Naga Kecil"
        assert "hijau" in (character.physical_description or "")
        assert "Cerdas" in (character.personality or "")


class TestEnhancedStoryElements:
    """TDD tests for enhanced StoryElements model with CharacterDetail objects"""

    def test_enhanced_story_elements_with_character_objects(self):
        """
        RED TEST: StoryElements accepts Dict[str, List[CharacterDetail]] structure

        This test will FAIL initially because StoryElements still uses Dict[str, str].
        After implementation, this test will PASS with enhanced character structure.
        """
        from Writer.Models import StoryElements, CharacterDetail

        # Create character details matching Indonesian prompt structure
        main_character = CharacterDetail(
            name="Rian",
            physical_description="Tinggi, berotot, dengan rambut cokelat yang acak-acakan",
            personality="Berani dan penuh semangat petualangan",
            background="Seorang petualang yang telah menjelajahi banyak tempat",
            motivation="Mencari kekayaan dan pengalaman baru"
        )

        supporting_character = CharacterDetail(
            name="Naga Kecil",
            physical_description="Berwarna hijau dengan sayap kecil, memiliki cakar tajam",
            personality="Cerdas dan bijaksana, sedikit curiga terhadap orang asing",
            background="Menjaga harta karun di gua selama berabad-abad",
            motivation="Menjaga harta karun yang menguji ketulusan"
        )

        story_elements = StoryElements(
            title="Harta Karun Naga Kecil",
            genre="Fantasi",
            themes=["Petualangan", "Keberanian"],
            characters={
                "karakter_utama": [main_character],
                "karakter_pendukung": [supporting_character]
            },
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        assert story_elements.title == "Harta Karun Naga Kecil"
        assert "karakter_utama" in story_elements.characters
        assert "karakter_pendukung" in story_elements.characters
        assert len(story_elements.characters["karakter_utama"]) == 1
        assert len(story_elements.characters["karakter_pendukung"]) == 1
        assert story_elements.characters["karakter_utama"][0].name == "Rian"
        assert story_elements.characters["karakter_pendukung"][0].name == "Naga Kecil"

    def test_enhanced_story_elements_multiple_characters(self):
        """
        RED TEST: StoryElements handles multiple characters per type

        This test will FAIL initially because StoryElements still uses Dict[str, str].
        After implementation, this test will PASS with multiple character support.
        """
        from Writer.Models import StoryElements, CharacterDetail

        # Multiple main characters
        protagonist = CharacterDetail(
            name="Alex",
            physical_description=None,
            personality=None,
            background=None,
            motivation="Save the kingdom"
        )
        companion = CharacterDetail(
            name="Sam",
            physical_description=None,
            personality=None,
            background=None,
            motivation="Help Alex"
        )

        # Multiple supporting characters
        mentor = CharacterDetail(
            name="Gandalf",
            physical_description=None,
            personality=None,
            background=None,
            motivation="Guide the heroes"
        )
        villain = CharacterDetail(
            name="Dark Lord",
            physical_description=None,
            personality=None,
            background=None,
            motivation="Conquer the world"
        )
        ally = CharacterDetail(
            name="King",
            physical_description=None,
            personality=None,
            background=None,
            motivation="Support the heroes"
        )

        story_elements = StoryElements(
            title="The Great Quest",
            genre="Fantasy Adventure",
            themes=["Good vs Evil", "Friendship"],
            characters={
                "protagonists": [protagonist, companion],
                "supporting_characters": [mentor, ally],
                "antagonists": [villain]
            },
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        assert len(story_elements.characters["protagonists"]) == 2
        assert len(story_elements.characters["supporting_characters"]) == 2
        assert len(story_elements.characters["antagonists"]) == 1
        assert story_elements.characters["protagonists"][0].name == "Alex"
        assert story_elements.characters["protagonists"][1].name == "Sam"

    def test_enhanced_story_elements_english_indonesian_compatibility(self):
        """
        RED TEST: Enhanced StoryElements works for both English and Indonesian prompts

        This test will FAIL initially because StoryElements doesn't support list structures.
        After implementation, this test will PASS with language-agnostic structure.
        """
        from Writer.Models import StoryElements, CharacterDetail

        # Indonesian-style character structure
        main_char = CharacterDetail(
            name="Rian",
            physical_description="Petualang tangguh",
            personality="Berani",
            background="Dari desa terpencil",
            motivation="Mencari harta karun"
        )

        # English-style character structure
        english_main_char = CharacterDetail(
            name="John",
            physical_description="Brave adventurer",
            personality="Courageous",
            background="From remote village",
            motivation="Seeking treasure"
        )

        # Both should work in same model
        story_elements_id = StoryElements(
            title="Petualangan Rian",
            genre="Fantasi",
            themes=["Petualangan", "Keberanian"],
            characters={"main_character": [main_char]},
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        story_elements_en = StoryElements(
            title="John's Adventure",
            genre="Fantasy",
            themes=["Adventure", "Courage"],
            characters={"main_character": [english_main_char]},
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        assert story_elements_id.characters["main_character"][0].name == "Rian"
        assert story_elements_en.characters["main_character"][0].name == "John"

    def test_enhanced_story_elements_preserves_optional_fields(self):
        """
        RED TEST: Enhanced StoryElements preserves all optional fields

        This test will FAIL initially because model doesn't exist yet.
        After implementation, this test will verify all fields are properly handled.
        """
        from Writer.Models import StoryElements, CharacterDetail

        character = CharacterDetail(
            name="Hero",
            physical_description=None,
            personality=None,
            background=None,
            motivation=None
        )

        story_elements = StoryElements(
            title="Test Story",
            genre="Test",
            themes=["test"],
            characters={"hero": [character]},
            pacing="Moderate",
            style="Literary",
            plot_structure={
                "exposition": "Beginning",
                "rising_action": "Conflict develops",
                "climax": "Peak tension",
                "falling_action": "Resolution begins",
                "resolution": "Story concludes"
            },
            settings={
                "forest": {
                    "time": "Present",
                    "location": "Deep woods",
                    "culture": "Magical",
                    "mood": "Mysterious"
                }
            },
            conflict="Hero vs villain",
            symbolism=[{"symbol": "Light", "meaning": "Hope"}],
            resolution="Hero wins"
        )

        assert story_elements.pacing == "Moderate"
        assert story_elements.style == "Literary"
        assert len(story_elements.plot_structure or {}) == 5
        assert "forest" in (story_elements.settings or {})
        assert story_elements.conflict == "Hero vs villain"
        assert len(story_elements.symbolism or []) == 1
        assert story_elements.resolution == "Hero wins"


class TestStoryElementsJsonSerialization:
    """TDD tests for JSON serialization/deserialization with enhanced models"""

    def test_enhanced_story_elements_json_export(self):
        """
        RED TEST: Enhanced StoryElements can be serialized to JSON

        This test will FAIL initially because models don't exist yet.
        After implementation, this test will verify proper JSON export.
        """
        from Writer.Models import StoryElements, CharacterDetail

        character = CharacterDetail(
            name="Test Character",
            physical_description=None,
            personality="Brave",
            background=None,
            motivation=None
        )

        story_elements = StoryElements(
            title="Test Story",
            genre="Fantasy",
            themes=["test"],
            characters={"main": [character]},
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        # Should serialize without errors
        json_data = story_elements.model_dump()

        assert json_data["title"] == "Test Story"
        assert isinstance(json_data["characters"], dict)
        assert isinstance(json_data["characters"]["main"], list)
        assert json_data["characters"]["main"][0]["name"] == "Test Character"

    def test_enhanced_story_elements_json_import(self):
        """
        RED TEST: Enhanced StoryElements can be created from JSON

        This test will FAIL initially because models don't exist yet.
        After implementation, this test will verify proper JSON import.
        """
        from Writer.Models import StoryElements

        json_data = {
            "title": "Story from JSON",
            "genre": "Adventure",
            "themes": ["action", "drama"],
            "characters": {
                "hero": [{
                    "name": "JSON Hero",
                    "physical_description": "Test description",
                    "personality": "Brave",
                    "background": "From JSON",
                    "motivation": "JSON quest"
                }]
            }
        }

        story_elements = StoryElements(**json_data)

        assert story_elements.title == "Story from JSON"
        assert len(story_elements.characters["hero"]) == 1
        hero = story_elements.characters["hero"][0]
        assert hero.name == "JSON Hero"
        assert hero.physical_description == "Test description"
        assert hero.personality == "Brave"
        assert hero.background == "From JSON"
        assert hero.motivation == "JSON quest"
