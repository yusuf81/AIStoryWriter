# Fix DetailedChapterOutlineForCheck Bug

## Problem Statement
Bug ditemukan di `/var/www/AIStoryWriter/Writer/Chapter/ChapterGenerator.py` line 265:
- `DetailedChapterOutlineForCheck` hanya return `ThisChapterOutline`
- Seharusnya combine dengan `FormattedLastChapterSummary` untuk temporal consistency
- Bug menyebabkan Chapter 2+ tidak punya context dari chapter sebelumnya saat validation
- Impact: Temporal inconsistency (Chapter 2 bisa "reset" timeline)

## Evidence
Developer comment di line 257-258:
```python
# This was likely a bug. A more logical DetailedChapterOutline for checking would be:
# DetailedChapterOutlineForCheck = f"{ThisChapterOutline}\n\n{FormattedLastChapterSummary}"
```

## Solution Design
1. Ubah line 234-265 untuk combine `ThisChapterOutline` dengan `FormattedLastChapterSummary`
2. Return value ke-5 dari `_prepare_initial_generation_context` harus berisi combined context
3. Pastikan backward compatibility - hanya combine jika `FormattedLastChapterSummary` tidak kosong

## Implementation Plan

### Phase 1: TDD - Write Test First
- [ ] Buat test `test_detailed_chapter_outline_combines_previous_summary` di `tests/test_chapter_generator_pydantic.py`
- [ ] Test harus verify bahwa untuk Chapter 2+, `DetailedChapterOutlineForCheck` berisi kombinasi outline + summary
- [ ] Test harus verify bahwa untuk Chapter 1, `DetailedChapterOutlineForCheck` hanya berisi outline (no previous chapter)
- [ ] Run pytest - test harus FAIL (red phase)

### Phase 2: Fix Implementation
- [ ] Edit `Writer/Chapter/ChapterGenerator.py` line 234-265
- [ ] Hapus comment block yang panjang (line 234-262)
- [ ] Implement logic:
  ```python
  DetailedChapterOutlineForCheck = ThisChapterOutline
  if FormattedLastChapterSummary:
      DetailedChapterOutlineForCheck = f"{ThisChapterOutline}\n\n### Previous Chapter Context:\n{FormattedLastChapterSummary}"
  ```
- [ ] Update return statement line 265 untuk return `DetailedChapterOutlineForCheck` instead of `ThisChapterOutline`

### Phase 3: Validation
- [ ] Run pytest untuk semua tests - harus 100% pass
- [ ] Run pyright untuk `Writer/Chapter/ChapterGenerator.py` - no errors
- [ ] Run flake8 untuk `Writer/Chapter/ChapterGenerator.py` - no errors

### Phase 4: Review
- [ ] Verify fix logic benar
- [ ] Verify tidak ada regression di existing tests
- [ ] Document perubahan di review section

## Expected Impact
✅ General improvement untuk semua model (Qwen, Gemma, etc)
✅ Chapter 2+ akan punya temporal consistency dengan Chapter 1
✅ Validation di `LLMSummaryCheck` akan lebih accurate
✅ Tidak ada side effect negatif

## Todo Checklist
- [x] Buat test untuk bug (TDD red phase)
- [x] Fix bug di ChapterGenerator.py (TDD green phase)
- [x] Run pytest semua tests (must be 100%)
- [x] Run pyright ChapterGenerator.py (no errors)
- [x] Run flake8 ChapterGenerator.py (no errors)
- [x] Add review section

---

## Review Section

### Implementation Summary

**Date:** 2025-12-28

**Files Changed:**
1. `Writer/Chapter/ChapterGenerator.py` - Bug fix
2. `tests/test_chapter_generator_pydantic.py` - 2 new tests added
3. `tests/writer/interface/test_wrapper_embedding.py` - Updated for centralized OLLAMA_HOST

### Changes Made

#### 1. Writer/Chapter/ChapterGenerator.py (Lines 234-241)

**Before (Buggy):**
```python
# Long comment block (lines 234-262) indicating developer knew this was likely a bug
...
return MessageHistory, ContextHistoryInsert, ThisChapterOutline, FormattedLastChapterSummary, ThisChapterOutline
```

**After (Fixed):**
```python
# Construct DetailedChapterOutlineForCheck for validation
# Combine ThisChapterOutline with FormattedLastChapterSummary for temporal consistency
DetailedChapterOutlineForCheck = ThisChapterOutline
if FormattedLastChapterSummary:
    DetailedChapterOutlineForCheck = f"{ThisChapterOutline}\n\n### Previous Chapter Context:\n{FormattedLastChapterSummary}"

return MessageHistory, ContextHistoryInsert, ThisChapterOutline, FormattedLastChapterSummary, DetailedChapterOutlineForCheck
```

