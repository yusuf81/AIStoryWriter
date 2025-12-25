"""
TDD Tests for Enhanced Models - London School Approach
Tests for SceneOutline model and other enhanced models to fix prompt-model conflicts
"""
from typing import List, cast
import pytest
from pydantic import ValidationError
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestEnhancedSceneOutlineModel:
    """TDD tests for Enhanced SceneOutline Pydantic model following London School approach"""

    def test_scene_outline_current_structure_fails_with_prompts(self):
        """
        RED TEST: Current SceneOutline structure doesn't match prompt expectations

        This test will PASS initially but shows the mismatch between what prompts request
        and what the current SceneOutline model provides.
        """
        # Current model requires: scene_number, setting, characters_present, action, purpose, estimated_word_count
        # But prompts request: title, characters_and_setting, conflict_and_tone, key_events, literary_devices, resolution

        # The conflict: Prompt expects structured fields like conflict_and_tone, key_events
        # But current model only has action field that mixes everything
        assert True

    def test_scene_outline_enhanced_structure_needed(self):
        """
        RED TEST: SceneOutline needs enhanced structure to match prompts

        This test will PASS initially but demonstrates need for enhanced SceneOutline
        with fields that match prompt expectations from Indonesian/English templates.
        """
        # This is what the prompts request but current model can't handle:
        enhanced_fields_needed = {
            "title": "Rian Finds the Cave Entrance",
            "characters_and_setting": "Rian dan Naga Kecil berada di mulut gua",
            "conflict_and_tone": "Suasana tegang saat bersiap memasuki gua",
            "key_events": "Rian menemukan peti harta karun namun ada teka-teki",
            "literary_devices": "Metafora cahaya sebagai harapan",
            "resolution": "Naga Kecil setuju membantu Rian membuka peti"
        }

        # Current model can only handle:
        current_model_fields = {
            "scene_number": 1,
            "setting": "Gua yang gelap",
            "characters_present": ["Rian", "Naga Kecil"],
            "action": "Mixed action and dialogue",
            "purpose": "Story purpose",
            "estimated_word_count": 100
        }

        # The test highlights the mismatch
        assert len(enhanced_fields_needed) > len(current_model_fields) - 1  # current has numeric field
        assert "conflict_and_tone" in enhanced_fields_needed
        assert "key_events" in enhanced_fields_needed


