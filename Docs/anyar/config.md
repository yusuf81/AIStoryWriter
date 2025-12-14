# AIStoryWriter Configuration (`Writer/Config.py`)

**Status Update (2025-12-11):** ⚠️ **PARTIALLY OUTDATED** - Documentation coverage: 68.4% (52/76 variables)

This file documents the configuration variables found in `Writer/Config.py`. These variables control various aspects of the story generation process, including model selection, quality control, and feature flags.

**Note:** Many of these default values can be overridden by command-line arguments when running `Write.py`.

## ⚠️ Missing Documentation (24 Variables)

The following variables exist in `Writer/Config.py` but are NOT documented below:

**Model Selection:**
- `FAST_MODEL` (line 35-38): Default fast model for quick tasks like titling

**Generation Control:**
- `NATIVE_LANGUAGE` (line 93): Language for prompts (default: "id" Indonesian)

**Chapter Title Management (10 variables, lines 102-112):**
- `CHAPTER_HEADER_FORMAT`, `CHAPTER_MEMORY_WORDS`, `GENERATE_CHAPTER_TITLES`
- `TITLE_MAX_TOKENS`, `MAX_WORDS_FOR_CHAPTER_TITLE_PROMPT`
- `MIN_WORDS_FOR_CHAPTER_TITLE`, `MAX_LENGTH_CHAPTER_TITLE`
- `MAX_RETRIES_CHAPTER_TITLE`, `AUTO_CHAPTER_TITLES`, `DEFAULT_CHAPTER_TITLE_PREFIX`

**Output Directories (2 variables, lines 114-115):**
- `STORIES_DIR`: Directory for generated stories
- `LOG_DIRECTORY`: Directory for log files

**Markdown Output Configuration (5 variables, lines 113, 118-121):**
- `ADD_CHAPTER_TITLES_TO_NOVEL_BODY_TEXT`
- `INCLUDE_OUTLINE_IN_MD`, `INCLUDE_STATS_IN_MD`
- `INCLUDE_SUMMARY_IN_MD`, `INCLUDE_TAGS_IN_MD`

**PDF Generation (5 variables, lines 124-128):**
- `ENABLE_PDF_GENERATION`, `PDF_FONT_FAMILY`, `PDF_FONT_SIZE`
- `PDF_TITLE_SIZE`, `PDF_CHAPTER_SIZE`

**Other:**
- `ENABLE_GLOBAL_OUTLINE_REFINEMENT` (line 110)

---

## Model Selection

These variables define which Large Language Model (LLM) is used for specific tasks in the generation pipeline. The format is typically `provider://model_name@host?parameters`.

-   **`INITIAL_OUTLINE_WRITER_MODEL`**:
    -   **Function:** Model used for generating the initial story outline based on the user's prompt and also for revising the outline based on feedback.
    -   **Usage:** Called by `Writer.OutlineGenerator.GenerateOutline` and `Writer.OutlineGenerator.ReviseOutline`.

-   **`CHAPTER_OUTLINE_WRITER_MODEL`**:
    -   **Function:** Model used for expanding the main outline into detailed, per-chapter outlines (if `EXPAND_OUTLINE` is enabled) or for generating scene-by-scene outlines from a chapter outline (if `SCENE_GENERATION_PIPELINE` is enabled).
    -   **Usage:** Called by `Writer.OutlineGenerator.GeneratePerChapterOutline` and `Writer.Scene.ChapterOutlineToScenes.ChapterOutlineToScenes`.

-   **`CHAPTER_STAGE1_WRITER_MODEL`**:
    -   **Function:** Model used for the first stage of chapter writing, focusing on generating the basic plot and narrative flow based on the chapter outline and previous context. Also used for generating scene content from scene outlines in the scene-by-scene pipeline.
    -   **Usage:** Called by `Writer.Chapter.ChapterGenerator.GenerateChapter` (Stage 1) and `Writer.Scene.SceneOutlineToScene.SceneOutlineToScene`. Also used for some internal summary checks (`Writer.Chapter.ChapterGenSummaryCheck`).

