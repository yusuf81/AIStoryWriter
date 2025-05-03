# Kritik Prompt dalam Writer/Prompts.py (Per 2024-07-01)

Analisis ini mengevaluasi efektivitas prompt yang didefinisikan dalam `Writer/Prompts.py` dalam konteks alur kerja pembuatan novel seperti yang diimplementasikan dalam kode saat ini.

## Ringkasan Alur Kerja Utama

1.  **Inisialisasi:** Terjemahan prompt awal (opsional), ekstraksi konteks dasar.
2.  **Pembuatan Outline:** Elemen cerita -> Outline awal -> Revisi outline (berdasarkan kritik & rating) -> Outline final.
3.  **Deteksi Bab:** Menghitung jumlah bab dari outline.
4.  **Ekspansi Outline per Bab (Opsional):** Membuat outline lebih detail untuk setiap bab.
5.  **Pembuatan Bab:**
    *   **Pipeline Adegan (Default):** Outline Bab -> Outline Adegan -> JSON Adegan -> Tulis Adegan -> Gabungkan Bab Kasar.
    *   **Pipeline Bertahap (Alternatif):** Ekstrak segmen outline bab -> Ringkasan bab terakhir -> Tahap 1 (Plot) -> Tahap 2 (Pengembangan Karakter) -> Tahap 3 (Dialog). Setiap tahap divalidasi dengan `LLMSummaryCheck`.
6.  **Revisi Bab:** Dapatkan kritik -> Dapatkan rating -> Revisi bab (loop hingga memenuhi syarat atau batas revisi).
7.  **Pasca-Pemrosesan:** Edit novel final (opsional) -> Scrubbing (opsional) -> Terjemahan (opsional).
8.  **Generasi Info Final:** Judul, Ringkasan, Tag, Rating.

## Analisis Prompt Berdasarkan Tahapan

### 1. Inisialisasi & Konteks Dasar

*   `TRANSLATE_PROMPT`: Cukup jelas untuk tugas terjemahan sederhana. Efektif.
*   `GET_IMPORTANT_BASE_PROMPT_INFO`: Bertujuan memisahkan instruksi meta (panjang bab, format) dari konten cerita. Templat respons jelas. **Kritik:** Efektivitasnya bergantung pada kemampuan LLM membedakan instruksi meta. Mungkin bisa redundan jika prompt utama pengguna sudah terstruktur dengan baik.

### 2. Pembuatan Outline

*   `GENERATE_STORY_ELEMENTS`: Meminta output yang sangat terstruktur dengan templat detail. Bagus untuk konsistensi. **Kritik:** Mungkin terlalu preskriptif dan membatasi kreativitas LLM jika hanya mengisi bagian kosong. Bisa menghasilkan elemen generik. Pertimbangkan apakah ini bisa digabung dengan prompt outline awal.
*   `INITIAL_OUTLINE_PROMPT`: Instruksi bagus (konflik, karakter, dll.). Meminta kejelasan per bab. Menggabungkan `StoryElements`. **Kritik:** Bergantung pada pemahaman LLM tentang "Show, don't tell". Menggabungkan elemen dan outline bisa jadi kompleks bagi LLM.
*   `CRITIC_OUTLINE_INTRO` / `CRITIC_OUTLINE_PROMPT`: Kriteria kritik standar dan jelas. Efektif.
*   `OUTLINE_REVISION_PROMPT`: Menggunakan kembali instruksi outline awal dan menyertakan feedback. Jelas dan efektif.
*   `OUTLINE_COMPLETE_INTRO` / `OUTLINE_COMPLETE_PROMPT`: Meminta output JSON boolean sederhana. Kriteria jelas. **Kritik:** Rating boolean (`IsComplete`) mungkin terlalu menyederhanakan. Skor atau feedback kualitatif bisa lebih baik, tetapi boolean lebih mudah diproses.

### 3. Deteksi Bab

*   `CHAPTER_COUNT_PROMPT`: Format JSON jelas. Tugas sederhana. Efektif.

### 4. Ekspansi Outline per Bab

