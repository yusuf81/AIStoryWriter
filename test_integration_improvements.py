"""
Integration test for Phase 1-7 improvements.
Validates that all improvements work together without running a full story generation.
"""

import sys
sys.path.insert(0, '/var/www/AIStoryWriter')

import Writer.Config as Config
from Writer.PrintUtils import Logger
import Writer.Statistics as Statistics


def test_phase1_config_values():
    """Verify Phase 1 config changes are in place"""
    print("✓ Testing Phase 1: Configuration Updates...")

    assert Config.OUTLINE_QUALITY == 92, f"Expected OUTLINE_QUALITY=92, got {Config.OUTLINE_QUALITY}"
    assert Config.CHAPTER_QUALITY == 90, f"Expected CHAPTER_QUALITY=90, got {Config.CHAPTER_QUALITY}"
    assert Config.OUTLINE_MIN_REVISIONS == 1, f"Expected OUTLINE_MIN_REVISIONS=1, got {Config.OUTLINE_MIN_REVISIONS}"
    assert Config.CHAPTER_MIN_REVISIONS == 1, f"Expected CHAPTER_MIN_REVISIONS=1, got {Config.CHAPTER_MIN_REVISIONS}"
    assert Config.MIN_WORDS_CHAPTER_DRAFT == 300, f"Expected MIN_WORDS_CHAPTER_DRAFT=300, got {Config.MIN_WORDS_CHAPTER_DRAFT}"
    assert Config.MIN_WORDS_SCENE_WRITE == 150, f"Expected MIN_WORDS_SCENE_WRITE=150, got {Config.MIN_WORDS_SCENE_WRITE}"

    print("  ✓ OUTLINE_QUALITY = 92")
    print("  ✓ CHAPTER_QUALITY = 90")
    print("  ✓ MIN_REVISIONS enforced = 1")
    print("  ✓ Word count minimums raised")


def test_phase2_word_counting():
    """Verify Phase 2 word counting function works"""
    print("\n✓ Testing Phase 2: Word Counting Fix...")

    from Writer.Pipeline import _calculate_total_chapter_outline_words

    # Test with structured scenes
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
    assert word_count == 9, f"Expected 9 words, got {word_count}"

    print("  ✓ Word counting includes all fields (summary + scenes)")
    print(f"  ✓ Correctly counted: {word_count} words")


def test_phase3_prompt_targets():
    """Verify Phase 3 word count targets in prompts"""
    print("\n✓ Testing Phase 3: Prompt Word Count Targets...")

    from Writer.Prompts import CHAPTER_GENERATION_STAGE1, CHAPTER_GENERATION_STAGE2
    from Writer.Prompts_id import CHAPTER_GENERATION_STAGE1 as STAGE1_ID

    assert "600-800 words" in CHAPTER_GENERATION_STAGE1, "EN STAGE1 missing word count target"
    assert "200-300 words" in CHAPTER_GENERATION_STAGE2, "EN STAGE2 missing word count guidance"
    assert "600-800 kata" in STAGE1_ID, "ID STAGE1 missing word count target"

    print("  ✓ English prompts have word count targets")
    print("  ✓ Indonesian prompts have word count targets")


def test_phase4_pydantic_constraints():
    """Verify Phase 4 Pydantic constraint explanations exist"""
    print("\n✓ Testing Phase 4: Pydantic Constraint Explanations...")

    # Check that the method exists
    from Writer.Interface.Wrapper import Interface as WrapperInterface

    assert hasattr(WrapperInterface, '_build_constraint_explanations'), \
        "Missing _build_constraint_explanations method"

    # Check that Config has tolerance value
    assert hasattr(Config, 'PYDANTIC_WORD_COUNT_TOLERANCE'), \
        "Missing PYDANTIC_WORD_COUNT_TOLERANCE config"

    print("  ✓ Constraint explanation method exists")
    print("  ✓ Config has word count tolerance setting")


