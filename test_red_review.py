#!/usr/bin/env python3
"""
Simple RED test to verify ReviewOutput fails with structured suggestions
"""

import sys
sys.path.insert(0, '/var/www/AIStoryWriter')

from Writer.Models import ReviewOutput
from pydantic import ValidationError

print("RED Test: ReviewOutput with structured suggestions")
print("This should FAIL - demonstrating the validation error")
print()

try:
    # This should fail with validation error
    review = ReviewOutput(
        feedback="Outline ini memiliki kekuatan dalam menggambarkan karakter.",
        suggestions=[
            {
                "detail": "Tambahkan lebih detail tentang tantangan",
                "laju": "Perbaiki laju cerita di bab pertama",
                "alur": "Pastikan alur naratif konsisten"
            }
        ],
        rating=7
    )

    print("❌ UNEXPECTED: ReviewOutput validation passed!")
    print(f"suggestions: {review.suggestions}")
    print(f"suggestions[0] type: {type(review.suggestions[0])}")

except ValidationError as e:
    print("✅ EXPECTED: ValidationError was raised")
    print(f"Error: {e}")
    exit(0)  # Success for RED test

except Exception as e:
    print(f"❌ UNEXPECTED: {type(e).__name__}: {e}")
    exit(1)  # Unexpected error

print()
print("RED test completed - this should show validation error")