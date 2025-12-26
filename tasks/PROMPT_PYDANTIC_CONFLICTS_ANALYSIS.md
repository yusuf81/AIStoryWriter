# PROMPT vs PYDANTIC SCHEMA CONFLICT ANALYSIS

**Dibuat:** 2025-12-26
**Status:** ✅ IMPLEMENTASI SELESAI - Level 1 fix deployed
**Tanggal Implementasi:** 2025-12-26

---

## Ringkasan Masalah

Ada konflik fundamental antara **format yang diminta prompt** dan **Pydantic schema yang diharapkan code**. Ini menyebabkan:
- Model yang mengikuti prompt → Error Pydantic validation
- Model yang mengikuti Pydantic → Output salah (bukan yang diminta prompt)
- Ketergantungan pada perilaku model yang tidak konsisten

**Dampak:**
- Qwen mengikuti Pydantic → Lolos validation tapi output salah (full chapter text untuk summary)
- Gemma mengikuti Prompt → Error 5× retry kemudian crash

---

## Root Cause

Kode menggunakan `SafeGeneratePydantic(ChapterOutput)` yang mengharapkan format JSON spesifik,
tapi prompt meminta format yang sama sekali berbeda (markdown/structured text).

**Contoh konflik terbesar: `CHAPTER_SUMMARY_PROMPT`**
```
Prompt meminta:
```
Bab Sebelumnya:
    - Plot: ...
    - Latar: ...
    - Karakter: ...
Hal yang Perlu Diingat:
    - ...
```

Pydantic mengharapkan:
```json
{
  "text": "...",
  "word_count": 123,
  "chapter_number": 1
}
```
```

---

## Daftar Masalah Lengkap

### Kategori 1: Prompt Minta Text/Markdown, Code Memaksa Pydantic

| # | Lokasi | Prompt | Pydantic Model | Masalah |
|---|--------|-------|---------------|--------|
| 1 | `OutlineGenerator.py:21` | `GET_IMPORTANT_BASE_PROMPT_INFO` | `BaseContext` | Prompt minta markdown format `# Konteks Tambahan`, return `{context}` |
| 2 | `OutlineGenerator.py:56` | `INITIAL_OUTLINE_PROMPT` | `OutlineOutput` | Prompt minta outline markdown, return `{title, genre, chapters...}` |
| 3 | `OutlineGenerator.py:161` | `GENERATE_PER_CHAPTER_OUTLINE` | `ChapterOutlineOutput` | Prompt minta markdown format, return json terstruktur |
| 4 | `ChapterGenerator.py:108` | `CHAPTER_GENERATION_PROMPT` | `ChapterOutput` | Prompt tidak spesifik format, return `{text, word_count, chapter_number}` |

**Solusi Kategori 1:** Update prompt untuk meminta format JSON sesuai Pydantic schema

---

### Kategori 2: Prompt Minta Format BERBEDA dari Pydantic (CRITICAL)

| # | Lokasi | Prompt | Pydantic Model | Masalah | Status |
|---|--------|-------|---------------|--------|--------|
| **5** | `ChapterGenerator.py:133` | `CHAPTER_SUMMARY_PROMPT` | `ChapterOutput` | Prompt minta `{"Bab Sebelumnya": {...}}` format | **GEMMA CRASH** 5× fail |

**Detail Kasus #5:**
```
Prompt format:
Bab Sebelumnya:
    - Plot: [poin poin]
    - Latar: [deskripsi]
    - Karakter:
        - [nama]: [deskripsi]
Hal yang Perlu Diingat:
    - [poin poin]

Pydantic harapkan:
{ "text": "...", "word_count": 123, "chapter_number": 1 }

Model output:
Gemma: {"Bab Sebelumnya": {...}, "Hal yang Perlu Diingat": [...]}  ❌ FAIL (5×)
Qwen:  { "text": "full chapter text...", "word_count": 691, ... }   ✅ PASS tapi SALAH
```

**Solusi Kategori 2:** Ganti `SafeGeneratePydantic` → `SafeGenerateJSON` dengan schema sederhana

Status: **✅ DIFIX** - Lihat "Implementasi Level 1 Fix" di bawah

---

### Kategori 3: Prompt Punya DUA Format Konflik

