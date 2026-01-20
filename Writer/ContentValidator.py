"""Content validation utilities for the AIStoryWriter pipeline."""
from typing import Any, Dict, Tuple
import Writer.Config
import Writer.Statistics


def validate_content_shrinkage(
    original_text: str,
    new_text: str,
    logger: Any,
    context: str = ""
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that content has not shrunk beyond the allowed threshold.

    Args:
        original_text: The original text before LLM processing
        new_text: The new text after LLM processing
        logger: Logger instance for logging
        context: Optional context string for log messages (e.g., "Stage 2", "Scrubber")

    Returns:
        Tuple of (is_valid, validation_report)
    """
    original_word_count = Writer.Statistics.GetWordCount(original_text)
    new_word_count = Writer.Statistics.GetWordCount(new_text)

    if original_word_count == 0:
        return True, {'is_valid': True, 'reason': 'original_empty'}

    min_word_count = int(original_word_count * (1 - Writer.Config.MAX_WORD_COUNT_REDUCTION_RATIO))
    reduction_ratio = (original_word_count - new_word_count) / original_word_count

    is_valid = new_word_count >= min_word_count

    report: Dict[str, Any] = {
        'is_valid': is_valid,
        'original_word_count': original_word_count,
        'new_word_count': new_word_count,
        'min_word_count': min_word_count,
        'reduction_ratio': reduction_ratio,
        'threshold': Writer.Config.MAX_WORD_COUNT_REDUCTION_RATIO,
        'context': context
    }

    if not is_valid:
        context_str = f" ({context})" if context else ""
        logger.Log(
            f"Content shrinkage validation FAILED{context_str}: "
            f"{original_word_count} -> {new_word_count} words "
            f"({reduction_ratio*100:.1f}% reduction, max allowed: "
            f"{Writer.Config.MAX_WORD_COUNT_REDUCTION_RATIO*100:.0f}%)",
            7
        )

    return is_valid, report
