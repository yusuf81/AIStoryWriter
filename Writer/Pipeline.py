import os
import json
import shutil
import time
import datetime

# Import Pydantic model for title generation
from Writer.Models import TitleOutput
# Import StateManager for proper Pydantic serialization
from Writer.StateManager import StateManager, serialize_for_json


# Assuming Writer.Config, Writer.Statistics, and other Writer modules will be imported
# by the consuming code or passed appropriately.


def save_state_pipeline(state_data, filepath, logger):
    """Saves the current state to a JSON file with proper Pydantic serialization."""
    temp_filepath = filepath + ".tmp"
    try:
        # Use StateManager to properly handle Pydantic objects
        StateManager.save_state(state_data, temp_filepath)
        shutil.move(temp_filepath, filepath)
    except Exception as e:
        if logger:
            logger.Log(f"PIPELINE SAVE_STATE FATAL: Failed to save state to {filepath}: {e}", 7)
        else:
            print(f"Error: Failed to save state to {filepath} from pipeline: {e}")

# Helper: Builds the comprehensive outline string used for chapter generation context.


def _build_mega_outline_pipeline_version(SysLogger, Config, ActivePrompts, current_state, chapter_index_for_context=None):
    SysLogger.Log(f"Pipeline: Building Mega Outline (Chapter Context: {chapter_index_for_context}).", 6)

    FullOutline = current_state.get("full_outline", "")
    StoryElements = current_state.get("story_elements", "")
    ExpandedChapterOutlines = current_state.get("expanded_chapter_outlines", [])  # List of strings
    RefinedGlobalOutline = current_state.get("refined_global_outline", "")  # Added

    # Use refined global outline if available and EXPAND_OUTLINE is true, otherwise use original full_outline
    base_outline_to_use = FullOutline
    if Config.EXPAND_OUTLINE and RefinedGlobalOutline:
        base_outline_to_use = RefinedGlobalOutline
        SysLogger.Log(f"Pipeline: Using refined_global_outline for Mega Outline base.", 6)
    elif Config.EXPAND_OUTLINE:
        SysLogger.Log(f"Pipeline: EXPAND_OUTLINE is true, but no refined_global_outline found. Using original full_outline for Mega Outline base.", 6)
    else:
        SysLogger.Log(f"Pipeline: Using original full_outline for Mega Outline base (EXPAND_OUTLINE is false or no refined_global_outline).", 6)

    Preamble = ActivePrompts.MEGA_OUTLINE_PREAMBLE
    ChapterOutlineFormat = ActivePrompts.MEGA_OUTLINE_CHAPTER_FORMAT

    MegaOutline = Preamble + "\n\n"
    if StoryElements:  # Only add if StoryElements exist
        MegaOutline += f"# Story Elements\n{StoryElements}\n\n"

    MegaOutline += f"# Base Narrative Outline\n{base_outline_to_use}\n\n"  # Use the determined base

    if Config.EXPAND_OUTLINE and ExpandedChapterOutlines:
        MegaOutline += "# Expanded Per-Chapter Outlines\n"
        for i, chapter_outline_text in enumerate(ExpandedChapterOutlines):
            chapter_num = i + 1
            is_current_chapter = (chapter_index_for_context is not None and chapter_num == chapter_index_for_context)
            prefix = ActivePrompts.MEGA_OUTLINE_CURRENT_CHAPTER_PREFIX if is_current_chapter else ""

            # Extract text and title from dict
            text = chapter_outline_text["text"]
            title = chapter_outline_text["title"]

            MegaOutline += ChapterOutlineFormat.format(
                chapter_num=chapter_num,
                chapter_title=title,
                chapter_content=text
            )
            MegaOutline += "\n\n"

    SysLogger.Log(f"Pipeline: Mega Outline Length: {len(MegaOutline)} chars.", 6)
    return MegaOutline.strip()


def _calculate_total_chapter_outline_words(chapter_outline_dict, Statistics):
    """
    Calculate total word count for a chapter outline including ALL fields.

    Counts words from:
    - outline_summary (stored as "text" field)
    - all scenes in the scenes array (if present)

    This fixes the bug where only outline_summary was counted,
    ignoring the richer scenes array content.

    Args:
        chapter_outline_dict: Dict with 'text', 'scenes' (optional), etc.
        Statistics: Statistics module for word counting

    Returns:
        int: Total word count across all fields
    """
    total_words = 0

    # Count outline_summary text
    if "text" in chapter_outline_dict:
        total_words += Statistics.GetWordCount(chapter_outline_dict["text"])

    # Count all scenes if present
    if "scenes" in chapter_outline_dict and chapter_outline_dict["scenes"]:
        for scene in chapter_outline_dict["scenes"]:
            if isinstance(scene, str):
                # Simple string scene
                total_words += Statistics.GetWordCount(scene)
            elif isinstance(scene, dict):
                # Structured scene - count all text fields
                for key, value in scene.items():
                    if isinstance(value, str):
                        total_words += Statistics.GetWordCount(value)
                    elif isinstance(value, list):
                        # Handle lists of strings (e.g., characters_present)
                        for item in value:
                            if isinstance(item, str):
                                total_words += Statistics.GetWordCount(item)

    return total_words


# Helper: Gets the specific outline to be used for generating a given chapter.
def _get_outline_for_chapter_pipeline_version(SysLogger, Config, Statistics, ActivePrompts, current_state, chapter_index):
    SysLogger.Log(f"Pipeline: Determining outline for Chapter {chapter_index}.", 6)

    ExpandedChapterOutlines = current_state.get("expanded_chapter_outlines", [])

    if Config.EXPAND_OUTLINE and ExpandedChapterOutlines and chapter_index > 0 and len(ExpandedChapterOutlines) >= chapter_index:
        potential_expanded_outline = ExpandedChapterOutlines[chapter_index - 1]
        min_len_threshold = Config.MIN_WORDS_PER_CHAPTER_OUTLINE

        # Calculate word count including ALL content (summary + scenes)
        if isinstance(potential_expanded_outline, dict):
            # NEW: Count ALL content, not just summary
            word_count = _calculate_total_chapter_outline_words(
                potential_expanded_outline, Statistics
            )
        else:
            # Fallback for old string format
            word_count = Statistics.GetWordCount(potential_expanded_outline)

        if word_count >= min_len_threshold:
            SysLogger.Log(f"Pipeline: Using specific expanded outline for Chapter {chapter_index} (Words: {word_count}).", 6)
            # Return extracted text for consistency
            if isinstance(potential_expanded_outline, dict):
                return potential_expanded_outline["text"]
            else:
                return potential_expanded_outline
        else:
            SysLogger.Log(f"Pipeline: Warning: Expanded outline for Chapter {chapter_index} is too short ({word_count} words, min {min_len_threshold}). Falling back to MegaOutline.", 6)
            # Fall through to use MegaOutline
    elif Config.EXPAND_OUTLINE:
        SysLogger.Log(f"Pipeline: Conditions not met for specific expanded outline for Chapter {chapter_index} (e.g., not found, index out of bounds). Falling back to MegaOutline.", 6)

    # Fallback: Construct and return the MegaOutline if no specific chapter outline is suitable or if EXPAND_OUTLINE is false (MegaOutline handles this)
    # The chapter_index_for_context in _build_mega_outline is to highlight the current chapter, not to select only one.
    # For chapter generation, the _get_current_context_for_chapter_gen_pipeline_version will build the more focused prompt.
    # This function's fallback is the comprehensive MegaOutline.
    SysLogger.Log(f"Pipeline: Using MegaOutline as the outline source for Chapter {chapter_index}.", 6)
    return _build_mega_outline_pipeline_version(SysLogger, Config, ActivePrompts, current_state, chapter_index_for_context=chapter_index)