-   **`CHAPTER_STAGE2_WRITER_MODEL`**:
    -   **Function:** Model used for the second stage of chapter writing, taking the output of Stage 1 and enriching it with character development, internal thoughts, and motivations.
    -   **Usage:** Called by `Writer.Chapter.ChapterGenerator.GenerateChapter` (Stage 2).

-   **`CHAPTER_STAGE3_WRITER_MODEL`**:
    -   **Function:** Model used for the third stage of chapter writing, taking the output of Stage 2 and adding dialogue between characters.
    -   **Usage:** Called by `Writer.Chapter.ChapterGenerator.GenerateChapter` (Stage 3).

-   **`FINAL_NOVEL_EDITOR_MODEL`**:
    -   **Function:** Model used for the optional final editing pass over the entire novel (triggered by `ENABLE_FINAL_EDIT_PASS`). This pass aims to improve consistency and flow across all chapters.
    -   **Usage:** Called by `Writer.NovelEditor.EditNovel`.

-   **`CHAPTER_REVISION_WRITER_MODEL`**:
    -   **Function:** Model used specifically during the chapter revision cycle (if enabled). It takes the generated chapter draft and feedback/critique to produce an improved version.
    -   **Usage:** Called by `Writer.Chapter.ChapterGenerator.ReviseChapter`.

-   **`REVISION_MODEL`**:
    -   **Function:** Model used to generate constructive criticism and feedback on the generated outline or chapter drafts. It evaluates the content against specific criteria.
    -   **Usage:** Called by `Writer.LLMEditor.GetFeedbackOnOutline` and `Writer.LLMEditor.GetFeedbackOnChapter`. Also used in `Writer.Chapter.ChapterGenSummaryCheck` for comparing summaries.

-   **`EVAL_MODEL`**:
    -   **Function:** Model used to evaluate whether an outline or chapter meets the required quality standards (outputting a simple true/false JSON). Also used by `Evaluate.py` for comparing stories and by `Writer.Chapter.ChapterDetector` for counting chapters.
    -   **Usage:** Called by `Writer.LLMEditor.GetOutlineRating`, `Writer.LLMEditor.GetChapterRating`, `Writer.Chapter.ChapterDetector.LLMCountChapters`, and `Evaluate.py`.

-   **`INFO_MODEL`**:
    -   **Function:** Model used at the end of the generation process to extract metadata from the completed story, such as Title, Summary, and Tags.
    -   **Usage:** Called by `Writer.StoryInfo.GetStoryInfo`.

-   **`SCRUB_MODEL`**:
    -   **Function:** Model used during the optional scrubbing pass to clean up the final chapters, removing any leftover instructions, outline fragments, or AI artifacts.
    -   **Usage:** Called by `Writer.Scrubber.ScrubNovel`.

-   **`CHECKER_MODEL`**:
    -   **Function:** Model used for internal checks, such as converting a markdown list of scenes into a JSON list.
    -   **Usage:** Called by `Writer.Scene.ScenesToJSON.ScenesToJSON`.

-   **`TRANSLATOR_MODEL`**:
    -   **Function:** Model used for translating the user's initial prompt or the final generated novel into a specified language.
    -   **Usage:** Called by `Writer.Translator.TranslatePrompt` and `Writer.Translator.TranslateNovel`.

## Ollama Specific

-   **`OLLAMA_CTX`**:
    -   **Function:** Default context window size (in tokens) to use for Ollama models if not specified in the model string parameters.
    -   **Usage:** Used by `Writer.Interface.Wrapper.ChatResponse` when setting Ollama options.

-   **`OLLAMA_HOST`**:
    -   **Function:** Default hostname and port for the Ollama server if not specified in the model string (e.g., `ollama://model_name` instead of `ollama://model_name@host`).
    -   **Usage:** Used by `Writer.Interface.Wrapper.GetModelAndProvider` and `Writer.Interface.Wrapper.LoadModels`.

## Generation Control

-   **`SEED`**:
    -   **Function:** Seed value used for LLM generation to attempt to make outputs more deterministic and reproducible. A specific seed is used for initial generation, and variations might be used during retries or revisions.
    -   **Usage:** Used by `Writer.Interface.Wrapper.ChatResponse` and potentially passed as an override in generation stages.

