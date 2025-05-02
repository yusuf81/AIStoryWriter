# Menghasilkan Output Bahasa Asli Secara Langsung

Dokumen ini membahas berbagai pendekatan untuk menghasilkan konten cerita secara native dalam bahasa target (misalnya, Bahasa Indonesia, Jepang) langsung di dalam pipeline AIStoryWriter, menghindari potensi penurunan kualitas akibat terjemahan pasca-generasi. Tujuannya adalah untuk mencapai output berkualitas tinggi yang terdengar alami dalam bahasa target sambil mempertahankan modularitas agar mudah mengganti bahasa melalui `Writer/Config.py`.

## Pendekatan 1: Menambahkan Instruksi Bahasa di Awal

-   **Cara Kerja:** Tambahkan instruksi sederhana seperti "Tulis semua respons dalam Bahasa Indonesia." di awal setiap prompt yang dikirim ke LLM. Bagian utama prompt tetap dalam Bahasa Inggris.
-   **Kelebihan:**
    -   Implementasi awal relatif sederhana (memodifikasi fungsi pengiriman prompt).
    -   Modularitas mudah melalui satu flag di `Config.py`.
-   **Kekurangan:**
    -   **Efektivitas Rendah:** LLM mungkin tidak konsisten mengikuti instruksi bahasa, terutama ketika konteks prompt utama dalam Bahasa Inggris.
    -   **Kualitas/Kealamian Lebih Rendah:** "Proses berpikir" LLM masih didorong oleh prompt Bahasa Inggris, berpotensi menghasilkan output yang terasa seperti terjemahan daripada ditulis secara native.
    -   **Masalah JSON Besar:** Menginstruksikan LLM untuk menghasilkan JSON "dalam Bahasa Indonesia" bermasalah. Kunci JSON (`"Title"`, `"DidFollowOutline"`, dll.) *harus* tetap dalam Bahasa Inggris agar kode Python dapat mem-parsingnya dengan benar. Instruksi bahasa dalam prompt JSON kemungkinan besar akan diabaikan atau menyebabkan kebingungan.
    -   **Inkonsistensi:** Kegagalan mengikuti instruksi dalam satu langkah dapat menyebabkan input bahasa yang salah untuk langkah-langkah berikutnya.

## Pendekatan 2: Menerjemahkan Seluruh Prompt

-   **Cara Kerja:** Terjemahkan semua string prompt yang relevan di `Writer/Prompts.py` ke dalam bahasa target. Sertakan instruksi untuk menghasilkan output dalam bahasa target di dalam prompt yang sudah diterjemahkan ini.
-   **Kelebihan:**
    -   **Potensi Kualitas/Kealamian Tertinggi:** Seluruh proses kreatif dan analitis terjadi dalam bahasa target, memaksimalkan peluang output yang idiomatik dan alami.
    -   **Konsistensi:** Semua tahap generasi beroperasi dalam bahasa yang sama.
-   **Kekurangan:**
    -   **Upaya Awal Tinggi:** Membutuhkan terjemahan manual *semua* prompt untuk *setiap* bahasa yang didukung.
    -   **Masalah JSON Tetap Ada (Secara Berbeda):** Meskipun instruksi umum dapat diterjemahkan, kunci JSON *harus* tetap dalam Bahasa Inggris. Prompt yang menghasilkan JSON memerlukan desain yang cermat untuk menginstruksikan LLM (dalam bahasa target) agar menggunakan kunci Bahasa Inggris spesifik yang disediakan dalam struktur contoh.
    -   **Modularitas Kompleks:** Membutuhkan file prompt terpisah per bahasa (misalnya, `Prompts_id.py`, `Prompts_ja.py`) dan modifikasi kode untuk memuat file prompt yang benar secara dinamis berdasarkan pengaturan `Config.py`.
    -   **Beban Pemeliharaan:** Mengelola beberapa file prompt yang diterjemahkan meningkatkan kompleksitas pemeliharaan.

