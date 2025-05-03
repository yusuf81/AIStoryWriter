# Solusi untuk Masalah Ukuran Konteks Jumbo `Writer.StoryInfo.GetStoryInfo`

**Masalah:** Fungsi `GetStoryInfo` (dan `SimulateStoryInfo.py`) saat ini mengirimkan seluruh teks novel (`StoryBodyText`) sebagai konteks ke `INFO_MODEL` untuk menghasilkan judul, ringkasan, tag, dll. Ini sangat berisiko melebihi batas konteks LLM untuk novel yang lebih panjang.

**Solusi yang Diusulkan:**

### Solusi 1: Gunakan Outline yang Lebih Detail (Jika Tersedia)

*   **Konsep:** Alih-alih mengirim seluruh novel, kirim gabungan dari outline per bab yang sudah diperluas (`expanded_chapter_outlines`) jika tersedia dan valid. Jika tidak, fallback ke outline dasar (`full_outline`).
*   **Implementasi:**
    *   Modifikasi `Write.py` dan `SimulateStoryInfo.py` untuk membangun `InfoQueryContent` dari `expanded_chapter_outlines` (jika ada & valid) atau `full_outline`. Jangan gunakan `StoryBodyText`.
    *   Pastikan `expanded_chapter_outlines` disimpan dengan benar di state.
*   **Pro:**
    *   Implementasi relatif mudah.
    *   Menggunakan data yang sudah ada.
    *   Ukuran konteks jauh lebih kecil.
*   **Kontra:**
    *   Ringkasan didasarkan pada *rencana* (outline), bukan teks akhir.
    *   Kembali ke outline dasar jika ekspansi gagal/tidak digunakan.
    *   Gabungan outline per bab masih bisa besar untuk novel *sangat* panjang.

### Solusi 2: Ringkasan Bertingkat (Map-Reduce Style)

*   **Konsep:**
    1.  **Map:** Minta LLM meringkas setiap bab secara individual.
    2.  **Reduce:** Gabungkan ringkasan per bab, lalu minta LLM meringkas gabungan tersebut untuk mendapatkan ringkasan akhir.
    3.  Gunakan ringkasan akhir ini sebagai input untuk `GetStoryInfo`.
*   **Implementasi:**
    *   Buat fungsi baru `SummarizeNovelForInfo(Interface, Logger, Chapters)`.
    *   Loop per bab, panggil LLM untuk ringkasan bab.
    *   Gabungkan ringkasan bab, panggil LLM lagi untuk ringkasan akhir.
    *   Panggil fungsi ini di `Write.py`.
    *   Ubah `GetStoryInfo` untuk menerima ringkasan akhir.
    *   Tambahkan penyimpanan state untuk ringkasan bertingkat.
*   **Pro:**
    *   Ringkasan akhir didasarkan pada *konten aktual*.
    *   Mengurangi konteks `GetStoryInfo` secara signifikan.
    *   Dapat menangani novel sangat panjang.
*   **Kontra:**
    *   Membutuhkan banyak panggilan LLM tambahan (waktu/biaya).
    *   Implementasi lebih kompleks.
    *   Potensi kehilangan informasi selama peringkasan bertingkat.

### Solusi 3: Gunakan Model Khusus dengan Konteks Sangat Besar

*   **Konsep:** Konfigurasikan `-InfoModel` ke model dengan jendela konteks sangat besar (misalnya, Claude 3, Gemini 1.5 Pro).
*   **Implementasi:**
    *   Biarkan pengguna menentukan `-InfoModel`.
    *   Dokumentasikan rekomendasi model konteks besar untuk novel panjang.
    *   (Opsional) Tambahkan peringatan jika estimasi token `StoryBodyText` sangat besar.
*   **Pro:**
    *   Implementasi kode paling sederhana.
    *   Potensi ringkasan paling akurat jika konteks muat.
*   **Kontra:**
    *   Tidak ada jaminan konteks cukup untuk novel ekstrem.
    *   Model konteks besar bisa lebih mahal/lambat.
    *   Memerlukan akses pengguna ke model tersebut.
    *   Tidak mengatasi masalah jika pengguna tidak bisa/mau menggunakan model tersebut.

### Solusi 4: Sampling Bab (Kurang Ideal)

*   **Konsep:** Hanya kirim beberapa bab kunci (awal, tengah, akhir) sebagai konteks.
*   **Implementasi:**
    *   Pilih subset bab di `Write.py`.
    *   Gabungkan subset ini untuk `InfoQueryContent`.
*   **Pro:**
    *   Mengurangi konteks.
*   **Kontra:**
    *   Sangat mungkin menghasilkan ringkasan tidak akurat/lengkap.
    *   Sulit menentukan bab kunci secara otomatis.

**Rekomendasi:**