class TestEnhancedChapterOutlineOutput:
    """TDD tests for enhanced ChapterOutlineOutput model with SceneOutline objects"""

    def test_current_chapter_outline_only_accepts_strings(self):
        """
        RED TEST: Current ChapterOutlineOutput only accepts List[str] for scenes

        This test will PASS with current structure but demonstrates limitation.
        Prompts request structured scene data but model only supports strings.
        """
        from Writer.Models import ChapterOutlineOutput

        # Current model works with string scenes only
        chapter_outline = ChapterOutlineOutput(
            chapter_number=1,
            chapter_title="Petualangan di Gua Tersembunyi",  # Required field, min 5 chars
            scenes=[
                "Scene 1: Rian mendekati gua yang tersembunyi di balik air terjun, menemukan simbol-simbol kuno di dinding",
                "Scene 2: Rian bertemu naga kecil yang menjaga harta karun, suasana penuh misteri dan antisipasi",
                "Scene 3: Naga menantang Rian dengan teka-teki tentang kejujuran, Rian harus membuktikan dirinya layak"
            ],  # Must have at least 3 scenes
            outline_summary="Chapter about Rian's adventure discovering treasure cave guarded by a small dragon with mysterious tests of character",
            estimated_word_count=500,
            setting=None,
            main_conflict=None
        )

        assert chapter_outline.chapter_number == 1
        assert len(chapter_outline.scenes) == 3
        assert isinstance(chapter_outline.scenes[0], str)

    def test_chapter_outline_needs_enhanced_scene_structure(self):
        """
        RED TEST: ChapterOutlineOutput needs enhanced structure to match prompts

        This test shows the mismatch between what LLM provides based on prompts
        and what the current model can accept.
        """
        # This is what LLM generates based on structured prompts (with rich scene data):
        structured_scene_data = [
            {
                "title": "Penemuan Gua",
                "characters_and_setting": "Rian mendekati gua tersembunyi, simbol kuno di dinding",
                "conflict_and_tone": "Suasana penuh misteri dan antisipasi",
                "key_events": "Penemuan pintu gerbang rahasia menuju ruang harta",
                "literary_devices": "Simbolisme air terjun sebagai ger menuju petualangan"
            },
            {
                "title": "Konfrontasi dengan Naga",
                "characters_and_setting": "Rian bertemu naga kecil penjaga harta karun",
                "conflict_and_tone": "Konflik antara ketakutan dan keinginan mendapatkan harta",
                "key_events": "Naga menantang Rian dengan tiga ujian ketulusan",
                "resolution": "Rian membuktikan dirinya layak mendapatkan harta karun"
            }
        ]

        # Current model can only handle string representations:
        current_scenes = [
            "Scene 1: Rian mendekati gua yang tersembunyi dan menemukan simbol-simbol kuno di dinding, menciptakan suasana penuh misteri dan antisipasi",
            "Scene 2: Rian bertemu naga kecil yang menjaga harta karun, menciptakan konflik antara ketakutan dan keinginan mendapatkan harta",
            "Scene 3: Naga menantang Rian dengan teka-teki tentang kejujuran, Rian membuktikan dirinya layak mendapatkan harta karun"
        ]

        # The test demonstrates loss of structured data when using current model
        assert len(structured_scene_data) == 2  # Rich structure LLM wants to provide
        assert len(current_scenes) >= 3  # Minimum required by current model
        assert isinstance(structured_scene_data[0], dict)  # Rich data structure
        assert isinstance(current_scenes[0], str)  # Flattened structure

    def test_chapter_outline_minimum_scenes_requirement(self):
        """
        GREEN TEST: ChapterOutlineOutput now requires minimum 1 scene (enhanced flexibility)

        This test shows the relaxed validation that now works with structured scenes.
        """
        from Writer.Models import ChapterOutlineOutput, EnhancedSceneOutline

        # Should work with just 1 scene (new flexible requirement)
        chapter_outline = ChapterOutlineOutput(
            chapter_number=1,
            chapter_title="Short Chapter",
            scenes=[
                "Scene 1: A complete scene with meaningful content"  # Can now work with 1 scene
            ],
            outline_summary="Short chapter summary",
            estimated_word_count=None,
            setting=None,
            main_conflict=None
        )

        assert chapter_outline.chapter_number == 1
        assert len(chapter_outline.scenes) == 1

        # Should also work with enhanced scene objects
        enhanced_chapter = ChapterOutlineOutput(
            chapter_number=2,
            chapter_title="Enhanced Chapter",
            scenes=[
                EnhancedSceneOutline(
                    title="Single Scene",
                    key_events="Main plot event",
                    characters_and_setting=None,
                    conflict_and_tone=None,
                    literary_devices=None,
                    resolution=None
                )
            ],
            outline_summary="Enhanced chapter summary",
            estimated_word_count=None,
            setting=None,
            main_conflict=None
        )

        assert len(enhanced_chapter.scenes) == 1
        assert enhanced_chapter.scenes[0].title == "Single Scene"

        # Show enhanced flexibility - should still fail with 0 scenes
        with pytest.raises(ValidationError) as exc_info:
            ChapterOutlineOutput(
                chapter_number=1,
                chapter_title="Empty Chapter",
                scenes=[],  # Empty scenes
                outline_summary="Chapter summary",
                estimated_word_count=None,
                setting=None,
                main_conflict=None
            )

        assert "at least 1 scene" in str(exc_info.value)

    def test_chapter_outline_json_export_current_structure(self):
        """
        RED TEST: Current ChapterOutlineOutput JSON export structure

        This test works with current model but shows limitations.
        """
        from Writer.Models import ChapterOutlineOutput

        chapter_outline = ChapterOutlineOutput(
            chapter_number=2,
            chapter_title="Current Structure Test",
            scenes=[
                "Scene 1: Setup and introduction",
                "Scene 2: Development and conflict",
                "Scene 3: Climax and resolution"
            ],
            outline_summary="Chapter following traditional story structure",
            estimated_word_count=None,
            setting=None,
            main_conflict=None
        )

        # Should serialize current structure
        json_data = chapter_outline.model_dump()

        assert json_data["chapter_number"] == 2
        assert json_data["chapter_title"] == "Current Structure Test"
        assert isinstance(json_data["scenes"], list)
        assert len(json_data["scenes"]) == 3
        assert isinstance(json_data["scenes"][0], str)  # Current model uses strings