# Helper: Builds the context for chapter generation (base story elements, previous text, current chapter outline).
def _get_current_context_for_chapter_gen_pipeline_version(SysLogger, Config, Statistics, ActivePrompts, current_state, chapter_num, base_context_text, lorebook=None):
    SysLogger.Log(f"Pipeline: Building generation context for Chapter {chapter_num}.", 6)

    # 1. Base Context (Story Elements, etc., from initial outline generation)
    context_components = [base_context_text]

    # 2. Relevant Lore (if lorebook is enabled)
    if lorebook and Config.USE_LOREBOOK:
        # Build query from chapter outline if available
        current_chapter_specific_outline = _get_outline_for_chapter_pipeline_version(
            SysLogger, Config, Statistics, ActivePrompts, current_state, chapter_num
        )
        lore_retrieval_query = f"{base_context_text}\n\n{current_chapter_specific_outline}"

        lore = lorebook.retrieve(lore_retrieval_query, k=Config.LOREBOOK_K_RETRIEVAL)
        if lore:
            formatted_lore = f"### Relevant Lore:\n{lore}"
            context_components.append(formatted_lore)
            SysLogger.Log(f"Pipeline: Added lorebook context ({len(lore)} chars) for Chapter {chapter_num}", 6)

    # 3. Previous Chapter Text (if enabled and available)
    if Config.CHAPTER_MEMORY_WORDS > 0 and chapter_num > 1:
        completed_chapters_data = current_state.get("completed_chapters_data", [])  # Expects list of dicts
        if len(completed_chapters_data) >= (chapter_num - 1) and chapter_num - 2 < len(completed_chapters_data):  # Ensure index is valid
            # completed_chapters_data stores dicts: {"number": N, "title": "T", "text": "actual chapter text"}
            previous_chapter_info = completed_chapters_data[chapter_num - 2]  # -2 because list is 0-indexed and chapter_num is 1-indexed
            previous_chapter_text = previous_chapter_info.get("text", "")

            if previous_chapter_text:
                previous_chapter_words = previous_chapter_text.split()

                # ADAPTIVE MEMORY LOGIC
                # For short stories (≤3 chapters), use min(100, CHAPTER_MEMORY_WORDS)
                # For longer stories (>3 chapters), use full CHAPTER_MEMORY_WORDS
                total_chapters = current_state.get("total_chapters", chapter_num)
                if total_chapters <= 3:
                    adaptive_memory_words = min(100, Config.CHAPTER_MEMORY_WORDS)
                    SysLogger.Log(f"Pipeline: Using adaptive memory {adaptive_memory_words} words for short story ({total_chapters} chapters).", 6)
                else:
                    adaptive_memory_words = Config.CHAPTER_MEMORY_WORDS
                    SysLogger.Log(f"Pipeline: Using full memory {adaptive_memory_words} words for long story ({total_chapters} chapters).", 6)

                # Ensure adaptive_memory_words is positive, else take all words
                context_words_count = adaptive_memory_words if adaptive_memory_words > 0 else len(previous_chapter_words)
                previous_chapter_segment = " ".join(previous_chapter_words[-context_words_count:])

                formatted_prev_chapter_text = ActivePrompts.PREVIOUS_CHAPTER_CONTEXT_FORMAT.format(
                    chapter_num=previous_chapter_info.get("number", chapter_num - 1),  # Use actual number from data if available
                    previous_chapter_title=previous_chapter_info.get("title", f"Chapter {chapter_num-1}"),
                    previous_chapter_text=previous_chapter_segment
                )
                context_components.append(formatted_prev_chapter_text)
                SysLogger.Log(f"Pipeline: Added last {Statistics.GetWordCount(previous_chapter_segment)} words from Chapter {chapter_num - 1} to context.", 6)
            else:
                SysLogger.Log(f"Pipeline: Previous Chapter {chapter_num - 1} text was empty. Not added to context.", 6)
        else:
            SysLogger.Log(f"Pipeline: Chapter {chapter_num -1} data not found in completed_chapters_data for context.", 6)

    # 4. Specific Outline for the Current Chapter
    # This uses _get_outline_for_chapter_pipeline_version, which might return a detailed chapter outline or the MegaOutline.
    current_chapter_specific_outline = _get_outline_for_chapter_pipeline_version(
        SysLogger, Config, Statistics, ActivePrompts, current_state, chapter_num
    )

    formatted_chapter_outline = ActivePrompts.CURRENT_CHAPTER_OUTLINE_FORMAT.format(
        chapter_num=chapter_num,
        chapter_outline_text=current_chapter_specific_outline
    )
    context_components.append(formatted_chapter_outline)

    final_context = "\n\n---\n\n".join(filter(None, context_components))  # Join non-empty components with a separator
    SysLogger.Log(f"Pipeline: Final context for Chapter {chapter_num} length: {len(final_context)} chars, Word Count: {Statistics.GetWordCount(final_context)}.", 6)
    return final_context.strip()

# Helper: Handles chapter title generation.


