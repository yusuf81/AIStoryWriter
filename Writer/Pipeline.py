import os
import json
import sys
import shutil
import time
import datetime

# Helper function for saving state (can be moved to a common utils if not already there)
def save_state_pipeline(state_data, filepath, logger):
    # (Implementation of save_state, perhaps calling a shared utility)
    # For now, can copy from Write.py and adapt if needed
    temp_filepath = filepath + ".tmp"
    try:
        with open(temp_filepath, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=4)
        shutil.move(temp_filepath, filepath)
    except Exception as e:
        if logger:
            logger.Log(f"FATAL: Failed to save state to {filepath} from pipeline: {e}", 7)
        else:
            print(f"FATAL: Failed to save state to {filepath} from pipeline: {e}")
        # Consider re-raising or specific error handling

class StoryPipeline:
    def __init__(self, interface, sys_logger, config, active_prompts):
        self.Interface = interface
        self.SysLogger = sys_logger
        self.Config = config # This should be the Writer.Config module/object
        self.ActivePrompts = active_prompts # The dynamically loaded prompt module

        # Import necessary generator modules here or pass them if preferred
        # Assuming these modules exist in the Writer package
        try:
            import Writer.OutlineGenerator
            import Writer.Chapter.ChapterDetector
            import Writer.Chapter.ChapterGenerator
            import Writer.NovelEditor
            import Writer.Scrubber
            import Writer.Translator
            import Writer.StoryInfo
            import Writer.Statistics

            self.OutlineGenerator = Writer.OutlineGenerator
            self.ChapterDetector = Writer.Chapter.ChapterDetector
            self.ChapterGenerator = Writer.Chapter.ChapterGenerator
            self.NovelEditor = Writer.NovelEditor
            self.Scrubber = Writer.Scrubber
            self.Translator = Writer.Translator
            self.StoryInfo = Writer.StoryInfo
            self.Statistics = Writer.Statistics
        except ImportError as e:
            self.SysLogger.Log(f"Pipeline FATAL: Failed to import core modules: {e}", 7)
            raise  # Re-raise the import error to halt execution if core components are missing

        # Helper for getting outline for chapter (copied from Write.py initially)
        # This might need access to self.Config, self.SysLogger, etc.
        # Or be passed current_state directly
        self._get_outline_for_chapter = _get_outline_for_chapter_pipeline_version


    def _save_state_wrapper(self, current_state, state_filepath):
        # Wrapper to use the logger from self.SysLogger
        save_state_pipeline(current_state, state_filepath, self.SysLogger)

    def _generate_outline_stage(self, current_state, prompt_content, state_filepath):
        self.SysLogger.Log("Pipeline: Starting Outline Generation Stage...", 3)
        Outline, Elements, RoughChapterOutline, BaseContext = \
            self.OutlineGenerator.GenerateOutline(
                self.Interface,
                self.SysLogger,
                prompt_content,
                self.Config.OUTLINE_QUALITY,
            )
        current_state["full_outline"] = Outline
        current_state["story_elements"] = Elements
        current_state["rough_chapter_outline"] = RoughChapterOutline
        current_state["base_context"] = BaseContext
        current_state["last_completed_step"] = "outline"
        self._save_state_wrapper(current_state, state_filepath)
        self.SysLogger.Log("Pipeline: Outline Generation Stage Complete. State Saved.", 4)
        return Outline, Elements, RoughChapterOutline, BaseContext

    def _detect_chapters_stage(self, current_state, Outline, state_filepath):
        self.SysLogger.Log("Pipeline: Starting Chapter Detection Stage...", 5)
        if not Outline:
            self.SysLogger.Log("FATAL: Cannot detect chapters, Outline is missing in pipeline for _detect_chapters_stage.", 7)
            # Consider how to handle fatal errors - maybe raise an exception
            # For now, returning None, and run_pipeline should check for this.
            raise ValueError("Outline is missing, cannot detect chapters.")
        Messages = [self.Interface.BuildUserQuery(Outline)]
        NumChapters = self.ChapterDetector.LLMCountChapters(
            self.Interface, self.SysLogger, self.Interface.GetLastMessageText(Messages)
        )
        current_state["total_chapters"] = NumChapters
        current_state["last_completed_step"] = "detect_chapters"
        self._save_state_wrapper(current_state, state_filepath)
        self.SysLogger.Log(f"Pipeline: Chapter Detection Found {NumChapters} Chapter(s). State Saved.", 5)
        return NumChapters

    def _expand_chapter_outlines_stage(self, current_state, Outline_param, NumChapters, state_filepath):
        self.SysLogger.Log("Pipeline: Starting Per-Chapter Outline Expansion Stage...", 3)

        # It's important that Outline_param is the most up-to-date version.
        # If it was refined in a previous step and saved to current_state["full_outline"],
        # that's the one that should be passed here.
        current_full_outline = Outline_param

        # --- High-Level Chapter Outline Refinement sub-step ---
        self.SysLogger.Log("Pipeline: Starting High-Level Chapter Outline Refinement sub-step...", 3)
        if not current_full_outline:
            self.SysLogger.Log("FATAL: Cannot refine chapters for expansion, Outline is missing.", 7)
            raise ValueError("Outline is missing for chapter outline refinement.")

        if not hasattr(self.ActivePrompts, 'EXPAND_OUTLINE_CHAPTER_BY_CHAPTER'):
            self.SysLogger.Log("FATAL: ActivePrompts module does not have 'EXPAND_OUTLINE_CHAPTER_BY_CHAPTER'. Prompts not loaded correctly for pipeline.", 7)
            raise AttributeError("EXPAND_OUTLINE_CHAPTER_BY_CHAPTER missing from ActivePrompts.")

        RefinementMessages = [
            self.Interface.BuildUserQuery(
                self.ActivePrompts.EXPAND_OUTLINE_CHAPTER_BY_CHAPTER.format(
                    _Outline=current_full_outline
                )
            )
        ]
        RefinementMessages, _ = self.Interface.SafeGenerateText(
            _Logger=self.SysLogger,
            _Messages=RefinementMessages,
            _Model=self.Config.INITIAL_OUTLINE_WRITER_MODEL,
            _MinWordCount=self.Config.MIN_WORDS_INITIAL_OUTLINE,
        )
        RefinedOutline = self.Interface.GetLastMessageText(RefinementMessages)

        current_state["refined_global_outline"] = RefinedOutline
        current_full_outline = RefinedOutline # Update the working outline with the refined version
        current_state["full_outline"] = current_full_outline # Save refined outline back to state's main key

        # Save state after this sub-step, changing last_completed_step to "refine_chapters"
        current_state["last_completed_step"] = "refine_chapters"
        self._save_state_wrapper(current_state, state_filepath)
        self.SysLogger.Log("Pipeline: High-Level Chapter Outline Refinement sub-step Complete. State Saved.", 4)
        # --- End of High-Level Chapter Outline Refinement ---

        GeneratedChapterOutlines = []
        for ChapterIdx in range(1, NumChapters + 1):
            self.SysLogger.Log(f"Pipeline: Generating outline for chapter {ChapterIdx}/{NumChapters}...", 6)
            ChapterOutlineText = self.OutlineGenerator.GeneratePerChapterOutline(
                self.Interface,
                self.SysLogger,
                ChapterIdx,
                NumChapters,
                current_full_outline, # Use the refined outline
            )
            GeneratedChapterOutlines.append(ChapterOutlineText)

        current_state["expanded_chapter_outlines"] = GeneratedChapterOutlines
        current_state["last_completed_step"] = "expand_chapters"
        self._save_state_wrapper(current_state, state_filepath)
        self.SysLogger.Log("Pipeline: Per-Chapter Outline Expansion Stage Complete. State Saved.", 4)
        return GeneratedChapterOutlines, current_full_outline # Return the generated outlines and the refined main outline

    def _write_chapters_stage(self, current_state, state_filepath, NumChaptersToGenerate, BaseContextText):
        self.SysLogger.Log("Pipeline: Starting Chapter Writing Stage...", 3)

        completed_chapters_list = current_state.get("completed_chapters", [])
        next_chapter_to_generate_index = current_state.get("next_chapter_index", 1)

        self.SysLogger.Log(f"Pipeline: Chapter writing from index {next_chapter_to_generate_index} up to {NumChaptersToGenerate}.", 4)

        if NumChaptersToGenerate is None or NumChaptersToGenerate < next_chapter_to_generate_index :
            self.SysLogger.Log(f"Pipeline: No chapters to generate (NumChaptersToGenerate: {NumChaptersToGenerate}, next_chapter_to_generate_index: {next_chapter_to_generate_index}). Skipping chapter writing.", 4)
            # Ensure last_completed_step is appropriate if skipping
            if not completed_chapters_list or len(completed_chapters_list) < NumChaptersToGenerate :
                 # This case should ideally not be hit if logic is correct prior to this stage
                 self.SysLogger.Log(f"Pipeline: WARNING - NumChaptersToGenerate ({NumChaptersToGenerate}) indicates chapters are pending, but loop condition prevents generation. Review state.", 6)
            current_state["last_completed_step"] = "chapter_generation_complete" # Or appropriate if truly no chapters were ever needed
            self._save_state_wrapper(current_state, state_filepath)
            return completed_chapters_list

        for i in range(next_chapter_to_generate_index, NumChaptersToGenerate + 1):
            self.SysLogger.Log(f"--- Pipeline: Generating Chapter {i}/{NumChaptersToGenerate} ---", 3)

            # Get outline for the current chapter (uses _get_outline_for_chapter_pipeline_version)
            # This helper needs access to self.Config and self.Statistics
            current_chapter_specific_outline = self._get_outline_for_chapter( # Calls the instance method assigned in __init__
                self.SysLogger, current_state, i, self.Config, self.Statistics
            )
            if not current_chapter_specific_outline:
                self.SysLogger.Log(f"FATAL: No outline could be determined for generating Chapter {i} in pipeline.", 7)
                raise ValueError(f"Missing outline for Chapter {i} generation in pipeline.")

            # Get current context for chapter generation (uses _get_current_context_for_chapter_gen_pipeline_version)
            current_context_for_generation = _get_current_context_for_chapter_gen_pipeline_version(
                self.SysLogger, self.Config, self.ActivePrompts, current_state, i, BaseContextText, self.Statistics # Pass self.Statistics
            )

            # Generate chapter content
            raw_chapter_content = self.ChapterGenerator.GenerateChapter(
                self.Interface,
                self.SysLogger,
                i, # chapter_num
                NumChaptersToGenerate, # total_chapters
                current_context_for_generation, # Pass the full built context now
                completed_chapters_list,
                self.Config.OUTLINE_QUALITY, # This param might be legacy for GenerateChapter, review usage.
                                             # The new GenerateChapter takes full_context.
                BaseContextText # Also potentially legacy if full_context is comprehensive.
            )

            # Generate chapter title (uses _handle_chapter_title_generation_pipeline_version)
            chapter_title = _handle_chapter_title_generation_pipeline_version(
                self.SysLogger, self.Interface, self.Config, self.ActivePrompts, raw_chapter_content, i, BaseContextText
            )

            # Format chapter
            formatted_chapter = self.Config.CHAPTER_HEADER_FORMAT.format(chapter_num=i, chapter_title=chapter_title) + "\n" + raw_chapter_content

            if len(completed_chapters_list) >= i:
                completed_chapters_list[i - 1] = formatted_chapter
                self.SysLogger.Log(f"Pipeline: Overwriting existing Chapter {i} data.", 6)
            else:
                completed_chapters_list.append(formatted_chapter)

            current_state["completed_chapters"] = completed_chapters_list
            current_state["next_chapter_index"] = i + 1
            current_state["last_completed_step"] = "chapter_generation" # In-progress step
            self._save_state_wrapper(current_state, state_filepath)
            self.SysLogger.Log(f"--- Pipeline: Chapter {i} Generation Complete. State Saved. ---", 4)

            ChapterWordCount = self.Statistics.GetWordCount(raw_chapter_content)
            self.SysLogger.Log(f"Pipeline: Chapter {i} Word Count: {ChapterWordCount}", 2)

        current_state["last_completed_step"] = "chapter_generation_complete"
        self._save_state_wrapper(current_state, state_filepath)
        self.SysLogger.Log("Pipeline: All Chapters Generated. State Saved.", 5)
        return completed_chapters_list

    def _perform_post_processing_stage(self, current_state, state_filepath, CliArgs,
                                     original_prompt_content_for_stats, translated_prompt_content_for_stats,
                                     input_prompt_file_for_stats, log_dir_for_paths, start_time_for_stats):
        self.SysLogger.Log("Pipeline: Starting Post-Processing Stage...", 3)

        # Retrieve necessary data from current_state
        # Chapters at this point are the ones from chapter_generation_complete
        ProcessedChapters = current_state.get("completed_chapters", [])
        FullOutlineForInfo = current_state.get("full_outline", "")
        StoryElementsForInfo = current_state.get("story_elements", "")
        RoughChapterOutlineForInfo = current_state.get("rough_chapter_outline", "")
        BaseContextForInfo = current_state.get("base_context", "") # Though less likely used for final info
        NumChapters = current_state.get("total_chapters")

        # Initialize StoryInfoJSON for this run
        StoryInfoJSON = {
            "Outline": FullOutlineForInfo,
            "StoryElements": StoryElementsForInfo,
            "RoughChapterOutline": RoughChapterOutlineForInfo,
            "BaseContext": BaseContextForInfo,
            "UnscrubbedChapters": ProcessedChapters[:] # Save a copy of pre-processed chapters
        }

        # --- Sub-step: Mark start of post-processing ---
        if current_state.get("last_completed_step") == "chapter_generation_complete":
            current_state["last_completed_step"] = "post_processing_started"
            self._save_state_wrapper(current_state, state_filepath)
            self.SysLogger.Log("Pipeline: Post-Processing Started. State Saved.", 4)

        post_processing_error_occurred = False

        # 1. Edit Novel (if enabled and not already done)
        if self.Config.ENABLE_FINAL_EDIT_PASS and current_state.get("last_completed_step") not in ["post_processing_edit_complete", "post_processing_scrub_complete", "post_processing_final_translate_complete", "post_processing_complete", "complete"]:
            self.SysLogger.Log("Pipeline: Starting Final Edit Pass...", 3)
            if not ProcessedChapters:
                self.SysLogger.Log("Pipeline: Warning: No chapters available for final edit pass.", 6)
            else:
                try:
                    # _get_full_story_for_editing_pipeline_version is a helper in Pipeline.py
                    # For NovelEditor, we might need to pass chapters as a list, not a single string.
                    # The original EditNovel took a list of chapters.
                    EditedChaptersList = self.NovelEditor.EditNovel(
                        self.Interface, self.SysLogger, ProcessedChapters, FullOutlineForInfo, NumChapters
                    )
                    ProcessedChapters = EditedChaptersList
                    current_state["EditedChapters"] = ProcessedChapters
                    StoryInfoJSON["EditedChapters"] = ProcessedChapters[:]
                    self.SysLogger.Log("Pipeline: Final Edit Pass Complete.", 4)
                except Exception as e:
                    post_processing_error_occurred = True
                    self.SysLogger.Log(f"Pipeline: ERROR during Final Edit Pass: {e}. Skipping further edits on this version.", 7)
                    import traceback; traceback.print_exc()
            current_state["last_completed_step"] = "post_processing_edit_complete"
            self._save_state_wrapper(current_state, state_filepath)
        elif self.Config.ENABLE_FINAL_EDIT_PASS:
             self.SysLogger.Log("Pipeline: Skipping Final Edit Pass (already completed or beyond that step).", 4)


        # 2. Scrub Novel (if enabled and not already done)
        if not self.Config.SCRUB_NO_SCRUB and not post_processing_error_occurred and \
           current_state.get("last_completed_step") not in ["post_processing_scrub_complete", "post_processing_final_translate_complete", "post_processing_complete", "complete"]:
            self.SysLogger.Log("Pipeline: Starting Scrubbing Pass...", 3)
            if not ProcessedChapters:
                self.SysLogger.Log("Pipeline: Warning: No chapters available for scrubbing pass.", 6)
            else:
                try:
                    ScrubbedChaptersList = self.Scrubber.ScrubNovel(
                        self.Interface, self.SysLogger, ProcessedChapters, NumChapters
                    )
                    ProcessedChapters = ScrubbedChaptersList
                    current_state["ScrubbedChapters"] = ProcessedChapters
                    StoryInfoJSON["ScrubbedChapters"] = ProcessedChapters[:]
                    self.SysLogger.Log("Pipeline: Scrubbing Pass Complete.", 4)
                except Exception as e:
                    post_processing_error_occurred = True
                    self.SysLogger.Log(f"Pipeline: ERROR during Scrubbing Pass: {e}. Skipping further scrubbing.", 7)
                    import traceback; traceback.print_exc()
            current_state["last_completed_step"] = "post_processing_scrub_complete"
            self._save_state_wrapper(current_state, state_filepath)
        elif not self.Config.SCRUB_NO_SCRUB and post_processing_error_occurred:
            self.SysLogger.Log("Pipeline: Skipping Scrubbing Pass due to prior error.",6)
        elif not self.Config.SCRUB_NO_SCRUB:
            self.SysLogger.Log("Pipeline: Skipping Scrubbing Pass (already completed or beyond that step).", 4)


        # 3. Translate Novel (if enabled and not already done)
        target_translation_lang = self.Config.TRANSLATE_LANGUAGE
        native_lang = self.Config.NATIVE_LANGUAGE
        if not post_processing_error_occurred and target_translation_lang and target_translation_lang.lower() != native_lang.lower() and \
           current_state.get("last_completed_step") not in ["post_processing_final_translate_complete", "post_processing_complete", "complete"]:
            self.SysLogger.Log(f"Pipeline: Starting Final Translation from '{native_lang}' to '{target_translation_lang}'...", 3)
            if not ProcessedChapters:
                self.SysLogger.Log("Pipeline: Warning: No chapters available for final translation.", 6)
            else:
                try:
                    TranslatedFinalChaptersList = self.Translator.TranslateNovel(
                        self.Interface, self.SysLogger, ProcessedChapters, NumChapters,
                        _TargetLanguage=target_translation_lang, _SourceLanguage=native_lang
                    )
                    ProcessedChapters = TranslatedFinalChaptersList
                    current_state["TranslatedFinalChapters"] = ProcessedChapters
                    StoryInfoJSON["TranslatedFinalChapters"] = ProcessedChapters[:]
                    self.SysLogger.Log(f"Pipeline: Final story translation to '{target_translation_lang}' complete.", 4)
                except Exception as e:
                    # Error here doesn't set post_processing_error_occurred, as we can still output native lang version.
                    self.SysLogger.Log(f"Pipeline: ERROR during final story translation: {e}. Using chapters in native language '{native_lang}'.", 7)
                    import traceback; traceback.print_exc()
            current_state["last_completed_step"] = "post_processing_final_translate_complete"
            self._save_state_wrapper(current_state, state_filepath)
        elif target_translation_lang and target_translation_lang.lower() != native_lang.lower() and post_processing_error_occurred:
             self.SysLogger.Log("Pipeline: Skipping Final Translation due to prior error.",6)
        elif target_translation_lang and target_translation_lang.lower() != native_lang.lower():
            self.SysLogger.Log("Pipeline: Skipping Final Translation (already completed or beyond that step).", 4)


        current_state["FinalProcessedChapters"] = ProcessedChapters # This is the list of chapter strings
        StoryInfoJSON["FinalProcessedChapters"] = ProcessedChapters[:]

        # Compile final story text
        FinalStoryBodyText = ""
        for chapter_text in ProcessedChapters:
            FinalStoryBodyText += chapter_text + "\n\n\n" # Original Write.py had 3 newlines

        # Generate Story Info (Title, Summary, Tags)
        self.SysLogger.Log("Pipeline: Generating Story Info (Title, Summary, Tags)...", 5)
        InfoQueryContentForStoryInfo = ""
        info_source_log_msg = "N/A"
        if self.Config.EXPAND_OUTLINE and current_state.get("expanded_chapter_outlines"):
            expanded_outlines_list = current_state.get("expanded_chapter_outlines", [])
            if isinstance(expanded_outlines_list, list) and expanded_outlines_list:
                InfoQueryContentForStoryInfo = "\n\n---\n\n".join(expanded_outlines_list)
                info_source_log_msg = "expanded_chapter_outlines from current_state"

        if not InfoQueryContentForStoryInfo: # Fallback to full_outline
            full_outline_from_state = current_state.get("full_outline")
            if full_outline_from_state:
                InfoQueryContentForStoryInfo = full_outline_from_state
                info_source_log_msg = "full_outline from current_state"
            else:
                InfoQueryContentForStoryInfo = "No outline information available."
                info_source_log_msg = "fallback string (no outline in state)"

        self.SysLogger.Log(f"Pipeline: Content source for GetStoryInfo: {info_source_log_msg}", 6)
        StoryInfoMessages = [self.Interface.BuildUserQuery(InfoQueryContentForStoryInfo)]

        GeneratedInfo = {}
        try:
            GeneratedInfo, _ = self.StoryInfo.GetStoryInfo(self.Interface, self.SysLogger, StoryInfoMessages)
            StoryInfoJSON.update(GeneratedInfo) # Add all keys from GeneratedInfo
            self.SysLogger.Log("Pipeline: Story Info Generation Complete.", 5)
        except Exception as e:
            self.SysLogger.Log(f"Pipeline: Error generating story info: {e}. Using defaults.", 7)
            GeneratedInfo = {"Title": "Untitled Story", "Summary": "Error generating summary.", "Tags": ""}
            StoryInfoJSON.update(GeneratedInfo)

        Title = GeneratedInfo.get("Title", "Untitled Story")
        Summary = GeneratedInfo.get("Summary", "No summary generated.")
        Tags = GeneratedInfo.get("Tags", "")

        self.SysLogger.Log(f"Pipeline: Title='{Title}', Summary='{Summary[:50]}...', Tags='{Tags}'", 5)

        # Calculate Elapsed Time & Stats
        ElapsedTime = time.time() - start_time_for_stats
        TotalWords = self.Statistics.GetWordCount(FinalStoryBodyText)
        self.SysLogger.Log(f"Pipeline: Story Total Word Count: {TotalWords}, Elapsed Time: {ElapsedTime:.2f}s", 4)

        gen_start_time_str_for_stats = datetime.datetime.fromtimestamp(start_time_for_stats).strftime("%Y/%m/%d %H:%M:%S")

        StatsString = "Work Statistics:  \n"
        StatsString += f" - Total Words: {TotalWords}  \n"
        StatsString += f" - Title: {Title}  \n"
        StatsString += f" - Summary: {Summary}  \n"
        StatsString += f" - Tags: {Tags}  \n"
        StatsString += f" - Generation Start Date: {gen_start_time_str_for_stats}\n"
        StatsString += f" - Generation Total Time: {ElapsedTime:.2f}s  \n"
        StatsString += f" - Generation Average WPM: {60 * (TotalWords/ElapsedTime):.2f}  \n" if ElapsedTime > 0 else "N/A"
        StatsString += "\n\nUser Settings:  \n"
        StatsString += f" - Base Prompt File: {input_prompt_file_for_stats or 'N/A'}  \n"
        if translated_prompt_content_for_stats: # If prompt was translated for generation
            StatsString += f" - Original Prompt Content (from {self.Config.TRANSLATE_PROMPT_LANGUAGE}): {original_prompt_content_for_stats or 'N/A'} \n"
            StatsString += f" - Translated Prompt Content (to {self.Config.NATIVE_LANGUAGE}): {translated_prompt_content_for_stats or 'N/A'} \n"
        else:
            StatsString += f" - Prompt Content: {original_prompt_content_for_stats or 'N/A'} \n"

        StatsString += "\n\nGeneration Settings:  \n"
        StatsString += f" - Generator: AIStoryGenerator_Refactored_{datetime.date.today().isoformat()}  \n"
        for key in dir(self.Config):
            if not key.startswith("_") and key.isupper():
                StatsString += f" - {key}: {getattr(self.Config, key)}  \n"

        # Save The Story To Disk
        self.SysLogger.Log("Pipeline: Saving Final Story To Disk", 3)
        os.makedirs("Stories", exist_ok=True)
        safe_title = "".join(c for c in Title if c.isalnum() or c in (" ", "_")).rstrip()
        run_timestamp_str = datetime.datetime.fromtimestamp(start_time_for_stats).strftime("%Y%m%d%H%M%S")

        FNameBase = f"Stories/Story_{safe_title.replace(' ', '_') if safe_title else 'Untitled'}_{run_timestamp_str}"
        if self.Config.OPTIONAL_OUTPUT_NAME:
            output_dir_for_file = os.path.dirname(self.Config.OPTIONAL_OUTPUT_NAME)
            if output_dir_for_file: os.makedirs(output_dir_for_file, exist_ok=True)
            FNameBase = self.Config.OPTIONAL_OUTPUT_NAME

        FinalMDPath = f"{FNameBase}.md"
        FinalJSONPath = f"{FNameBase}.json"

        try:
            with open(FinalMDPath, "w", encoding="utf-8") as F:
                OutMD = f"{StatsString}\n\n---\n\nNote: An outline of the story is available at the bottom of this document.\nPlease scroll to the bottom if you wish to read that.\n\n---\n# {Title}\n\n{FinalStoryBodyText}\n\n---\n# Outline\n```\n{FullOutlineForInfo if FullOutlineForInfo else 'No outline generated.'}\n```\n"
                F.write(OutMD)
            self.SysLogger.Log(f"Pipeline: Final story saved to {FinalMDPath}", 5)
        except Exception as e:
            self.SysLogger.Log(f"Pipeline: Error writing final story file {FinalMDPath}: {e}", 7)

        StoryInfoJSON["Stats"] = {
            "TotalWords": TotalWords, "GenerationTimeSeconds": ElapsedTime,
            "AverageWPM": (60 * (TotalWords / ElapsedTime) if ElapsedTime > 0 else 0),
            "GenerationStartDate": gen_start_time_str_for_stats,
        }
        StoryInfoJSON["OutputFiles"] = {
            "Markdown": FinalMDPath, "JSONInfo": FinalJSONPath,
            "StateFile": state_filepath, "LogDirectory": log_dir_for_paths,
        }
        try:
            with open(FinalJSONPath, "w", encoding="utf-8") as F:
                json.dump(StoryInfoJSON, F, indent=4)
            self.SysLogger.Log(f"Pipeline: Story info JSON saved to {FinalJSONPath}", 5)
        except Exception as e:
            self.SysLogger.Log(f"Pipeline: Error writing story info JSON file {FinalJSONPath}: {e}", 7)

        current_state["status"] = "completed"
        current_state["final_story_path"] = FinalMDPath
        current_state["final_json_path"] = FinalJSONPath
        current_state["last_completed_step"] = "complete" # Final step
        self._save_state_wrapper(current_state, state_filepath)
        self.SysLogger.Log("Pipeline: Post-Processing Stage Finished. Final State Saved. Run COMPLETED.", 5)
        return current_state


    def run_pipeline(self, current_state, state_filepath, initial_prompt_for_outline, Args=None, original_prompt_content_for_post_processing=None, translated_prompt_content_for_post_processing=None, start_time_for_post_processing=None, log_directory_for_post_processing=None, input_prompt_file_for_post_processing=None):
        self.SysLogger.Log("Pipeline: Starting run_pipeline method.", 3)
        last_completed_step = current_state.get("last_completed_step", "init")

        # Retrieve necessary items from state or initialize them
        Outline = current_state.get("full_outline")
        Elements = current_state.get("story_elements")
        RoughChapterOutline = current_state.get("rough_chapter_outline")
        BaseContext = current_state.get("base_context")
        NumChapters = current_state.get("total_chapters")
        # ChapterOutlines = current_state.get("expanded_chapter_outlines", []) # Will be populated by a stage
        # Chapters = current_state.get("completed_chapters", []) # Will be populated by a stage
        # start_chapter_index = current_state.get("next_chapter_index", 1) # Will be managed by chapter writing stage

        # --- Start of pipeline ---
        # Actual stages will be implemented later
        self.SysLogger.Log(f"Pipeline: Current step is '{last_completed_step}'.", 4)

        Outline = current_state.get("full_outline")
        # Retrieve necessary items from state. These are managed and updated by the stages as pipeline progresses.
        Outline = current_state.get("full_outline")
        Elements = current_state.get("story_elements")
        RoughChapterOutline = current_state.get("rough_chapter_outline")
        BaseContext = current_state.get("base_context")
        NumChapters = current_state.get("total_chapters")
        ChapterOutlines = current_state.get("expanded_chapter_outlines", [])
        Chapters = current_state.get("completed_chapters", [])

        # --- Start of pipeline ---
        if last_completed_step == "init":
            self.SysLogger.Log("Pipeline: 'init' step. Executing Outline Generation.", 4)
            Outline, Elements, RoughChapterOutline, BaseContext = \
                self._generate_outline_stage(current_state, initial_prompt_for_outline, state_filepath)
            last_completed_step = current_state.get("last_completed_step")

        if Outline is None and last_completed_step not in ["init"]:
             self.SysLogger.Log("FATAL: Outline data is missing in state after 'init' stage completion.", 7)
             raise Exception("Pipeline Error: Outline missing in state where it's expected.")

        if last_completed_step == "outline":
            self.SysLogger.Log("Pipeline: 'outline' step complete. Executing Chapter Detection.", 4)
            NumChapters = self._detect_chapters_stage(current_state, Outline, state_filepath)
            last_completed_step = current_state.get("last_completed_step")

        if NumChapters is None and last_completed_step not in ["init", "outline"]:
            self.SysLogger.Log("FATAL: NumChapters data is missing in state after 'outline' stage completion.", 7)
            raise Exception("Pipeline Error: NumChapters missing in state where it's expected.")

        if last_completed_step == "detect_chapters" or last_completed_step == "refine_chapters":
            if self.Config.EXPAND_OUTLINE:
                self.SysLogger.Log(f"Pipeline: '{last_completed_step}' step complete. Executing Chapter Outline Expansion.", 4)
                outline_for_expansion = current_state.get("full_outline")
                if not outline_for_expansion:
                     self.SysLogger.Log("FATAL: Full outline missing before chapter outline expansion stage.", 7)
                     raise ValueError("Full outline missing for expansion stage.")
                ChapterOutlines, Outline = self._expand_chapter_outlines_stage(current_state, outline_for_expansion, NumChapters, state_filepath)
                last_completed_step = current_state.get("last_completed_step")
            else:
                self.SysLogger.Log("Pipeline: Skipping Per-Chapter Outline Expansion (disabled in config). Advancing to 'expand_chapters' state.", 4)
                current_state["last_completed_step"] = "expand_chapters"
                self._save_state_wrapper(current_state, state_filepath)
                last_completed_step = "expand_chapters"

        if last_completed_step == "expand_chapters" or last_completed_step == "chapter_generation":
            if NumChapters is None:
                 self.SysLogger.Log("FATAL: Total number of chapters (NumChapters) is None before chapter writing stage.", 7)
                 raise ValueError("NumChapters is None before chapter writing.")
            if BaseContext is None:
                 self.SysLogger.Log("FATAL: BaseContext is None before chapter writing stage.", 7)
                 raise ValueError("BaseContext is None before chapter writing.")
            self.SysLogger.Log(f"Pipeline: '{last_completed_step}' step complete. Executing Chapter Writing.", 4)
            Chapters = self._write_chapters_stage(current_state, state_filepath, NumChapters, BaseContext)
            last_completed_step = current_state.get("last_completed_step")

        # Post-Processing Stage
        if last_completed_step == "chapter_generation_complete" or \
           (last_completed_step.startswith("post_processing_") and last_completed_step != "post_processing_complete"): # Allow resuming from sub-steps
            self.SysLogger.Log(f"Pipeline: '{last_completed_step}' step complete. Executing Post-Processing.", 4)
            current_state = self._perform_post_processing_stage(
                current_state, state_filepath, Args,
                original_prompt_content_for_post_processing,
                translated_prompt_content_for_post_processing,
                input_prompt_file_for_post_processing,
                log_directory_for_post_processing,
                start_time_for_post_processing # This is the main StartTime from Write.py
            )
            last_completed_step = current_state.get("last_completed_step") # Should be "complete" if successful

        self.SysLogger.Log(f"Pipeline execution finished. Final reported step by pipeline: {last_completed_step}", 5)

        # Final state saving is done within _perform_post_processing_stage if it reaches "complete"
        # or here if it ended on an earlier, now-finalized major step.
        if last_completed_step != "complete": # If post-processing didn't run or didn't finish with "complete"
            # Update final "completion" marker based on actual progress for this refactoring phase
            if last_completed_step == "chapter_generation_complete":
                current_state["last_completed_step"] = "complete_through_chapter_writing"
            elif last_completed_step == "expand_chapters":
                current_state["last_completed_step"] = "complete_through_expand_chapters"
            elif last_completed_step == "refine_chapters":
                 current_state["last_completed_step"] = "complete_through_refine_chapters"
            elif last_completed_step == "detect_chapters":
                 current_state["last_completed_step"] = "complete_through_detect_chapters"
            elif last_completed_step == "outline":
                 current_state["last_completed_step"] = "complete_through_outline"
            else: # Should not happen if all stages are covered
                current_state["last_completed_step"] = f"ended_at_unknown_state ({last_completed_step})"
            self._save_state_wrapper(current_state, state_filepath)

        return current_state

