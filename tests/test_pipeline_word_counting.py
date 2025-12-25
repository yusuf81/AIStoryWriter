"""
Tests for Phase 2: Word Counting Fix

Verifies that _calculate_total_chapter_outline_words() correctly counts
ALL content from ChapterOutlineOutput, not just the outline_summary field.

This fixes the bug where expanded outlines with rich scene data were being
rejected as "too short" because only the summary was counted.
"""

import Writer.Statistics as Statistics
from Writer.Pipeline import _calculate_total_chapter_outline_words
import sys
sys.path.insert(0, '/var/www/AIStoryWriter')


def test_counts_outline_summary_only():
    """Baseline: counts outline_summary when no scenes present"""
    chapter_outline = {
        "text": "This is a summary with ten words total here now."
    }

    word_count = _calculate_total_chapter_outline_words(chapter_outline, Statistics)
    assert word_count == 10, f"Expected 10 words, got {word_count}"


def test_counts_outline_plus_string_scenes():
    """Verify counts outline_summary + string scenes"""
    chapter_outline = {
        "text": "Summary four words.",  # 3 words
        "scenes": [
            "Scene one content.",  # 3 words
            "Scene two content."   # 3 words
        ]
    }

    word_count = _calculate_total_chapter_outline_words(chapter_outline, Statistics)
    assert word_count == 9, f"Expected 9 words (3+3+3), got {word_count}"


def test_counts_outline_plus_structured_scenes():
    """Verify counts outline_summary + SceneOutline dict objects"""
    chapter_outline = {
        "text": "Summary text",  # 2 words
        "scenes": [
            {
                "setting": "Castle hall",  # 2 words
                "action": "Hero fights dragon",  # 3 words
                "purpose": "Build tension"  # 2 words
            }
        ]
    }

    word_count = _calculate_total_chapter_outline_words(chapter_outline, Statistics)
    assert word_count == 9, f"Expected 9 words (2+2+3+2), got {word_count}"


def test_counts_multiple_structured_scenes():
    """Verify counts across multiple structured scenes"""
    chapter_outline = {
        "text": "Chapter summary",  # 2 words
        "scenes": [
            {
                "setting": "Forest",  # 1 word
                "action": "Hero enters dark forest",  # 4 words
                "purpose": "Setup"  # 1 word
            },
            {
                "setting": "Cave entrance",  # 2 words
                "action": "Discovers hidden cave",  # 3 words
                "purpose": "Mystery"  # 1 word
            }
        ]
    }

    word_count = _calculate_total_chapter_outline_words(chapter_outline, Statistics)
    # 2 + (1+4+1) + (2+3+1) = 14 words
    assert word_count == 14, f"Expected 14 words, got {word_count}"


def test_handles_characters_present_list():
    """Verify counts words from character lists in scenes"""
    chapter_outline = {
        "text": "Summary",  # 1 word
        "scenes": [
            {
                "action": "Battle scene",  # 2 words
                "characters_present": ["Hero", "Villain"]  # 2 words
            }
        ]
    }

    word_count = _calculate_total_chapter_outline_words(chapter_outline, Statistics)
    assert word_count == 5, f"Expected 5 words (1+2+2), got {word_count}"


def test_mixed_string_and_dict_scenes():
    """Verify handles mix of string and dict scenes"""
    chapter_outline = {
        "text": "Summary",  # 1 word
        "scenes": [
            "String scene one",  # 3 words
            {
                "action": "Dict scene two"  # 3 words
            }
        ]
    }

    word_count = _calculate_total_chapter_outline_words(chapter_outline, Statistics)
    assert word_count == 7, f"Expected 7 words (1+3+3), got {word_count}"


def test_empty_scenes_array():
    """Verify handles empty scenes array gracefully"""
    chapter_outline = {
        "text": "Summary words here",  # 3 words
        "scenes": []
    }

    word_count = _calculate_total_chapter_outline_words(chapter_outline, Statistics)
    assert word_count == 3, f"Expected 3 words (just summary), got {word_count}"


def test_missing_scenes_key():
    """Verify handles missing scenes key gracefully"""
    chapter_outline = {
        "text": "Summary words here"  # 3 words
        # No 'scenes' key at all
    }

    word_count = _calculate_total_chapter_outline_words(chapter_outline, Statistics)
    assert word_count == 3, f"Expected 3 words (just summary), got {word_count}"


def test_missing_text_key():
    """Verify handles missing text key gracefully"""
    chapter_outline = {
        # No 'text' key
        "scenes": [
            "Scene content here"  # 3 words
        ]
    }

    word_count = _calculate_total_chapter_outline_words(chapter_outline, Statistics)
    assert word_count == 3, f"Expected 3 words (just scenes), got {word_count}"


def test_realistic_expanded_outline():
    """Test with realistic ChapterOutlineOutput structure"""
    chapter_outline = {
        "text": "Aria meets the forest elder who gives her a mysterious map",  # 11 words
        "scenes": [
            {
                "title": "Elder's Hut",  # 2 words
                "setting": "Small wooden hut in deep forest",  # 6 words
                "characters_present": ["Aria", "Forest Elder"],  # 3 words
                "action": "Aria approaches the elder seeking guidance about the ancient ruins",  # 11 words
                "purpose": "Establish mentor relationship and inciting incident"  # 6 words
            },
            {
                "title": "The Map Revealed",  # 3 words
                "setting": "Inside the elder's hut",  # 5 words
                "characters_present": ["Aria", "Forest Elder"],  # 3 words
                "action": "Elder unfolds an ancient map and explains the dangers ahead",  # 11 words
                "purpose": "Provide quest direction and build tension"  # 6 words
            }
        ]
    }

    word_count = _calculate_total_chapter_outline_words(chapter_outline, Statistics)
    # Summary: 11
    # Scene 1: 2+6+3+10+6 = 27
    # Scene 2: 3+4+3+10+6 = 26
    # Total: 11 + 27 + 26 = 64
    assert word_count == 64, f"Expected 64 words, got {word_count}"


def test_indonesian_text_word_counting():
    """Verify word counting works with Indonesian text"""
    chapter_outline = {
        "text": "Aria bertemu dengan tetua hutan yang memberikan peta misterius",  # 9 words
        "scenes": [
            {
                "action": "Aria mendekati tetua untuk mencari petunjuk",  # 6 words
                "purpose": "Membangun hubungan mentor"  # 3 words
            }
        ]
    }

    word_count = _calculate_total_chapter_outline_words(chapter_outline, Statistics)
    assert word_count == 18, f"Expected 18 words, got {word_count}"