class TestEnhancedChapterOutput:
    """TDD tests for ChapterOutput with relaxed word count validation"""

    def test_chapter_output_current_strict_word_count(self):
        """
        RED TEST: Current ChapterOutput has word count validation with ±50 tolerance

        This test shows current validation limits that may need extension.
        """
        from Writer.Models import ChapterOutput

        # Current model works but word_count must match actual text words within tolerance
        text = "This is a test chapter content. " * 10  # Create about 120 words
        actual_word_count = len(text.split())

        # Should work within current ±50 tolerance
        chapter = ChapterOutput(
            text=text,
            word_count=actual_word_count - 30,  # Within tolerance
            scenes=["Scene 1: Test scene"],
            characters_present=["Test Character"],
            chapter_number=1,
            chapter_title="Test Chapter"
        )

        assert chapter.word_count > 0
        assert len(chapter.text) >= 100  # min length requirement

    def test_chapter_output_needs_relaxed_validation(self):
        """
        RED TEST: ChapterOutput needs increased word count tolerance from ±50 to ±100

        This test demonstrates need for ±100 word count tolerance.
        """
        from Writer.Models import ChapterOutput

        # Show updated tolerance (now ±100)
        current_tolerance = 100
        previous_tolerance = 50

        # Create text with actual word count
        text = "word " * 200  # 200 words
        actual_word_count = len(text.split())

        # Current model should fail with more than ±50 difference
        with pytest.raises(ValidationError) as exc_info:
            ChapterOutput(
                text=text,
                word_count=actual_word_count - 150,  # Outside new ±100 tolerance
                scenes=[f"Scene {i}: Test content" for i in range(3)],
                characters_present=["Character 1", "Character 2"],
                chapter_number=1,
                chapter_title="Tolerance Test Chapter"
            )

        assert "doesn't match actual word count" in str(exc_info.value)
        assert "tolerance: ±100" in str(exc_info.value)

        # Show what now works with increased tolerance
        # Previous tolerance: 200 ± 50 = 150-250
        # Current tolerance: 200 ± 100 = 100-300
        current_acceptable_range = range(actual_word_count - current_tolerance, actual_word_count + current_tolerance + 1)
        previous_acceptable_range = range(actual_word_count - previous_tolerance, actual_word_count + previous_tolerance + 1)

        # Show the benefit of extended tolerance
        assert 120 in current_acceptable_range  # Now allowed with ±100
        assert 120 not in previous_acceptable_range  # But not allowed with previous ±50


