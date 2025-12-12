"""Test actual prompt usage in Indonesian."""

from Writer.PromptsHelper import get_prompts, ensure_prompts_language

def test_indonesian_prompts_are_used():
    """Verify Indonesian prompts are loaded when NATIVE_LANGUAGE is 'id'."""

    # Get prompts
    prompts = get_prompts()

    # Check that we have Indonesian content
    assert 'Bahasa Indonesia' in prompts.OUTLINE_REVISION_PROMPT
    assert 'revisi outline' in prompts.OUTLINE_REVISION_PROMPT.lower()
    assert 'Pastikan seluruh respons Anda ditulis dalam Bahasa Indonesia' in prompts.CHAPTER_GENERATION_STAGE1

    print("✓ Indonesian prompts are correctly loaded")

def test_english_prompts_are_used():
    """Verify English prompts are loaded when NATIVE_LANGUAGE is 'en'."""

    # Temporarily set language to English
    import Writer.Config as Config
    original_lang = getattr(Config, 'NATIVE_LANGUAGE', 'en')

    try:
        Config.NATIVE_LANGUAGE = 'en'
        prompts = get_prompts()

        # Should have English content (no specific "Write in English" phrase in current prompts)
        assert 'Please write the plot' in prompts.CHAPTER_GENERATION_STAGE1
        assert 'Please revise the following outline' in prompts.OUTLINE_REVISION_PROMPT

    finally:
        # Restore original
        Config.NATIVE_LANGUAGE = original_lang

    print("✓ English prompts are correctly loaded")

def test_prompt_helper_ensures_consistency():
    """Test that the helper ensures language consistency."""

    # This should not raise an assertion error
    prompts = ensure_prompts_language()
    assert prompts is not None

    print("✓ Language consistency is maintained")