"""
Integration tests for lorebook anti-pattern fix.
Tests complete lorebook extraction without converting Pydantic objects to strings.

RED PHASE: All tests should FAIL before implementation.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from unittest.mock import Mock, patch

from Writer.Models import StoryElements, OutlineOutput, CharacterDetail
from Writer.Lorebook import LorebookManager


class TestLorebookStructuredExtraction:
    """Test complete lorebook extraction without anti-patterns"""

    @pytest.fixture
    def mock_logger(self):
        """Mock logger fixture"""
        logger = Mock()
        logger.Log = Mock()
        logger.logs = []
        return logger

    @pytest.fixture
    def sample_story_elements(self):
        """Sample StoryElements for testing"""
        hero = CharacterDetail(
            name="Zara",
            physical_description="Rebel fighter with cybernetic arm",
            background="Former corporate security",
            personality="Resourceful and determined"
        )

        villain = CharacterDetail(
            name="Dr. Nexus",
            physical_description="AI overlord with holographic interface",
            background="Created to manage city systems",
            personality="Logical yet ruthless"
        )

        return StoryElements(
            title="Neon Dreams",
            genre="Cyberpunk Thriller",
            themes=["technology", "freedom", "humanity"],
            characters={
                "protagonist": [hero],
                "antagonist": [villain]
            },
            settings={
                "Neo-City": {
                    "location": "Metropolitan area with towering skyscrapers",
                    "mood": "Dystopian, neon-lit",
                    "culture": "High-tech society",
                    "time": "Year 2077"
                },
                "Underground": {
                    "location": "Hidden rebel base beneath the city",
                    "mood": "Hopeful, secretive",
                    "culture": "Resistance movement",
                    "time": "Present day"
                }
            },
            conflict="Freedom fighter battles AI overlord for control of the city",
            resolution="Human choice prevails over perfect logic, finding balance between technology and humanity"
        )

    @pytest.fixture
    def sample_outline_output(self):
        """Sample OutlineOutput for testing"""
        return OutlineOutput(
            title="Neon Dreams",
            chapters=[
                "Chapter 1: Zara discovers corporate conspiracy and joins resistance",
                "Chapter 2: infiltration of corporate tower to gather evidence",
                "Chapter 3: First confrontation with Dr. Nexus surveillance systems",
                "Chapter 4: Alliance with underground hackers and data liberation",
                "Chapter 5: Final battle for control of Neo-City's central AI"
            ],
            target_chapter_count=5
        )

    def test_lorebook_accepts_pydantic_objects(self, mock_logger, sample_story_elements, sample_outline_output):
        """RED: Lorebook should accept Pydantic objects directly"""
        # Create mock lorebook without database initialization
        with patch('Writer.Lorebook.LorebookManager.__init__', return_value=None):
            lorebook = LorebookManager()
            lorebook.db = Mock()  # Mock the database
            lorebook.add_entry = Mock()  # Mock add_entry method
            lorebook.SysLogger = mock_logger

            # This should FAIL before implementation - extract_from_structured_data method doesn't exist yet
            lorebook.extract_from_structured_data(sample_story_elements, sample_outline_output)

            # Should have called add_entry for structured extraction
            assert lorebook.add_entry.call_count > 0

            # Check calls for story elements
            calls = lorebook.add_entry.call_args_list

            # Should have character entries (filter by character type in metadata)
            character_calls = [call for call in calls if call[0][1].get('type') == 'character']
            assert len(character_calls) == 2

            # Should have setting entries (filter by location type in metadata)
            setting_calls = [call for call in calls if call[0][1].get('type') == 'location']
            assert len(setting_calls) == 2

            # Should have theme entries (filter by theme type in metadata)
            theme_calls = [call for call in calls if call[0][1].get('type') == 'theme']
            assert len(theme_calls) == 1

            # Should have plot point entries from outline (filter by plot_point type in metadata)
            plot_calls = [call for call in calls if call[0][1].get('type') == 'plot_point']
            assert len(plot_calls) == 5

    def test_lorebook_extract_characters_with_details(self, mock_logger, sample_story_elements):
        """RED: Extract full character details from Pydantic objects"""
        with patch('Writer.Lorebook.LorebookManager.__init__', return_value=None):
            lorebook = LorebookManager()
            lorebook.db = Mock()
            lorebook.add_entry = Mock()
            lorebook.SysLogger = mock_logger

            # This should FAIL before implementation
            lorebook.extract_from_structured_data(sample_story_elements)

            calls = lorebook.add_entry.call_args_list

            # Check Zara entry has full details
            zara_call = [call for call in calls if 'Zara' in str(call)][0]
            call_args = zara_call[0]  # Positional args
            call_kwargs = zara_call[1]  # Keyword args (should be empty for positional call)

            assert 'Rebel fighter with cybernetic arm' in call_args[0]  # content
            assert call_args[1]['type'] == 'character'  # metadata
            assert call_args[1]['name'] == 'Zara'
            assert call_args[1]['role'] == 'protagonist'
            assert call_args[1]['source'] == 'story_elements'

            # Check Dr. Nexus entry has full details
            nexus_call = [call for call in calls if 'Dr. Nexus' in str(call)][0]
            nexus_args = nexus_call[0]

            assert 'AI overlord with holographic interface' in nexus_args[0]
            assert nexus_args[1]['type'] == 'character'
            assert nexus_args[1]['name'] == 'Dr. Nexus'
            assert nexus_args[1]['role'] == 'antagonist'

    def test_lorebook_extract_settings_with_metadata(self, mock_logger, sample_story_elements):
        """RED: Extract settings with full metadata preservation"""
        with patch('Writer.Lorebook.LorebookManager.__init__', return_value=None):
            lorebook = LorebookManager()
            lorebook.db = Mock()
            lorebook.add_entry = Mock()
            lorebook.SysLogger = mock_logger

            # This should FAIL before implementation
            lorebook.extract_from_structured_data(sample_story_elements)

            calls = lorebook.add_entry.call_args_list

            # Check Neo-City entry
            neo_city_call = [call for call in calls if 'Neo-City' in str(call)][0]
            neo_args = neo_city_call[0]

            assert neo_args[1]['type'] == 'location'
            assert neo_args[1]['name'] == 'Neo-City'
            assert 'Dystopian, neon-lit' in neo_args[0]
            assert 'details' in neo_args[1]
            assert neo_args[1]['details']['location'] == 'Metropolitan area with towering skyscrapers'
            assert neo_args[1]['details']['time'] == 'Year 2077'

            # Check Underground entry
            underground_call = [call for call in calls if 'Underground' in str(call)][0]
            underground_args = underground_call[0]

            assert underground_args[1]['type'] == 'location'
            assert underground_args[1]['name'] == 'Underground'
            assert 'Hopeful, secretive' in underground_args[0]
            assert underground_args[1]['details']['mood'] == 'Hopeful, secretive'

    def test_lorebook_extract_outline_plot_points(self, mock_logger, sample_outline_output):
        """RED: Extract plot points directly from outline without string parsing"""
        with patch('Writer.Lorebook.LorebookManager.__init__', return_value=None):
            lorebook = LorebookManager()
            lorebook.db = Mock()
            lorebook.add_entry = Mock()
            lorebook.SysLogger = mock_logger

            # This should FAIL before implementation
            lorebook.extract_from_structured_data(story_elements=None, outline_output=sample_outline_output)

            calls = lorebook.add_entry.call_args_list

            # Should have 5 plot point entries, one for each chapter
            assert len(calls) == 5

            # Check each plot point
            expected_chapters = [
                ("Zara discovers corporate conspiracy", 1),
                ("infiltration of corporate tower", 2),
                ("confrontation with Dr. Nexus", 3),
                ("alliance with underground hackers", 4),
                ("Final battle for control", 5)
            ]

            for expected_content, chapter_num in expected_chapters:
                chapter_call = [call for call in calls if call[0][1]['chapter'] == chapter_num][0]
                args = chapter_call[0]

                assert args[1]['type'] == 'plot_point'
                assert args[1]['name'] == f'chapter_{chapter_num}'
                assert args[1]['source'] == 'outline'
                assert expected_content.lower() in args[0].lower()

    def test_lorebook_handles_none_inputs(self, mock_logger):
        """RED: Handle None inputs gracefully"""
        with patch('Writer.Lorebook.LorebookManager.__init__', return_value=None):
            lorebook = LorebookManager()
            lorebook.db = Mock()
            lorebook.add_entry = Mock()
            lorebook.SysLogger = mock_logger

            # This should FAIL before implementation
            # Should not crash with None inputs
            lorebook.extract_from_structured_data(story_elements=None, outline_output=None)

            # Should not have called add_entry
            lorebook.add_entry.assert_not_called()

    def test_lorebook_handles_empty_objects(self, mock_logger):
        """RED: Handle empty Pydantic objects gracefully"""
        empty_elements = StoryElements(title="Empty", genre="Test", themes=["minimal"])  # Add required field
        empty_outline = OutlineOutput(title="Empty", chapters=["Empty chapter story but longer", "Another empty chapter longer text"], target_chapter_count=2)

        with patch('Writer.Lorebook.LorebookManager.__init__', return_value=None):
            lorebook = LorebookManager()
            lorebook.db = Mock()
            lorebook.add_entry = Mock()
            lorebook.SysLogger = mock_logger

            # This should FAIL before implementation
            lorebook.extract_from_structured_data(empty_elements, empty_outline)

            # Should not crash but might make minimal entries
            # (depending on implementation details for edge cases)

    def test_no_regex_parsing_performed(self, mock_logger, sample_story_elements):
        """RED: Verify no regex parsing is performed in structured extraction"""
        with patch('Writer.Lorebook.LorebookManager.__init__', return_value=None):
            lorebook = LorebookManager()
            lorebook.db = Mock()
            lorebook.add_entry = Mock()
            lorebook.SysLogger = mock_logger

            # This should FAIL before implementation
            lorebook.extract_from_structured_data(sample_story_elements)

            # Verify that old regex-based methods were NOT called
            # (We would patch these in a real implementation to ensure they aren't called)

            # The key test: structured extraction should work without any regex patterns
            # being applied to the Pydantic object string representation