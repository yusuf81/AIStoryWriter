"""
Paragraph Formatter - Fallback formatting for chapter text.

This module provides fallback paragraph formatting when LLM fails to add
adequate paragraph breaks after max retries. Uses heuristic-based approach
with regex for sentence tokenization (no external NLP dependencies).

Fallback Strategy:
1. Check if text already has adequate paragraph breaks
2. If not, apply heuristic-based formatting (dialogue/scene boundaries + word count)
3. If still insufficient, force split at sentence boundaries

Author: AI Story Writer
"""

import re
from typing import Optional

import Writer.Config as Config
from Writer.Chapter.ParagraphValidator import validate_paragraph_breaks


def regex_sent_tokenize(text: str) -> list[str]:
    """
    Split text into sentences using regex.

    Handles:
    - Standard punctuation: . ! ?
    - Dialogue with quotes
    - Ellipsis (...)

    Args:
        text: Text to tokenize

    Returns:
        List of sentences
    """
    if not text or not text.strip():
        return []

    # Normalize whitespace
    text = ' '.join(text.split())

    # Pattern explanation:
    # - Look for sentence-ending punctuation (.!?)
    # - Followed by space(s)
    # - Followed by uppercase letter, quote, or opening bracket
    # - But NOT after common abbreviations (Mr. Mrs. Dr. etc.)

    # First, protect common abbreviations by replacing with placeholder
    abbreviations = [
        (r'\bMr\.', 'Mr\x00'),
        (r'\bMrs\.', 'Mrs\x00'),
        (r'\bMs\.', 'Ms\x00'),
        (r'\bDr\.', 'Dr\x00'),
        (r'\bProf\.', 'Prof\x00'),
        (r'\bSr\.', 'Sr\x00'),
        (r'\bJr\.', 'Jr\x00'),
        (r'\bvs\.', 'vs\x00'),
        (r'\betc\.', 'etc\x00'),
        (r'\bi\.e\.', 'i\x00e\x00'),
        (r'\be\.g\.', 'e\x00g\x00'),
    ]

    protected_text = text
    for pattern, replacement in abbreviations:
        protected_text = re.sub(pattern, replacement, protected_text, flags=re.IGNORECASE)

    # Also protect ellipsis by treating it as single unit
    protected_text = re.sub(r'\.\.\.', '\x01\x01\x01', protected_text)

    # Split on sentence boundaries
    # Pattern: punctuation followed by space and start of new sentence
    pattern = r'(?<=[.!?])\s+(?=[A-Z\"\'\"\'\(\[「])'
    raw_sentences = re.split(pattern, protected_text)

    # Restore abbreviations and ellipsis
    sentences = []
    for sent in raw_sentences:
        sent = sent.replace('\x00', '.')
        sent = sent.replace('\x01\x01\x01', '...')
        sent = sent.strip()
        if sent:
            sentences.append(sent)

    return sentences


def auto_format_paragraphs(text: str, target_words: Optional[int] = None) -> str:
    """
    Format text into paragraphs using heuristics.

    Priority rules:
    1. Start new paragraph before dialogue (quotes)
    2. Start new paragraph at scene indicators
    3. Start new paragraph when word count threshold reached

    Args:
        text: Text to format
        target_words: Target words per paragraph (default: Config.PARAGRAPH_TARGET_WORDS)

    Returns:
        Formatted text with paragraph breaks
    """
    if target_words is None:
        target_words = int(getattr(Config, 'PARAGRAPH_TARGET_WORDS', 150))

    sentences = regex_sent_tokenize(text)
    if not sentences:
        return text

    # Get scene indicators based on text language detection (simple heuristic)
    scene_indicators_en = getattr(Config, 'PARAGRAPH_SCENE_INDICATORS_EN', [])
    scene_indicators_id = getattr(Config, 'PARAGRAPH_SCENE_INDICATORS_ID', [])
    scene_indicators = scene_indicators_en + scene_indicators_id

    # Dialogue start characters (using unicode for smart quotes)
    dialogue_chars = (
        '"',      # Standard double quote
        "'",      # Standard single quote
        '\u201c',  # Left double quotation mark "
        '\u201d',  # Right double quotation mark "
        '\u2018',  # Left single quotation mark '
        '\u2019',  # Right single quotation mark '
        '\u300c',  # Japanese left corner bracket 「
        '\u300e',  # Japanese left white corner bracket 『
    )

    paragraphs: list[str] = []
    current_para: list[str] = []
    current_word_count = 0

    for sentence in sentences:
        words = sentence.split()
        word_count = len(words)

        # Check for natural break points
        stripped = sentence.lstrip()
        is_dialogue = stripped.startswith(dialogue_chars)
        is_scene_break = any(stripped.startswith(ind) for ind in scene_indicators)

        # Start new paragraph at natural break (if we have content)
        if (is_dialogue or is_scene_break) and current_para:
            paragraphs.append(' '.join(current_para))
            current_para = []
            current_word_count = 0

        current_para.append(sentence)
        current_word_count += word_count

        # Word count threshold - start new paragraph
        if current_word_count >= target_words:
            paragraphs.append(' '.join(current_para))
            current_para = []
            current_word_count = 0

    # Don't forget remaining sentences
    if current_para:
        paragraphs.append(' '.join(current_para))

    return '\n\n'.join(paragraphs)


def force_split_paragraphs(text: str, max_chars: int = 500) -> str:
    """
    Force split text into paragraphs at sentence boundaries.

    Last resort fallback - splits purely based on character count
    but ensures splits happen at sentence boundaries.

    Args:
        text: Text to split
        max_chars: Maximum characters per paragraph

    Returns:
        Formatted text with paragraph breaks
    """
    sentences = regex_sent_tokenize(text)
    if not sentences:
        return text

    paragraphs: list[str] = []
    current_para: list[str] = []
    current_len = 0

    for sentence in sentences:
        current_para.append(sentence)
        current_len += len(sentence) + 1  # +1 for space

        if current_len >= max_chars:
            paragraphs.append(' '.join(current_para))
            current_para = []
            current_len = 0

    # Don't forget remaining sentences
    if current_para:
        paragraphs.append(' '.join(current_para))

    return '\n\n'.join(paragraphs)


def ensure_paragraph_formatting(
    text: str,
    chapter_num: int,
    native_language: str = "en",
    target_words_per_para: Optional[int] = None
) -> tuple[str, bool]:
    """
    Ensure text has adequate paragraph breaks.

    Fallback strategy:
    1. Check if already valid -> return unchanged
    2. Apply heuristic formatting -> check again
    3. Apply force split (last resort)

    Args:
        text: Text to format
        chapter_num: Chapter number for validation
        native_language: Language code ('en' or 'id')
        target_words_per_para: Target words per paragraph (default: from Config)

    Returns:
        Tuple of (formatted_text, was_modified)
        - formatted_text: The text with paragraph breaks
        - was_modified: True if text was modified, False if already valid
    """
    # Check if already valid
    is_valid, _ = validate_paragraph_breaks(text, chapter_num, native_language)
    if is_valid:
        return text, False

    # Fallback 1: Heuristic-based formatting
    formatted = auto_format_paragraphs(text, target_words_per_para)
    is_valid, _ = validate_paragraph_breaks(formatted, chapter_num, native_language)
    if is_valid:
        return formatted, True

    # Fallback 2: Force split (last resort)
    formatted = force_split_paragraphs(formatted, max_chars=500)
    return formatted, True