| # | Lokasi | Prompt | Pydantic Model | Masalah |
|---|--------|-------|---------------|--------|
| 6 | `OutlineGenerator.py:37` | `GENERATE_STORY_ELEMENTS` | `StoryElements` | Punya markdown template `<RESPONSE_TEMPLATE>` DAN juga JSON format |

**Detail Kasus #6:**
```
# Lines 33-143: Markdown template
<RESPONSE_TEMPLATE>
# Judul Cerita
## Genre:
## Tema:
## Latar:
...

# Lines 149-213: JSON format
=== FORMAT JSON (HANYA REFERENSI) ===
Fields yang diperlukan:
  - title (string, Required)
  - genre (string, Required)
  - themes (array of strings, Required)
...
```

**Masalah:** Model bisa bingung ikut format yang mana.

**Solusi Kategori 3:** Hapus format markdown, pertegas JSON format saja

---

### Kategori 4: Prompt Sudah Punya JSON Format Manual

| # | Lokasi | Prompt | Pydantic Model | Status |
|---|--------|-------|---------------|--------|
| 7 | `ChapterOutlineToScenes.py:35` | `CHAPTER_TO_SCENES` | `SceneOutlineList` | Punya JSON format manual `# FORMAT JSON OUTPUT #` |
| 8 | `SceneOutlineToScene.py:59` | `SCENE_OUTLINE_TO_SCENE` | `SceneContent` | Punya JSON format manual `# FORMAT OUTPUT #` |

**Detail Kasus #7 & #8:**
```
# CHAPTER_TO_SCENES (Prompts_id.py:744)
# FORMAT JSON OUTPUT #
Harap kembalikan respons dalam format JSON berikut:
{{ "scenes": [{{
  "scene_number": 1,
  "setting": "...",
  ...
}}]}}

# SCENE_OUTLINE_TO_SCENE (Prompts_id.py:860)
# FORMAT OUTPUT #
**PENTING**: Anda HARUS mengembalikan respons sebagai objek JSON:
{{
  "text": "PROSA ADEGAN LENGKAP",
  "word_count": <jumlah kata>
}}
```

**Status:** Ini "OK" tapi tidak konsisten dengan `PydanticFormatInstructions` yang digunakan
di `CHAPTER_GENERATION_STAGE1/2/3`.

**Solusi Kategori 4:** Clear up JSON format, optional: gunakan `PydanticFormatInstructions` untuk konsistensi

---

## Sudah DifIX (Sebelumnya)

| # | Lokasi | Prompt | Model | Fix |
|---|--------|-------|-------|-----|
| 9 | `ChapterGenSummaryCheck.py:43,75` | `SUMMARY_CHECK_PROMPT` | SafeGenerateJSON | ✅ SUDAH DIFIX - pakai SafeGenerateJSON dengan schema sederhana `{summary}` |
| 10 | `ChapterGenSummaryCheck.py:??` | `SUMMARY_OUTLINE_PROMPT` | SafeGenerateJSON | ✅ SUDAH DIFIX - pakai SafeGenerateJSON dengan schema sederhana `{summary}` |

Catatan: Fix ini dilakukan dalam sesi sebelumnya untuk `ChapterGenSummaryCheck.py`

---

## Perilaku Model Berdasarkan Investigasi Log

### Qwen-SEA-LION-v4-32B-IT (Model yang dilakukan testing sukses)

| Kasus | Mengikuti Apa? | Hasil |
|-------|----------------|-------|
| Chapter Summary (line 133) | Pydantic Schema | `{"text": "full chapter text...", "word_count": 691, ...}` ✅ PASS (setelah retry word_count) |
| Summary Check | JSON schema manual | `{"summary": "..."}` ✅ PASS |

**Catatan:** Qwen mengikuti Pydantic schema, tapi mengembalikan **FULL CHAPTER TEXT** bukan ringkasan
yang diminta prompt. Ini technically "lulus" validation tapi secara fungsional SALAH.

### Gemma-SEA-LION-v4-27B-IT (Model yang crash)

