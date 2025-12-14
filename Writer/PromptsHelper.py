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


def validate_prompt_format(prompt_text: str, placeholders: list) -> tuple[bool, str]:
    """
    Validate that a prompt can be safely formatted with the given placeholders.

    Args:
        prompt_text: The prompt template to validate
        placeholders: List of placeholder names (without underscores)

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        is_valid, error = validate_prompt_format(
            "Hello {_Name}", ["Name"]
        )
    """
    # Create test values
    test_values = {f"_{p}": f"TEST_{p}" for p in placeholders}

    try:
        formatted = prompt_text.format(**test_values)

        # Check for unescaped JSON braces that would cause KeyError
        if ('{' in formatted or '}' in formatted) and not (('{{' in formatted or '}}' in formatted)):
            # This might indicate unescaped JSON
            json_indicators = ['"feedback":', '"rating":', '"suggestions":', '"detail":', '"pacing":', '"flow":']
            if any(indicator in formatted for indicator in json_indicators):
                return False, "Unescaped JSON braces detected - use {{}} instead of {}"

        return True, ""
    except KeyError as e:
        return False, f"Missing placeholder: {e}"
    except Exception as e:
        return False, f"Formatting error: {e}"


def validate_all_prompts() -> tuple[bool, list]:
    """
    Validate all prompts in both language modules for JSON format issues.

    Returns:
        Tuple of (all_valid, list_of_issues)
    """
    issues = []

    # Check both English and Indonesian prompts
    from Writer import Prompts as EnglishPrompts
    english_prompts = {k: v for k, v in vars(EnglishPrompts).items()
                      if not k.startswith('_') and isinstance(v, str)}

    # Get Indonesian prompts
    if getattr(Config, 'NATIVE_LANGUAGE', 'en') == 'id':
        from Writer import Prompts_id as IndonesianPrompts
    else:
        from Writer import Prompts_id as IndonesianPrompts

    indonesian_prompts = {k: v for k, v in vars(IndonesianPrompts).items()
                         if not k.startswith('_') and isinstance(v, str)}

    all_prompts = [
        ('English', english_prompts),
        ('Indonesian', indonesian_prompts)
    ]

    for lang_name, prompts in all_prompts:
        for prompt_name, prompt_text in prompts.items():
            # Check for unescaped JSON patterns
            if '{"' in prompt_text and not '{{' in prompt_text:
                # Look for JSON key patterns
                json_keys = ['"feedback":', '"rating":', '"suggestions":', '"detail":', '"pacing":', '"flow":', '"laju":', '"alur":']
                if any(key in prompt_text for key in json_keys):
                    issues.append(f"{lang_name}.{prompt_name}: Contains unescaped JSON braces")

    return len(issues) == 0, issues