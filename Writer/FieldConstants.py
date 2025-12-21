"""
Writer/FieldConstants.py

Robust constants and utility functions to replace fragile string patterns.
This module provides centralized field detection and pattern matching capabilities
that are maintainable and testable.

Following TDD London School approach - minimal implementation to pass tests.
"""

# Character field constants for robust detection
CHARACTER_FIELDS = {
    'characters_present',
    'character_list',
    'character_details',
    'characters',
    'characters_and_setting'
}

# Section pattern constants for PDF generation
STORY_OUTLINE = "# Story Outline"
GENERATION_STATISTICS = "# Generation Statistics"

# Support both English and Indonesian metadata sections
METADATA_SECTIONS = [
    "## Summary", "## Tags",  # English
    "## Ringkasan", "## Label"  # Indonesian
]

# Consolidated section patterns dictionary
SECTION_PATTERNS = {
    'story_outline': STORY_OUTLINE,
    'generation_statistics': GENERATION_STATISTICS,
    'metadata_sections': METADATA_SECTIONS
}

# Error pattern constants for error classification
MISSING_FIELD_ERROR = "missing"
VALIDATION_ERROR = "validation"


def is_character_field(field_name: str) -> bool:
    """
    Robust character field detection using exact matching.

    Args:
        field_name: Name of the field to check

    Returns:
        True if field is a character field, False otherwise
    """
    if field_name is None:
        return False

    return field_name.lower() in CHARACTER_FIELDS


def is_story_outline_section(line: str) -> bool:
    """
    Detect story outline section markers.

    Args:
        line: Text line to check

    Returns:
        True if line is a story outline section header
    """
    if line is None:
        return False

    # Handle extra spaces between # and text
    import re
    # Remove extra spaces after # (but keep at least one space)
    normalized = re.sub(r'^#\s+', '# ', line.strip())
    return normalized.startswith(STORY_OUTLINE)


def is_generation_statistics_section(line: str) -> bool:
    """
    Detect generation statistics section markers.

    Args:
        line: Text line to check

    Returns:
        True if line is a generation statistics section header
    """
    if line is None:
        return False

    # Handle extra spaces between # and text
    import re
    # Remove extra spaces after # (but keep at least one space)
    normalized = re.sub(r'^#\s+', '# ', line.strip())
    return normalized.startswith(GENERATION_STATISTICS)


def is_metadata_section(line: str) -> bool:
    """
    Detect metadata section markers (Summary, Tags).

    Args:
        line: Text line to check

    Returns:
        True if line is a metadata section header
    """
    if line is None:
        return False

    line_stripped = line.strip()

    # Handle extra spaces after ## for each metadata section
    import re
    for section in METADATA_SECTIONS:
        # Normalize extra spaces after ## (but keep at least one space)
        normalized = re.sub(r'^##\s+', '## ', line_stripped)
        if normalized.startswith(section):
            return True

    return False


def classify_error(error_message: str) -> list:
    """
    Classify error messages into error types.

    Args:
        error_message: Error message to classify (can be None or empty)

    Returns:
        List of error type strings found in the message
    """
    if error_message is None:
        return []

    error_str = str(error_message).lower()
    classifications = []

    if MISSING_FIELD_ERROR in error_str:
        classifications.append("missing_field")

    if VALIDATION_ERROR in error_str:
        classifications.append("validation_error")

    return classifications