# Need to define/copy _get_outline_for_chapter_pipeline_version
# This function needs to be defined at the module level in Pipeline.py or be a method of StoryPipeline
# It was _get_outline_for_chapter in Write.py
def _get_outline_for_chapter_pipeline_version(SysLogger, current_state, chapter_index, config_module, statistics_module):
    Outline = current_state.get("full_outline", "")
    ChapterOutlines = current_state.get("expanded_chapter_outlines", [])

    # _build_mega_outline logic needs to be available here
    # For now, this is a simplified version. Will need to move _build_mega_outline later.
    MegaOutline = ""
    Elements = current_state.get("story_elements", "")
    DetailedOutlineText = ""
    if config_module.EXPAND_OUTLINE and ChapterOutlines:
        for ChapterOutline in ChapterOutlines: # Corrected variable name
            DetailedOutlineText += ChapterOutline + "\n\n" # Corrected variable name

    # Simplified _build_mega_outline from Write.py
    # Actual _build_mega_outline might be more complex and use self.ActivePrompts
    # This is a placeholder and might need refinement when moving _build_mega_outline
    MegaOutline = f"""
# Base Outline
{Elements if Elements else "N/A"}

# Detailed Outline
{DetailedOutlineText if DetailedOutlineText else "N/A"}
"""
    UsedOutline = (
        MegaOutline if config_module.EXPAND_OUTLINE and ChapterOutlines else Outline
    )
    if (
        config_module.EXPAND_OUTLINE
        and ChapterOutlines
        and len(ChapterOutlines) >= chapter_index
    ):
        potential_expanded_outline = ChapterOutlines[chapter_index - 1]
        # Using statistics_module for word count
        min_len_threshold = config_module.MIN_WORDS_PER_CHAPTER_OUTLINE
        word_count = statistics_module.GetWordCount(potential_expanded_outline)

        if word_count >= min_len_threshold:
            SysLogger.Log(
                f"Pipeline: Using valid expanded outline for Chapter {chapter_index} from state.", 6,
            )
            return potential_expanded_outline
        else:
            SysLogger.Log(
                f"Pipeline: Warning: Expanded outline for Chapter {chapter_index} from state is too short ({word_count} words, min {min_len_threshold}). Falling back.", 6,
            )

    if not UsedOutline: # This was 'Outline' before, should be UsedOutline
        SysLogger.Log(
            f"Pipeline: Warning: No valid outline found for Chapter {chapter_index}, using base outline as last resort.", 6,
        )
        return Outline if Outline else "" # Fallback to original outline if UsedOutline is empty
    else:
        # This branch might be redundant if UsedOutline is correctly constructed above.
        # If EXPAND_OUTLINE is false, UsedOutline will be the base Outline.
        # If EXPAND_OUTLINE is true but no valid chapter outline, UsedOutline will be MegaOutline.
        SysLogger.Log(
            f"Pipeline: Using general outline (MegaOutline or Base) for Chapter {chapter_index}.", 6,
        )
        return UsedOutline

