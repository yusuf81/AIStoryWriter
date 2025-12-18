"""
Tests for Phase 5: Quality System Improvements

Verifies that critic prompts have been updated with stricter quality standards,
detailed evaluation criteria, and scoring rubrics.
"""

import Writer.Prompts as Prompts
import Writer.Prompts_id as Prompts_id


def test_outline_critic_en_has_strict_criteria():
    """Verify English outline critic has strict quality criteria"""
    prompt = Prompts.CRITIC_OUTLINE_PROMPT

    assert "92/100" in prompt, \
        "Should specify minimum threshold of 92"
    assert "STRUCTURAL INTEGRITY" in prompt, \
        "Should have STRUCTURAL INTEGRITY criterion"
    assert "CHARACTER DEPTH" in prompt, \
        "Should have CHARACTER DEPTH criterion"
    assert "NARRATIVE COHESION" in prompt, \
        "Should have NARRATIVE COHESION criterion"
    assert "GENRE ALIGNMENT" in prompt, \
        "Should have GENRE ALIGNMENT criterion"
    assert "PACING & DETAIL BALANCE" in prompt, \
        "Should have PACING & DETAIL BALANCE criterion"


def test_outline_critic_id_has_strict_criteria():
    """Verify Indonesian outline critic has strict quality criteria"""
    prompt = Prompts_id.CRITIC_OUTLINE_PROMPT

    assert "92/100" in prompt, \
        "Should specify minimum threshold of 92"
    assert "INTEGRITAS STRUKTURAL" in prompt, \
        "Should have STRUCTURAL INTEGRITY in Indonesian"
    assert "KEDALAMAN KARAKTER" in prompt, \
        "Should have CHARACTER DEPTH in Indonesian"
    assert "KOHESI NARATIF" in prompt, \
        "Should have NARRATIVE COHESION in Indonesian"
    assert "KESELARASAN GENRE" in prompt, \
        "Should have GENRE ALIGNMENT in Indonesian"
    assert "KESEIMBANGAN LAJU & DETAIL" in prompt, \
        "Should have PACING & DETAIL BALANCE in Indonesian"


def test_outline_critic_en_mentions_actionable_feedback():
    """Verify English outline critic requires actionable feedback"""
    prompt = Prompts.CRITIC_OUTLINE_PROMPT

    assert "specific" in prompt.lower() and "actionable" in prompt.lower(), \
        "Should require specific, actionable feedback"
    assert "chapter numbers" in prompt.lower(), \
        "Should require feedback with chapter numbers"


def test_outline_critic_id_mentions_actionable_feedback():
    """Verify Indonesian outline critic requires actionable feedback"""
    prompt = Prompts_id.CRITIC_OUTLINE_PROMPT

    assert "spesifik" in prompt.lower() and "dapat ditindaklanjuti" in prompt.lower(), \
        "Should require specific, actionable feedback in Indonesian"
    assert "nomor bab" in prompt.lower(), \
        "Should require feedback with chapter numbers in Indonesian"


def test_outline_critic_en_updated_score_range():
    """Verify English outline critic uses 0-100 scale"""
    prompt = Prompts.CRITIC_OUTLINE_PROMPT

    assert "0-100" in prompt, \
        "Should use 0-100 score range"
    assert "minimum 92" in prompt.lower(), \
        "Should specify minimum score for acceptance"


def test_outline_critic_id_updated_score_range():
    """Verify Indonesian outline critic uses 0-100 scale"""
    prompt = Prompts_id.CRITIC_OUTLINE_PROMPT

    assert "0-100" in prompt, \
        "Should use 0-100 score range"
    assert "minimum 92" in prompt.lower(), \
        "Should specify minimum score for acceptance"


def test_chapter_critic_en_has_scoring_guide():
    """Verify English chapter critic has scoring rubric"""
    prompt = Prompts.CRITIC_CHAPTER_PROMPT

    assert "SCORING GUIDE" in prompt, \
        "Should have SCORING GUIDE section"
    assert "90-100" in prompt, \
        "Should specify excellent range (90-100)"
    assert "80-89" in prompt, \
        "Should specify good range (80-89)"
    assert "70-79" in prompt, \
        "Should specify needs improvement range (70-79)"
    assert "Below 70" in prompt, \
        "Should specify poor range (below 70)"