*   `EXPAND_OUTLINE_CHAPTER_BY_CHAPTER`: Prompt **sangat** sederhana dan ambigu. Bergantung sepenuhnya pada LLM untuk memahami tugas implisit. **Kritik:** Terlalu kabur. Seharusnya memberikan lebih banyak konteks atau instruksi. Tampaknya tidak digunakan secara efektif atau digantikan oleh `CHAPTER_OUTLINE_PROMPT`.
*   `CHAPTER_OUTLINE_PROMPT`: Meminta templat berbasis adegan yang detail. Struktur bagus. Menggunakan kembali pertanyaan pembuatan outline. **Kritik:** Ini tampaknya menjadi prompt ekspansi yang sebenarnya. Templatnya bagus tapi kompleks. Digunakan oleh `GeneratePerChapterOutline` yang sesuai. Nama `EXPAND_OUTLINE_CHAPTER_BY_CHAPTER` menyesatkan.

### 5. Pembuatan Bab (Pipeline Bertahap)

*   `CHAPTER_GENERATION_INTRO`: Generik, tidak masalah.
*   `CHAPTER_GENERATION_PROMPT` (Ekstrak Segmen): Tugas jelas. Efektif.
*   `CHAPTER_HISTORY_INSERT`: Ide bagus untuk memberikan konteks bab sebelumnya. Format jelas.
*   `CHAPTER_SUMMARY_INTRO` / `CHAPTER_SUMMARY_PROMPT`: Meminta ringkasan bab sebelumnya dengan templat detail. Struktur bagus. Tujuan jelas.
*   `CHAPTER_GENERATION_STAGE1` (Plot): Menggunakan konteks, outline, ringkasan, feedback. Instruksi jelas (pacing, flow, genre). **Kritik:** Pendekatan bertahap menarik tetapi berpotensi terputus-putus. Prompt meminta "tulis plot", yang ambigu. Seharusnya meminta *narasi yang berfokus pada peristiwa plot*. Bergantung pada `LLMSummaryCheck`.
*   `CHAPTER_GENERATION_STAGE2` (Karakter): Membangun Tahap 1. Meminta untuk memperluas, bukan menghapus. Kriteria jelas. **Kritik:** Ambiguitas serupa ("tulis pengembangan karakter"). Seharusnya meminta *meningkatkan narasi dengan kedalaman karakter, pemikiran internal, dan motivasi*. Bergantung pada `LLMSummaryCheck`.
*   `CHAPTER_GENERATION_STAGE3` (Dialog): Membangun Tahap 2. Meminta menambahkan dialog. Kriteria jelas. Meminta menghapus heading. **Kritik:** "tambahkan dialog" lebih jelas. Bergantung pada `LLMSummaryCheck`.
*   `SUMMARY_CHECK_INTRO` / `SUMMARY_CHECK_PROMPT`: Tugas ringkasan sederhana. Jelas.
*   `SUMMARY_OUTLINE_INTRO` / `SUMMARY_OUTLINE_PROMPT`: Tugas ringkasan sederhana. Jelas.
*   `SUMMARY_COMPARE_INTRO` / `SUMMARY_COMPARE_PROMPT`: Meminta output JSON. Membandingkan ringkasan bab vs outline. Meminta saran untuk iterasi *berikutnya*. **Kritik:** Ini inti dari loop revisi tahap. Logika tampak solid. `DidFollowOutline` (boolean) mungkin terlalu sederhana. Kualitas saran sangat penting.

### 6. Pembuatan Bab (Pipeline Adegan)

*   `DEFAULT_SYSTEM_PROMPT`: Minimalis. Cukup.
*   `CHAPTER_TO_SCENES`: Mengonversi outline bab menjadi outline adegan-per-adegan. Tujuan, gaya, instruksi audiens jelas. **Kritik:** Tampaknya efektif untuk memecah outline bab.
*   `SCENES_TO_JSON`: Mengonversi outline adegan markdown menjadi list JSON. Tujuan jelas, format JSON ditentukan. **Kritik:** Sangat bergantung pada LLM untuk mem-parsing markdown dengan benar dan menghasilkan JSON valid. Penggunaan `json_repair` membantu, tetapi prompt bisa lebih kuat (misalnya, instruksi eksplisit tentang cara menangani item list).
*   `SCENE_OUTLINE_TO_SCENE`: Menulis adegan penuh dari segmen outline-nya dan konteks outline cerita. Tujuan, gaya, audiens jelas. **Kritik:** Tampaknya efektif untuk menghasilkan adegan individual.

