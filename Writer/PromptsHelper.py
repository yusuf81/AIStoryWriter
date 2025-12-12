"""Helper module to handle dynamic prompt imports based on language."""

import Writer.Config as Config


def get_prompts():
    """
    Get the correct prompts module based on NATIVE_LANGUAGE setting.

    Returns:
        Prompts module (either Writer.Prompts or Writer.Prompts_id)
    """
    if getattr(Config, 'NATIVE_LANGUAGE', 'en') == 'id':
        from Writer import Prompts_id as Prompts
    else:
        from Writer import Prompts

    return Prompts


def ensure_prompts_language():
    """
    Ensure we're using the correct language prompts.
    Can be called to verify language consistency.
    """
    prompts = get_prompts()
    lang = getattr(Config, 'NATIVE_LANGUAGE', 'en')

    # Check if prompts have the expected language indicators
    if lang == 'id':
        # Indonesian prompts should contain Indonesian text
        assert hasattr(prompts, 'OUTLINE_REVISION_PROMPT')
        assert 'Bahasa Indonesia' in str(prompts.OUTLINE_REVISION_PROMPT), \
            "Expected Indonesian prompts but got English"

    return prompts