# Placeholder for _build_mega_outline_pipeline_version
# This function will be moved from Write.py and adapted
def _build_mega_outline_pipeline_version(SysLogger, config_module, active_prompts_module, current_state, chapter_index_for_context=None):
    SysLogger.Log(f"Pipeline: Building Mega Outline (Chapter Context: {chapter_index_for_context}).", 6)

    FullOutline = current_state.get("full_outline", "")
    StoryElements = current_state.get("story_elements", "")
    ExpandedChapterOutlines = current_state.get("expanded_chapter_outlines", [])

    Preamble = active_prompts_module.MEGA_OUTLINE_PREAMBLE
    ChapterOutlineFormat = active_prompts_module.MEGA_OUTLINE_CHAPTER_FORMAT

    MegaOutline = Preamble + "\n\n"
    MegaOutline += f"# Story Elements\n{StoryElements}\n\n"
    MegaOutline += f"# Full Original Outline\n{FullOutline}\n\n"

    if config_module.EXPAND_OUTLINE and ExpandedChapterOutlines:
        MegaOutline += "# Expanded Chapter Outlines\n"
        for i, chapter_outline_text in enumerate(ExpandedChapterOutlines):
            chapter_num = i + 1
            # Highlight current chapter if chapter_index_for_context is provided
            is_current_chapter = (chapter_index_for_context is not None and chapter_num == chapter_index_for_context)
            prefix = "** (Current Chapter for Generation) **\n" if is_current_chapter else ""

            MegaOutline += ChapterOutlineFormat.format(
                chapter_num=chapter_num,
                prefix=prefix,
                chapter_outline_text=chapter_outline_text
            )
            MegaOutline += "\n\n"

    SysLogger.Log(f"Pipeline: Mega Outline Length: {len(MegaOutline)} chars.", 6)
    return MegaOutline.strip()