### 7. Revisi Bab

*   `CRITIC_CHAPTER_INTRO` / `CRITIC_CHAPTER_PROMPT`: Kriteria detail mencakup plot, gaya, karakter, dialog. Jelas.
*   `CHAPTER_COMPLETE_INTRO` / `CHAPTER_COMPLETE_PROMPT`: Output JSON boolean sederhana. Kriteria jelas (sama dengan cek outline). **Kritik:** Sekali lagi, boolean mungkin terlalu sederhana.
*   `CHAPTER_REVISION`: Menerima bab dan feedback. Meminta bab yang ditingkatkan. Jelas.

### 8. Pasca-Pemrosesan

*   `CHAPTER_EDIT_PROMPT` (NovelEditor): Menerima outline, teks novel *lengkap*, nomor bab. Meminta edit bab `i` agar sesuai. **Kritik:** Prompt sederhana untuk tugas kompleks. Memberikan *seluruh* teks novel mungkin melebihi batas konteks untuk novel besar. Bisa ditingkatkan dengan hanya memberikan bab-bab di sekitarnya? Efektivitas sangat bergantung pada model.
*   `CHAPTER_SCRUB_PROMPT`: Tugas jelas - hapus komentar/outline. Efektif.
*   `CHAPTER_TRANSLATE_PROMPT`: Instruksi sangat ketat untuk HANYA mengeluarkan terjemahan. Perbaikan yang bagus.

### 9. Generasi Info Final

*   `STATS_PROMPT`: Format JSON jelas diminta (Judul, Ringkasan, Tag, Rating). **Kritik:** Rating 0-100 bersifat subjektif dan sulit bagi LLM. Tag mungkin generik. Judul/Ringkasan adalah standar.
*   **Ukuran Konteks `STATS_PROMPT`:** Prompt ini, saat digunakan oleh `GetStoryInfo` (dan disimulasikan oleh `SimulateStoryInfo.py`), mengirimkan *seluruh teks novel* yang telah diproses sebagai konteks ke `INFO_MODEL`. Ini sangat berisiko melebihi batas konteks LLM, terutama untuk novel panjang, yang dapat mengakibatkan error, pemotongan konteks, atau ringkasan/tag/rating yang tidak akurat karena LLM tidak dapat memproses keseluruhan cerita. Fallback ke outline lebih aman dari segi konteks tetapi kurang representatif terhadap karya akhir. # Add this critique point

### 10. Evaluasi (Evaluate.py)

*   `EVALUATE_SYSTEM_PROMPT`: Minimalis.
*   `EVALUATE_OUTLINES` / `EVALUATE_CHAPTERS`: Format JSON detail diminta untuk membandingkan A vs B berdasarkan kriteria. Instruksi jelas. **Kritik:** Bagus untuk pengujian A/B, tetapi bergantung pada konsistensi dan pemahaman LLM evaluator terhadap kriteria.

## Kesimpulan dan Rekomendasi

**Kekuatan:**

*   Pendekatan terstruktur dengan tahapan yang jelas.
*   Penggunaan JSON untuk tugas-tugas spesifik (rating, deteksi bab, perbandingan ringkasan, info akhir) memudahkan pemrosesan otomatis.
*   Banyak prompt memiliki instruksi yang jelas dan kriteria spesifik.
*   Adanya loop revisi untuk outline dan bab berdasarkan feedback LLM.
*   Injeksi konteks (sejarah bab, ringkasan bab terakhir) membantu menjaga kesinambungan.
*   Pemisahan tugas pasca-pemrosesan (edit, scrub, translate).
*   Pipeline adegan-per-adegan adalah pendekatan modern yang menjanjikan.

**Kelemahan & Area Peningkatan:**

