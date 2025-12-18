"""
Tests for Phase 3: Prompt Enhancements (Word Count Targets)

Verifies that explicit word count targets have been added to both English
and Indonesian prompts to guide LLMs on expected content length.
"""

import Writer.Prompts as Prompts
import Writer.Prompts_id as Prompts_id


def test_stage1_en_includes_word_count_target():
    """Verify STAGE1 English prompt has word count target"""
    assert "600-800 words" in Prompts.CHAPTER_GENERATION_STAGE1, \
        "STAGE1 should specify 600-800 word target"
    assert "WORD COUNT TARGET" in Prompts.CHAPTER_GENERATION_STAGE1, \
        "STAGE1 should have explicit WORD COUNT TARGET section"


def test_stage1_id_includes_word_count_target():
    """Verify STAGE1 Indonesian prompt has word count target"""
    assert "600-800 kata" in Prompts_id.CHAPTER_GENERATION_STAGE1, \
        "STAGE1 Indonesian should specify 600-800 kata target"
    assert "TARGET JUMLAH KATA" in Prompts_id.CHAPTER_GENERATION_STAGE1, \
        "STAGE1 Indonesian should have TARGET JUMLAH KATA section"


def test_stage2_en_includes_word_count_guidance():
    """Verify STAGE2 English prompt has word count guidance"""
    assert "200-300 words" in Prompts.CHAPTER_GENERATION_STAGE2, \
        "STAGE2 should specify 200-300 word expansion"
    assert "WORD COUNT GUIDANCE" in Prompts.CHAPTER_GENERATION_STAGE2, \
        "STAGE2 should have WORD COUNT GUIDANCE section"


def test_stage2_id_includes_word_count_guidance():
    """Verify STAGE2 Indonesian prompt has word count guidance"""
    assert "200-300 kata" in Prompts_id.CHAPTER_GENERATION_STAGE2, \
        "STAGE2 Indonesian should specify 200-300 kata expansion"
    assert "PANDUAN JUMLAH KATA" in Prompts_id.CHAPTER_GENERATION_STAGE2, \
        "STAGE2 Indonesian should have PANDUAN JUMLAH KATA section"


def test_stage3_en_includes_word_count_guidance():
    """Verify STAGE3 English prompt has word count guidance"""
    assert "150-250 words" in Prompts.CHAPTER_GENERATION_STAGE3, \
        "STAGE3 should specify 150-250 word dialogue expansion"
    assert "WORD COUNT GUIDANCE" in Prompts.CHAPTER_GENERATION_STAGE3, \
        "STAGE3 should have WORD COUNT GUIDANCE section"


def test_stage3_id_includes_word_count_guidance():
    """Verify STAGE3 Indonesian prompt has word count guidance"""
    assert "150-250 kata" in Prompts_id.CHAPTER_GENERATION_STAGE3, \
        "STAGE3 Indonesian should specify 150-250 kata dialogue expansion"
    assert "PANDUAN JUMLAH KATA" in Prompts_id.CHAPTER_GENERATION_STAGE3, \
        "STAGE3 Indonesian should have PANDUAN JUMLAH KATA section"


def test_chapter_to_scenes_en_has_scene_word_targets():
    """Verify CHAPTER_TO_SCENES English has realistic scene word targets"""
    prompt = Prompts.CHAPTER_TO_SCENES
    assert "150-250 words" in prompt, \
        "Should have simple scene word count (150-250)"
    assert "200-350 words" in prompt, \
        "Should have action scene word count (200-350)"
    assert "300-500 words" in prompt, \
        "Should have complex scene word count (300-500)"
    assert "600-1000 words total" in prompt, \
        "Should specify total chapter target"


def test_chapter_to_scenes_id_has_scene_word_targets():
    """Verify CHAPTER_TO_SCENES Indonesian has realistic scene word targets"""
    prompt = Prompts_id.CHAPTER_TO_SCENES
    assert "150-250 kata" in prompt, \
        "Should have simple scene word count in Indonesian (150-250 kata)"
    assert "200-350 kata" in prompt, \
        "Should have action scene word count in Indonesian (200-350 kata)"
    assert "300-500 kata" in prompt, \
        "Should have complex scene word count in Indonesian (300-500 kata)"
    assert "600-1000 kata" in prompt, \
        "Should specify total chapter target in Indonesian"


def test_scene_outline_to_scene_en_has_word_target():
    """Verify SCENE_OUTLINE_TO_SCENE English has word count target"""
    assert "WORD COUNT TARGET" in Prompts.SCENE_OUTLINE_TO_SCENE, \
        "Scene writing prompt should have explicit word count target"
    assert "estimated word count" in Prompts.SCENE_OUTLINE_TO_SCENE, \
        "Should reference estimated word count from scene metadata"


def test_scene_outline_to_scene_id_has_word_target():
    """Verify SCENE_OUTLINE_TO_SCENE Indonesian has word count target"""
    assert "TARGET JUMLAH KATA" in Prompts_id.SCENE_OUTLINE_TO_SCENE, \
        "Scene writing Indonesian prompt should have word count target"
    assert "jumlah kata yang diperkirakan" in Prompts_id.SCENE_OUTLINE_TO_SCENE, \
        "Should reference estimated word count in Indonesian"


def test_prompts_emphasize_quality_over_exact_count():
    """Verify prompts prioritize quality over exact word count"""
    # English prompts should mention quality/completeness
    assert "quality and completeness" in Prompts.CHAPTER_GENERATION_STAGE1.lower(), \
        "STAGE1 should emphasize quality over exact count"
    assert "depth and authenticity" in Prompts.CHAPTER_GENERATION_STAGE2.lower(), \
        "STAGE2 should emphasize depth over padding"
    assert "natural conversation" in Prompts.CHAPTER_GENERATION_STAGE3.lower(), \
        "STAGE3 should prioritize natural dialogue"

    # Indonesian prompts should have similar emphasis
    assert "kualitas dan kelengkapan" in Prompts_id.CHAPTER_GENERATION_STAGE1.lower(), \
        "Indonesian STAGE1 should emphasize quality"
    assert "kedalaman dan keaslian" in Prompts_id.CHAPTER_GENERATION_STAGE2.lower(), \
        "Indonesian STAGE2 should emphasize depth"
    assert "percakapan yang alami" in Prompts_id.CHAPTER_GENERATION_STAGE3.lower(), \
        "Indonesian STAGE3 should prioritize natural dialogue"
