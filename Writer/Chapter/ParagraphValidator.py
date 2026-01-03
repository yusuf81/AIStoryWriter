"""
Paragraph Break Validation Module

Validates that generated chapters have sufficient paragraph breaks to avoid
wall-of-text formatting issues. Particularly important for Chapter 1 where
some LLMs (e.g., Qwen) tend to remove all paragraph breaks.
"""


def validate_paragraph_breaks(text: str, chapter_num: int):
    """
    Validate that chapter has sufficient paragraph breaks.

    Args:
        text: Chapter text to validate
        chapter_num: Chapter number (for logging/debugging)

    Returns:
        Tuple of (is_valid: bool, feedback: str)
        - is_valid: True if breaks are adequate, False otherwise
        - feedback: Indonesian feedback message for LLM retry (empty if valid)

    Validation Rule:
        At least 1 paragraph break per 500 characters, with a minimum of 3 breaks.
        This ensures readable formatting without being overly strict.

    Example:
        >>> validate_paragraph_breaks("Para 1.\\n\\nPara 2.\\n\\nPara 3.", 1)
        (True, "")
        >>> validate_paragraph_breaks("Wall of text" * 500, 1)
        (False, "Output memiliki terlalu sedikit pemisah paragraf...")
    """
    text_length = len(text)
    break_count = text.count('\n\n')

    # Rule: At least 1 break per 500 characters, minimum 3
    min_breaks_expected = max(3, text_length // 500)

    if break_count < min_breaks_expected:
        feedback = (
            f"Output memiliki terlalu sedikit pemisah paragraf ({break_count} paragraf "
            f"dalam {text_length} karakter). Harap pisahkan teks menjadi paragraf-paragraf "
            f"yang lebih pendek dengan menambahkan baris kosong (dua kali enter) antara "
            f"adegan, dialog, atau perubahan waktu/lokasi. Target: minimal {min_breaks_expected} paragraf."
        )
        return False, feedback

    return True, ""
