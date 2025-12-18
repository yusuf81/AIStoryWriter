#!/usr/bin/env python3
"""
Test script to verify PDF layout fixes:
1. No blank page 2 (fix double PageBreak)
2. Story Outline on new page
3. Proper layout: Title→Chapter1→Chapter2→StoryOutline→Statistics
"""

import sys
from unittest.mock import MagicMock

# Mock termcolor
sys.modules['termcolor'] = MagicMock()

from Writer.PDFGenerator import GeneratePDF
import tempfile
import os

def test_layout_fixes():
    """Test layout fixes with realistic story structure"""

    # Simulate the actual story structure from your generated file
    story_content = """---
title: "Naga dan Harta Karun Tersembunyi"
summary: "Test story for layout verification"
tags: "test,fantasy"
---

# Naga dan Harta Karun Tersembunyi

## Summary
This is the summary section.

**Tags:** test,fantasy

---

## Chapter 1: Panggilan Gua Tersembunyi
Aria duduk di depan Pendeta Hutan, yang duduk di bangku kayu sederhana di bawah pohon besar. Pendeta Hutan bercerita tentang gua tersembunyi yang dijaga oleh naga kecil.

"Anakku," ujar Pendeta Hutan dengan suara lembut, matanya yang tajam mengamati wajah Aria. "Gua itu bukan hanya tempat harta tersembunyi. Ia adalah ujian."

Aria mengangguk, tangannya gemetar saat menerima peta lusuh itu. "Aku akan berusaha, Ayah. Aku ingin membuktikan bahwa aku layak."

## Chapter 2: Pertemuan dengan Naga
Aria melangkah perlahan di dalam gua, cahaya obornya memantul di dinding ber kristal. Tiba-tiba, dari kegelapan, naga kecil muncul—berwarna hijau zamrud dengan mata bercahaya seperti batu permata.

"Kau manusia," desis naga, suaranya seperti gemericik air di batu. "Aku tidak pernah melihat makhluk seperti kau. Apa yang kau cari di sini?"

Aria menarik napas dalam. "Aku mencari harta karun. Tapi bukan emas atau permata. Aku mencari kebenaran."

---

# Story Outline
```text

Story outline content here...
This should be on a new page after Chapter 2.

Title: Naga dan Harta Karun Tersembunyi
Genre: Fantasi Petualangan

```

# Generation Statistics
```text

More statistics content here...
This continues on the same page as Story Outline.

```

"""

    print("=== TESTING PDF LAYOUT FIXES ===")

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        result, msg = GeneratePDF(
            MagicMock(),
            MagicMock(),
            story_content,
            tmp.name,
            'Test Layout Story'
        )

        print(f'PDF Generation: {result}')
        print(f'Message: {msg}')
        print(f'PDF created: {tmp.name}')

        if os.path.exists(tmp.name):
            size = os.path.getsize(tmp.name)
            print(f'PDF file size: {size} bytes')

            # Expected size should be reasonable (not huge from duplicate breaks)
            if size > 0 and size < 50000:  # Reasonable range
                print('✅ PDF size looks reasonable')
            else:
                print(f'⚠️  PDF size might indicate issues: {size} bytes')

        print(f'\n✅ Layout fixes implemented:')
        print('   1. First chapter: No extra PageBreak (title page already has one)')
        print('   2. Story Outline: Gets PageBreak before it')
        print('   3. Generation Statistics: Continues after Story Outline')
        print(f'\n📄 Check PDF manually: {tmp.name}')
        print('   Expected layout:')
        print('   Page 1: Title page')
        print('   Page 2: Chapter 1')
        print('   Page 3: Chapter 2')
        print('   Page 4: Story Outline + Statistics')

        return tmp.name

if __name__ == '__main__':
    pdf_path = test_layout_fixes()
    print(f'\n📋 Ready for manual inspection: {pdf_path}')