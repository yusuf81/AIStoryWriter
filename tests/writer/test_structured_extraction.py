"""
TDD London School - Test structured extraction from Pydantic models.
This tests that StoryElements and OutlineOutput can extract lore entries
directly without converting to strings and parsing with regex.

RED PHASE: All tests should FAIL before implementation.
"""
from Writer.Models import StoryElements, CharacterDetail
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestStoryElementsStructuredExtraction:
    """Test that StoryElements can extract lore entries directly without string conversion"""

    def test_extract_characters_from_story_elements(self):
        """RED: Direct character extraction from Pydantic object"""
        # Create StoryElements with characters
        hero = CharacterDetail(
            name="Arthur",
            physical_description="Brave knight with silver armor",
            background="Seeking the Holy Grail",
            personality="Noble and determined",
            motivation="Save his kingdom from darkness"
        )

        villain = CharacterDetail(
            name="Morgana",
            physical_description="Dark sorceress with flowing black robes",
            background="Former apprentice of Merlin",
            personality="Ambitious and ruthless",
            motivation="Conquer the magical realm"
        )

        story_elements = StoryElements(
            title="The Grail Quest",
            genre="Fantasy Adventure",
            themes=["courage", "honor", "redemption"],
            characters={
                "protagonist": [hero],
                "antagonist": [villain]
            },
            settings={
                "Camelot": {
                    "location": "Medieval castle on hill",
                    "mood": "Majestic, hopeful",
                    "culture": "Arthurian legend",
                    "time": "Medieval era"
                }
            },
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        # This should FAIL before implementation - extract_lorebook_entries method doesn't exist yet
        entries = story_elements.extract_lorebook_entries()

        # Validate character entries
        character_entries = [e for e in entries if e["type"] == "character"]
        assert len(character_entries) == 2

        # Check Arthur entry
        arthur_entry = next(e for e in character_entries if e["name"] == "Arthur")
        assert arthur_entry["type"] == "character"
        assert arthur_entry["role"] == "protagonist"
        assert "Brave knight" in arthur_entry["content"]
        assert arthur_entry["metadata"]["source"] == "story_elements"

        # Check Morgana entry
        morgana_entry = next(e for e in character_entries if e["name"] == "Morgana")
        assert morgana_entry["type"] == "character"
        assert morgana_entry["role"] == "antagonist"
        assert "Dark sorceress" in morgana_entry["content"]

    def test_extract_settings_from_story_elements(self):
        """RED: Direct setting extraction from Pydantic object"""
        story_elements = StoryElements(
            title="Test Story",
            genre="Fantasy",
            themes=["magic"],
            settings={
                "Enchanted Forest": {
                    "location": "Ancient woods beyond the mountains",
                    "mood": "Mysterious, magical",
                    "culture": "Elven civilization",
                    "time": "Timeless"
                },
                "Dragon's Lair": {
                    "location": "Cave beneath the castle",
                    "mood": "Dark, dangerous",
                    "culture": "Wyvern culture",
                    "time": "Medieval era"
                }
            },
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        # This should FAIL before implementation
        entries = story_elements.extract_lorebook_entries()

        # Validate setting entries
        setting_entries = [e for e in entries if e["type"] == "location"]
        assert len(setting_entries) == 2

        # Check Enchanted Forest entry
        forest_entry = next(e for e in setting_entries if e["name"] == "Enchanted Forest")
        assert forest_entry["type"] == "location"
        assert "Mysterious, magical" in forest_entry["content"]
        assert "Ancient woods" in forest_entry["content"]

        # Check Dragon's Lair entry
        lair_entry = next(e for e in setting_entries if e["name"] == "Dragon's Lair")
        assert lair_entry["type"] == "location"
        assert "Dark, dangerous" in lair_entry["content"]

    def test_extract_themes_from_story_elements(self):
        """RED: Direct theme extraction without regex"""
        story_elements = StoryElements(
            title="Test Story",
            genre="Fantasy",
            themes=["courage", "friendship", "redemption", "sacrifice"],
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        # This should FAIL before implementation
        entries = story_elements.extract_lorebook_entries()

        # Validate theme entry
        theme_entries = [e for e in entries if e["type"] == "theme"]
        assert len(theme_entries) == 1

        theme_entry = theme_entries[0]
        assert theme_entry["type"] == "theme"
        assert theme_entry["name"] == "main_themes"
        assert "courage" in theme_entry["content"]
        assert "friendship" in theme_entry["content"]
        assert "redemption" in theme_entry["content"]
        assert "sacrifice" in theme_entry["content"]

    def test_extract_empty_story_elements(self):
        """RED: Handle empty StoryElements gracefully"""
        story_elements = StoryElements(
            title="Minimal Story",
            genre="Test",
            themes=["minimal"],  # Required field with at least 1 theme
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        # This should FAIL before implementation
        entries = story_elements.extract_lorebook_entries()

        # Should return only theme entry for minimal story elements
        assert len(entries) == 1
        assert entries[0]["type"] == "theme"
        assert entries[0]["name"] == "main_themes"

    def test_extract_partial_story_elements(self):
        """RED: Handle partial data gracefully"""
        hero = CharacterDetail(
            name="Solo",
            physical_description="Lone warrior",
            personality=None,
            background=None,
            motivation=None
        )

        story_elements = StoryElements(
            title="Partial Story",
            genre="Adventure",
            themes=["survival"],
            characters={"main": [hero]},
            # No settings
            pacing=None,
            style=None,
            plot_structure=None,
            conflict=None,
            symbolism=None,
            resolution=None
        )

        # This should FAIL before implementation
        entries = story_elements.extract_lorebook_entries()

        # Should have character and theme, but no location entries
        assert len([e for e in entries if e["type"] == "character"]) == 1
        assert len([e for e in entries if e["type"] == "theme"]) == 1
        assert len([e for e in entries if e["type"] == "location"]) == 0