def _handle_chapter_title_generation_pipeline_version(SysLogger, Interface, Config, ActivePrompts, chapter_text, chapter_num, base_context_for_title, current_chapter_outline_for_title, Statistics):
    SysLogger.Log(f"Pipeline: Generating title for Chapter {chapter_num}.", 6)
    if not Config.AUTO_CHAPTER_TITLES:  # Changed from GENERATE_CHAPTER_TITLES
        SysLogger.Log("Pipeline: Chapter title generation is disabled by config (AUTO_CHAPTER_TITLES=False).", 6)
        return f"{Config.DEFAULT_CHAPTER_TITLE_PREFIX}{chapter_num}"

    try:
        # Ensure chapter_text is not excessively long for a title prompt
        max_words_for_title_prompt = Config.MAX_WORDS_FOR_CHAPTER_TITLE_PROMPT
        chapter_text_segment_for_title = " ".join(chapter_text.split()[:max_words_for_title_prompt])

        title_prompt_content = ActivePrompts.GET_CHAPTER_TITLE_PROMPT.format(
            base_story_context=base_context_for_title,
            current_chapter_outline=current_chapter_outline_for_title,
            chapter_num=chapter_num,
            chapter_text_segment=chapter_text_segment_for_title,  # Use segmented text
            word_count=Statistics.GetWordCount(chapter_text_segment_for_title)
        )

        title_messages = [Interface.BuildUserQuery(title_prompt_content)]
        # Use SafeGeneratePydantic for structured title generation
        title_response_messages, Title_obj, _ = Interface.SafeGeneratePydantic(
            _Logger=SysLogger,
            _Messages=title_messages,
            _Model=Config.FAST_MODEL,
            _PydanticModel=TitleOutput,
            _max_retries_override=Config.MAX_RETRIES_CHAPTER_TITLE
        )
        # Extract title from validated Pydantic model
        ChapterTitle = Title_obj.title.strip()  # Title already cleaned by validator

        if not ChapterTitle or len(ChapterTitle) > Config.MAX_LENGTH_CHAPTER_TITLE:
            SysLogger.Log(f"Pipeline: Warning: Generated title for Chapter {chapter_num} is invalid ('{ChapterTitle}'). Using default.", 6)
            return f"{Config.DEFAULT_CHAPTER_TITLE_PREFIX}{chapter_num}"

        SysLogger.Log(f"Pipeline: Generated title for Chapter {chapter_num}: '{ChapterTitle}'.", 5)  # Changed log level
        return ChapterTitle

    except Exception as e:
        SysLogger.Log(f"Pipeline: Error during chapter title generation for Chapter {chapter_num}: {e}. Using default title.", 7)
        import traceback
        SysLogger.Log(traceback.format_exc(), 1)  # Log stack trace at debug level
        return f"{Config.DEFAULT_CHAPTER_TITLE_PREFIX}{chapter_num}"

# Helper: Compiles all chapter texts into a single string for editing or final output.


def _get_full_story_text_pipeline_version(chapters_data_list, Config, add_titles_to_body):
    FullStory = ""
    for chapter_info in chapters_data_list:  # Expects list of dicts
        title = chapter_info.get("title", f"{Config.DEFAULT_CHAPTER_TITLE_PREFIX}{chapter_info.get('number', 'N/A')}")
        text = chapter_info.get("text", "")
        if add_titles_to_body:  # Use the passed boolean
            # Use CHAPTER_HEADER_FORMAT from Config for consistency
            FullStory += f"{Config.CHAPTER_HEADER_FORMAT.replace('{chapter_title}', title).replace('{chapter_num}', str(chapter_info.get('number', 'N/A')))}\n{text}\n\n"
        else:
            FullStory += f"{text}\n\n"  # Just text and newlines if not adding titles
    return FullStory.strip()