1.  **Implementasikan Solusi 1 (Gunakan Outline Detail) sebagai default.** Ini perbaikan termudah dengan dampak signifikan.
2.  **Pertimbangkan Solusi 2 (Ringkasan Bertingkat) sebagai opsi.** Ini solusi paling kuat untuk ringkasan berbasis teks aktual, meskipun kompleks.
3.  **Sebutkan Solusi 3 (Model Konteks Besar) dalam dokumentasi.**

---

# Solusi untuk Masalah Ukuran Konteks Jumbo `Writer.Chapter.ChapterGenerator` (ChapterSuperlist)

**Masalah:** Fungsi `GenerateChapter` (Tahap 1/2/3) saat ini mengirimkan *semua bab sebelumnya* (`ChapterSuperlist`) ditambah outline global sebagai bagian dari konteks (`ContextHistoryInsert`) untuk setiap tahap generasi bab baru. Ini menyebabkan ukuran konteks tumbuh secara linear dengan jumlah bab dan berisiko tinggi melebihi batas token LLM.

**Solusi yang Diusulkan:**

### Solusi 1: Andalkan Outline Detail dan Ringkasan Bab Terakhir (Paling Direkomendasikan)

*   **Konsep:** Hapus `ChapterSuperlist` sepenuhnya dari konteks. Andalkan outline global/refined (`_Outline`), outline bab spesifik (`ThisChapterOutline`), dan ringkasan bab terakhir (`FormattedLastChapterSummary`) untuk memberikan konteks.
*   **Implementasi:**
    *   Di `Writer\Chapter\ChapterGenerator.py`, ubah pemformatan `ContextHistoryInsert` agar tidak menyertakan `ChapterSuperlist`.
    *   Di `Writer\Prompts.py`, hapus bagian `<PREVIOUS_CHAPTERS>` dari prompt `CHAPTER_HISTORY_INSERT`.
    *   Pastikan prompt Stage 1/2/3 masih menerima `ThisChapterOutline` dan `FormattedLastChapterSummary`.
*   **Pro:**
    *   Pengurangan konteks paling drastis, menghentikan pertumbuhan linear.
    *   Implementasi relatif sederhana.
    *   Memaksa ketergantungan pada kualitas outline, sejalan dengan filosofi proyek.
*   **Kontra:**
    *   Kehilangan konteks teks penuh dari bab-bab sebelumnya. Kesinambungan bisa terganggu jika outline/ringkasan kurang detail.
    *   Sangat bergantung pada kualitas `ThisChapterOutline` dan `FormattedLastChapterSummary`.

### Solusi 2: Batasi Konteks ke N Bab Terakhir

*   **Konsep:** Hanya kirim teks lengkap dari N bab terakhir (misalnya, N=1 atau N=2) sebagai `ChapterSuperlist`.
*   **Implementasi:**
    *   Di `Writer\Chapter\ChapterGenerator.py`, ubah logika pembuatan `ChapterSuperlist` untuk hanya mengambil `_Chapters[-N:]`.
    *   Tambahkan konstanta `CHAPTER_CONTEXT_PREVIOUS_N` ke `Writer\Config.py` (misal, `1`).
    *   (Opsional) Tambahkan argumen `-ChapterContextN` ke `Write.py`.
    *   Biarkan prompt `CHAPTER_HISTORY_INSERT` tetap sama.
*   **Pro:**
    *   Mengurangi konteks secara signifikan.
    *   Mempertahankan konteks teks penuh dari bab terdekat.
    *   Implementasi cukup mudah.
*   **Kontra:**
    *   Masih bisa melebihi konteks jika N bab terakhir sangat panjang.
    *   Kehilangan konteks dari bab yang lebih awal dari N.
    *   Memilih N optimal bisa sulit.

### Solusi 3: Gunakan Ringkasan Bergulir (Rolling Summary)

*   **Konsep:** Pertahankan satu ringkasan yang terus diperbarui yang mencakup inti cerita dari awal hingga bab terakhir yang selesai. Kirim ringkasan ini sebagai ganti `ChapterSuperlist`.
*   **Implementasi:**
    *   Tambahkan variabel `rolling_summary` ke `current_state` di `Write.py`.
    *   Buat fungsi baru `UpdateRollingSummary(Interface, Logger, current_summary, new_chapter_text)` yang meminta LLM memperbarui ringkasan.
    *   Panggil `UpdateRollingSummary` setelah setiap bab selesai. Simpan hasilnya ke state.
    *   Di `Writer\Chapter\ChapterGenerator.py`, ambil `rolling_summary`.
    *   Modifikasi prompt `CHAPTER_HISTORY_INSERT` untuk menerima `_RollingSummary`.
    *   Ubah pemanggilan format `ContextHistoryInsert`.
*   **Pro:**
    *   Menjaga ukuran konteks relatif konstan.
    *   Memberikan ringkasan dari *seluruh* cerita sebelumnya.
*   **Kontra:**
    *   Implementasi paling kompleks.
    *   Membutuhkan panggilan LLM tambahan per bab (waktu/biaya).
    *   Potensi kehilangan informasi atau penyimpangan (drift) dalam ringkasan.