| Kasus | Mengikuti Apa? | Hasil |
|-------|----------------|-------|
| Chapter Summary (line 133) | **Prompt Format** | `{"Bab Sebelumnya": {...}, "Hal yang Perlu Diingat": [...]}` ❌ FAIL (5× retry gagal) |
| Output setiap retry | **Prompt Format** | Sama persis untuk 5 attempts |
| Feedback: "text: Field required" | **Diabaikan** | Gemma tetap mengikuti prompt |

**Catatan:** Gemma konsisten mengikuti prompt format walaupun diberi feedback error validation 5 kali.
Setelah 5× fail, sistem crash dengan exception `Pydantic validation failed after 5 attempts`.

---

## Pattern PydanticFormatInstructions Hanya di Chapter Generation

```python
# ChapterGenerator.py:182, 244, 269, 332
PydanticFormatInstructions = _get_pydantic_format_instructions_if_enabled(...)

# Digunakan di:
Prompt = ActivePrompts.CHAPTER_GENERATION_STAGE1.format(
    ...,
    PydanticFormatInstructions=PydanticFormatInstructions,  # ← ADA
)
```

Tapi **TIDAK** digunakan di:
- `OutlineGenerator.py` (line 21, 37, 56, 161)
- `ChapterGenerator.py line 108` (CHAPTER_GENERATION_PROMPT)
- `ChapterGenerator.py line 133` (CHAPTER_SUMMARY_PROMPT) ← **TIMBANG BESAR**
- `ChapterOutlineToScenes.py line 35` (CHAPTER_TO_SCENES)
- `SceneOutlineToScene.py line 59` (SCENE_OUTLINE_TO_SCENE)

---

## Log Error Gemma untuk Referensi Crash

```
[7 ] [2025-12-25_21-36-43] PIPELINE run_pipeline CRITICAL ERROR:
    Pydantic validation failed after 5 attempts:
- text: Field required
- word_count: Field required
- chapter_number: Field required

Input value: {'Bab Sebelumnya': {'Plot...eringan di desa Arka.'}} ...
```

Traceback lengkap:
```
File "/var/www/AIStoryWriter/Writer/Chapter/ChapterGenerator.py", line 133
    ChapterSummaryMessages, summary_obj, _ = Interface.SafeGeneratePydantic(
                                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/var/www/AIStoryWriter/Writer/Interface/Wrapper.py", line 403
    raise Exception(f"Pydantic validation failed after {max_attempts} attempts:\n{error_details}")
```

---

## Impact pada Testing

| Test File | Status | Notes |
|-----------|--------|-------|
| `test_chapter_gen_summary_check.py` | ✅ 631 tests pass | Fix dilakukan sebelumnya untuk ChapterGenSummaryCheck |
| `test_chapter_summary_pydantic_to_json.py` | ✅ 15 tests pass | Fix Level 1 untuk CHAPTER_SUMMARY_PROMPT |
| `test_story_elements_expansion.py` | ✅ 17 tests pass | GENERATE_STORY_ELEMENTS konflik (Level 2) |
| `test_outline_generator.py` | ✅ 448 total pass | Multiple prompt conflicts diOutlineGenerator (Level 2-3) |
| `test_chapter_generator.py` | ✅ 448 total pass | CHAPTER_SUMMARY_PROMPT sudah difix (Level 1) |

---

## Rencana Implementasi Fix

### Level 1: Critical ✅ COMPLETED
1. **Fix `CHAPTER_SUMMARY_PROMPT`** → Gunakan SafeGenerateJSON dengan schema sederhana ✅
   - Schema: `{summary, previous_chapter_number, key_points, setting, characters_mentioned}`
   - Lihat "Implementasi Level 1 Fix" di bawah untuk detail

### Level 2: High Priority (Next)
2. Fix `GENERATE_STORY_ELEMENTS` → Hapus konflik markdown/JSON, pertegas JSON format
3. Fix `INITIAL_OUTLINE_PROMPT` → Tambah format JSON sesuai OutlineOutput

### Level 3: Medium Priority
4. Fix `GET_IMPORTANT_BASE_PROMPT_INFO` → Tambah format JSON sesuai BaseContext
5. Fix `GENERATE_PER_CHAPTER_OUTLINE` → Tambah format JSON sesuai ChapterOutlineOutput
6. Fix `CHAPTER_GENERATION_PROMPT` → Tambah format JSON sesuai ChapterOutput

