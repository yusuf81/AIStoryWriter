# Generating Native Language Output Directly

This document explores different approaches to generating story content natively in a target language (e.g., Bahasa Indonesia, Japanese) directly within the AIStoryWriter pipeline, avoiding the potential quality loss from post-generation translation. The goal is to achieve high-quality, natural-sounding output in the target language while maintaining modularity for easy language switching via `Writer/Config.py`.

## Approach 1: Prefixing Language Instructions

-   **How it Works:** Add a simple instruction like "Write all responses in Bahasa Indonesia." at the beginning of every prompt sent to the LLM. The main body of the prompt remains in English.
-   **Pros:**
    -   Relatively simple initial implementation (modify prompt sending function).
    -   Easy modularity via a single flag in `Config.py`.
-   **Cons:**
    -   **Low Effectiveness:** LLMs may inconsistently follow the language instruction, especially when the main prompt context is in English.
    -   **Lower Quality/Naturalness:** The LLM's "thought process" is still driven by the English prompt, potentially leading to output that feels translated rather than natively written.
    -   **Major JSON Issues:** Instructing an LLM to produce JSON "in Bahasa Indonesia" is problematic. JSON keys (`"Title"`, `"DidFollowOutline"`, etc.) *must* remain in English for the Python code to parse them correctly. Language instructions in JSON prompts are likely to be ignored or cause confusion.
    -   **Inconsistency:** Failure to follow the instruction in one step can lead to incorrect language input for subsequent steps.

## Approach 2: Translating Entire Prompts

-   **How it Works:** Translate all relevant prompt strings in `Writer/Prompts.py` into the target language. Include instructions for outputting in the target language within these translated prompts.
-   **Pros:**
    -   **Highest Potential Quality/Naturalness:** The entire creative and analytical process occurs in the target language, maximizing the chance of idiomatic and natural output.
    -   **Consistency:** All generation stages operate in the same language.
-   **Cons:**
    -   **High Initial Effort:** Requires manual translation of *all* prompts for *each* supported language.
    -   **JSON Issues Persist (Differently):** While general instructions can be translated, JSON keys *must* remain in English. Prompts generating JSON need careful design to instruct the LLM (in the target language) to use the specific English keys provided in the example structure.
    -   **Complex Modularity:** Requires separate prompt files per language (e.g., `Prompts_id.py`, `Prompts_ja.py`) and code modifications to dynamically load the correct prompt file based on a `Config.py` setting.
    -   **Maintenance Overhead:** Managing multiple translated prompt files increases maintenance complexity.

## Recommended Hybrid Approach (Dynamic Prompt Loading)

This approach combines the benefits of full translation with better modularity.

1.  **Configuration Setting:** Add a variable in `Writer/Config.py` to specify the target language:
    ```python
    NATIVE_LANGUAGE = "id" # Options: "en", "id", "ja", etc.
    ```

2.  **Separate Prompt Files:** Create distinct prompt files for each supported language within the `Writer` directory:
    *   `Prompts_en.py` (Original English prompts)
    *   `Prompts_id.py` (Indonesian translated prompts)
    *   `Prompts_ja.py` (Japanese translated prompts)
    *   ... etc.

3.  **Dynamic Prompt Loading:** Implement a mechanism (e.g., in `Write.py` during initialization or a dedicated `PromptLoader` module) that:
    *   Reads the `Writer.Config.NATIVE_LANGUAGE` setting.
    *   Dynamically imports the corresponding prompt module (e.g., `import Writer.Prompts_id as Prompts`).
    *   All subsequent code referencing `Writer.Prompts.SOME_PROMPT_VARIABLE` will automatically use the version from the loaded language module.

4.  **Careful JSON Prompt Handling:** Within each translated prompt file (e.g., `Prompts_id.py`):
    *   **Text/Markdown Prompts:** Translate the *entire* prompt content and instructions into the target language.
    *   **JSON Prompts:**
        *   Translate general instructions and explanations into the target language.
        *   **Crucially:** Keep the example JSON structure and all JSON **key names** (e.g., `"TotalChapters"`, `"DidFollowOutline"`, `"scenes"`) **exactly as they are in English**.
        *   Instruct the LLM (using the target language) to provide values for the fields while adhering strictly to the provided English keys and structure.

## Interaksi dengan Flag Terjemahan yang Ada

Pendekatan hybrid dengan `NATIVE_LANGUAGE` perlu berinteraksi secara cerdas dengan flag terjemahan yang sudah ada (`-TranslatePrompt`, `-Translate`, `-TranslatorModel`) untuk memberikan fleksibilitas maksimum tanpa menyebabkan kebingungan atau redundansi. Berikut adalah peran yang disesuaikan untuk flag-flag ini ketika `NATIVE_LANGUAGE` digunakan:

