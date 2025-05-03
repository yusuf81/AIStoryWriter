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