**Impact:**
- Chapter 2+ validation now includes previous chapter context
- LLMSummaryCheck receives combined outline + summary for temporal consistency checking
- Chapter 1 behavior unchanged (no previous chapter to combine)

#### 2. tests/test_chapter_generator_pydantic.py (Lines 226-345)

**Added 2 TDD tests:**
1. `test_detailed_chapter_outline_combines_previous_summary_for_chapter2` - Verifies Chapter 2+ combines outline with previous summary
2. `test_detailed_chapter_outline_is_just_outline_for_chapter1` - Verifies Chapter 1 only uses outline (no previous chapter)

**Test Results:**
- Both tests FAILED in red phase (proving bug existed)
- Both tests PASSED after fix (proving fix works)

#### 3. tests/writer/interface/test_wrapper_embedding.py (Line 27, 106)

**Changes:**
- Line 27: Updated expected host from hardcoded `"10.23.82.116:11434"` to `Config.OLLAMA_HOST`
- Line 106: Fixed flake8 E712 error - changed `== False` to `is False`

**Reason:** This file was edited to support centralized OLLAMA_HOST configuration (from previous work)

### Test Results

**pytest:** ✅ **748/748 tests passed (100%)**
- No regression detected
- All new tests passing
- All existing tests still passing

**pyright:** ✅ **0 errors, 0 warnings, 0 informations**
- Writer/Chapter/ChapterGenerator.py: Clean
- tests/test_chapter_generator_pydantic.py: Clean
- tests/writer/interface/test_wrapper_embedding.py: Clean

**flake8:** ✅ **No errors**
- All files comply with flake8 standards (ignoring E501, W504, W503 as per project config)

### Code Quality

**TDD Approach:** ✅ Followed London School TDD
1. **Red Phase:** Created failing tests first
2. **Green Phase:** Implemented minimal fix to pass tests
3. **Refactor Phase:** Cleaned up comments, maintained clean code

**DRY Principle:** ✅ Applied
- Removed duplicated long comment block
- Simplified logic to 4 lines

**Simplicity:** ✅ Maintained
- Minimal code change (only touched necessary lines)
- No over-engineering
- Clear, readable implementation

### Bug Fix Verification

**Problem:** Chapter 2+ temporal inconsistency
**Root Cause:** `DetailedChapterOutlineForCheck` didn't include previous chapter summary during validation
**Fix:** Combine outline with previous chapter summary before passing to `LLMSummaryCheck`
**Evidence Fix Works:**
- Test `test_detailed_chapter_outline_combines_previous_summary_for_chapter2` verifies combination happens
- Test `test_detailed_chapter_outline_is_just_outline_for_chapter1` verifies Chapter 1 behavior unchanged

### Expected User Impact

**For Qwen Model:**
- ✅ Should reduce temporal inconsistency in Chapter 2+
- ✅ Validation will now catch timeline resets
- ⚠️ Word count and paragraph break issues remain (model limitation, not code bug)

**For Gemma Model:**
- ✅ Already excellent, will be even more consistent
- ✅ No negative side effects expected
- ✅ Validation will be more accurate

**For All Models:**
- ✅ General improvement to story coherence
- ✅ Better multi-chapter continuity
- ✅ More accurate quality validation

### Next Steps for User

1. ✅ **Run story generation test** with both Qwen and Gemma on Runpod
2. ✅ **Compare Chapter 2 temporal consistency** before/after fix
3. ✅ **Verify no regression** in story quality
4. 📊 **Analyze retry statistics** to see if Qwen retry count improves

### Notes

- This fix addresses CODE BUG, not prompt issue
- Prompt remains unchanged (already optimal for Gemma)
- Qwen's word count and paragraph issues are MODEL LIMITATIONS, require different solution (model upgrade or parameter tuning)
- All 748 tests remain at 100% pass rate

---

# Documentation Consolidation - Docs/ Folder Restructure

## Problem Statement
Documentation is scattered across multiple locations:
- Root directory: 8 markdown files (EXPANDED_OUTLINE_ANALYSIS.md, GEMINI_SETUP.md, etc.)
- `Docs/`: Upstream legacy docs (BlockDiagram, ExamplePrompts, Models.md, Todo.md, anyar/)
- `docs/`: Newer content (PIPELINE_FLOWCHART, embedding_integration.md, etc.)

