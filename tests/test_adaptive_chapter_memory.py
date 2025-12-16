"""
Adaptive Chapter Memory Tests - TDD London School Approach
Tests for adaptive CHAPTER_MEMORY_WORDS based on story length
"""
import pytest
from unittest.mock import Mock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestAdaptiveChapterMemory:
    """Test adaptive memory logic for short vs long stories"""

    def test_short_story_2_chapters_uses_100_words(self, mock_logger):
        """Verify 2-chapter story uses 100 words (not 250) from previous chapter"""
        from Writer.Pipeline import _get_current_context_for_chapter_gen_pipeline_version
        import Writer.Config as Config

        # Save original config
        orig_memory_words = Config.CHAPTER_MEMORY_WORDS
        orig_use_lorebook = Config.USE_LOREBOOK
        orig_expand_outline = Config.EXPAND_OUTLINE

        try:
            # Arrange: Set config for test
            Config.CHAPTER_MEMORY_WORDS = 250  # Default value
            Config.USE_LOREBOOK = False  # Disable lorebook for simplicity
            Config.EXPAND_OUTLINE = False  # Disable outline expansion for simplicity

            # Mock Statistics
            mock_stats = Mock()
            mock_stats.GetWordCount.return_value = 100  # Will be called on result

            # Mock ActivePrompts
            mock_prompts = Mock()
            mock_prompts.PREVIOUS_CHAPTER_CONTEXT_FORMAT = "Chapter {chapter_num}: {previous_chapter_title}\n{previous_chapter_text}"
            mock_prompts.CURRENT_CHAPTER_OUTLINE_FORMAT = "Current Chapter {chapter_num}:\n{chapter_outline_text}"
            mock_prompts.MEGA_OUTLINE_PREAMBLE = "Mega Outline Preamble"
            mock_prompts.MEGA_OUTLINE_CHAPTER_FORMAT = "Chapter {chapter_num}: {chapter_title}\n{chapter_content}"
            mock_prompts.MEGA_OUTLINE_CURRENT_CHAPTER_PREFIX = ">> CURRENT << "

            # Create previous chapter with 300 words
            previous_chapter_text = " ".join([f"word{i}" for i in range(300)])

            # Mock current_state with 2 total chapters
            current_state = {
                "total_chapters": 2,
                "completed_chapters_data": [
                    {"number": 1, "title": "Chapter 1", "text": previous_chapter_text}
                ],
                "chapter_expanded_outlines": ["", "Chapter 2 outline"],
                "full_outline": "Base story outline",
                "story_elements": "Story elements",
                "expanded_chapter_outlines": [],
                "refined_global_outline": ""
            }

            # Act: Generate context for chapter 2
            result = _get_current_context_for_chapter_gen_pipeline_version(
                mock_logger(),
                Config,
                mock_stats,
                mock_prompts,
                current_state,
                chapter_num=2,
                base_context_text="Base context",
                lorebook=None
            )

            # Assert: Should use 100 words (not 250) for short story
            # Count actual words in the previous chapter segment
            # The result includes base context + previous chapter context + current outline
            # We need to verify the previous chapter segment has exactly 100 words

            # Extract the previous chapter segment from result
            # Format: "Chapter 1: Chapter 1\n{previous_chapter_text}"
            if "Chapter 1:" in result:
                # Find the previous chapter section
                parts = result.split("---")
                prev_chapter_section = None
                for part in parts:
                    if "Chapter 1:" in part:
                        prev_chapter_section = part
                        break

                if prev_chapter_section:
                    # Extract just the chapter text (after the title line)
                    lines = prev_chapter_section.strip().split("\n", 1)
                    if len(lines) > 1:
                        actual_chapter_text = lines[1].strip()
                        actual_word_count = len(actual_chapter_text.split())

                        # Should be 100 words for short story (≤3 chapters)
                        assert actual_word_count == 100, f"Expected 100 words for 2-chapter story, got {actual_word_count}"
                    else:
                        pytest.fail("Could not extract chapter text from previous chapter section")
                else:
                    pytest.fail("Could not find previous chapter section in result")
            else:
                pytest.fail("Previous chapter context not found in result")

        finally:
            # Restore original config
            Config.CHAPTER_MEMORY_WORDS = orig_memory_words
            Config.USE_LOREBOOK = orig_use_lorebook
            Config.EXPAND_OUTLINE = orig_expand_outline

    def test_short_story_3_chapters_uses_100_words(self, mock_logger):
        """Verify 3-chapter story (boundary case) uses 100 words from previous chapter"""
        from Writer.Pipeline import _get_current_context_for_chapter_gen_pipeline_version
        import Writer.Config as Config

        # Save original config
        orig_memory_words = Config.CHAPTER_MEMORY_WORDS
        orig_use_lorebook = Config.USE_LOREBOOK
        orig_expand_outline = Config.EXPAND_OUTLINE

        try:
            # Arrange
            Config.CHAPTER_MEMORY_WORDS = 250
            Config.USE_LOREBOOK = False
            Config.EXPAND_OUTLINE = False

            mock_stats = Mock()
            mock_stats.GetWordCount.return_value = 100

            mock_prompts = Mock()
            mock_prompts.PREVIOUS_CHAPTER_CONTEXT_FORMAT = "Chapter {chapter_num}: {previous_chapter_title}\n{previous_chapter_text}"
            mock_prompts.CURRENT_CHAPTER_OUTLINE_FORMAT = "Current Chapter {chapter_num}:\n{chapter_outline_text}"
            mock_prompts.MEGA_OUTLINE_PREAMBLE = "Mega Outline Preamble"
            mock_prompts.MEGA_OUTLINE_CHAPTER_FORMAT = "Chapter {chapter_num}: {chapter_title}\n{chapter_content}"
            mock_prompts.MEGA_OUTLINE_CURRENT_CHAPTER_PREFIX = ">> CURRENT << "

            # Create previous chapter with 300 words
            previous_chapter_text = " ".join([f"word{i}" for i in range(300)])

            # Mock current_state with EXACTLY 3 total chapters (boundary condition)
            current_state = {
                "total_chapters": 3,
                "completed_chapters_data": [
                    {"number": 1, "title": "Chapter 1", "text": previous_chapter_text},
                    {"number": 2, "title": "Chapter 2", "text": previous_chapter_text}
                ],
                "chapter_expanded_outlines": ["", "", "Chapter 3 outline"],
                "full_outline": "Base story outline",
                "story_elements": "Story elements",
                "expanded_chapter_outlines": [],
                "refined_global_outline": ""
            }

            # Act: Generate context for chapter 3
            result = _get_current_context_for_chapter_gen_pipeline_version(
                mock_logger(),
                Config,
                mock_stats,
                mock_prompts,
                current_state,
                chapter_num=3,
                base_context_text="Base context",
                lorebook=None
            )

            # Assert: Should use 100 words (≤3 is short story)
            if "Chapter 2:" in result:
                parts = result.split("---")
                prev_chapter_section = None
                for part in parts:
                    if "Chapter 2:" in part:
                        prev_chapter_section = part
                        break

                if prev_chapter_section:
                    lines = prev_chapter_section.strip().split("\n", 1)
                    if len(lines) > 1:
                        actual_chapter_text = lines[1].strip()
                        actual_word_count = len(actual_chapter_text.split())

                        # Should be 100 words for 3-chapter story (boundary case)
                        assert actual_word_count == 100, f"Expected 100 words for 3-chapter story, got {actual_word_count}"
                    else:
                        pytest.fail("Could not extract chapter text from previous chapter section")
                else:
                    pytest.fail("Could not find previous chapter section in result")
            else:
                pytest.fail("Previous chapter context not found in result")

        finally:
            Config.CHAPTER_MEMORY_WORDS = orig_memory_words
            Config.USE_LOREBOOK = orig_use_lorebook
            Config.EXPAND_OUTLINE = orig_expand_outline

    def test_long_story_4_chapters_uses_250_words(self, mock_logger):
        """Verify 4-chapter story uses full 250 words from previous chapter"""
        from Writer.Pipeline import _get_current_context_for_chapter_gen_pipeline_version
        import Writer.Config as Config

        # Save original config
        orig_memory_words = Config.CHAPTER_MEMORY_WORDS
        orig_use_lorebook = Config.USE_LOREBOOK
        orig_expand_outline = Config.EXPAND_OUTLINE

        try:
            # Arrange
            Config.CHAPTER_MEMORY_WORDS = 250
            Config.USE_LOREBOOK = False
            Config.EXPAND_OUTLINE = False

            mock_stats = Mock()
            mock_stats.GetWordCount.return_value = 250

            mock_prompts = Mock()
            mock_prompts.PREVIOUS_CHAPTER_CONTEXT_FORMAT = "Chapter {chapter_num}: {previous_chapter_title}\n{previous_chapter_text}"
            mock_prompts.CURRENT_CHAPTER_OUTLINE_FORMAT = "Current Chapter {chapter_num}:\n{chapter_outline_text}"
            mock_prompts.MEGA_OUTLINE_PREAMBLE = "Mega Outline Preamble"
            mock_prompts.MEGA_OUTLINE_CHAPTER_FORMAT = "Chapter {chapter_num}: {chapter_title}\n{chapter_content}"
            mock_prompts.MEGA_OUTLINE_CURRENT_CHAPTER_PREFIX = ">> CURRENT << "

            # Create previous chapter with 400 words (more than 250)
            previous_chapter_text = " ".join([f"word{i}" for i in range(400)])

            # Mock current_state with 4 total chapters (long story)
            current_state = {
                "total_chapters": 4,
                "completed_chapters_data": [
                    {"number": 1, "title": "Chapter 1", "text": previous_chapter_text},
                    {"number": 2, "title": "Chapter 2", "text": previous_chapter_text},
                    {"number": 3, "title": "Chapter 3", "text": previous_chapter_text}
                ],
                "chapter_expanded_outlines": ["", "", "", "Chapter 4 outline"],
                "full_outline": "Base story outline",
                "story_elements": "Story elements",
                "expanded_chapter_outlines": [],
                "refined_global_outline": ""
            }

            # Act: Generate context for chapter 4
            result = _get_current_context_for_chapter_gen_pipeline_version(
                mock_logger(),
                Config,
                mock_stats,
                mock_prompts,
                current_state,
                chapter_num=4,
                base_context_text="Base context",
                lorebook=None
            )

            # Assert: Should use full 250 words for long story (>3 chapters)
            if "Chapter 3:" in result:
                parts = result.split("---")
                prev_chapter_section = None
                for part in parts:
                    if "Chapter 3:" in part:
                        prev_chapter_section = part
                        break

                if prev_chapter_section:
                    lines = prev_chapter_section.strip().split("\n", 1)
                    if len(lines) > 1:
                        actual_chapter_text = lines[1].strip()
                        actual_word_count = len(actual_chapter_text.split())

                        # Should be 250 words for long story (>3 chapters)
                        assert actual_word_count == 250, f"Expected 250 words for 4-chapter story, got {actual_word_count}"
                    else:
                        pytest.fail("Could not extract chapter text from previous chapter section")
                else:
                    pytest.fail("Could not find previous chapter section in result")
            else:
                pytest.fail("Previous chapter context not found in result")

        finally:
            Config.CHAPTER_MEMORY_WORDS = orig_memory_words
            Config.USE_LOREBOOK = orig_use_lorebook
            Config.EXPAND_OUTLINE = orig_expand_outline

    def test_adaptive_memory_with_insufficient_previous_content(self, mock_logger):
        """Verify graceful handling when previous chapter has fewer words than adaptive limit"""
        from Writer.Pipeline import _get_current_context_for_chapter_gen_pipeline_version
        import Writer.Config as Config

        # Save original config
        orig_memory_words = Config.CHAPTER_MEMORY_WORDS
        orig_use_lorebook = Config.USE_LOREBOOK
        orig_expand_outline = Config.EXPAND_OUTLINE

        try:
            # Arrange
            Config.CHAPTER_MEMORY_WORDS = 250
            Config.USE_LOREBOOK = False
            Config.EXPAND_OUTLINE = False

            mock_stats = Mock()
            mock_stats.GetWordCount.return_value = 50  # Actual available words

            mock_prompts = Mock()
            mock_prompts.PREVIOUS_CHAPTER_CONTEXT_FORMAT = "Chapter {chapter_num}: {previous_chapter_title}\n{previous_chapter_text}"
            mock_prompts.CURRENT_CHAPTER_OUTLINE_FORMAT = "Current Chapter {chapter_num}:\n{chapter_outline_text}"
            mock_prompts.MEGA_OUTLINE_PREAMBLE = "Mega Outline Preamble"
            mock_prompts.MEGA_OUTLINE_CHAPTER_FORMAT = "Chapter {chapter_num}: {chapter_title}\n{chapter_content}"
            mock_prompts.MEGA_OUTLINE_CURRENT_CHAPTER_PREFIX = ">> CURRENT << "

            # Create previous chapter with ONLY 50 words (less than adaptive 100)
            previous_chapter_text = " ".join([f"word{i}" for i in range(50)])

            # Mock current_state with 2 chapters (should use 100 words, but only 50 available)
            current_state = {
                "total_chapters": 2,
                "completed_chapters_data": [
                    {"number": 1, "title": "Chapter 1", "text": previous_chapter_text}
                ],
                "chapter_expanded_outlines": ["", "Chapter 2 outline"],
                "full_outline": "Base story outline",
                "story_elements": "Story elements",
                "expanded_chapter_outlines": [],
                "refined_global_outline": ""
            }

            # Act: Generate context for chapter 2
            result = _get_current_context_for_chapter_gen_pipeline_version(
                mock_logger(),
                Config,
                mock_stats,
                mock_prompts,
                current_state,
                chapter_num=2,
                base_context_text="Base context",
                lorebook=None
            )

            # Assert: Should gracefully use all 50 available words (not fail)
            if "Chapter 1:" in result:
                parts = result.split("---")
                prev_chapter_section = None
                for part in parts:
                    if "Chapter 1:" in part:
                        prev_chapter_section = part
                        break

                if prev_chapter_section:
                    lines = prev_chapter_section.strip().split("\n", 1)
                    if len(lines) > 1:
                        actual_chapter_text = lines[1].strip()
                        actual_word_count = len(actual_chapter_text.split())

                        # Should use all 50 available words (graceful fallback)
                        assert actual_word_count == 50, f"Expected 50 words (all available), got {actual_word_count}"
                    else:
                        pytest.fail("Could not extract chapter text from previous chapter section")
                else:
                    pytest.fail("Could not find previous chapter section in result")
            else:
                pytest.fail("Previous chapter context not found in result")

        finally:
            Config.CHAPTER_MEMORY_WORDS = orig_memory_words
            Config.USE_LOREBOOK = orig_use_lorebook
            Config.EXPAND_OUTLINE = orig_expand_outline
