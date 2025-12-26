# PROMPT vs PYDANTIC SCHEMA CONFLICT ANALYSIS

**Dibuat:** 2025-12-26
**Status:** Investigasi selesai, menunggu implementasi fix

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

Status: **BELUM DIFIX** - ini CRITICAL BUG saat ini

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
| `test_story_elements_expansion.py` | ⚠️ Perlu verifikasi | GENERATE_STORY_ELEMENTS ada konflik format |
| `test_outline_generator.py` | ⚠️ Perlu verifikasi | Multiple prompt conflicts |
| `test_chapter_generator.py` | ⚠️ Perlu verifikasi | CHAPTER_SUMMARY_PROMPT konflik |

---

## Rencana Implementasi Fix

### Level 1: Critical (Dilakukan sekarang)
1. **Fix `CHAPTER_SUMMARY_PROMPT`** → Gunakan SafeGenerateJSON dengan schema sederhana
   - Mirip fix yang dikejakan di `ChapterGenSummaryCheck.py`
   - Schema: `{summary, key_points?, emotional_state?}`

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

**Document Status:** Draft - Menunggu review dan implementasi