This causes confusion and makes documentation hard to navigate.

## Target Structure (Final)
```
Docs/
├── README.md                    # Index/TOC for all documentation
│
├── analysis/                    # All proposals, analyses, case studies
│   ├── PRD.md
│   ├── IMPROVEMENTS.md
│   ├── EXPANDED_OUTLINE_ANALYSIS.md
│   ├── SCENE_PIPELINE_INEFFICIENCY_ANALYSIS.md
│   ├── WORD_COUNT_VALIDATION_PROPOSAL.md
│   ├── EMBEDDING_INTEGRATION.md
│   ├── LANGCHAIN_ENHANCEMENTS.md
│   ├── OPENROUTER_COMPLIANCE_ANALYSIS.md
│   └── STORY_ELEMENTS_VALIDATION.md
│
├── setup/                       # Setup guides
│   └── GEMINI_SETUP.md
│
├── architecture/                # Flowcharts, diagrams, technical docs
│   ├── PIPELINE_FLOWCHART.md
│   ├── pipeline_flowchart.mmd
│   ├── pipeline_flowchart.png
│   ├── pipeline_flowchart.svg
│   ├── pipeline_flowchart_updated.png
│   ├── pipeline_flowchart_updated.svg
│   ├── BlockDiagram.drawio
│   ├── BlockDiagram.drawio.svg
│   └── MODELS.md
│
├── examples/                    # Example prompts (from upstream)
│   └── *.txt (from Docs/ExamplePrompts/)
│
└── history/                     # Archive old/legacy docs
    ├── Todo.md
    └── anyar/ (from Docs/anyar/)
```

**Keep in Root:**
- `README.md` - Project entry point
- `CLAUDE.md` - Claude Code instructions

**Delete After Merge:**
- `docs/` directory (all content merged to `Docs/`)

## Implementation Plan

### Phase 1: Create Directory Structure
- [x] Create `Docs/analysis/`
- [x] Create `Docs/setup/`
- [x] Create `Docs/architecture/`
- [x] Create `Docs/examples/`
- [x] Create `Docs/history/`

### Phase 2: Move Root MD Files (git mv)
# From root to Docs/analysis/
- [x] git mv EXPANDED_OUTLINE_ANALYSIS.md Docs/analysis/
- [x] git mv GEMINI_SETUP.md Docs/setup/
- [x] git mv IMPROVEMENTS.md Docs/analysis/
- [x] git mv PRD.md Docs/analysis/
- [x] git mv SCENE_PIPELINE_INEFFICIENCY_ANALYSIS.md Docs/analysis/
- [x] git mv WORD_COUNT_VALIDATION_PROPOSAL.md Docs/analysis/

### Phase 3: Merge docs/ to Docs/ (git mv)
# From docs/ to Docs/analysis/
- [x] git mv docs/embedding_integration.md Docs/analysis/
- [x] git mv docs/langchain_enhancements.md Docs/analysis/
- [x] git mv docs/openrouter_api_compliance_analysis.md Docs/analysis/OPENROUTER_COMPLIANCE_ANALYSIS.md
- [x] git mv docs/story_elements_validation_case_study.md Docs/analysis/STORY_ELEMENTS_VALIDATION.md

# From docs/ to Docs/architecture/
- [x] git mv docs/PIPELINE_FLOWCHART.md Docs/architecture/
- [x] git mv docs/pipeline_flowchart.mmd Docs/architecture/
- [x] git mv docs/pipeline_flowchart.png Docs/architecture/
- [x] git mv docs/pipeline_flowchart.svg Docs/architecture/
- [x] git mv docs/pipeline_flowchart_updated.png Docs/architecture/
- [x] git mv docs/pipeline_flowchart_updated.svg Docs/architecture/