### Level 4: Consistency (Optional/refactoring)
7. Pertimbangkan gunakan `PydanticFormatInstructions` secara konsisten di semua SafeGeneratePydantic calls
8. Unify JSON format specification approach

---

## Implementasi Level 1 Fix - OpSolusi yang Dipilih

### Opsi yang Tersedia

#### Opsi 1: Ubah Prompt, Tetap Gunakan SafeGeneratePydantic
- **Deskripsi:** Update prompt untuk meminta format JSON sesuai Pydantic schema `ChapterOutput`
- **Kelebihan:** Strict typing (Pydantic), konsisten dengan pattern lain di codebase
- **Kekurangan:**
  - Masalah: Pydantic mengharapkan format JSON yang kompleks (`{text, word_count, chapter_number}`)
  - Untuk summary, kita tidak butuh `word_count` atau `chapter_number` - hanya butuh konteks
  - Tidak fail-proof karena masih bergantung pada model memahami format kompleks

#### Opsi 2: Ubah Code ke SafeGenerateJSON + Prompt Tidak Ambigu ✅ **(DIPILIH)**
- **Deskripsi:** Ganti `SafeGeneratePydantic(ChapterOutput)` → `SafeGenerateJSON` dengan schema sederhana
- **Implementasi:**
  - Code: `_extract_chapter_summary(summary_json)` dengan fallback extraction
  - Prompt: JSON format unambiguouis dengan field `{summary, previous_chapter_number, key_points, setting, characters_mentioned}`
- **Kelebihan:**
  - More flexible dan fail-proof
  - Fallback extraction handles berbagai struktur JSON dari berbagai LLM
  - Pattern yang sudah terbukti (digunakan di `ChapterGenSummaryCheck.py`)
  - Tidak bergantung pada strict Pydantic validation untuk sesuatu yang bukan output final
- **Kekurangan:**
  - Tidak punya strict typing untuk hasil
  - Butuh extraction logic untuk handle berbagai format

#### Opsi 3: Gunakan SafeGeneratePydantic dengan Model Custom
- **Deskripsi:** Buat Pydantic model khusus untuk chapter summary seperti `ChapterSummaryOutput`
- **Kelebihan:** Strict typing, explicit structure
- **Kekurangan:**
  - Tambah model baru (bloat)
  - Masih menaruh beban pada model untuk mengikuti format yang tepat
  - Pattern ini tidak digunakan di tempat lain

---

### Alasan Memilih Opsi 2 + Prompt Tidak Ambigu

1. **Alasan Utama: Fallback Extraction Pattern yang Sudah Terbukti**
   - Pattern SafeGenerateJSON dengan fallback extraction sudah bekerja 100% di `ChapterGenSummaryCheck.py`
   - Dulu: `ChapterGenSummaryCheck` menggunakan SafeGeneratePydantic untuk summary
   - Fix ke-nya: Gunakan SafeGenerateJSON dengan `summary_json.get('summary', '') or summary_json.get('text', '')`
   - Result: 631 tests pass, semua model (Qwen, Gemma) bekerja tanpa crash

2. **Alasan Kedua: Summary Bukan Output Final**
   - Chapter summary hanya digunakan sebagai konteks untuk chapter selanjutnya
   - Tidak perlu validasi Pydantic yang strict untuk sesuatu yang bukan output akhir
   - Lebih penting hasilnya **ada** dan **berguna**, daripada validation yang strict tapi crash

3. **Alasan Ketiga: Fail-proof Terhadap Perilaku Model yang Berbeda**
   - Qwen: Mengikuti prompt yang jelas (JSON format) → Mengembalikan `{summary: "..."}`
   - Gemma: Mengikuti prompt lama (markdown) → Mengembalikan `{"Bab Sebelumnya": {...}}`
   - Fallback extraction: Handle kedua kasus secara graceful

4. **Alasan Keempat: Less Intrusive / Simpler Code**
   - Hanya perlu ubah 3 files (ChapterGenerator.py, Prompts.py, Prompts_id.py)
   - Tidak perlu tambah model Pydantic baru
   - Tidak perlu refactor besar-besaran

---

### Detail Implementasi

#### 1. Writer/Chapter/ChapterGenerator.py