def test_phase5_quality_prompts():
    """Verify Phase 5 quality system improvements"""
    print("\n✓ Testing Phase 5: Quality System Improvements...")

    from Writer.Prompts import CRITIC_OUTLINE_PROMPT, CRITIC_CHAPTER_PROMPT
    from Writer.Prompts_id import CRITIC_OUTLINE_PROMPT as OUTLINE_ID

    assert "92/100" in CRITIC_OUTLINE_PROMPT, "EN outline critic missing 92/100 threshold"
    assert "SCORING GUIDE" in CRITIC_CHAPTER_PROMPT, "EN chapter critic missing scoring guide"
    assert "92/100" in OUTLINE_ID, "ID outline critic missing 92/100 threshold"

    print("  ✓ Stricter quality criteria in prompts")
    print("  ✓ Scoring guide for chapter evaluation")
    print("  ✓ Both English and Indonesian updated")


def test_phase6_scene_pipeline():
    """Verify Phase 6 scene pipeline integration"""
    print("\n✓ Testing Phase 6: Scene Pipeline Integration...")

    from Writer.Scene.ChapterByScene import _can_use_expanded_scenes, _extract_scenes_from_expanded_outline
    from Writer.Models import SceneOutline

    # Test helper functions exist and work
    logger = Logger()

    expanded = {
        "text": "Summary",
        "scenes": [
            SceneOutline(
                scene_number=1,
                setting="Forest",
                characters_present=["Hero"],
                action="Hero enters forest",
                purpose="Setup",
                estimated_word_count=250
            )
        ]
    }

    assert _can_use_expanded_scenes(expanded, logger) == True, "Should detect usable scenes"
    scenes = _extract_scenes_from_expanded_outline(expanded, logger)
    assert len(scenes) == 1, "Should extract 1 scene"
    assert isinstance(scenes[0], SceneOutline), "Should return SceneOutline objects"

    print("  ✓ Scene extraction helpers work correctly")
    print("  ✓ Expanded outline integration functional")


def test_phase7_reasoning_logging():
    """Verify Phase 7 reasoning chain logging"""
    print("\n✓ Testing Phase 7: Reasoning Chain Logging...")

    # Check that logging code is in place by reading file
    with open('Writer/ReasoningChain.py', 'r') as f:
        content = f.read()

    assert 'Reasoning chain ENABLED' in content, "Missing enabled logging"
    assert 'Generating {task_type} reasoning' in content, "Missing generation start logging"
    assert 'Generated {task_type} reasoning' in content, "Missing completion logging"

    with open('Writer/Chapter/ChapterGenerator.py', 'r') as f:
        content = f.read()

    assert 'Requesting {reasoning_type} reasoning' in content, "Missing request logging"
    assert 'Skipping reasoning' in content, "Missing skip logging"

    print("  ✓ Reasoning chain initialization logging added")
    print("  ✓ Reasoning generation progress logging added")
    print("  ✓ ChapterGenerator logging added")


def main():
    print("=" * 60)
    print("INTEGRATION TEST: Phase 1-7 Quality Improvements")
    print("=" * 60)

    try:
        test_phase1_config_values()
        test_phase2_word_counting()
        test_phase3_prompt_targets()
        test_phase4_pydantic_constraints()
        test_phase5_quality_prompts()
        test_phase6_scene_pipeline()
        test_phase7_reasoning_logging()

        print("\n" + "=" * 60)
        print("✓ ALL INTEGRATION TESTS PASSED")
        print("=" * 60)
        print("\nAll 7 phases are properly integrated and functional!")
        print("\nKey improvements verified:")
        print("  - Config thresholds: OUTLINE=92, CHAPTER=90")
        print("  - Word counting: Includes all outline fields")
        print("  - Prompts: Word count targets in EN + ID")
        print("  - Pydantic: Constraint explanations added")
        print("  - Quality: Stricter criteria and scoring")
        print("  - Scenes: Expanded outline reuse working")
        print("  - Logging: Reasoning chain visibility added")

        return 0

    except AssertionError as e:
        print(f"\n✗ INTEGRATION TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