1.  **`NATIVE_LANGUAGE` (Config Baru):**
    *   Menjadi pengendali **utama** bahasa generasi.
    *   Menentukan file prompt yang dimuat (misalnya, `Prompts_id.py` jika `NATIVE_LANGUAGE="id"`).
    *   Menentukan bahasa target di mana LLM diharapkan untuk "berpikir" dan menghasilkan konten kreatif.

2.  **`-TranslatePrompt <language_code>` (Flag yang Ada):**
    *   **Peran yang Disesuaikan:** Menerjemahkan *prompt input pengguna awal* (dari file yang ditentukan oleh `-Prompt`) **ke dalam** bahasa yang ditentukan oleh `NATIVE_LANGUAGE`, *sebelum* proses generasi utama dimulai.
    *   **Logika:**
        *   Jika `-TranslatePrompt` diatur ke kode bahasa yang **sama** dengan `NATIVE_LANGUAGE` (dan `NATIVE_LANGUAGE` bukan bahasa default prompt, biasanya Inggris), maka `Translator.TranslatePrompt` akan dipanggil untuk menerjemahkan input prompt.
        *   Jika `-TranslatePrompt` tidak diatur, atau nilainya berbeda dari `NATIVE_LANGUAGE`, diasumsikan prompt input sudah dalam `NATIVE_LANGUAGE` atau bahasa default yang dapat diproses langsung oleh prompt native.
    *   **Kasus Penggunaan:** Memungkinkan pengguna memberikan prompt dalam satu bahasa (misalnya, Prancis) tetapi meminta generasi native dalam bahasa lain (misalnya, Indonesia) dengan mengatur `NATIVE_LANGUAGE="id"` dan `-TranslatePrompt id`.

3.  **`-Translate <language_code>` (Flag yang Ada):**
    *   **Peran yang Disesuaikan:** Menerjemahkan *output cerita akhir yang sudah digenerasi secara native* (setelah semua langkah seperti edit dan scrub selesai) **dari** bahasa `NATIVE_LANGUAGE` **ke** bahasa target yang ditentukan oleh flag ini.
    *   **Logika:**
        *   Jika `-Translate` diatur ke kode bahasa yang **berbeda** dari `NATIVE_LANGUAGE`, maka `Translator.TranslateNovel` akan dipanggil pada *akhir* pipeline, setelah `FinalProcessedChapters` siap.
        *   Jika `-Translate` tidak diatur, atau nilainya sama dengan `NATIVE_LANGUAGE`, maka langkah terjemahan akhir ini akan dilewati (karena output sudah dalam bahasa yang diinginkan atau tidak ada terjemahan tambahan yang diminta).
    *   **Kasus Penggunaan:** Memungkinkan pengguna mendapatkan output native dalam satu bahasa (misalnya, Indonesia dengan `NATIVE_LANGUAGE="id"`) dan *juga* mendapatkan versi terjemahan akhir dalam bahasa lain (misalnya, Jepang dengan `-Translate ja`).

4.  **`-TranslatorModel <model_name>` (Flag yang Ada):**
    *   **Peran:** Tetap tidak berubah. Flag ini menentukan model LLM mana yang akan digunakan untuk *semua* tugas terjemahan yang diperlukan, baik itu terjemahan prompt input awal (jika dipicu oleh `-TranslatePrompt`) maupun terjemahan output akhir (jika dipicu oleh `-Translate`).
    *   **Pertimbangan:** Model yang dipilih untuk `-TranslatorModel` idealnya memiliki kemampuan terjemahan yang baik antara berbagai pasangan bahasa yang mungkin digunakan.

Dengan penyesuaian ini, kita dapat memanfaatkan kekuatan generasi native sambil mempertahankan kemampuan untuk menangani input dalam berbagai bahasa dan menghasilkan output terjemahan tambahan jika diperlukan, semuanya dikendalikan secara logis melalui kombinasi `NATIVE_LANGUAGE` dan flag terjemahan yang ada.

## Conclusion: Why the Hybrid Approach is Preferred

While requiring more setup than simply prefixing instructions, the **Hybrid Approach (Dynamic Prompt Loading)** offers the best balance:

-   **Native Quality:** Maximizes the potential for natural, high-quality output for creative text generation.
-   **Compatibility:** Ensures JSON outputs remain compatible with the existing Python parsing logic.
-   **Modularity:** Allows switching languages primarily through `Config.py` (after initial setup) and adding new languages by creating new prompt files.
-   **Effectiveness:** Significantly more reliable than prefixing instructions alone.

This approach represents the most robust and scalable way to achieve native language generation within the current AIStoryWriter framework.
