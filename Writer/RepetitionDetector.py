"""
Repetition detection for LLM outputs.

Detects character explosion, n-gram loops, and phrase repetition
based on research: https://arxiv.org/html/2504.12608v1
"""
from collections import Counter
from typing import Tuple, Dict, Any, Optional
import Writer.Config


class RepetitionDetector:
    """Detect repetition issues in LLM-generated text"""

    @staticmethod
    def detect_character_explosion(text: str, threshold: Optional[int] = None) -> Tuple[bool, str]:
        """
        Detect excessive consecutive character repetition.

        Args:
            text: Text to analyze
            threshold: Max consecutive chars (defaults to Config.MAX_CONSECUTIVE_CHARS)

        Returns:
            (is_detected: bool, diagnostic_message: str)

        Example:
            >>> detect_character_explosion("aaaaaaaaaaaa", 10)
            (True, "Character 'a' repeated 12 times")
        """
        threshold_value: int = threshold if threshold is not None else getattr(Writer.Config, 'MAX_CONSECUTIVE_CHARS', 10)

        if not text or len(text) < threshold_value:
            return False, ""

        max_consecutive = 1
        current_consecutive = 1
        problem_char = None

        for i in range(1, len(text)):
            if text[i] == text[i - 1]:
                current_consecutive += 1
                if current_consecutive > max_consecutive:
                    max_consecutive = current_consecutive
                    problem_char = text[i]
            else:
                current_consecutive = 1

        if max_consecutive >= threshold_value:
            return True, f"Character '{problem_char}' repeated {max_consecutive} times consecutively"

        return False, ""

    @staticmethod
    def detect_ngram_loop(text: str, ngram_size: Optional[int] = None,
                          threshold: Optional[int] = None) -> Tuple[bool, str]:
        """
        Detect phrase repetition using n-gram counting.

        Based on research: https://arxiv.org/html/2504.12608v1

        Args:
            text: Text to analyze
            ngram_size: Number of words per n-gram (defaults to Config.NGRAM_SIZE)
            threshold: Max repetitions (defaults to Config.MAX_NGRAM_REPETITIONS)

        Returns:
            (is_detected: bool, diagnostic_message: str)

        Example:
            >>> text = "The cat sat. The cat sat. The cat sat."
            >>> detect_ngram_loop(text, 3, 2)
            (True, "Phrase 'The cat sat' repeated 3 times")
        """
        ngram_size_value: int = ngram_size if ngram_size is not None else getattr(Writer.Config, 'NGRAM_SIZE', 5)
        threshold_value: int = threshold if threshold is not None else getattr(Writer.Config, 'MAX_NGRAM_REPETITIONS', 3)

        words = text.split()
        if len(words) < ngram_size_value * 2:
            return False, ""

        # Build n-grams
        ngrams = []
        for i in range(len(words) - ngram_size_value + 1):
            ngram = tuple(words[i:i + ngram_size_value])
            ngrams.append(ngram)

        # Count occurrences
        ngram_counts = Counter(ngrams)

        # Find most repeated n-gram
        for ngram, count in ngram_counts.items():
            if count >= threshold_value:
                phrase = ' '.join(ngram)
                truncated = phrase[:50] + '...' if len(phrase) > 50 else phrase
                return True, f"Phrase '{truncated}' repeated {count} times"

        return False, ""

    @staticmethod
    def detect_phrase_repetition(text: str, min_phrase_length: Optional[int] = None,
                                 threshold: Optional[int] = None) -> Tuple[bool, str]:
        """
        Detect longer phrase repetition using substring matching.

        Args:
            text: Text to analyze
            min_phrase_length: Minimum phrase length (defaults to Config.MIN_PHRASE_LENGTH)
            threshold: Max repetitions (defaults to Config.MAX_PHRASE_REPETITIONS)

        Returns:
            (is_detected: bool, diagnostic_message: str)
        """
        min_phrase_length_value: int = min_phrase_length if min_phrase_length is not None else getattr(Writer.Config, 'MIN_PHRASE_LENGTH', 20)
        threshold_value: int = threshold if threshold is not None else getattr(Writer.Config, 'MAX_PHRASE_REPETITIONS', 2)

        if len(text) < min_phrase_length_value * 2:
            return False, ""

        text_clean = text.lower().strip()

        # Sliding window to find repeated substrings
        for phrase_len in range(min_phrase_length_value, len(text_clean) // 3):
            phrase_counts = {}

            for i in range(len(text_clean) - phrase_len + 1):
                phrase = text_clean[i:i + phrase_len]
                phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

                if phrase_counts[phrase] >= threshold_value:
                    truncated = phrase[:50] + '...' if len(phrase) > 50 else phrase
                    return True, f"Long phrase '{truncated}' repeated {phrase_counts[phrase]} times"

        return False, ""

    @staticmethod
    def analyze(text: str) -> Dict[str, Any]:
        """
        Comprehensive repetition analysis.

        Returns:
            dict with detection results and recommendations
                {
                    "has_repetition": bool,
                    "character_explosion": bool,
                    "ngram_loop": bool,
                    "phrase_repetition": bool,
                    "diagnostics": {
                        "character": str,
                        "ngram": str,
                        "phrase": str
                    },
                    "should_retry": bool,
                    "text_length": int,
                    "unique_char_ratio": float
                }
        """
        char_detected, char_msg = RepetitionDetector.detect_character_explosion(text)
        ngram_detected, ngram_msg = RepetitionDetector.detect_ngram_loop(text)
        phrase_detected, phrase_msg = RepetitionDetector.detect_phrase_repetition(text)

        has_issue = char_detected or ngram_detected or phrase_detected

        return {
            "has_repetition": has_issue,
            "character_explosion": char_detected,
            "ngram_loop": ngram_detected,
            "phrase_repetition": phrase_detected,
            "diagnostics": {
                "character": char_msg,
                "ngram": ngram_msg,
                "phrase": phrase_msg
            },
            "should_retry": has_issue,
            "text_length": len(text),
            "unique_char_ratio": len(set(text)) / len(text) if text else 0
        }