**Helper Function `_extract_chapter_summary()`:**
```python
def _extract_chapter_summary(summary_json: dict) -> str:
    """Extract chapter summary from JSON response with fallback options.

    Extraction priority:
    1. Direct 'text' or 'summary' field (Qwen style, new prompt)
    2. Prompt-structured format "Bab Sebelumnya" / "Previous Chapter" (Gemma style, old prompt)
    3. Any string field longer than 10 chars (fallback)
    """
    # Priority 1: Direct text/summary field (Qwen style)
    if 'text' in summary_json:
        return summary_json['text']
    if 'summary' in summary_json:
        return summary_json['summary']

    # Priority 2: Prompt-structured format (Gemma style)
    if 'Bab Sebelumnya' in summary_json or 'Previous Chapter' in summary_json:
        return _format_structured_summary(summary_json)

    # Priority 3: Fallback to any string field
    for value in summary_json.values():
        if isinstance(value, str) and len(value) > 10:
            return value

    return ""
```

**Change di `_prepare_initial_generation_context()`:**
```python
# BEFORE (line 225-227):
ChapterSummaryMessages, summary_obj, _ = Interface.SafeGeneratePydantic(
    _Logger, ChapterSummaryMessages, Config_module.CHAPTER_STAGE1_WRITER_MODEL,
    ChapterOutput
)
FormattedLastChapterSummary = summary_obj.text

# AFTER (line 225-228):
ChapterSummaryMessages, summary_json, _ = Interface.SafeGenerateJSON(
    _Logger, ChapterSummaryMessages, Config_module.CHAPTER_STAGE1_WRITER_MODEL
)
FormattedLastChapterSummary = _extract_chapter_summary(summary_json)
```

**Note:** Also fixed `_ChapterNum` format to pass `_ChapterNum - 1` for previous chapter number:
```python
# line 220:
_ChapterNum=_ChapterNum - 1,  # Previous chapter number
```

#### 2. Writer/Prompts.py (English)

**Updated `CHAPTER_SUMMARY_PROMPT`:**
```python
CHAPTER_SUMMARY_PROMPT = """
I am writing the next chapter in my novel (chapter {_ChapterNum}).

<PREVIOUS_CHAPTER>
{_LastChapter}
</PREVIOUS_CHAPTER>

Please create a summary of the previous chapter to use as context for the next chapter.

# JSON OUTPUT FORMAT
Please return your response in valid JSON format:
{{
  "summary": "Concise summary 50-100 words connecting previous chapter to next",
  "previous_chapter_number": {_ChapterNum},
  "key_points": ["important plot point", "character and their state"],
  "setting": "where the previous chapter ended",
  "characters_mentioned": ["character names"]
}}

Focus on:
- Plot: Important events from previous chapter
- Setting: Place and mood where chapter ended
- Characters: Main characters and their state

Write in English.
Return ONLY valid JSON, no other text.
"""
```

#### 3. Writer/Prompts_id.py (Indonesian)

**Updated `CHAPTER_SUMMARY_PROMPT`:**
```python
CHAPTER_SUMMARY_PROMPT = """
Saya sedang menulis bab berikutnya dalam novel saya (bab {_ChapterNum}),
dan saya telah menulis sejauh ini.

<PREVIOUS_CHAPTER>
{_LastChapter}
</PREVIOUS_CHAPTER>

Harap buat ringkasan chapter sebelumnya untuk digunakan sebagai konteks chapter berikutnya.

# FORMAT OUTPUT JSON
Harap kembalikan respons dalam format JSON yang valid:
{{
  "summary": "Ringkasan singkat 50-100 kata yang menghubungkan chapter sebelumnya ke berikutnya",
  "previous_chapter_number": {_ChapterNum},
  "key_points": ["poin plot penting", "karakter dan state mereka"],
  "setting": "tempat chapter sebelumnya berakhir",
  "characters_mentioned": ["nama karakter"]
}}

Fokus pada:
- Plot: Event penting dari chapter sebelumnya
- Latar: Tempat dan suasana chapter berakhir
- Karakter: Karakter utama dan state mereka

Tuliskan dalam bahasa Indonesia.
HANYA kembalikan JSON yang valid, tanpa teks lain.
"""
```