-   **`TRANSLATE_LANGUAGE`**:
    -   **Function:** Target language for translating the final novel. If empty or `None`, translation is skipped. Set via `-Translate` argument.
    -   **Usage:** Checked in `Write.py` to trigger `Writer.Translator.TranslateNovel`.

-   **`TRANSLATE_PROMPT_LANGUAGE`**:
    -   **Function:** Target language for translating the initial user prompt before generation begins. If empty or `None`, prompt translation is skipped. Set via `-TranslatePrompt` argument.
    -   **Usage:** Checked in `Write.py` to trigger `Writer.Translator.TranslatePrompt`.

## Quality & Revision Control

-   **`OUTLINE_QUALITY`**:
    -   **Function:** (Potentially deprecated/unused) Previously likely intended as a target quality score (0-100) for outline revision, but the current revision logic uses a boolean `IsComplete` check.
    -   **Usage:** Passed to `Writer.OutlineGenerator.GenerateOutline` but might not be actively used by the revision loop logic which relies on `LLMEditor.GetOutlineRating`.

-   **`OUTLINE_MIN_REVISIONS`**:
    -   **Function:** The minimum number of revision cycles the initial outline must go through, even if the `EVAL_MODEL` deems it complete earlier.
    -   **Usage:** Checked in the outline revision loop in `Writer.OutlineGenerator.GenerateOutline`.

-   **`OUTLINE_MAX_REVISIONS`**:
    -   **Function:** The maximum number of revision cycles allowed for the initial outline. The loop terminates if this limit is reached, regardless of quality.
    -   **Usage:** Checked in the outline revision loop in `Writer.OutlineGenerator.GenerateOutline`.

-   **`CHAPTER_NO_REVISIONS`**:
    -   **Function:** A boolean flag (True/False) to completely disable the feedback and revision cycle for *all* chapters, overriding other chapter quality settings. Set via `-NoChapterRevision` argument.
    -   **Usage:** Checked in `Writer.Chapter.ChapterGenerator.GenerateChapter` before entering the revision loop (Stage 5).

-   **`CHAPTER_QUALITY`**:
    -   **Function:** (Potentially deprecated/unused) Similar to `OUTLINE_QUALITY`, likely intended as a target score, but the current chapter revision loop uses a boolean `IsComplete` check.
    -   **Usage:** Passed to `Writer.Chapter.ChapterGenerator.GenerateChapter` but might not be actively used by the revision loop logic which relies on `LLMEditor.GetChapterRating`.

-   **`CHAPTER_MIN_REVISIONS`**:
    -   **Function:** The minimum number of revision cycles each chapter must go through (if revisions are enabled), even if deemed complete earlier.
    -   **Usage:** Checked in the chapter revision loop in `Writer.Chapter.ChapterGenerator.GenerateChapter`.

-   **`CHAPTER_MAX_REVISIONS`**:
    -   **Function:** The maximum number of revision cycles allowed for each chapter. Also used as the maximum retry limit within Stages 1, 2, and 3 if the `LLMSummaryCheck` fails repeatedly.
    -   **Usage:** Checked in the chapter revision loop and the internal stage loops in `Writer.Chapter.ChapterGenerator.GenerateChapter`.

## Minimum Word Counts

These variables set minimum word count thresholds for the `SafeGenerateText` function to ensure that the LLM provides a reasonably substantial response for various tasks, preventing empty or overly short outputs.

