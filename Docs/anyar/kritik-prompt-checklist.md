# Checklist Implementasi Kritik Prompt (Docs/anyar/kritik-prompt.md)

Daftar ini digunakan untuk melacak implementasi perbaikan berdasarkan kritik dan rekomendasi yang diidentifikasi dalam dokumen `Docs/anyar/kritik-prompt.md`.

## Pipeline Generasi Bertahap (Stage 1/2/3)

-   [ ] **Perjelas Prompt:** Revisi prompt `CHAPTER_GENERATION_STAGE1`, `CHAPTER_GENERATION_STAGE2`, dan `CHAPTER_GENERATION_STAGE3` agar lebih fokus pada *peningkatan narasi* secara kohesif (mengintegrasikan plot, karakter, dialog) daripada hanya "menulis" atau "menambahkan" elemen secara terpisah.

## Validasi Kualitas

-   [ ] **Tingkatkan Validasi:** Jelajahi dan implementasikan alternatif untuk output boolean sederhana (`IsComplete`, `DidFollowOutline`) pada `OUTLINE_COMPLETE_PROMPT`, `SUMMARY_COMPARE_PROMPT`, dan `CHAPTER_COMPLETE_PROMPT`. Pertimbangkan skor numerik dengan rubrik atau feedback kualitatif terstruktur (misalnya dalam JSON).

## Kejelasan dan Konsistensi Prompt

-   [x] **Bersihkan Prompt Usang/Tidak Jelas:** Perjelas fungsi atau hapus prompt `EXPAND_OUTLINE_CHAPTER_BY_CHAPTER` karena ambigu dan tampaknya digantikan oleh `CHAPTER_OUTLINE_PROMPT`. # Fungsi diperjelas di Write.py sebagai refinement outline global
-   [ ] **Perkuat Prompt JSON:** Tinjau dan perkuat prompt yang meminta output JSON (`SCENES_TO_JSON`, `STATS_PROMPT`, `CHAPTER_COUNT_PROMPT`, dll.) dengan instruksi yang lebih eksplisit mengenai format, penanganan error (jika relevan), dan struktur data yang kompleks (list, nested object).

## Manajemen Konteks

-   [x] **Optimalkan Konteks `CHAPTER_EDIT_PROMPT`:** Uji coba dan implementasikan strategi untuk mengurangi konteks yang dikirim ke `CHAPTER_EDIT_PROMPT`, misalnya hanya mengirim bab N-1, N, dan N+1, bukan seluruh teks novel, untuk menghindari batas konteks LLM. # Diimplementasikan di Writer/NovelEditor.py
-   [ ] **Atasi Ukuran Konteks `STATS_PROMPT`:** Selidiki dan implementasikan strategi untuk mengurangi konteks yang dikirim saat menghasilkan info akhir (judul, ringkasan, tag), karena mengirim seluruh novel berisiko melebihi batas konteks. # Add this checklist item

## Panduan Gaya dan Genre

-   [ ] **Implementasikan Panduan Konsisten:** Manfaatkan prompt `_INTRO` (atau buat variabel pusat) untuk memberikan panduan genre, nada, dan gaya penulisan yang konsisten di seluruh tahapan penulisan kreatif (outline, generasi bab, kritik).

## Fokus Strategis

-   [ ] **Prioritaskan Pipeline Adegan:** Fokuskan upaya pengembangan dan penyempurnaan pada pipeline generasi bab berbasis adegan (`ChapterByScene`) karena potensinya untuk menghasilkan narasi yang lebih modern dan kohesif.

## Lain-lain (Berdasarkan Kritik Implisit)

-   [ ] **Tinjau `GENERATE_STORY_ELEMENTS`:** Pertimbangkan apakah prompt ini terlalu preskriptif dan apakah bisa digabungkan atau dibuat lebih fleksibel untuk mendorong kreativitas LLM.
-   [ ] **Tinjau Rating `STATS_PROMPT`:** Evaluasi kegunaan `OverallRating` 0-100 karena subjektivitasnya bagi LLM. Pertimbangkan untuk menghapusnya atau menggantinya dengan metrik lain.
