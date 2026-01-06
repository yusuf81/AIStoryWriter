# Rencana Urutan Prompt untuk AI Story Writer

**Status Update (2025-12-11):** ❌ **TIDAK TERIMPLEMENTASI** - Ini adalah proposal reorganisasi yang belum dijalankan.

**Current Reality:** Writer/Prompts.py menggunakan urutan berbeda (tidak strict sesuai workflow). Prompts diorganisir secara alphabetical-ish dan berdasarkan kapan ditambahkan, bukan workflow logical order.

Berikut adalah urutan yang diusulkan untuk prompt dalam file `Writer/Prompts.py` dan `Writer/Prompts_id.py`, berdasarkan alur kerja pemrosesan dari awal hingga akhir.

## 📊 Status Implementasi

| Prompt Kategori | Jumlah dalam Plan | Status | Notes |
|-----------------|-------------------|--------|-------|
| I. Sistem & Inisiasi | 3 | ✅ Ada semua | DEFAULT_SYSTEM_PROMPT, GET_IMPORTANT_BASE_PROMPT_INFO, GENERATE_STORY_ELEMENTS |
| II. Outline Keseluruhan | 8 | ✅ Ada semua | Termasuk EXPAND_OUTLINE_CHAPTER_BY_CHAPTER (dead code) |
| III. Per Bab | 23 | ⚠️ Sebagian | Beberapa prompt ada, tapi urutan berbeda |
| IV. Finalisasi | 3 | ✅ Ada semua | CHAPTER_EDIT_PROMPT, CHAPTER_SCRUB_PROMPT, STATS_PROMPT |
| V. Evaluasi | 3 | ✅ Ada semua | EVALUATE_* prompts |
| VI. Terjemahan | 2 | ✅ Ada semua | TRANSLATE_PROMPT, CHAPTER_TRANSLATE_PROMPT |

**Prompts Baru (Tidak dalam Plan):**
- `GET_CHAPTER_TITLE_PROMPT` (line 917): Generate chapter titles
- `MEGA_OUTLINE_PREAMBLE` (line 904): Preamble for mega outline
- `MEGA_OUTLINE_CHAPTER_FORMAT` (line 906): Chapter format template
- `MEGA_OUTLINE_CURRENT_CHAPTER_PREFIX` (line 910): Current chapter marker
- `CURRENT_CHAPTER_OUTLINE_FORMAT` (line 895): Chapter outline format
- `PREVIOUS_CHAPTER_CONTEXT_FORMAT` (line 891): Previous chapter context
- `CHAPTER_GENERATION_STAGE1`, `STAGE2`, `STAGE3`: Tidak ada dalam prompts.py saat ini (logic berbeda)

**Total Prompts:**
- **Plan ini:** 42 prompts
- **Aktual di Prompts.py:** 45 prompts (termasuk format templates)
- **Match rate:** ~85% (35/42 prompts dari plan ada, plus 10 baru)

---

## I. Pengaturan Sistem & Inisiasi Proyek Awal
1.  `DEFAULT_SYSTEM_PROMPT`
    *   **Fungsi:** Prompt sistem umum/default yang mungkin digunakan secara luas.
2.  `GET_IMPORTANT_BASE_PROMPT_INFO`
    *   **Fungsi:** Mengekstrak informasi penting dari ide cerita awal pengguna.
3.  `GENERATE_STORY_ELEMENTS`
    *   **Fungsi:** Mendefinisikan komponen inti cerita seperti genre, tema, karakter, berdasarkan ide awal.

## II. Pembuatan & Penyempurnaan Outline Cerita Keseluruhan
4.  `INITIAL_OUTLINE_PROMPT`
    *   **Fungsi:** Menghasilkan draf pertama dari outline cerita multi-bab.
5.  `EXPAND_OUTLINE_CHAPTER_BY_CHAPTER`
    *   **Fungsi:** Memastikan outline terstruktur dengan jelas per bab, lengkap dengan tujuan masing-masing bab.
6.  `CRITIC_OUTLINE_INTRO`
7.  `CRITIC_OUTLINE_PROMPT`
    *   **Fungsi:** Mengkritik kondisi terkini dari outline cerita keseluruhan.
8.  `OUTLINE_REVISION_PROMPT`
    *   **Fungsi:** Merevisi outline cerita keseluruhan berdasarkan kritik/umpan balik.
9.  `OUTLINE_COMPLETE_INTRO`
10. `OUTLINE_COMPLETE_PROMPT`
    *   **Fungsi:** Memeriksa apakah outline cerita keseluruhan telah memenuhi semua kriteria.
