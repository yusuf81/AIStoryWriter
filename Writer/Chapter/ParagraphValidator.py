"""
Paragraph Break Validation Module

Validates that generated chapters have sufficient paragraph breaks to avoid
wall-of-text formatting issues. Particularly important for Chapter 1 where
some LLMs (e.g., Qwen) tend to remove all paragraph breaks.
"""


def validate_paragraph_breaks(text: str, chapter_num: int, native_language: str = "en"):
    """
    Validate that chapter has sufficient paragraph breaks.

    Args:
        text: Chapter text to validate
        chapter_num: Chapter number (for logging/debugging)
        native_language: Language code ('en' or 'id') for feedback message

    Returns:
        Tuple of (is_valid: bool, feedback: str)
        - is_valid: True if breaks are adequate, False otherwise
        - feedback: Feedback message for LLM retry (empty if valid), in the specified language

    Validation Rule:
        At least 1 paragraph break per 500 characters, with a minimum of 3 breaks.
        This ensures readable formatting without being overly strict.

    Example:
        >>> validate_paragraph_breaks("Para 1.\\n\\nPara 2.\\n\\nPara 3.", 1, "en")
        (True, "")
        >>> validate_paragraph_breaks("Wall of text" * 500, 1, "en")
        (False, "Output has too few paragraph breaks...")
    """
    text_length = len(text)
    break_count = text.count('\n\n')

    # Rule: At least 1 break per 500 characters, minimum 3
    min_breaks_expected = max(3, text_length // 500)

    if break_count < min_breaks_expected:
        # Get feedback in the appropriate language
        if native_language == "id":
            feedback = (
                f"Output memiliki terlalu sedikit pemisah paragraf ({break_count} paragraf "
                f"dalam {text_length} karakter). Harap tambahkan baris kosong (dua kali enter) "
                f"antara paragraf untuk memisahkan adegan, dialog, atau perubahan waktu/lokasi. "
                f"Jangan mengurangi atau mempersingkat konten. Target: minimal {min_breaks_expected} paragraf."
            )
        else:
            feedback = (
                f"Output has too few paragraph breaks ({break_count} paragraphs "
                f"in {text_length} characters). Please add blank lines (double enter) "
                f"between paragraphs to separate scenes, dialogue, or time/location changes. "
                f"Do not reduce or shorten the content. Target: minimum {min_breaks_expected} paragraphs."
            )
        return False, feedback

    return True, ""
