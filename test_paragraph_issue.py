#!/usr/bin/env python3
"""
Debug script to understand the actual paragraph issue
"""

import sys
from unittest.mock import MagicMock

# Mock termcolor
sys.modules['termcolor'] = MagicMock()

from Writer.PDFGenerator import GeneratePDF, extract_story_content
import tempfile
import os

def test_paragraph_processing():
    """Test with exact content structure from the generated story"""

    # Simulate the exact content structure from your generated story
    story_content = """---
title: "Test Story"
summary: "Test paragraph processing"
tags: "test"
---

# Harta Karun Naga Kecil

## Summary
Test summary here.

**Tags:** test

---

## Chapter 1: Jejak Naga dan Bisikan Leluhur
Rian menarik napas dalam-dalam, aroma tanah basah dan lumut memenuhi paru-parunya saat ia melangkah meninggalkan desa. Kakeknya, Pak Tua Lintau, telah mengingatkannya tentang Gua Naga, bukan sebagai tempat harta karun berkilauan, melainkan sebagai pusaka leluhur yang menyimpan pengetahuan kuno.

Perjalanan menuju Sungai Mahakam terasa seperti ujian pertama. Air sungai berarus deras menghempas perahu bambunya, memaksanya untuk menggunakan seluruh keahlian memancing yang diajarkan Kakek. Setiap kali ombak mengancam menenggelamkan perahunya, ia merenung pada nasihat Kakek.

Di tengah hutan, akar pohon ara raksasa menyerupai ular naga purba yang melilit jalan. Rian terhenti, jantungnya berdebar kencang.

## Chapter 2: Chapter Two Here
Rian continues his journey in the second chapter.

More content follows here in the second paragraph.

## Chapter 3: Final Chapter
Third chapter content wraps up the story.

Final paragraph with conclusion."""

    print("=== TESTING EXTRACT STORY CONTENT ===")
    extracted = extract_story_content(story_content)
    print("Extracted content:")
    print(extracted)
    print()

    print("=== TESTING PDF GENERATION ===")

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        result, msg = GeneratePDF(
            MagicMock(),
            MagicMock(),
            extracted,  # Use extracted content
            tmp.name,
            'Test Story'
        )

        print(f'PDF Generation: {result}')
        print(f'Message: {msg}')
        print(f'PDF created: {tmp.name}')
        print(f'File size: {os.path.getsize(tmp.name)} bytes')

        # Keep the file for manual inspection
        print(f'PDF saved at: {tmp.name}')
        print('(Check this PDF to see if paragraphs are separated correctly)')

        return tmp.name

if __name__ == '__main__':
    pdf_path = test_paragraph_processing()
    print(f'\nPDF file for inspection: {pdf_path}')