## Pendekatan Hybrid yang Direkomendasikan (Pemuatan Prompt Dinamis)

Pendekatan ini menggabungkan manfaat terjemahan penuh dengan modularitas yang lebih baik.

1.  **Pengaturan Konfigurasi:** Tambahkan variabel di `Writer/Config.py` untuk menentukan bahasa target:
    ```python
    NATIVE_LANGUAGE = "id" # Pilihan: "en", "id", "ja", dll.
    ```

2.  **File Prompt Terpisah:** Buat file prompt yang berbeda untuk setiap bahasa yang didukung di dalam direktori `Writer`:
    *   `Prompts_en.py` (Prompt asli Bahasa Inggris)
    *   `Prompts_id.py` (Prompt terjemahan Bahasa Indonesia)
    *   `Prompts_ja.py` (Prompt terjemahan Bahasa Jepang)
    *   ... dll.

3.  **Pemuatan Prompt Dinamis:** Implementasikan mekanisme (misalnya, di `Write.py` selama inisialisasi atau modul `PromptLoader` khusus) yang:
    *   Membaca pengaturan `Writer.Config.NATIVE_LANGUAGE`.
    *   Secara dinamis mengimpor modul prompt yang sesuai (misalnya, `import Writer.Prompts_id as Prompts`).
    *   Semua kode selanjutnya yang mereferensikan `Writer.Prompts.SOME_PROMPT_VARIABLE` akan secara otomatis menggunakan versi dari modul bahasa yang dimuat.

4.  **Penanganan Prompt JSON yang Hati-hati:** Di dalam setiap file prompt yang diterjemahkan (misalnya, `Prompts_id.py`):
    *   **Prompt Teks/Markdown:** Terjemahkan *seluruh* konten prompt dan instruksi ke dalam bahasa target.
    *   **Prompt JSON:**
        *   Terjemahkan instruksi umum dan penjelasan ke dalam bahasa target.
        *   **Penting:** Pertahankan struktur JSON contoh dan semua **nama kunci** JSON (misalnya, `"TotalChapters"`, `"DidFollowOutline"`, `"scenes"`) **persis seperti dalam Bahasa Inggris**.
        *   Instruksikan LLM (menggunakan bahasa target) untuk memberikan nilai untuk field sambil mematuhi secara ketat kunci dan struktur Bahasa Inggris yang disediakan.

## Interaksi dengan Flag Terjemahan yang Ada

Pendekatan hybrid dengan `NATIVE_LANGUAGE` perlu berinteraksi secara cerdas dengan flag terjemahan yang sudah ada (`-TranslatePrompt`, `-Translate`, `-TranslatorModel`) untuk memberikan fleksibilitas maksimum tanpa menyebabkan kebingungan atau redundansi. Berikut adalah peran yang disesuaikan untuk flag-flag ini ketika `NATIVE_LANGUAGE` digunakan:

1.  **`NATIVE_LANGUAGE` (Config Baru):**
    *   Menjadi pengendali **utama** bahasa generasi.
    *   Menentukan file prompt yang dimuat (misalnya, `Prompts_id.py` jika `NATIVE_LANGUAGE="id"`).
    *   Menentukan bahasa target di mana LLM diharapkan untuk "berpikir" dan menghasilkan konten kreatif.