class StoryPipeline:
    def __init__(self, interface, sys_logger, config, active_prompts, is_fresh_run=True):
        self.Interface = interface
        self.SysLogger = sys_logger
        self.Config = config
        self.ActivePrompts = active_prompts
        self.is_fresh_run = is_fresh_run

        try:
            import Writer.OutlineGenerator
            import Writer.Chapter.ChapterDetector
            import Writer.Chapter.ChapterGenerator
            import Writer.NovelEditor
            import Writer.Scrubber
            import Writer.Translator
            import Writer.StoryInfo
            import Writer.Statistics
            import Writer.Chapter.ChapterGenSummaryCheck
            # ChapterTitleGenerator is used via _handle_chapter_title_generation_pipeline_version, not directly here.

            self.OutlineGenerator = Writer.OutlineGenerator
            self.ChapterDetector = Writer.Chapter.ChapterDetector
            self.ChapterGenerator = Writer.Chapter.ChapterGenerator
            self.NovelEditor = Writer.NovelEditor
            self.Scrubber = Writer.Scrubber
            self.Translator = Writer.Translator
            self.StoryInfo = Writer.StoryInfo
            self.Statistics = Writer.Statistics
            self.ChapterGenSummaryCheck = Writer.Chapter.ChapterGenSummaryCheck

            # Initialize Lorebook if enabled
            if self.Config.USE_LOREBOOK:
                try:
                    import Writer.Lorebook
                    self.lorebook = Writer.Lorebook.LorebookManager(
                        persist_dir=self.Config.LOREBOOK_PERSIST_DIR
                    )

                    # NEW: Handle lorebook state restoration for resume
                    if self.lorebook and not self.is_fresh_run:
                        # For resume, look for state file in current run logs
                        import glob
                        log_dirs = glob.glob("Logs/Generation_*/")
                        if log_dirs:
                            latest_dir = sorted(log_dirs)[-1]
                            state_file = os.path.join(latest_dir, "run.state.json")
                            if os.path.exists(state_file):
                                try:
                                    self.lorebook.load_entries_from_state(state_file)
                                    self.SysLogger.Log(f"Lorebook state restored from {state_file}", 5)
                                except Exception as e:
                                    self.SysLogger.Log(f"Failed to restore lorebook from {state_file}: {e}", 3)

                    # Auto-clear logic remains for fresh runs
                    if (self.lorebook and
                        self.is_fresh_run and
                            getattr(self.Config, 'LOREBOOK_AUTO_CLEAR', True)):
                        self.lorebook.clear()
                        self.SysLogger.Log("Lorebook auto-cleared for fresh run", 5)

                except ImportError as e:
                    self.SysLogger.Log(f"Failed to import Lorebook: {e}", 6)
                    self.lorebook = None
                except Exception as e:
                    self.SysLogger.Log(f"Failed to initialize Lorebook: {e}", 3)
                    self.lorebook = None
            else:
                self.lorebook = None

        except ImportError as e:
            self.SysLogger.Log(f"PIPELINE __INIT__ FATAL: Failed to import one or more core Writer modules: {e}", 7)
            raise

    def _save_state_wrapper(self, current_state, state_filepath):
        """Enhanced state save that includes lorebook entries"""
        try:
            # Add lorebook entries to state if lorebook is enabled and has entries
            if self.Config.USE_LOREBOOK and self.lorebook:
                try:
                    lorebook_entries = self.lorebook.get_all_entries()
                    if "other_data" not in current_state:
                        current_state["other_data"] = {}
                    current_state["other_data"]["lorebook_entries"] = lorebook_entries
                    self.SysLogger.Log(f"Added {len(lorebook_entries)} lorebook entries to state", 5)
                except Exception as e:
                    self.SysLogger.Log(f"Failed to get lorebook entries for state: {e}", 3)

            # Use existing save function
            save_state_pipeline(current_state, state_filepath, self.SysLogger)

        except Exception as e:
            self.SysLogger.Log(f"Failed to save state with lorebook entries: {e}", 3)
            # Fallback to original save without lorebook
            save_state_pipeline(current_state, state_filepath, self.SysLogger)

    def _generate_outline_stage(self, current_state, prompt_content, state_filepath):
        self.SysLogger.Log("Pipeline: Starting Outline Generation Stage...", 3)
        Outline, Elements, RoughChapterOutline, BaseContext = \
            self.OutlineGenerator.GenerateOutline(
                self.Interface, self.SysLogger, prompt_content, self.Config.OUTLINE_QUALITY
            )
        current_state["full_outline"] = Outline
        current_state["story_elements"] = Elements
        current_state["rough_chapter_outline"] = RoughChapterOutline
        current_state["base_context"] = BaseContext  # This is crucial for subsequent steps

        # Extract lore from outline if lorebook is enabled
        if self.lorebook:
            # NEW: Direct structured extraction (preferred method)
            self.lorebook.extract_from_structured_data(Elements, Outline)
            self.SysLogger.Log("Pipeline: Extracted lore from structured data", 5)

        current_state["last_completed_step"] = "outline"
        self._save_state_wrapper(current_state, state_filepath)
        self.SysLogger.Log("Pipeline: Outline Generation Stage Complete. State Saved.", 4)
        return Outline, Elements, RoughChapterOutline, BaseContext

    def _detect_chapters_stage(self, current_state, Outline, state_filepath):
        self.SysLogger.Log("Pipeline: Starting Chapter Detection Stage...", 5)
        if not Outline:
            self.SysLogger.Log("PIPELINE _detect_chapters_stage FATAL: Outline is missing.", 7)
            raise ValueError("Outline is missing, cannot detect chapters.")

        NumChapters = self.ChapterDetector.LLMCountChapters(
            self.Interface, self.SysLogger, Outline
        )
        current_state["total_chapters"] = NumChapters
        current_state["last_completed_step"] = "detect_chapters"
        self._save_state_wrapper(current_state, state_filepath)
        self.SysLogger.Log(f"Pipeline: Chapter Detection Found {NumChapters} Chapter(s). State Saved.", 5)
        return NumChapters

    def _expand_chapter_outlines_stage(self, current_state, base_outline_for_expansion, num_chapters, state_filepath):
        self.SysLogger.Log("Pipeline: Starting Per-Chapter Outline Expansion Stage...", 3)

        # Sub-step: High-Level Chapter Outline Refinement (Global Refinement)
        # This refined outline becomes the basis for per-chapter expansion if enabled.
        refined_global_outline = base_outline_for_expansion  # Start with the current best outline
        if self.Config.ENABLE_GLOBAL_OUTLINE_REFINEMENT:  # New config flag
            self.SysLogger.Log("Pipeline: Starting High-Level Global Outline Refinement sub-step...", 3)
            if not base_outline_for_expansion:
                self.SysLogger.Log("PIPELINE _expand_chapter_outlines_stage FATAL: Base outline for expansion is missing.", 7)
                raise ValueError("Base outline missing for global refinement.")

            # Assuming RefineOutline is a function in OutlineGenerator now
            refined_global_outline, _ = self.OutlineGenerator.ReviseOutline(
                self.Interface, self.SysLogger, base_outline_for_expansion,
                "Perluas setiap outline bab dengan detail plot, karakter, dan konflik. "
                "Setiap bab harus minimal 200 kata dengan menyebutkan nama-nama karakter. "
                "PENTING: Jaga SEMUA nama karakter yang sudah ada dari outline asli!"
            )
            current_state["refined_global_outline"] = refined_global_outline
            current_state["last_completed_step"] = "refine_global_outline"  # Intermediate step
            self._save_state_wrapper(current_state, state_filepath)
            self.SysLogger.Log("Pipeline: High-Level Global Outline Refinement sub-step Complete. State Saved.", 4)
        else:
            self.SysLogger.Log("Pipeline: Skipping High-Level Global Outline Refinement (disabled by Config.ENABLE_GLOBAL_OUTLINE_REFINEMENT).", 4)
            current_state["refined_global_outline"] = base_outline_for_expansion  # Store original as "refined" to simplify downstream logic

        # Per-Chapter Expansion using the (potentially) refined global outline
        GeneratedChapterOutlines = []
        if num_chapters > 0:  # Only proceed if there are chapters to outline
            for ChapterIdx in range(1, num_chapters + 1):
                self.SysLogger.Log(f"Pipeline: Generating outline for chapter {ChapterIdx}/{num_chapters}...", 6)
                ChapterOutlineText, ChapterTitle = self.OutlineGenerator.GeneratePerChapterOutline(
                    self.Interface, self.SysLogger, ChapterIdx, num_chapters, refined_global_outline
                )
                GeneratedChapterOutlines.append({"text": ChapterOutlineText, "title": ChapterTitle})
            self.SysLogger.Log(f"Pipeline: Generated {len(GeneratedChapterOutlines)} per-chapter outlines.", 4)
        else:
            self.SysLogger.Log(f"Pipeline: Skipping per-chapter outline generation as num_chapters is {num_chapters}.", 4)

        current_state["expanded_chapter_outlines"] = GeneratedChapterOutlines
        current_state["last_completed_step"] = "expand_chapters"  # Main step completion
        self._save_state_wrapper(current_state, state_filepath)
        self.SysLogger.Log("Pipeline: Per-Chapter Outline Expansion Stage Complete (or skipped). State Saved.", 4)
        return GeneratedChapterOutlines  # Return only the list of chapter outlines

    def _write_chapters_stage(self, current_state, state_filepath, total_num_chapters_overall, base_context_text):
        self.SysLogger.Log("Pipeline: Starting Chapter Writing Stage...", 3)

        # completed_chapters_data stores: [{"number": 1, "title": "T", "text": "C1"}, {"number": 2, ...}]
        completed_chapters_data = current_state.get("completed_chapters_data", [])
        next_chapter_to_generate_num = current_state.get("next_chapter_index", 1)  # 1-based index

        self.SysLogger.Log(f"Pipeline: Chapter writing from number {next_chapter_to_generate_num} up to {total_num_chapters_overall}.", 4)

        if total_num_chapters_overall is None or total_num_chapters_overall < next_chapter_to_generate_num:
            self.SysLogger.Log(f"Pipeline: No chapters to generate (total_num_chapters_overall: {total_num_chapters_overall}, next_chapter_to_generate_num: {next_chapter_to_generate_num}). Skipping chapter writing.", 4)
            current_state["last_completed_step"] = "chapter_generation_complete"
            self._save_state_wrapper(current_state, state_filepath)
            return completed_chapters_data  # Return existing data

        for current_chap_num in range(next_chapter_to_generate_num, total_num_chapters_overall + 1):
            self.SysLogger.Log(f"--- Pipeline: Generating Chapter {current_chap_num}/{total_num_chapters_overall} ---", 3)

            # Get combined context (base, previous chapters, current chapter outline) for generation
            # This uses _get_current_context_for_chapter_gen_pipeline_version
            current_gen_context = _get_current_context_for_chapter_gen_pipeline_version(
                self.SysLogger, self.Config, self.Statistics, self.ActivePrompts, current_state, current_chap_num, base_context_text, lorebook=self.lorebook
            )
            if not current_gen_context:
                self.SysLogger.Log(f"PIPELINE _write_chapters_stage FATAL: Generation context for Chapter {current_chap_num} is empty.", 7)
                raise ValueError(f"Empty generation context for Chapter {current_chap_num}.")

            # Get expanded chapter outline for scene pipeline (if available)
            expanded_chapter_outline_dict = None
            expanded_chapter_outlines = current_state.get("expanded_chapter_outlines", [])
            if self.Config.EXPAND_OUTLINE and self.Config.SCENE_GENERATION_PIPELINE and expanded_chapter_outlines:
                if current_chap_num > 0 and len(expanded_chapter_outlines) >= current_chap_num:
                    potential_expanded = expanded_chapter_outlines[current_chap_num - 1]
                    if isinstance(potential_expanded, dict):
                        expanded_chapter_outline_dict = potential_expanded
                        self.SysLogger.Log(f"Passing expanded outline dict for Chapter {current_chap_num} to scene pipeline", 5)

            # Generate chapter content using ChapterGenerator.GenerateChapter
            raw_chapter_content = self.ChapterGenerator.GenerateChapter(
                self.Interface,              # Interface
                self.SysLogger,             # _Logger
                current_chap_num,           # _ChapterNum
                total_num_chapters_overall,  # _TotalChapters
                current_gen_context,        # _Outline (full context string)
                completed_chapters_data,    # _Chapters (list of prior chapters)
                "",                         # _BaseContext (empty for now)
                current_gen_context,        # _FullOutlineForSceneGen (same as outline)
                expanded_chapter_outline_dict  # type: ignore # _ExpandedChapterOutline (dict with scenes)
            )

            # Get specific outline for title generation (can be different from full gen context)
            current_chapter_specific_outline_for_title = _get_outline_for_chapter_pipeline_version(
                self.SysLogger, self.Config, self.Statistics, self.ActivePrompts, current_state, current_chap_num
            )

            # Generate chapter title using helper
            chapter_title = _handle_chapter_title_generation_pipeline_version(
                self.SysLogger, self.Interface, self.Config, self.ActivePrompts,
                raw_chapter_content, current_chap_num,
                base_context_text,  # Base outline/elements for broader context
                current_chapter_specific_outline_for_title,  # Specific outline for this chapter
                self.Statistics
            )

            chapter_data_entry = {
                "number": current_chap_num,
                "title": chapter_title,
                "text": raw_chapter_content,  # Store raw text, formatting applied at higher levels if needed
                "word_count": self.Statistics.GetWordCount(raw_chapter_content)
            }

            # Add or update chapter in list
            # Ensure list is long enough if overwriting (shouldn't happen with next_chapter_index logic)
            if len(completed_chapters_data) >= current_chap_num:
                completed_chapters_data[current_chap_num - 1] = chapter_data_entry
                self.SysLogger.Log(f"Pipeline: Overwriting existing Chapter {current_chap_num} data.", 6)
            else:
                completed_chapters_data.append(chapter_data_entry)

            current_state["completed_chapters_data"] = completed_chapters_data
            current_state["next_chapter_index"] = current_chap_num + 1
            current_state["last_completed_step"] = "chapter_generation"  # Mark as in-progress
            self._save_state_wrapper(current_state, state_filepath)
            self.SysLogger.Log(f"--- Pipeline: Chapter {current_chap_num} (Title: '{chapter_title}') Generation Complete. Word Count: {chapter_data_entry['word_count']}. State Saved. ---", 4)

        current_state["last_completed_step"] = "chapter_generation_complete"  # All chapters for this run done
        self._save_state_wrapper(current_state, state_filepath)
        self.SysLogger.Log("Pipeline: All Chapters Generated for this run. State Saved.", 5)
        return completed_chapters_data

    def _perform_post_processing_stage(self, current_state, state_filepath, Args, StartTime):
        self.SysLogger.Log("Pipeline: Starting Post-Processing Stage...", 3)

        # Retrieve necessary data from current_state
        FinalChaptersData = current_state.get("completed_chapters_data", [])  # This is list of dicts
        FullOutlineForInfo = current_state.get("full_outline", "")
        StoryElementsForInfo = current_state.get("story_elements", "")
        RoughChapterOutlineForInfo = current_state.get("rough_chapter_outline", "")  # Potentially less used if full_outline is primary
        BaseContextForInfo = current_state.get("base_context", "")
        NumChaptersActual = len(FinalChaptersData)  # Actual number of chapters generated

        StoryInfoJSON = current_state.get("StoryInfoJSON", {})  # Load existing or init
        StoryInfoJSON.update({  # Update with latest structural info if not already there
            "Outline": FullOutlineForInfo, "StoryElements": StoryElementsForInfo,
            "RoughChapterOutline": RoughChapterOutlineForInfo, "BaseContext": BaseContextForInfo,
            "TotalChaptersDetected": current_state.get("total_chapters"),  # From detection phase
            "TotalChaptersGenerated": NumChaptersActual,
            "UnprocessedChaptersData": [ch.copy() for ch in FinalChaptersData]  # Save a copy before processing
        })

        current_working_chapters_data = [ch.copy() for ch in FinalChaptersData]  # Work on a copy

        # --- Sub-step: Mark start of post-processing ---
        if current_state.get("last_completed_step") == "chapter_generation_complete":
            current_state["last_completed_step"] = "post_processing_started"
            self._save_state_wrapper(current_state, state_filepath)
            self.SysLogger.Log("Pipeline: Post-Processing Started. State Saved.", 4)

        # 1. Edit Novel (if enabled)
        if self.Config.ENABLE_FINAL_EDIT_PASS and current_state.get("last_completed_step") not in ["post_processing_edit_complete", "post_processing_scrub_complete", "post_processing_final_translate_complete", "complete"]:
            self.SysLogger.Log("Pipeline: Starting Final Edit Pass...", 3)
            if not current_working_chapters_data:
                self.SysLogger.Log("Pipeline: Warning: No chapters data available for final edit pass.", 6)
            else:
                try:
                    # NovelEditor.EditNovel now expects list of chapter data dicts
                    # Extract text content from chapter data dicts
                    chapter_texts = [ch.get("text", "") for ch in current_working_chapters_data]
                    edited_chapter_texts = self.NovelEditor.EditNovel(
                        self.Interface, self.SysLogger,
                        chapter_texts,
                        FullOutlineForInfo,
                        NumChaptersActual
                    )
                    # Convert back to chapter data format
                    edited_chapters_data = []
                    for i, text in enumerate(edited_chapter_texts):
                        chapter_data = current_working_chapters_data[i].copy()
                        chapter_data["text"] = text
                        edited_chapters_data.append(chapter_data)
                    current_working_chapters_data = edited_chapters_data
                    StoryInfoJSON["EditedChaptersData"] = [ch.copy() for ch in edited_chapters_data]
                    self.SysLogger.Log("Pipeline: Final Edit Pass Complete.", 4)
                except Exception as e:
                    self.SysLogger.Log(f"Pipeline: ERROR during Final Edit Pass: {e}. Continuing with unedited text for subsequent steps.", 7)
                    # No critical failure, just skip this step's result
            current_state["last_completed_step"] = "post_processing_edit_complete"
            self._save_state_wrapper(current_state, state_filepath)

        # 2. Scrub Novel (if enabled)
        if not self.Config.SCRUB_NO_SCRUB and current_state.get("last_completed_step") not in ["post_processing_scrub_complete", "post_processing_final_translate_complete", "complete"]:
            self.SysLogger.Log("Pipeline: Starting Scrubbing Pass...", 3)
            if not current_working_chapters_data:
                self.SysLogger.Log("Pipeline: Warning: No chapters data available for scrubbing pass.", 6)
            else:
                try:
                    # Scrubber.ScrubNovel now expects list of chapter data dicts
                    # Extract text content from chapter data dicts
                    chapter_texts = [ch.get("text", "") for ch in current_working_chapters_data]
                    scrubbed_chapter_texts = self.Scrubber.ScrubNovel(
                        self.Interface, self.SysLogger,
                        chapter_texts,
                        NumChaptersActual
                    )
                    # Convert back to chapter data format
                    scrubbed_chapters_data = []
                    for i, text in enumerate(scrubbed_chapter_texts):
                        chapter_data = current_working_chapters_data[i].copy()
                        chapter_data["text"] = text
                        scrubbed_chapters_data.append(chapter_data)
                    current_working_chapters_data = scrubbed_chapters_data
                    StoryInfoJSON["ScrubbedChaptersData"] = [ch.copy() for ch in scrubbed_chapters_data]
                    self.SysLogger.Log("Pipeline: Scrubbing Pass Complete.", 4)
                except Exception as e:
                    self.SysLogger.Log(f"Pipeline: ERROR during Scrubbing Pass: {e}. Continuing with unscrubbed text for subsequent steps.", 7)
            current_state["last_completed_step"] = "post_processing_scrub_complete"
            self._save_state_wrapper(current_state, state_filepath)

        # 3. Translate Novel (if enabled)
        target_translation_lang = self.Config.TRANSLATE_LANGUAGE
        native_lang = self.Config.NATIVE_LANGUAGE  # Assuming this is the current language of chapters
        if target_translation_lang and target_translation_lang.lower() != native_lang.lower() and \
           current_state.get("last_completed_step") not in ["post_processing_final_translate_complete", "complete"]:
            self.SysLogger.Log(f"Pipeline: Starting Final Translation from '{native_lang}' to '{target_translation_lang}'...", 3)
            if not current_working_chapters_data:
                self.SysLogger.Log("Pipeline: Warning: No chapters data available for final translation.", 6)
            else:
                try:
                    # Translator.TranslateNovel now expects list of chapter data dicts
                    # Extract text content from chapter data dicts
                    chapter_texts = [ch.get("text", "") for ch in current_working_chapters_data]
                    translated_chapter_texts = self.Translator.TranslateNovel(
                        self.Interface, self.SysLogger,
                        chapter_texts,
                        NumChaptersActual,
                        target_translation_lang, native_lang
                    )
                    # Convert back to chapter data format
                    translated_chapters_data = []
                    for i, text in enumerate(translated_chapter_texts):
                        chapter_data = current_working_chapters_data[i].copy()
                        chapter_data["text"] = text
                        translated_chapters_data.append(chapter_data)
                    current_working_chapters_data = translated_chapters_data
                    StoryInfoJSON["TranslatedFinalChaptersData"] = [ch.copy() for ch in translated_chapters_data]
                    StoryInfoJSON["FinalOutputLanguage"] = target_translation_lang
                    self.SysLogger.Log(f"Pipeline: Final story translation to '{target_translation_lang}' complete.", 4)
                except Exception as e:
                    self.SysLogger.Log(f"Pipeline: ERROR during final story translation: {e}. Outputting in native language '{native_lang}'.", 7)
                    StoryInfoJSON["FinalOutputLanguage"] = native_lang  # Record that translation failed
            current_state["last_completed_step"] = "post_processing_final_translate_complete"
            self._save_state_wrapper(current_state, state_filepath)
        else:
            StoryInfoJSON["FinalOutputLanguage"] = native_lang  # If not translated

        current_state["FinalProcessedChaptersData"] = current_working_chapters_data  # list of dicts

        # Generate Story Info (Title, Summary, Tags) using StoryInfo module
        self.SysLogger.Log("Pipeline: Generating Story Info (Title, Summary, Tags)...", 5)
        # Use the final processed chapter data to build a body of text for summary, if appropriate, or use outline
        # For now, using outline as per original logic
        info_query_text = FullOutlineForInfo if FullOutlineForInfo else StoryElementsForInfo
        if not info_query_text and current_working_chapters_data:  # Fallback to using first chapter text
            info_query_text = current_working_chapters_data[0].get("text", "No content available for story info generation.")

        GeneratedInfo = {}
        try:
            # Convert info_query_text to proper message format
            info_messages = [{"role": "user", "content": info_query_text}]
            GeneratedInfo, _ = self.StoryInfo.GetStoryInfo(
                self.Interface, self.SysLogger, info_messages
            )
            StoryInfoJSON.update(GeneratedInfo)  # Add Title, Summary, Tags
            self.SysLogger.Log("Pipeline: Story Info Generation Complete.", 5)
        except Exception as e:
            self.SysLogger.Log(f"Pipeline: Error generating story info: {e}. Using defaults.", 7)
            GeneratedInfo = {"Title": "Untitled Story", "Summary": "Error generating summary.", "Tags": ""}  # Ensure keys exist
            StoryInfoJSON.update(GeneratedInfo)

        Title = StoryInfoJSON.get("Title", "Untitled Story")  # Get from StoryInfoJSON now

        # Compile final story body text using the final processed chapters
        # Use _get_full_story_text_pipeline_version with final data
        FinalStoryBodyText = _get_full_story_text_pipeline_version(current_working_chapters_data, self.Config, self.Config.ADD_CHAPTER_TITLES_TO_NOVEL_BODY_TEXT)

        # Calculate Elapsed Time & Stats
        ElapsedTime = time.time() - StartTime  # StartTime passed from Write.py
        TotalWords = self.Statistics.GetWordCount(FinalStoryBodyText)
        self.SysLogger.Log(f"Pipeline: Story Total Word Count: {TotalWords}, Elapsed Time: {ElapsedTime:.2f}s", 4)

        # Create StatsString (moved from Write.py)
        gen_start_time_str = datetime.datetime.fromtimestamp(StartTime).strftime("%Y/%m/%d %H:%M:%S")
        StatsString = f"Work Statistics:\n"
        StatsString += f" - Title: {Title}\n"
        StatsString += f" - Summary: {StoryInfoJSON.get('Summary', 'N/A')}\n"
        StatsString += f" - Tags: {StoryInfoJSON.get('Tags', 'N/A')}\n"
        StatsString += f" - Total Chapters: {NumChaptersActual}\n"
        StatsString += f" - Total Words: {TotalWords}\n"
        StatsString += f" - Generation Start Date: {gen_start_time_str}\n"
        StatsString += f" - Generation Total Time: {ElapsedTime:.2f}s\n"
        StatsString += f" - Generation Average WPM: {(60 * (TotalWords/ElapsedTime)):.2f}\n" if ElapsedTime > 0 else "N/A\n"
        StatsString += f" - Output Language: {StoryInfoJSON.get('FinalOutputLanguage', native_lang)}\n"
        StatsString += f"\nUser Settings:\n"
        StatsString += f" - Base Prompt File: {current_state.get('input_prompt_file', 'N/A')}\n"
        if current_state.get("translated_to_native_prompt_content"):
            StatsString += f" - Original Prompt Language: {self.Config.TRANSLATE_PROMPT_LANGUAGE}\n"
            StatsString += f" - Generation Prompt Language: {self.Config.NATIVE_LANGUAGE}\n"
        StatsString += f"\nGeneration Configuration:\n"
        for key in dir(self.Config):
            if not key.startswith("_") and key.isupper():  # Only public config variables
                StatsString += f" - {key}: {getattr(self.Config, key)}\n"
        StoryInfoJSON["StatsString"] = StatsString  # Save comprehensive stats string

        # Save The Story To Disk
        self.SysLogger.Log("Pipeline: Saving Final Story To Disk", 3)
        os.makedirs(self.Config.STORIES_DIR, exist_ok=True)  # Use config for stories directory
        safe_title = "".join(c for c in Title if c.isalnum() or c in (" ", "_")).rstrip().replace(" ", "_")
        run_timestamp_str = datetime.datetime.fromtimestamp(StartTime).strftime("%Y%m%d%H%M%S")

        FNameBase = os.path.join(self.Config.STORIES_DIR, f"Story_{safe_title if safe_title else 'Untitled'}_{run_timestamp_str}")
        if Args and Args.Output:  # Use command-line arg for output name if provided
            base_output_path = Args.Output
            # Ensure directory exists for custom output path
            output_dir = os.path.dirname(base_output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            FNameBase = base_output_path  # No extension, will be added

        FinalMDPath = f"{FNameBase}.md"
        FinalJSONPath = f"{FNameBase}_info.json"  # Changed suffix for clarity

        try:
            with open(FinalMDPath, "w", encoding="utf-8") as F:
                # Create valid YAML front matter for pandoc compatibility
                OutMD = "---\n"
                # Escape quotes for YAML
                escaped_title = Title.replace('"', '\\"')
                OutMD += f"title: \"{escaped_title}\"\n"
                if self.Config.INCLUDE_SUMMARY_IN_MD:
                    escaped_summary = StoryInfoJSON.get('Summary', 'N/A').replace('"', '\\"').replace('\n', ' ')
                    OutMD += f"summary: \"{escaped_summary}\"\n"
                if self.Config.INCLUDE_TAGS_IN_MD:
                    escaped_tags = StoryInfoJSON.get('Tags', 'N/A').replace('"', '\\"')
                    OutMD += f"tags: \"{escaped_tags}\"\n"
                OutMD += "---\n\n"
                OutMD += f"# {Title}\n\n"
                if self.Config.INCLUDE_SUMMARY_IN_MD:
                    OutMD += f"## Summary\n{StoryInfoJSON.get('Summary', 'N/A')}\n\n"
                if self.Config.INCLUDE_TAGS_IN_MD:
                    OutMD += f"**Tags:** {StoryInfoJSON.get('Tags', 'N/A')}\n\n"
                OutMD += "---\n\n"
                OutMD += FinalStoryBodyText  # Already has chapter titles if configured
                if self.Config.INCLUDE_OUTLINE_IN_MD:
                    OutMD += f"\n\n---\n# Story Outline\n```text\n{FullOutlineForInfo if FullOutlineForInfo else 'No outline generated.'}\n```\n"
                if self.Config.INCLUDE_STATS_IN_MD:
                    OutMD += f"\n\n---\n# Generation Statistics\n```text\n{StatsString}\n```\n"
                F.write(OutMD)
            self.SysLogger.Log(f"Pipeline: Final story saved to {FinalMDPath}", 5)
        except Exception as e:
            self.SysLogger.Log(f"PIPELINE _perform_post_processing_stage FATAL: Error writing final story file {FinalMDPath}: {e}", 7)

        StoryInfoJSON["OutputFiles"] = {
            "Markdown": FinalMDPath, "JSONInfo": FinalJSONPath,
            "StateFile": state_filepath, "LogDirectory": self.Config.LOG_DIRECTORY,
        }
        current_state["StoryInfoJSON"] = StoryInfoJSON  # Save updated StoryInfoJSON to state
        try:
            with open(FinalJSONPath, "w", encoding="utf-8") as F:
                # Serialize Pydantic objects to JSON-compatible dicts before dumping
                serializable_story_info = serialize_for_json(StoryInfoJSON)
                json.dump(serializable_story_info, F, indent=4, ensure_ascii=False)
            self.SysLogger.Log(f"Pipeline: Story info JSON saved to {FinalJSONPath}", 5)
        except Exception as e:
            self.SysLogger.Log(f"PIPELINE _perform_post_processing_stage FATAL: Error writing story info JSON file {FinalJSONPath}: {e}", 7)

        # PDF Generation (if enabled)
        # Early exit check - avoid heavy imports if PDF generation is disabled in args
        if (self.Config.ENABLE_PDF_GENERATION or
                (Args and getattr(Args, 'GeneratePDF', False))):
            try:
                self.SysLogger.Log("Pipeline: Starting PDF generation...", 5)
                pdf_path = f"{FNameBase}.pdf"

                from Writer import PDFGenerator
                success, message = PDFGenerator.GeneratePDF(
                    self.Interface, self.SysLogger, OutMD, pdf_path, Title
                )

                if success:
                    StoryInfoJSON["OutputFiles"]["PDF"] = pdf_path
                    self.SysLogger.Log(f"Pipeline: PDF generated successfully at {pdf_path}", 5)
                else:
                    self.SysLogger.Log(f"Pipeline: PDF generation failed: {message}", 6)
            except Exception as e:
                self.SysLogger.Log(f"Pipeline: PDF generation error: {e}", 6)

        current_state["status"] = "completed"
        current_state["final_story_path"] = FinalMDPath
        current_state["final_json_path"] = FinalJSONPath
        current_state["last_completed_step"] = "complete"  # Final step
        self._save_state_wrapper(current_state, state_filepath)
        self.SysLogger.Log("Pipeline: Post-Processing Stage Finished. Final State Saved. Run COMPLETED.", 5)
        return current_state

    def run_pipeline(self, current_state, state_filepath, initial_prompt_for_outline, Args, StartTime):  # Added Args, StartTime
        self.SysLogger.Log("Pipeline: Starting run_pipeline method.", 3)
        last_completed_step = current_state.get("last_completed_step", "init")

        Outline = current_state.get("full_outline")
        BaseContext = current_state.get("base_context")  # Elements, Rough Outline, etc.
        NumChapters = current_state.get("total_chapters")

        try:  # Wrap entire pipeline in try-except for robust error logging of unexpected issues
            # --- Outline Generation ---
            if last_completed_step == "init":
                self.SysLogger.Log("Pipeline: 'init' step. Executing Outline Generation.", 4)
                Outline, _, _, BaseContext = \
                    self._generate_outline_stage(current_state, initial_prompt_for_outline, state_filepath)
                last_completed_step = current_state.get("last_completed_step")

            if Outline is None and last_completed_step not in ["init"]:  # Outline must exist beyond init
                self.SysLogger.Log("PIPELINE run_pipeline FATAL: Outline data is missing after 'init' stage.", 7)
                raise Exception("Pipeline Error: Outline missing in state where it's expected.")

            # --- Chapter Detection ---
            if last_completed_step == "outline":
                self.SysLogger.Log("Pipeline: 'outline' step complete. Executing Chapter Detection.", 4)
                NumChapters = self._detect_chapters_stage(current_state, Outline, state_filepath)
                last_completed_step = current_state.get("last_completed_step")

            if NumChapters is None and last_completed_step not in ["init", "outline"]:
                self.SysLogger.Log("PIPELINE run_pipeline FATAL: NumChapters data is missing after 'outline' stage.", 7)
                raise Exception("Pipeline Error: NumChapters missing in state where it's expected.")

            # --- Chapter Outline Expansion (includes optional global refinement) ---
            if last_completed_step == "detect_chapters" or last_completed_step == "refine_global_outline":  # Allow resume from internal step
                if self.Config.EXPAND_OUTLINE:
                    self.SysLogger.Log(f"Pipeline: '{last_completed_step}' step complete. Executing Chapter Outline Expansion.", 4)
                    # Use current_state["full_outline"] which might have been refined if refine_global_outline was run
                    outline_for_expansion = current_state.get("refined_global_outline") or current_state.get("full_outline")
                    if not outline_for_expansion:
                        self.SysLogger.Log("PIPELINE run_pipeline FATAL: Outline for expansion is missing.", 7)
                        raise ValueError("Full outline for expansion stage is missing.")
                    self._expand_chapter_outlines_stage(current_state, outline_for_expansion, NumChapters, state_filepath)
                else:  # EXPAND_OUTLINE is false
                    self.SysLogger.Log("Pipeline: Skipping Per-Chapter Outline Expansion (Config.EXPAND_OUTLINE=False).", 4)
                    current_state["expanded_chapter_outlines"] = []  # Ensure it's an empty list
                    current_state["last_completed_step"] = "expand_chapters"  # Mark as logically complete
                    self._save_state_wrapper(current_state, state_filepath)
                last_completed_step = current_state.get("last_completed_step")

            # --- Chapter Writing ---
            # Can start if expand_chapters is done, or if resuming chapter_generation
            if last_completed_step == "expand_chapters" or last_completed_step == "chapter_generation":
                if NumChapters is None:
                    self.SysLogger.Log("PIPELINE run_pipeline FATAL: Total number of chapters (NumChapters) is None before chapter writing stage.", 7)
                    raise ValueError("NumChapters is None before chapter writing.")
                if BaseContext is None:  # BaseContext comes from _generate_outline_stage, should be in state
                    self.SysLogger.Log("PIPELINE run_pipeline FATAL: BaseContext is None before chapter writing stage. State may be corrupted.", 7)
                    raise ValueError("BaseContext is None before chapter writing. Check if base_context exists in state file.")
                self.SysLogger.Log(f"Pipeline: '{last_completed_step}' step complete. Executing Chapter Writing.", 4)
                self._write_chapters_stage(current_state, state_filepath, NumChapters, BaseContext)
                last_completed_step = current_state.get("last_completed_step")

            # --- Post-Processing ---
            # Can start if chapter_generation_complete, or if resuming any post_processing_ sub-step
            if last_completed_step == "chapter_generation_complete" or \
                    (last_completed_step.startswith("post_processing_") and last_completed_step != "complete"):
                self.SysLogger.Log(f"Pipeline: '{last_completed_step}' step complete. Executing Post-Processing.", 4)
                current_state = self._perform_post_processing_stage(current_state, state_filepath, Args, StartTime)
                last_completed_step = current_state.get("last_completed_step")

            if last_completed_step == "complete":
                self.SysLogger.Log("Pipeline execution finished successfully. Final reported step: 'complete'.", 5)
            else:
                self.SysLogger.Log(f"Pipeline execution ended. Final reported step by pipeline: '{last_completed_step}'. This may be normal if resuming or an error occurred.", 6)

        except Exception as e:
            self.SysLogger.Log(f"PIPELINE run_pipeline CRITICAL ERROR: An unhandled exception occurred: {e}", 7)
            import traceback
            self.SysLogger.Log(f"Traceback:\n{traceback.format_exc()}", 1)  # Log stack trace at debug
            current_state["error"] = str(e)
            current_state["error_traceback"] = traceback.format_exc()
            current_state["last_known_step_before_error"] = last_completed_step
            # Attempt to save the error state
            try:
                self._save_state_wrapper(current_state, state_filepath)
                self.SysLogger.Log("Pipeline: Saved state with error information.", 6)
            except Exception as save_err:
                self.SysLogger.Log(f"PIPELINE run_pipeline FATAL: Could not even save error state: {save_err}", 7)
            # Depending on policy, might re-raise or sys.exit. For now, return state.
            # Re-raising allows Write.py to catch and handle it.
            raise

        return current_state