11. `CHAPTER_COUNT_PROMPT`
    *   **Fungsi:** Menentukan jumlah total bab dari outline yang sudah final.

## III. Pemrosesan Per Bab (Diulang untuk setiap bab)

### A. Persiapan Outline Spesifik Bab
12. `CHAPTER_GENERATION_PROMPT`
    *   **Fungsi:** Mengekstrak bagian yang relevan untuk bab *saat ini* dari outline cerita utama.

### B. Pembuatan Konten Bab (Metode Utama: Pendekatan Bertahap/Staged)
13. `CHAPTER_HISTORY_INSERT`
    *   **Fungsi:** Menyediakan konteks historis (misalnya, bab yang telah ditulis sebelumnya atau ringkasan cerita keseluruhan) untuk pembuatan bab saat ini.
14. `CHAPTER_SUMMARY_INTRO`
15. `CHAPTER_SUMMARY_PROMPT`
    *   **Fungsi:** Meringkas bab *sebelumnya* untuk memastikan kesinambungan dengan bab saat ini.
16. `CHAPTER_GENERATION_INTRO`
    *   **Fungsi:** Pesan sistem/persona untuk LLM yang bertugas membuat bab.
17. `CHAPTER_GENERATION_STAGE1`
    *   **Fungsi:** Menghasilkan plot untuk bab saat ini.
18. `CHAPTER_GENERATION_STAGE2`
    *   **Fungsi:** Menambahkan pengembangan karakter ke plot yang dihasilkan di Tahap 1.
19. `CHAPTER_GENERATION_STAGE3`
    *   **Fungsi:** Menambahkan dialog ke konten dari Tahap 2, menyelesaikan draf bab.

### C. Alternatif/Detail Pembuatan Outline & Konten Bab Berbasis Adegan (Scene-Based)
    *(Bagian ini bisa digunakan sebagai alternatif atau setelah Bagian B untuk detail lebih lanjut)*
20. `CHAPTER_OUTLINE_PROMPT`
    *   **Fungsi:** Menghasilkan outline yang detail dan adegan-per-adegan *untuk bab saat ini*, berdasarkan outline utama. Ini lebih granular daripada `CHAPTER_GENERATION_PROMPT`.
21. `CHAPTER_TO_SCENES`
    *   **Fungsi:** Mengambil outline umum sebuah bab (mungkin dari `CHAPTER_GENERATION_PROMPT` atau versi prosa) dan menyusunnya menjadi outline adegan-per-adegan yang detail.
22. `SCENES_TO_JSON`
    *   **Fungsi:** Mengonversi outline adegan-per-adegan menjadi format JSON, mungkin untuk penanganan data terstruktur atau input ke alat lain.
23. `SCENE_OUTLINE_TO_SCENE`
    *   **Fungsi:** Menghasilkan prosa lengkap untuk *satu adegan* berdasarkan outline detailnya. Ini akan dipanggil secara berulang untuk setiap adegan jika menggunakan pendekatan penulisan adegan-per-adegan.

### D. Validasi, Kritik, dan Revisi Bab (Diterapkan pada draf bab yang dihasilkan dari B atau C)
24. `SUMMARY_CHECK_INTRO`
25. `SUMMARY_CHECK_PROMPT`
    *   **Fungsi:** Menghasilkan ringkasan dari konten bab yang *baru ditulis*.
26. `SUMMARY_OUTLINE_INTRO`
27. `SUMMARY_OUTLINE_PROMPT`
    *   **Fungsi:** Menghasilkan ringkasan dari *outline yang dituju* untuk bab saat ini.
28. `SUMMARY_COMPARE_INTRO`
29. `SUMMARY_COMPARE_PROMPT`
    *   **Fungsi:** Membandingkan ringkasan bab yang ditulis dengan ringkasan outline-nya untuk memeriksa kesesuaian dan perbedaan.
30. `CRITIC_CHAPTER_INTRO`
31. `CRITIC_CHAPTER_PROMPT`
    *   **Fungsi:** Memberikan kritik terhadap bab yang ditulis berdasarkan berbagai kriteria sastra.
32. `CHAPTER_REVISION`
    *   **Fungsi:** Merevisi bab yang ditulis berdasarkan umpan balik dari perbandingan, kritik, atau masukan pengguna.
33. `CHAPTER_COMPLETE_INTRO`
34. `CHAPTER_COMPLETE_PROMPT`
    *   **Fungsi:** Memeriksa apakah bab yang direvisi sekarang memenuhi semua kriteria penyelesaian.