### Phase 4: Reorganize Docs/ Original Files
# Keep upstream content, move to appropriate places
- [x] git mv Docs/BlockDiagram.drawio Docs/architecture/
- [x] git mv Docs/BlockDiagram.drawio.svg Docs/architecture/
- [x] git mv Docs/Models.md Docs/architecture/
- [x] git mv Docs/ExamplePrompts/* Docs/examples/
- [x] rmdir Docs/ExamplePrompts/ (after moving files)

# Archive legacy content
- [x] git mv Docs/Todo.md Docs/history/
- [x] git mv Docs/anyar/* Docs/history/anyar/
- [x] rmdir Docs/anyar/ (after moving files)

### Phase 5: Create Docs/README.md
- [x] Create index file with TOC
- [x] List all files by category
- [x] Add brief descriptions
- [x] Include status markers (COMPLETED, FIXED, NOT IMPLEMENTED)

### Phase 6: Clean Up
- [x] Verify all files moved successfully
- [x] Ensure `docs/` is empty or delete it
- [x] Ensure `Docs/ExamplePrompts/` and `Docs/anyar/` are empty
- [x] Run `git status` to verify changes

### Phase 7: Review
- [x] Verify git history preserved (git log --follow)
- [x] Check that root only has README.md and CLAUDE.md
- [x] Verify Docs/ structure matches plan
- [x] Update review section

## Important Notes

### Use git mv for All Moves
- `git mv` preserves file history
- All changes will be recorded as renames in git
- Use only `git mv`, NEVER `mv` or `cp` then `rm`

### File Renamings
- `openrouter_api_compliance_analysis.md` → `OPENROUTER_COMPLIANCE_ANALYSIS.md` (consistency with other UPPERCASE files)
- `story_elements_validation_case_study.md` → `STORY_ELEMENTS_VALIDATION.md` (shorter, consistent naming)

### Order of Operations
1. Create all directories first
2. Move root files first (clear root)
3. Merge docs/ content to Docs/
4. Reorganize original Docs/ content
5. Delete old/cleanup empty directories
6. Create README.md last (after structure is final)

## Expected Outcome
✅ Single documentation location (`Docs/`)
✅ Organized by category (analysis, setup, architecture, examples, history)
✅ Git history preserved for all files
✅ Clean root directory (only README.md, CLAUDE.md)
✅ No duplication between `Docs/` and `docs/`

## Todo Checklist
- [x] Create directory structure
- [x] Move root MD files (using git mv)
- [x] Merge docs/ to Docs/ (using git mv)
- [x] Reorganize Docs/ original files
- [x] Create Docs/README.md
- [x] Clean up empty directories
- [x] Verify git history preserved
- [x] Add review section

---

## Review Section (Documentation Consolidation)

### Implementation Summary

**Date:** January 6, 2026

**Purpose:** Consolidate all documentation from three locations (root, Docs/, docs/) into single organized Docs/ directory structure.

### Changes Made

#### Phase 1: Directory Structure Created
- `Docs/analysis/` - All proposals, analyses, case studies
- `Docs/setup/` - Setup guides
- `Docs/architecture/` - Flowcharts, diagrams, technical docs
- `Docs/examples/` - Example prompts and outputs
- `Docs/history/` - Archive old/legacy docs

#### Phase 2: Root Files Moved (6 files)
- `EXPANDED_OUTLINE_ANALYSIS.md` → `Docs/analysis/`
- `GEMINI_SETUP.md` → `Docs/setup/`
- `IMPROVEMENTS.md` → `Docs/analysis/`
- `PRD.md` → `Docs/analysis/`
- `SCENE_PIPELINE_INEFFICIENCY_ANALYSIS.md` → `Docs/analysis/`
- `WORD_COUNT_VALIDATION_PROPOSAL.md` → `Docs/analysis/`

#### Phase 3: docs/ Content Merged (10 files)
To `Docs/analysis/`:
- `embedding_integration.md`
- `langchain_enhancements.md`
- `OPENROUTER_COMPLIANCE_ANALYSIS.md` (renamed)
- `STORY_ELEMENTS_VALIDATION.md` (renamed)

To `Docs/architecture/`:
- `PIPELINE_FLOWCHART.md`
- `pipeline_flowchart.mmd`
- `pipeline_flowchart.png`
- `pipeline_flowchart.svg`
- `pipeline_flowchart_updated.png`
- `pipeline_flowchart_updated.svg`

#### Phase 4: Original Docs/ Reorganized
To `Docs/architecture/`:
- `BlockDiagram.drawio`
- `BlockDiagram.drawio.svg`
- `Models.md`

To `Docs/examples/`:
- All `ExamplePrompts/` content (Example1, Example2, ShortDebuggingStory)

To `Docs/history/`:
- `Todo.md`
- All `anyar/` content

#### Phase 5: Docs/README.md Created
- Index/TOC for all documentation
- Files organized by category with status markers
- Quick links to project files
- Status legend (COMPLETED, FIXED, NOT IMPLEMENTED, etc.)

### Final Structure

```
Docs/
├── README.md                    # Index/TOC
├── analysis/                    # 9 files
│   ├── EMBEDDING_INTEGRATION.md
│   ├── EXPANDED_OUTLINE_ANALYSIS.md
│   ├── IMPROVEMENTS.md
│   ├── LANGCHAIN_ENHANCEMENTS.md
│   ├── OPENROUTER_COMPLIANCE_ANALYSIS.md
│   ├── PRD.md
│   ├── SCENE_PIPELINE_INEFFICIENCY_ANALYSIS.md
│   ├── STORY_ELEMENTS_VALIDATION.md
│   └── WORD_COUNT_VALIDATION_PROPOSAL.md
├── setup/                       # 1 file
│   └── GEMINI_SETUP.md
├── architecture/                # 9 files
│   ├── BlockDiagram.drawio
│   ├── BlockDiagram.drawio.svg
│   ├── MODELS.md
│   ├── PIPELINE_FLOWCHART.md
│   └── pipeline_flowchart.* (mmd, png, svg, updated.png, updated.svg)
├── examples/                    # 3 directories with content
│   ├── Example1/
│   ├── Example2/
│   └── ShortDebuggingStory/
└── history/                     # 1 file + 1 directory
    ├── Todo.md
    └── anyar/ (8 files)
```

**Root Directory After:**
- `README.md` ✅ (kept)
- `CLAUDE.md` ✅ (kept)
- All other MD files moved

**Deleted:**
- `docs/` directory ✅ (merged)
- `Docs/ExamplePrompts/` ✅ (moved content)
- `Docs/anyar/` ✅ (moved content)

### Git Status

```
$ git status
Changes to be committed:
  renamed:    EXPANDED_OUTLINE_ANALYSIS.md -> Docs/analysis/EXPANDED_OUTLINE_ANALYSIS.md
  renamed:    IMPROVEMENTS.md -> Docs/analysis/IMPROVEMENTS.md
  renamed:    docs/openrouter_api_compliance_analysis.md -> Docs/analysis/OPENROUTER_COMPLIANCE_ANALYSIS.md
  ... (40 more renames)
```

All 42+ files moved using `git mv`, preserving git history.

### Verification

**Git History Preserved:** ✅
- All renames recorded with `git mv`
- `git log --follow` shows complete history for moved files

**Structure Verification:** ✅
- Root now only has `README.md` and `CLAUDE.md`
- Docs/ organized into 5 categories
- No duplicate content between Docs/ and deleted directories

**File Counts:**
- Analysis: 9 markdown files
- Setup: 1 markdown file
- Architecture: 9 files (drawio, svg, mmd, png)
- Examples: 3 directories with outputs
- History: 1 file + 8 archived files in anyar/

### Impact

**Positive Outcomes:**
- ✅ Single documentation location (`Docs/`)
- ✅ Clear organization by category
- ✅ No documentation duplication
- ✅ Clean root directory
- ✅ Git history preserved for all files
- ✅ Easy navigation via Docs/README.md

**No Breaking Changes:**
- All content preserved
- No content lost
- All git history intact

---

*Documentation restructure completed January 6, 2026*

---

# Fix vLLM JSON Parsing & Dynamic Max Tokens

## Problem Statement

Dua masalah ditemukan saat testing vLLM dengan model gemma-3-12b-it:

### Problem 1: JSON Parsing - Unescaped Quotes
Model menghasilkan JSON dengan quotes yang tidak di-escape di dalam string:
```json
{"text": "...pekat... "Jangan pernah menyerah," gumamnya..."}
```

`json_repair.loads()` menginterpretasi ini sebagai JSON valid tapi salah semantik:
```json
{
    "text": "...pekat...",
    "Jangan pernah menyerah,": "gumamnya...",
    "hadapannya": "..."
}
```

**Impact:** Field `text` hanya 29 karakter (seharusnya 1500+), validation fail terus-menerus.

### Problem 2: vLLM Max Tokens Overflow
Error ketika input tokens besar:
```
'max_tokens' is too large: 4096. Model context=16384, input=12625 (4096 > 16384-12625)
```

**Impact:** Request gagal karena `max_tokens=4096` hardcoded tanpa memperhitungkan sisa context.

## Solution Design

### Problem 1: Schema-Aware JSON Repair (Code Reuse)
- Gunakan Pydantic schema yang sudah ada di `SafeGeneratePydantic`
- Setelah `json_repair.loads()`, detect extra keys yang bukan dari schema
- Merge extra keys kembali ke field `text` jika ada
- **Lokasi:** `SafeGeneratePydantic` (setelah line 803)
- **Library baru:** Tidak ada (reuse json_repair + Pydantic)

### Problem 2: Dynamic Max Tokens vLLM
- Hitung available tokens: `context_length - input_tokens - buffer`
- Set max_tokens = min(requested, available)
- Tambah `VLLM_CONTEXT_LENGTH` di Config.py
- **Lokasi:** `_vllm_chat` (line 1500-1502)
- **Library baru:** Tidak ada

## Implementation Plan

### Phase 1: TDD - Write Tests First
- [ ] Test untuk Problem 1: `test_json_repair_merges_extra_keys_to_text_field`
- [ ] Test untuk Problem 2: `test_vllm_dynamic_max_tokens_calculation`
- [ ] Run pytest - tests harus FAIL (red phase)

### Phase 2: Implement Problem 2 (Dynamic Max Tokens)
- [ ] Add `VLLM_CONTEXT_LENGTH = 16384` di Config.py
- [ ] Di `_vllm_chat`, hitung EstInputTokens dari _Messages_list
- [ ] Hitung available_tokens = VLLM_CONTEXT_LENGTH - EstInputTokens - 100 (buffer)
- [ ] Set max_tokens = min(requested, max(available, 256))
- [ ] Run test - should pass

### Phase 3: Implement Problem 1 (Schema-Aware JSON Repair)
- [ ] Di `SafeGeneratePydantic`, setelah `SafeGenerateJSON` return
- [ ] Get expected keys dari Pydantic model: `_PydanticModel.model_fields.keys()`
- [ ] Detect extra keys: `extra_keys = set(JSONResponse.keys()) - expected_keys`
- [ ] Jika extra_keys dan 'text' in expected_keys: merge extra ke text
- [ ] Run test - should pass

### Phase 4: Validation
- [ ] Run pytest semua tests
- [ ] Run pyright untuk files yang diedit
- [ ] Run flake8 untuk files yang diedit

### Phase 5: Review
- [ ] Verify fix logic benar
- [ ] Document perubahan di review section

## Expected Impact
- ✅ JSON parsing lebih robust untuk model yang tidak escape quotes dengan benar
- ✅ vLLM tidak error saat input tokens besar
- ✅ Code reuse - tidak ada library baru
- ✅ Hanya affects vLLM (Problem 2), semua provider (Problem 1 - tapi fix di SafeGeneratePydantic)

## Todo Checklist
- [x] Write tests (TDD red phase)
- [x] Implement Problem 2 (dynamic max_tokens)
- [x] Implement Problem 1 (schema-aware JSON repair)
- [x] Run pytest (100%)
- [x] Run pyright (no errors)
- [x] Run flake8 (no errors)
- [x] Add review section

---

## Review Section

### Implementation Summary

**Date:** January 18, 2026

**Files Changed:**
1. `Writer/Config.py` - Added VLLM_CONTEXT_LENGTH config
2. `Writer/Interface/Wrapper.py` - Dynamic max_tokens & schema-aware JSON repair
3. `tests/writer/interface/test_vllm_compliance.py` - 2 new tests for dynamic max_tokens
4. `tests/writer/interface/test_json_repair_extra_keys.py` - 4 new tests for JSON repair

### Changes Made

#### 1. Writer/Config.py (Line 319-321)

**Added:**
```python
# Context length for dynamic max_tokens calculation
# Set this to match your vLLM model's context window (default: gemma-3-12b-it = 16384)
VLLM_CONTEXT_LENGTH = 16384
```

#### 2. Writer/Interface/Wrapper.py - Dynamic Max Tokens (Lines 1570-1592)

**Added logic in `_vllm_chat`:**
- Calculate estimated input tokens from message content
- Compute available tokens: `context_length - est_input_tokens - safety_buffer`
- Adjust max_tokens: `min(requested, max(available, 256))`
- Log when reduction occurs for debugging

**Impact:**
- Prevents "max_tokens too large" errors when input is large
- Ensures at least 256 tokens for generation (minimum viable)
- Only affects vLLM provider

#### 3. Writer/Interface/Wrapper.py - Schema-Aware JSON Repair (Lines 821-865)

**Added logic in `SafeGeneratePydantic` after `SafeGenerateJSON` returns:**
1. Get expected field names from Pydantic model
2. Identify extra keys not in schema
3. Check if any extra key looks like broken quote fragment (contains comma, space, colon, etc.)
4. If found, merge ALL extra keys back into 'text' field
5. Delete merged keys from JSONResponse before Pydantic validation

**Key insight:** When JSON breaks due to unescaped quotes, ALL subsequent key:value pairs
are continuations of the original text, so they should all be merged.

**Impact:**
- Handles models that don't properly escape quotes in JSON output
- Recovers full text content that would otherwise be truncated
- Affects all providers (logic is in SafeGeneratePydantic which is shared)

### Test Results

**pytest:** ✅ **922/922 tests passed (100%)**
- 6 new tests added (2 for vLLM max_tokens, 4 for JSON repair)
- No regression detected

**pyright:** ✅ **0 errors, 0 warnings, 0 informations**

**flake8:** ✅ **No errors** (ignoring E501, W504, W503)

### Code Quality

**TDD Approach:** ✅ Followed London School TDD
1. **RED Phase:** Tests written first, all failed initially
2. **GREEN Phase:** Minimal implementation to pass tests
3. **REFACTOR Phase:** Improved logic to handle edge cases (normal extra fields vs broken quotes)

**Code Reuse:** ✅ No new libraries added
- Reused existing `json_repair` library
- Reused Pydantic model introspection (`model_fields`)
- Reused existing token estimation (`CHARS_PER_TOKEN_ESTIMATE`)

**Simplicity:** ✅ Minimal changes
- Problem 2: ~20 lines added to `_vllm_chat`
- Problem 1: ~35 lines added to `SafeGeneratePydantic`
- Both changes are self-contained and well-documented

### Bug Fix Verification

**Problem 1 - JSON Parsing:**
- Before: Text truncated at 29 chars due to unescaped quotes
- After: Full text recovered by merging broken quote fragments

**Problem 2 - Max Tokens:**
- Before: Error when input_tokens + max_tokens > context_length
- After: max_tokens automatically reduced to fit available context

### Expected User Impact

**For vLLM with gemma-3-12b-it:**
- ✅ No more "max_tokens too large" errors
- ✅ Better JSON parsing when model produces unescaped quotes
- ✅ Full chapter text recovered instead of truncated

**For All Providers:**
- ✅ Schema-aware JSON repair benefits any provider that produces malformed JSON
- ✅ No negative side effects for providers that produce correct JSON

---

*vLLM JSON Parsing & Dynamic Max Tokens fix completed January 18, 2026*

---

# Paragraph Formatting Fallback

## Problem Statement

Ketika LLM gagal menambahkan paragraph breaks yang memadai setelah max retries tercapai, chapter akan di-output dengan formatting yang buruk (wall of text). Perlu fallback mechanism untuk memastikan output selalu readable.

## Solution Design

**Option Chosen:** Hybrid (LLM + Rule-Based Fallback)
- LLM tetap mencoba formatting dengan feedback loop
- Jika max revisions tercapai, apply rule-based fallback

**Fallback Strategy:**
1. Check if text already has adequate paragraph breaks → return unchanged
2. Apply heuristic formatting (dialogue/scene boundaries + word count) → check again
3. Force split at sentence boundaries (last resort)

**Key Decisions:**
- Use regex for sentence tokenization (no NLTK dependency)
- 150 words per paragraph target
- Scene indicators stored in Config.py (symmetric EN/ID lists)
- Trigger fallback after CHAPTER_MAX_REVISIONS reached
- Log at warning level (6)

## Implementation Plan

### Phase 1: TDD - Write Tests First
- [x] Create `tests/writer/chapter/test_paragraph_formatter.py`
- [x] 24 tests for regex tokenizer, auto formatting, force split, main function
- [x] Run pytest - tests FAIL (red phase)

### Phase 2: Add Config Values
- [x] Add `PARAGRAPH_TARGET_WORDS = 150` to Config.py
- [x] Add `PARAGRAPH_SCENE_INDICATORS_EN` list
- [x] Add `PARAGRAPH_SCENE_INDICATORS_ID` list (symmetric with EN)

### Phase 3: Create ParagraphFormatter.py
- [x] `regex_sent_tokenize()` - Split text into sentences using regex
- [x] `auto_format_paragraphs()` - Heuristic-based formatting
- [x] `force_split_paragraphs()` - Last resort split
- [x] `ensure_paragraph_formatting()` - Main entry point

### Phase 4: Integrate into ChapterGenerator.py
- [x] Add import for `ensure_paragraph_formatting`
- [x] In Stage 2 and Stage 3, apply fallback when max revisions exceeded
- [x] Log warning when fallback applied

### Phase 5: Validation
- [x] Run pytest (950 tests)
- [x] Run pyright (0 errors)
- [x] Run flake8 (no errors)

### Phase 6: Review
- [x] Update tasks/todo.md with review section

## Todo Checklist
- [x] Write tests (TDD red phase)
- [x] Add config values to Config.py
- [x] Create ParagraphFormatter.py
- [x] Integrate fallback in ChapterGenerator.py
- [x] Run pytest (100%)
- [x] Run pyright (no errors)
- [x] Run flake8 (no errors)
- [x] Add review section

---

## Review Section

### Implementation Summary

**Date:** January 19, 2026

**Files Changed:**
1. `Writer/Config.py` - Added paragraph formatting config values
2. `Writer/Chapter/ParagraphFormatter.py` - NEW: Fallback formatting module
3. `Writer/Chapter/ChapterGenerator.py` - Integrated fallback after max retries
4. `tests/writer/chapter/test_paragraph_formatter.py` - NEW: 24 tests
5. `tests/writer/chapter/test_chapter_generator_fallback.py` - NEW: 4 integration tests

### Changes Made

#### 1. Writer/Config.py (Lines 350-369)

**Added:**
```python
# Paragraph formatting fallback settings
PARAGRAPH_TARGET_WORDS = 150

# Scene indicators for paragraph breaks (EN)
PARAGRAPH_SCENE_INDICATORS_EN = [
    "Meanwhile", "Later", "Suddenly", "The next", "That night",
    "That morning", "That afternoon", "After", "Before long",
]

# Scene indicators for paragraph breaks (ID) - must be symmetric with EN
PARAGRAPH_SCENE_INDICATORS_ID = [
    "Sementara itu", "Kemudian", "Tiba-tiba", "Keesokan", "Malam itu",
    "Pagi itu", "Sore itu", "Setelah", "Tak lama",
]
```

#### 2. Writer/Chapter/ParagraphFormatter.py (NEW - 241 lines)

**Key Functions:**
- `regex_sent_tokenize(text)` - Regex-based sentence splitter with abbreviation handling
- `auto_format_paragraphs(text, target_words)` - Heuristic formatting with dialogue/scene detection
- `force_split_paragraphs(text, max_chars)` - Last resort character-based splitting
- `ensure_paragraph_formatting(text, chapter_num, native_language)` - Main entry point

**Features:**
- Handles abbreviations (Mr., Mrs., Dr., etc.) without false splits
- Detects dialogue start (quotes, smart quotes, Japanese brackets)
- Detects scene indicators (EN and ID)
- Falls back gracefully through three levels

#### 3. Writer/Chapter/ChapterGenerator.py (Lines 8, 359-368, 444-453)

**Added import:**
```python
from Writer.Chapter.ParagraphFormatter import ensure_paragraph_formatting
```

**Added fallback in Stage 2:**
```python
if IterCounter > Config_module.CHAPTER_MAX_REVISIONS:
    # Apply paragraph formatting fallback before exiting
    native_lang = getattr(Config_module, 'NATIVE_LANGUAGE', 'en')
    Stage2Chapter, was_modified = ensure_paragraph_formatting(
        Stage2Chapter, _ChapterNum, native_lang
    )
    if was_modified:
        _Logger.Log(f"Paragraph formatting fallback applied to Chapter {_ChapterNum} (Stage 2)", 6)
    break
```

**Same pattern added to Stage 3 (dialogue generation)**

### Test Results

**pytest:** ✅ **950/950 tests passed (100%)**
- 28 new tests added (24 for ParagraphFormatter, 4 for integration)
- No regression detected

**pyright:** ✅ **0 errors, 0 warnings, 0 informations**

**flake8:** ✅ **No errors** (ignoring E501, W504, W503)

### Code Quality

**TDD Approach:** ✅ Followed London School TDD
1. **RED Phase:** 24 tests written first, all failed
2. **GREEN Phase:** ParagraphFormatter.py implemented to pass tests
3. **REFACTOR Phase:** Fixed syntax error (smart quotes), cleaned up flake8 warnings

**Code Reuse:** ✅ No new libraries
- Pure regex for sentence tokenization
- Reused ParagraphValidator for validation checks
- Reused Config values pattern

**Simplicity:** ✅ Minimal implementation
- Single file module (241 lines)
- Clear function responsibilities
- Config-driven (no hardcoded values in logic)

### Expected Impact

**For Chapter Generation:**
- ✅ Chapters always output with readable paragraph formatting
- ✅ Fallback only triggers after max retries exhausted
- ✅ Warning logged when fallback applied (for debugging)

**For Both Languages:**
- ✅ Works with English and Indonesian text
- ✅ Symmetric scene indicator lists ensure consistent behavior
- ✅ Dialogue detection handles multiple quote styles

**No Breaking Changes:**
- Fallback only triggers when LLM fails after max retries
- Existing well-formatted chapters are returned unchanged
- All existing tests still pass

---

*Paragraph Formatting Fallback completed January 19, 2026*