# Add the _get_full_story_for_editing to pipeline, to be used by NovelEditor stage
def _get_full_story_for_editing_pipeline_version(ChaptersList, SysLogger, Config):
    SysLogger.Log("Pipeline: Compiling full story for editing.", 6)
    FullStoryText = ""
    for i, ChapterText in enumerate(ChaptersList):
        ChapterNum = i + 1
        # Use the chapter format from config, similar to how it's done for final output
        FullStoryText += Config.CHAPTER_HEADER_FORMAT.format(chapter_num=ChapterNum, chapter_title=f"Chapter {ChapterNum}") + "\n"
        FullStoryText += ChapterText + "\n\n"
    return FullStoryText.strip()

# Add the _get_current_context_for_chapter_gen from Write.py
def _get_current_context_for_chapter_gen_pipeline_version(SysLogger, Config, ActivePrompts, current_state, chapter_num, base_context_text, statistics_module): # Added statistics_module
    SysLogger.Log(f"Pipeline: Building context for Chapter {chapter_num} generation.", 6)

    context_components = [base_context_text]

    # Add previous chapter text if configured and available
    if Config.CHAPTER_MEMORY_WORDS > 0 and chapter_num > 1:
        completed_chapters = current_state.get("completed_chapters", [])
        if len(completed_chapters) >= (chapter_num -1):
            previous_chapter_text = completed_chapters[chapter_num - 2] # -2 because list is 0-indexed
            # Get last N words
            previous_chapter_words = previous_chapter_text.split()
            context_words_count = Config.CHAPTER_MEMORY_WORDS
            previous_chapter_segment = " ".join(previous_chapter_words[-context_words_count:])

            formatted_prev_chapter_text = ActivePrompts.PREVIOUS_CHAPTER_CONTEXT_FORMAT.format(
                chapter_num=chapter_num - 1,
                previous_chapter_text=previous_chapter_segment
            )
            context_components.append(formatted_prev_chapter_text)
            SysLogger.Log(f"Pipeline: Added last {context_words_count} words from Chapter {chapter_num - 1} to context.", 6)
        else:
            SysLogger.Log(f"Pipeline: Chapter {chapter_num -1} text not found in completed_chapters for context.",6)


    # Add specific outline for the current chapter
    chapter_specific_outline = _get_outline_for_chapter_pipeline_version(
        SysLogger, current_state, chapter_num, Config, statistics_module # Use passed statistics_module
    )

    formatted_chapter_outline = ActivePrompts.CURRENT_CHAPTER_OUTLINE_FORMAT.format(
        chapter_num=chapter_num,
        chapter_outline_text=chapter_specific_outline
    )
    context_components.append(formatted_chapter_outline)

    final_context = "\n\n".join(filter(None, context_components)) # Join non-empty components
    SysLogger.Log(f"Pipeline: Final context for Chapter {chapter_num} length: {len(final_context)} chars.", 6)
    return final_context.strip()