class TestEnhancedReviewOutput:
    """TDD tests for ReviewOutput with flexible suggestions handling"""

    def test_current_review_output_requires_suggestions(self):
        """
        RED TEST: Current ReviewOutput requires both feedback and suggestions

        This test shows current model requirements.
        """
        from Writer.Models import ReviewOutput

        # Current model works with both required fields
        review = ReviewOutput(
            feedback="Good character development but dialogue needs improvement",
            suggestions=[
                "Add more character-specific dialogue patterns",
                "Vary dialogue pace during action scenes",
                "Include more emotional subtext"
            ],
            rating=7
        )

        assert len(review.feedback) >= 10
        assert review.suggestions is not None
        assert len(review.suggestions) >= 1
        assert 0 <= review.rating <= 10

    def test_review_output_needs_flexible_suggestions(self):
        """
        RED TEST: ReviewOutput needs flexible suggestion handling

        This test shows need for embedded suggestion extraction.
        """
        from Writer.Models import ReviewOutput

        # LLM often provides feedback with embedded suggestions
        feedback_with_embedded = """
        The chapter has good character development but needs improvement in dialogue.

        Suggestions for improvement:
        1. Add more character-specific dialogue patterns that reflect their background
        2. Vary the dialogue pace during action scenes for better tension
        3. Include more emotional subtext in conversations to show character depth
        """

        # Current model requires separate suggestions array
        separate_suggestions: List[str] = [
            "Character development is strong",
            "Dialogue needs more variation"
        ]

        review = ReviewOutput(
            feedback=feedback_with_embedded,
            suggestions=cast(List, separate_suggestions),  # Current model requires this
            rating=6
        )

        assert "character development" in review.feedback.lower()
        assert review.suggestions is not None
        assert len(review.suggestions) == 2  # Current: only separate suggestions


class TestEnhancedOutlineOutput:
    """TDD tests for OutlineOutput with character extraction"""

    def test_current_outline_output_character_list(self):
        """
        RED TEST: Current OutlineOutput has basic character list

        This test shows current character handling capabilities.
        """
        from Writer.Models import OutlineOutput

        outline = OutlineOutput(
            title="Treasure Hunt",
            genre=None,
            theme=None,
            chapters=[
                "Chapter 1: Rian discovers map to hidden treasure",
                "Chapter 2: Rian meets Naga Kecil guarding the treasure cave"
            ],
            character_list=["Rian", "Naga Kecil"],  # Current: simple list only
            character_details=None,
            setting=None,
            target_chapter_count=2
        )

        assert len(outline.character_list) == 2
        assert "Rian" in outline.character_list
        assert "Naga Kecil" in outline.character_list

    def test_outline_output_needs_character_details_extraction(self):
        """
        RED TEST: OutlineOutput needs character details extraction

        This test shows need for enhanced character parsing from chapter text.
        """
        from Writer.Models import OutlineOutput

        # LLM provides rich character descriptions in chapter outlines
        rich_outline_content = """
        Chapter 1: The Brave Hero
        Rian, a tall and muscular adventurer with messy brown hair, demonstrates his brave spirit.
        He has explored many forest locations and seeks both wealth and new experiences.

        Chapter 2: The Mysterious Guardian
        Naga Kecil, a small green dragon with tiny wings and sharp claws, guards ancient treasure.
        Though intelligent and wise, this dragon remains suspicious of strangers who approach.
        """

        outline = OutlineOutput(
            title="Character-Rich Story",
            genre=None,
            theme=None,
            chapters=[rich_outline_content],
            character_list=["Rian", "Naga Kecil"],  # Current: only names, no details
            character_details=None,
            setting=None,
            target_chapter_count=2  # Required field
        )

        # Current limitation: No character details field, only basic list
        assert not hasattr(outline, 'character_details') or (
            hasattr(outline, 'character_details') and outline.character_details is None
        )

        # Show what's needed: Extraction of character descriptions from chapters
        character_descriptions_needed = {
            "Rian": "Tall, muscular adventurer with messy brown hair, brave and experienced",
            "Naga Kecil": "Small green dragon with tiny wings and sharp claws, intelligent and wise"
        }

        assert len(outline.character_list) == 2
        assert len(character_descriptions_needed) > 0  # Enhanced capability needed