## IV. Penyuntingan Tingkat Cerita & Finalisasi (Setelah draf/revisi bab individual selesai)
35. `CHAPTER_EDIT_PROMPT`
    *   **Fungsi:** Menyunting bab tertentu dengan fokus pada koherensi lokal dengan bab sebelum dan sesudahnya, memastikan transisi yang mulus.
36. `CHAPTER_SCRUB_PROMPT`
    *   **Fungsi:** Membersihkan teks final sebuah bab, menghapus catatan penulis, sisa outline, atau komentar editorial, menyiapkannya untuk "publikasi".
37. `STATS_PROMPT`
    *   **Fungsi:** Menghasilkan statistik keseluruhan untuk cerita yang telah selesai, seperti judul, ringkasan, tag, peringkat.

## V. Alat Evaluasi (Tingkat Meta, untuk membandingkan versi atau draf yang berbeda)
38. `EVALUATE_SYSTEM_PROMPT`
    *   **Fungsi:** Prompt sistem untuk tugas evaluasi.
39. `EVALUATE_OUTLINES`
    *   **Fungsi:** Membandingkan dua outline cerita yang berbeda dan menentukan mana yang lebih baik berdasarkan kriteria yang ditetapkan.
40. `EVALUATE_CHAPTERS`
    *   **Fungsi:** Membandingkan dua versi bab yang berbeda dan menentukan mana yang lebih baik.

## VI. Terjemahan (Langkah opsional terakhir untuk lokalisasi)
41. `TRANSLATE_PROMPT`
    *   **Fungsi:** Prompt serbaguna untuk menerjemahkan teks apa pun ke bahasa target.
42. `CHAPTER_TRANSLATE_PROMPT`
    *   **Fungsi:** Secara khusus menerjemahkan konten seluruh bab ke bahasa target.

---

## 🔍 Analisis: Apakah Reorganisasi Perlu Dilakukan?

### ✅ Arguments FOR Implementation (Reorganize Prompts)

1. **Better Code Readability**
   - Developer baru lebih mudah understand workflow
   - Jelas urutan eksekusi dari awal sampai akhir
   - Debugging lebih intuitif (tahu prompt mana dipanggil kapan)

2. **Maintenance Benefits**
   - Modifikasi workflow lebih mudah (grouped by stage)
   - Menambah prompt baru di tempat yang logis
   - Code review lebih mudah (understand context)

3. **Documentation Alignment**
   - Plan ini bisa jadi "table of contents" untuk Prompts.py
   - Easier to reference specific workflow stages
   - Better onboarding for contributors

### ❌ Arguments AGAINST Implementation (Keep Current)

1. **No Functional Benefit**
   - Order in file doesn't affect runtime execution
   - All prompts work correctly as-is
   - Zero performance impact

2. **Risk of Breaking Changes**
   - Git history might become harder to track
   - Merge conflicts jika ada branches aktif
   - Manual testing required after reorganization

3. **Effort vs Value**
   - **Estimated effort:** 2-3 hours (reorder + verify + test)
   - **Value gained:** Purely organizational (no bug fixes, no features)
   - Better spend time on actual improvements

4. **Version Control Noise**
   - Massive diff dari reordering
   - Git blame jadi less useful
   - "Who changed this?" becomes "Who reorganized?"

### 🎯 Recommendation

**DON'T IMPLEMENT** - Keep current order.

**Reasoning:**
1. Current file works perfectly fine
2. Prompts are already findable (Ctrl+F, grep works)
3. Most important: **There are actual issues to fix** (context overflow, dead code cleanup, testing)
4. Reorganization is "nice to have", not "need to have"

**Alternative Solution:**
- Keep this document as **reference guide** for understanding workflow
- Add comment sections in Prompts.py (Group 1: Initialization, Group 2: Outline, etc.)
- No file reordering needed, just add 6 comment lines like:
  ```python
  # ===== I. SYSTEM INITIALIZATION =====
  DEFAULT_SYSTEM_PROMPT = """..."""
  ...
  # ===== II. OUTLINE GENERATION =====
  INITIAL_OUTLINE_PROMPT = """..."""
  ```

**If Reorganization Happens Anyway:**
- Do it in a dedicated PR/commit
- Run full test suite before and after
- Update this document with implementation date
- Add migration notes for developers

---

## 📝 Document Purpose

**Current Status:** Reference guide for understanding prompt workflow, NOT an implementation task.

**Use Cases:**
1. Understand story generation pipeline flow
2. Find which prompt handles which stage
3. Plan new prompt additions (where to add?)
4. Debugging workflow issues (which stage failed?)