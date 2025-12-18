"""
Tests for Phase 1: Configuration Quality Updates

Verifies that quality thresholds and word count minimums have been raised
to ensure better story generation quality.
"""

import Writer.Config as Config


def test_quality_thresholds_increased():
    """Verify quality thresholds are stricter than before"""
    assert Config.OUTLINE_QUALITY == 92, \
        f"Expected OUTLINE_QUALITY=92, got {Config.OUTLINE_QUALITY}"
    assert Config.CHAPTER_QUALITY == 90, \
        f"Expected CHAPTER_QUALITY=90, got {Config.CHAPTER_QUALITY}"


def test_minimum_revisions_enforced():
    """Verify at least 1 revision required for both outline and chapter"""
    assert Config.OUTLINE_MIN_REVISIONS >= 1, \
        f"Expected OUTLINE_MIN_REVISIONS>=1, got {Config.OUTLINE_MIN_REVISIONS}"
    assert Config.CHAPTER_MIN_REVISIONS >= 1, \
        f"Expected CHAPTER_MIN_REVISIONS>=1, got {Config.CHAPTER_MIN_REVISIONS}"


def test_word_count_minimums_raised():
    """Verify word count targets increased for better content length"""
    assert Config.MIN_WORDS_CHAPTER_DRAFT == 300, \
        f"Expected MIN_WORDS_CHAPTER_DRAFT=300, got {Config.MIN_WORDS_CHAPTER_DRAFT}"
    assert Config.MIN_WORDS_SCENE_WRITE == 150, \
        f"Expected MIN_WORDS_SCENE_WRITE=150, got {Config.MIN_WORDS_SCENE_WRITE}"


def test_max_revisions_unchanged():
    """Verify MAX_REVISIONS safety limits remain unchanged"""
    assert Config.OUTLINE_MAX_REVISIONS == 3, \
        "MAX_REVISIONS should remain as safety limit"
    assert Config.CHAPTER_MAX_REVISIONS == 3, \
        "MAX_REVISIONS should remain as safety limit"
