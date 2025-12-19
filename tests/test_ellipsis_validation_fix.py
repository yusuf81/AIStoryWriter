"""
Integration test for ellipsis validation fix.
Tests that ellipsis is allowed in chapter text and reasoning.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from Writer.Models import ChapterOutput, ReasoningOutput  # noqa: E402


class TestEllipsisAllowedInContent:
    """Test that ellipsis (...) is now allowed in generated content"""

    def test_chapter_with_ellipsis_dialogue(self):
        """Dialogue with ellipsis should be valid"""
        text = '"Aku tidak tahu..." bisiknya pelan. Ruangan menjadi sunyi. Hanya terdengar detak jantungnya yang berdebar kencang di tengah kegelapan malam.'

        chapter = ChapterOutput(
            text=text,
            word_count=len(text.split()),
            scenes=["Opening scene"],
            characters_present=["Protagonist"],
            chapter_number=1
        )

        assert "..." in chapter.text
        assert chapter.word_count > 0

    def test_chapter_with_trailing_ellipsis(self):
        """Suspenseful trailing ellipsis should be valid"""
        text = 'Aria melangkah hati-hati di lorong gua yang gelap dan lembap.... Suara aneh bergema dari kedalaman yang tak terjangkau oleh cahaya obor.'

        chapter = ChapterOutput(
            text=text,
            word_count=len(text.split()),
            scenes=["Cave exploration"],
            characters_present=["Aria"],
            chapter_number=2
        )

        assert chapter.text.count("....") >= 1  # Four dots for emphasis

    def test_reasoning_with_ellipsis(self):
        """Reasoning text with ellipsis should be valid"""
        text = "Character development shows growth... motivation becomes clearer in chapter 3."

        reasoning = ReasoningOutput(reasoning=text)
        assert "..." in reasoning.reasoning

    def test_placeholders_still_rejected(self):
        """Actual placeholders should still be rejected"""
        placeholders = ["TODO", "FIXME", "TBD", "[PLACEHOLDER]"]

        for placeholder in placeholders:
            text = f"Some text here {placeholder} more text needed to meet minimum length requirement for validation purposes. This text has been extended to ensure it meets the one hundred character minimum required by the validator."

            with pytest.raises(ValidationError) as exc_info:
                ChapterOutput(
                    text=text,
                    word_count=len(text.split()),
                    scenes=[],
                    characters_present=[],
                    chapter_number=1
                )

            assert "placeholder text" in str(exc_info.value).lower()
            assert placeholder in str(exc_info.value)


def main():
    """Run integration test"""
    print("=" * 60)
    print("ELLIPSIS VALIDATION FIX - INTEGRATION TEST")
    print("=" * 60)

    exit_code = pytest.main([__file__, "-v", "--tb=short"])

    if exit_code == 0:
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        print("\nValidated:")
        print("  ✓ Ellipsis allowed in chapter text")
        print("  ✓ Ellipsis allowed in reasoning")
        print("  ✓ Placeholders (TODO, FIXME, etc.) still rejected")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