# Add _handle_chapter_title_generation from Write.py
def _handle_chapter_title_generation_pipeline_version(SysLogger, Interface, Config, ActivePrompts, chapter_text, chapter_num, base_context_text):
    SysLogger.Log(f"Pipeline: Generating title for Chapter {chapter_num}.", 6)
    if not Config.GENERATE_CHAPTER_TITLES:
        SysLogger.Log("Pipeline: Chapter title generation is disabled by config.", 6)
        return f"Chapter {chapter_num}" # Default title

    try:
        title_prompt_template = ActivePrompts.GET_CHAPTER_TITLE_PROMPT
        title_prompt_content = title_prompt_template.format(
            base_story_context=base_context_text,
            chapter_num=chapter_num,
            chapter_text=chapter_text
        )

        # Use a simpler query for title generation, assuming it's less complex than story generation
        title_messages = [Interface.BuildUserQuery(title_prompt_content)]
        # Using FAST_MODEL_NAME from Config
        # Seed override can be random or a fixed one for titles if preferred
        # SafeGenerateText returns (_Messages, TokenUsage), so we need to unpack
        title_response_messages, _ = Interface.SafeGenerateText( # Modified call
            _Logger=SysLogger,
            _Messages=title_messages,
            _Model=Config.FAST_MODEL_NAME,
            _MinWordCount=1
            # Temperature and max_tokens are typically part of model options / config string,
            # or would require a more specialized Interface method if needing explicit override here.
        )
        ChapterTitle = Interface.GetLastMessageText(title_response_messages) # Get text from messages

        ChapterTitle = ChapterTitle.strip().replace('"',"") # Clean up title

        # Basic validation for title (e.g., not empty, not excessively long)
        if not ChapterTitle or len(ChapterTitle) > 150: # Max length for a title
            SysLogger.Log(f"Pipeline: Warning: Generated title for Chapter {chapter_num} is invalid or too long: '{ChapterTitle}'. Using default.", 6)
            return f"Chapter {chapter_num}"

        SysLogger.Log(f"Pipeline: Generated title for Chapter {chapter_num}: '{ChapterTitle}'.", 6)
        return ChapterTitle

    except Exception as e:
        SysLogger.Log(f"Pipeline: Error during chapter title generation for Chapter {chapter_num}: {e}. Using default title.", 7)
        return f"Chapter {chapter_num}"