**Rekomendasi:**

1.  **Coba Solusi 1 (Andalkan Outline + Ringkasan Bab Terakhir) terlebih dahulu.** Ini perubahan termudah dan paling drastis.
2.  **Jika Solusi 1 bermasalah, implementasikan Solusi 2 (Batasi ke N Bab Terakhir) dengan N=1.** Ini kompromi yang baik.
3.  **Pertimbangkan Solusi 3 (Ringkasan Bergulir) sebagai peningkatan di masa mendatang.**

---

# Solusi untuk Masalah Ukuran Konteks Jumbo `Writer.OutlineGenerator.GeneratePerChapterOutline` (Akumulasi Riwayat)

**Masalah:** Fungsi `GeneratePerChapterOutline` dipanggil dalam loop untuk setiap bab. Variabel riwayat pesan (`Messages` di `Write.py`, diteruskan sebagai `_History`) diakumulasikan dari setiap panggilan sebelumnya. Ini berarti seluruh riwayat generasi outline bab sebelumnya dikirim sebagai konteks untuk menghasilkan outline bab berikutnya, menyebabkan ukuran konteks tumbuh secara linear dengan jumlah bab dan berisiko tinggi melebihi batas token LLM.

**Solusi yang Diusulkan:**

### Solusi 1: Hapus Riwayat Akumulasi (Paling Direkomendasikan)

*   **Konsep:** Hentikan pengiriman riwayat pesan (`_History`) yang terakumulasi. Setiap panggilan `GeneratePerChapterOutline` hanya akan menerima outline global (yang mungkin sudah di-refine) dan prompt untuk bab spesifik tersebut.
*   **Implementasi:**
    1.  **Di `Write.py`:** Hapus inisialisasi dan pembaruan variabel `Messages` yang digunakan untuk akumulasi riwayat dalam loop ekspansi outline. Ubah pemanggilan `GeneratePerChapterOutline` agar tidak meneruskan argumen `_History`. Abaikan nilai return riwayat dari fungsi tersebut.
    2.  **Di `Writer\OutlineGenerator.py`:** Hapus parameter `_History` dari definisi fungsi `GeneratePerChapterOutline`. Inisialisasi `Messages = []` di dalam fungsi. Ubah nilai return fungsi menjadi hanya teks outline bab (`SummaryText`).
*   **Pro:**
    *   Solusi paling sederhana dan efektif menghentikan pertumbuhan konteks linear.
    *   Konteks tetap relevan dan ukurannya relatif konstan per panggilan.
    *   Sejalan dengan adanya langkah refinement outline global sebelumnya.
*   **Kontra:**
    *   Kehilangan sedikit konteks tentang *bagaimana* outline bab sebelumnya dibuat (kemungkinan dampaknya kecil).

### Solusi 2: Gunakan Hanya Outline Bab Sebelumnya (N-1)

*   **Konsep:** Hanya kirim teks dari outline bab N-1 sebagai konteks tambahan saat membuat outline bab N.
*   **Implementasi:**
    1.  **Di `Write.py`:** Simpan hasil `ChapterOutline` dari iterasi sebelumnya. Teruskan sebagai argumen baru (misal `_PreviousChapterOutlineText`) ke `GeneratePerChapterOutline`.
    2.  **Di `Writer\OutlineGenerator.py`:** Tambahkan parameter baru `_PreviousChapterOutlineText`. Modifikasi prompt `CHAPTER_OUTLINE_PROMPT` untuk menyertakan placeholder konteks N-1. Format prompt dengan teks N-1 jika ada. Hapus akumulasi riwayat `Messages` (seperti Solusi 1).
*   **Pro:**
    *   Memberikan konteks lokal dari bab sebelumnya.
    *   Mencegah pertumbuhan konteks *sepenuhnya* linear.
*   **Kontra:**
    *   Lebih kompleks dari Solusi 1.
    *   Ukuran konteks tidak sepenuhnya tetap.
    *   Manfaat konteks N-1 mungkin minimal.

### Solusi 3: Ringkasan Bergulir Outline

*   **Konsep:** Pertahankan ringkasan bergulir dari semua outline bab yang telah dibuat. Kirim ringkasan ini sebagai konteks.
*   **Implementasi:**
    *   Memerlukan fungsi baru untuk memperbarui ringkasan outline.
    *   Menambah panggilan LLM dan kompleksitas state.
*   **Pro:**
    *   Ukuran konteks tetap.
    *   Menangkap esensi dari semua outline sebelumnya.
*   **Kontra:**
    *   Paling kompleks.
    *   Panggilan LLM tambahan (waktu/biaya).
    *   Potensi kehilangan detail dalam ringkasan.

**Rekomendasi:**

1.  **Implementasikan Solusi 1 (Hapus Riwayat Akumulasi).** Ini adalah solusi paling bersih, mudah, dan langsung mengatasi masalah pertumbuhan konteks linear.