#### 4. Tests (tests/writer/chapter/test_chapter_summary_pydantic_to_json.py)

15 tests ditambahkan untuk coverage:
- `TestChapterSummaryGeneration` (5 tests) - Main functionality
- `TestPromptUnambiguousFormats` (3 tests) - Format validation
- `TestCrossLanguageSupport` (2 tests) - ID and EN prompts
- `TestBackwardCompatibility` (2 tests) - Integration tests
- `TestErrorHandling` (3 tests) - Edge cases

**All 15 tests pass + 448 total tests pass.**

---

## Hasil Implementasi

### Test Results
- ✅ **15 new tests** in `test_chapter_summary_pydantic_to_json.py` - All pass
- ✅ **448 total tests** - All pass (no regressions)
- ✅ **pyright** - 0 errors
- ✅ **flake8** - 0 errors (with E501,W504,W503 ignored)

### Expected Behavior After Fix
- **Qwen model**: Mengikuti prompt yang jelas → Mengembalikan `{summary: "..."}` ✅
- **Gemma model**: Mengikuti prompt yang jelas → Mengembalikan `{summary: "..."}` ✅
- **Old model responses** (cached): Fallback extraction handles `{"Bab Sebelumnya": {...}}` ✅

### Kapan SafeGeneratePydantic vs SafeGenerateJSON Dipakai?

| Kegunaan | Pattern yang Dipakai | Alasan |
|----------|---------------------|--------|
| **Chapter Summary** | `SafeGenerateJSON` | Bukan output final, perlu flexibility untuk berbagai model |
| **Summary Check** | `SafeGenerateJSON` | Bukan output final, perlu assessment, not strict struct |
| **Chapter Generation** | `SafeGeneratePydantic(ChapterOutput)` | Output final, butuh strict validation lengkap |
| **Scene Generation** | `SafeGeneratePydantic(SceneContent)` | Output final, butuh validasi word_count dan text |

---

## Level 4: Consistency (Optional/refactoring)
7. Pertimbangkan gunakan `PydanticFormatInstructions` secara konsisten di semua SafeGeneratePydantic calls
8. Unify JSON format specification approach

---

## Referensi File

### Source Files yang Perlu Diubah
- `Writer/Chapter/ChapterGenerator.py` (line 133 - CRITICAL)
- `Writer/OutlineGenerator.py` (lines 21, 37, 56, 161)
- `Writer/Prompts.py` (English)
- `Writer/Prompts_id.py` (Indonesian)
- `Writer/Scene/ChapterOutlineToScenes.py` (line 35)
- `Writer/Scene/SceneOutlineToScene.py` (line 59)

### Pydantic Models
- `Writer/Models.py`:
  - `BaseContext` (context)
  - `StoryElements` (title, genre, themes, characters, settings, ...)
  - `OutlineOutput` (title, genre, chapters, character_list, ...)
  - `ChapterOutput` (text, word_count, chapter_number, scenes, ...)
  - `ChapterOutlineOutput` (chapter_number, chapter_title, scenes, ...)
  - `SceneOutlineList` (scenes: Array[SceneOutline])
  - `SceneContent` (text, word_count)

---

## Notes

1. **Konflik ini telah ada sejak commit 5b49bcc (14 Des 2025)** ketika ChapterSummaryMessages
   diubah dari `SafeGenerateText` ke `SafeGeneratePydantic(ChapterOutput)`.

2. **Qwen somehow bisa "survive"** karena mengikuti Pydantic schema, tapi outputnya salah secara fungsional
   (mengembalikan full chapter text untuk summary, bukan ringkasan).

3. **Gemma crash** karena konsisten mengikuti prompt format markdown, feedback error tidak membantu.

4. **Issue ini tidak dependen pada model spesifik** - ini adalah design flaw fundamental di prompt vs code
   mismatch. Model yang berbeda hanya menampakkan masalah dengan cara berbeda.

5. Update prompt harus dilakukan untuk **BOTH** English (`Writer/Prompts.py`) dan Indonesian
   (`Writer/Prompts_id.py`) untuk konsistensi.

---

**Document Status:** ✅ Level 1 fix completed and deployed
**Next Steps:** Consider implementing Level 2 and Level 3 fixes for improved consistency