1.  **Potensi Keterputusan (Pipeline Bertahap):** Prompt untuk Tahap 1, 2, dan 3 (`CHAPTER_GENERATION_STAGE1/2/3`) bisa lebih eksplisit tentang *bagaimana* mengintegrasikan plot, karakter, dan dialog, daripada hanya meminta "tulis plot" atau "tambah dialog". Saat ini, hasilnya mungkin terasa seperti lapisan yang ditambahkan secara terpisah, bukan narasi yang kohesif.
2.  **Validasi Kualitas Sederhana:** Penggunaan output boolean (`IsComplete`, `DidFollowOutline`) untuk validasi kualitas outline, bab, dan kesesuaian tahap mungkin terlalu menyederhanakan. Pertimbangkan metrik yang lebih bernuansa atau feedback kualitatif yang dapat diproses (meskipun lebih sulit).
3.  **Ambiguitas Prompt:** `EXPAND_OUTLINE_CHAPTER_BY_CHAPTER` terlalu kabur dan tampaknya tidak digunakan atau digantikan oleh `CHAPTER_OUTLINE_PROMPT`. Perjelas atau hapus.
4.  **Potensi Masalah Konteks:** `CHAPTER_EDIT_PROMPT` yang menggunakan seluruh teks novel bisa melebihi batas konteks LLM untuk cerita panjang. Selidiki pengoptimalan konteks (misalnya, hanya mengirim bab sebelum dan sesudah).
5.  **Kompleksitas:** Alur kerja memiliki banyak tahapan dan prompt. Meskipun modular, ini meningkatkan potensi titik kegagalan atau hasil yang tidak konsisten antar tahapan.
6.  **Panduan Genre/Gaya:** Prompt `_INTRO` saat ini sangat generik. Memanfaatkan system prompt ini (atau variabel terpusat) untuk memberikan panduan genre, nada, atau gaya penulisan yang konsisten di seluruh tahapan kreatif akan sangat bermanfaat.
7.  **Robustness Prompt JSON:** Meskipun `json_repair` digunakan, prompt yang meminta JSON (`SCENES_TO_JSON`, `STATS_PROMPT`, dll.) dapat diperkuat dengan instruksi yang lebih eksplisit tentang penanganan error atau format list/nested object jika diperlukan.

**Rekomendasi Utama:**

*   **Perjelas Prompt Generasi Bertahap:** Ubah prompt `CHAPTER_GENERATION_STAGE1/2/3` agar lebih fokus pada *peningkatan narasi* dengan elemen spesifik (plot, karakter, dialog) daripada hanya "menulis" elemen tersebut secara terpisah.
*   **Tingkatkan Validasi Kualitas:** Jelajahi alternatif selain cek boolean sederhana. Mungkin skor numerik (dengan rubrik yang jelas) atau feedback kualitatif terstruktur dalam JSON.
*   **Optimalkan Konteks `CHAPTER_EDIT_PROMPT`:** Uji coba hanya memberikan bab-bab sekitar (misalnya, N-1, N, N+1) daripada seluruh novel.
*   **Implementasikan Panduan Genre/Gaya:** Gunakan system prompt (`_INTRO`) atau variabel pusat untuk menetapkan panduan genre/gaya yang konsisten untuk tahapan penulisan kreatif.
*   **Bersihkan Prompt Tidak Jelas/Usang:** Perjelas atau hapus `EXPAND_OUTLINE_CHAPTER_BY_CHAPTER`.
*   **Prioritaskan Pipeline Adegan:** Pipeline adegan-per-adegan (`ChapterByScene`) tampaknya lebih modern dan berpotensi menghasilkan narasi yang lebih kohesif daripada pipeline bertahap. Fokuskan pengembangan dan penyempurnaan pada pipeline ini.

Secara keseluruhan, sistem prompt menunjukkan pemikiran yang matang dalam memecah tugas penulisan novel yang kompleks. Dengan beberapa penyempurnaan pada kejelasan prompt, validasi kualitas, dan manajemen konteks, efektivitasnya dapat ditingkatkan lebih lanjut.