def test_chapter_critic_id_has_scoring_guide():
    """Verify Indonesian chapter critic has scoring rubric"""
    prompt = Prompts_id.CRITIC_CHAPTER_PROMPT

    assert "PANDUAN PENILAIAN" in prompt, \
        "Should have SCORING GUIDE in Indonesian"
    assert "90-100" in prompt, \
        "Should specify excellent range (90-100)"
    assert "80-89" in prompt, \
        "Should specify good range (80-89)"
    assert "70-79" in prompt, \
        "Should specify needs improvement range (70-79)"
    assert "Di bawah 70" in prompt, \
        "Should specify poor range in Indonesian"


def test_chapter_critic_en_has_quality_standards():
    """Verify English chapter critic has detailed quality standards"""
    prompt = Prompts.CRITIC_CHAPTER_PROMPT

    assert "NARRATIVE PROGRESSION" in prompt, \
        "Should have NARRATIVE PROGRESSION criterion"
    assert "CHARACTER AUTHENTICITY" in prompt, \
        "Should have CHARACTER AUTHENTICITY criterion"
    assert "DESCRIPTIVE BALANCE" in prompt, \
        "Should have DESCRIPTIVE BALANCE criterion"
    assert "INTERNAL CONSISTENCY" in prompt, \
        "Should have INTERNAL CONSISTENCY criterion"
    assert "GENRE MASTERY" in prompt, \
        "Should have GENRE MASTERY criterion"


def test_chapter_critic_id_has_quality_standards():
    """Verify Indonesian chapter critic has detailed quality standards"""
    prompt = Prompts_id.CRITIC_CHAPTER_PROMPT

    assert "PROGRESI NARATIF" in prompt, \
        "Should have NARRATIVE PROGRESSION in Indonesian"
    assert "AUTENTISITAS KARAKTER" in prompt, \
        "Should have CHARACTER AUTHENTICITY in Indonesian"
    assert "KESEIMBANGAN DESKRIPTIF" in prompt, \
        "Should have DESCRIPTIVE BALANCE in Indonesian"
    assert "KONSISTENSI INTERNAL" in prompt, \
        "Should have INTERNAL CONSISTENCY in Indonesian"
    assert "PENGUASAAN GENRE" in prompt, \
        "Should have GENRE MASTERY in Indonesian"


def test_chapter_critic_en_requires_specific_examples():
    """Verify English chapter critic requires specific examples"""
    prompt = Prompts.CRITIC_CHAPTER_PROMPT

    assert "line-by-line" in prompt.lower() or "scene-by-scene" in prompt.lower(), \
        "Should require line-by-line or scene-by-scene feedback"
    assert "specific" in prompt.lower() and "examples" in prompt.lower(), \
        "Should require specific examples from text"


def test_chapter_critic_id_requires_specific_examples():
    """Verify Indonesian chapter critic requires specific examples"""
    prompt = Prompts_id.CRITIC_CHAPTER_PROMPT

    assert "baris-demi-baris" in prompt.lower() or "adegan-demi-adegan" in prompt.lower(), \
        "Should require line-by-line or scene-by-scene feedback in Indonesian"
    assert "spesifik" in prompt.lower() and ("contoh" in prompt.lower() or "bagian" in prompt.lower()), \
        "Should require specific examples from text in Indonesian"


def test_chapter_critic_en_minimum_threshold():
    """Verify English chapter critic specifies minimum threshold"""
    prompt = Prompts.CRITIC_CHAPTER_PROMPT

    assert "90/100" in prompt, \
        "Should specify minimum threshold of 90"
    assert "minimum 90" in prompt.lower(), \
        "Should explicitly state minimum 90 for acceptance"


def test_chapter_critic_id_minimum_threshold():
    """Verify Indonesian chapter critic specifies minimum threshold"""
    prompt = Prompts_id.CRITIC_CHAPTER_PROMPT

    assert "90/100" in prompt, \
        "Should specify minimum threshold of 90"
    assert "minimum 90" in prompt.lower(), \
        "Should explicitly state minimum 90 for acceptance"