-   **`MIN_WORDS_TRANSLATE_PROMPT`**: Minimum words for the translated user prompt.
-   **`MIN_WORDS_INITIAL_OUTLINE`**: Minimum words for the first generated story outline.
-   **`MIN_WORDS_REVISE_OUTLINE`**: Minimum words for a revised story outline.
-   **`MIN_WORDS_PER_CHAPTER_OUTLINE`**: Minimum words when generating a detailed outline for a single chapter.
-   **`MIN_WORDS_STORY_ELEMENTS`**: Minimum words when generating the initial story elements (characters, setting, etc.).
-   **`MIN_WORDS_CHAPTER_SEGMENT_EXTRACT`**: Minimum words when extracting the specific outline portion for the current chapter.
-   **`MIN_WORDS_CHAPTER_SUMMARY`**: Minimum words when summarizing the previous chapter's content.
-   **`MIN_WORDS_CHAPTER_DRAFT`**: Minimum words for the outputs of chapter generation stages 1, 2, and 3.
-   **`MIN_WORDS_REVISE_CHAPTER`**: Minimum words for a revised chapter during the feedback loop.
-   **`MIN_WORDS_OUTLINE_FEEDBACK`**: Minimum words for the critique/feedback generated for the outline.
-   **`MIN_WORDS_SCENE_OUTLINE`**: Minimum words when generating a scene-by-scene outline for a chapter.
-   **`MIN_WORDS_SCENE_WRITE`**: Minimum words when writing a full scene based on its outline.
-   **`MIN_WORDS_SCRUB_CHAPTER`**: Minimum words for a chapter after it has been processed by the scrubbing model.
-   **`MIN_WORDS_EDIT_NOVEL`**: Minimum words for a chapter after it has been processed during the final novel-wide edit pass.

## Feature Flags

These boolean flags control whether certain optional steps or pipelines are executed.

-   **`SCRUB_NO_SCRUB`**:
    -   **Function:** If `True`, disables the final scrubbing pass intended to remove AI artifacts. Set via `-NoScrubChapters` argument.
    -   **Usage:** Checked in `Write.py` before calling `Writer.Scrubber.ScrubNovel`.

-   **`EXPAND_OUTLINE`**:
    -   **Function:** If `True`, enables the step where the main outline is expanded into detailed per-chapter outlines before chapter writing begins. Set via `-ExpandOutline` argument (note: the argument description says it *disables* expansion, which seems contradictory to the variable name and default `True` in `Write.py`'s `argparse` setup - the code logic uses `if Writer.Config.EXPAND_OUTLINE:`).
    -   **Usage:** Checked in `Write.py` to control the per-chapter outline generation loop and determine which outline (`MegaOutline` or base `Outline`) is passed to chapter generation.

-   **`ENABLE_FINAL_EDIT_PASS`**:
    -   **Function:** If `True`, enables an additional editing pass over the entire novel *after* all chapters are initially generated and revised, but *before* scrubbing/translation. Set via `-EnableFinalEditPass` argument.
    -   **Usage:** Checked in `Write.py` before calling `Writer.NovelEditor.EditNovel`.

-   **`SCENE_GENERATION_PIPELINE`**:
    -   **Function:** If `True`, uses the newer scene-by-scene generation method (Chapter Outline -> Scene Outlines -> Scene JSON -> Write Scenes -> Combine Scenes) as the *initial draft* for chapters (Stage 1 output), before proceeding to Stages 2 and 3. If `False`, uses the older direct Stage 1 plot generation. Set via `-SceneGenerationPipeline` argument.
    -   **Usage:** Checked in `Writer.Chapter.ChapterGenerator.GenerateChapter` to decide between calling `Writer.Scene.ChapterByScene.ChapterByScene` or the Stage 1 generation loop.

-   **`OPTIONAL_OUTPUT_NAME`**:
    -   **Function:** Allows specifying a custom base filename (and potentially path) for the final output `.md` and `.json` files. If empty, a name is automatically generated based on the story title and timestamp. Set via `-Output` argument.
    -   **Usage:** Used in `Write.py` when constructing the final output file paths.

-   **`DEBUG`**:
    -   **Function:** If `True`, enables additional verbose logging, potentially including printing full message histories sent to the LLM. Set via `-Debug` argument.
    -   **Usage:** Checked in `Writer.Interface.Wrapper.ChatResponse` and potentially other places for conditional logging/printing.

## Retry Limits

-   **`MAX_JSON_RETRIES`**:
    -   **Function:** Maximum number of times the system will retry generating a response when using `SafeGenerateJSON` if the initial response is not valid JSON or fails parsing.
    -   **Usage:** Used within the retry loop in `Writer.Interface.Wrapper.SafeGenerateJSON`.

-   **`MAX_TEXT_RETRIES`**:
    -   **Function:** Maximum number of times the system will retry generating a response when using `SafeGenerateText` if the initial response is empty, whitespace-only, or shorter than the specified minimum word count.
    -   **Usage:** Used within the retry loop in `Writer.Interface.Wrapper.SafeGenerateText`.