2.  **`-TranslatePrompt <kode_bahasa>` (Flag yang Ada):**
    *   **Peran yang Disesuaikan:** Menerjemahkan *prompt input pengguna awal* (dari file yang ditentukan oleh `-Prompt`) **ke dalam** bahasa yang ditentukan oleh `NATIVE_LANGUAGE`, *sebelum* proses generasi utama dimulai.
    *   **Logika:**
        *   Jika `-TranslatePrompt` diatur ke kode bahasa yang **sama** dengan `NATIVE_LANGUAGE` (dan `NATIVE_LANGUAGE` bukan bahasa default prompt, biasanya Inggris), maka `Translator.TranslatePrompt` akan dipanggil untuk menerjemahkan input prompt.
        *   Jika `-TranslatePrompt` tidak diatur, atau nilainya berbeda dari `NATIVE_LANGUAGE`, diasumsikan prompt input sudah dalam `NATIVE_LANGUAGE` atau bahasa default yang dapat diproses langsung oleh prompt native.
    *   **Kasus Penggunaan:** Memungkinkan pengguna memberikan prompt dalam satu bahasa (misalnya, Prancis) tetapi meminta generasi native dalam bahasa lain (misalnya, Indonesia) dengan mengatur `NATIVE_LANGUAGE="id"` dan `-TranslatePrompt id`.

3.  **`-Translate <kode_bahasa>` (Flag yang Ada):**
    *   **Peran yang Disesuaikan:** Menerjemahkan *output cerita akhir yang sudah digenerasi secara native* (setelah semua langkah seperti edit dan scrub selesai) **dari** bahasa `NATIVE_LANGUAGE` **ke** bahasa target yang ditentukan oleh flag ini.
    *   **Logika:**
        *   Jika `-Translate` diatur ke kode bahasa yang **berbeda** dari `NATIVE_LANGUAGE`, maka `Translator.TranslateNovel` akan dipanggil pada *akhir* pipeline, setelah `FinalProcessedChapters` siap.
        *   Jika `-Translate` tidak diatur, atau nilainya sama dengan `NATIVE_LANGUAGE`, maka langkah terjemahan akhir ini akan dilewati (karena output sudah dalam bahasa yang diinginkan atau tidak ada terjemahan tambahan yang diminta).
    *   **Kasus Penggunaan:** Memungkinkan pengguna mendapatkan output native dalam satu bahasa (misalnya, Indonesia dengan `NATIVE_LANGUAGE="id"`) dan *juga* mendapatkan versi terjemahan akhir dalam bahasa lain (misalnya, Jepang dengan `-Translate ja`).

4.  **`-TranslatorModel <nama_model>` (Flag yang Ada):**
    *   **Peran:** Tetap tidak berubah. Flag ini menentukan model LLM mana yang akan digunakan untuk *semua* tugas terjemahan yang diperlukan, baik itu terjemahan prompt input awal (jika dipicu oleh `-TranslatePrompt`) maupun terjemahan output akhir (jika dipicu oleh `-Translate`).
    *   **Pertimbangan:** Model yang dipilih untuk `-TranslatorModel` idealnya memiliki kemampuan terjemahan yang baik antara berbagai pasangan bahasa yang mungkin digunakan.

Dengan penyesuaian ini, kita dapat memanfaatkan kekuatan generasi native sambil mempertahankan kemampuan untuk menangani input dalam berbagai bahasa dan menghasilkan output terjemahan tambahan jika diperlukan, semuanya dikendalikan secara logis melalui kombinasi `NATIVE_LANGUAGE` dan flag terjemahan yang ada.

## Kesimpulan: Mengapa Pendekatan Hybrid Lebih Disukai

Meskipun membutuhkan penyiapan lebih banyak daripada sekadar menambahkan instruksi di awal, **Pendekatan Hybrid (Pemuatan Prompt Dinamis)** menawarkan keseimbangan terbaik:

-   **Kualitas Native:** Memaksimalkan potensi output alami berkualitas tinggi untuk generasi teks kreatif.
-   **Kompatibilitas:** Memastikan output JSON tetap kompatibel dengan logika parsing Python yang ada.
-   **Modularitas:** Memungkinkan penggantian bahasa terutama melalui `Config.py` (setelah penyiapan awal) dan penambahan bahasa baru dengan membuat file prompt baru.
-   **Efektivitas:** Secara signifikan lebih andal daripada hanya menambahkan instruksi di awal.

Pendekatan ini mewakili cara yang paling kuat dan terukur untuk mencapai generasi bahasa native dalam kerangka kerja AIStoryWriter saat ini.
