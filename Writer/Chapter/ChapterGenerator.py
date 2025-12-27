import Writer.Config
# import Writer.Prompts # Dihapus untuk pemuatan dinamis
import Writer.Statistics  # Add near other imports at the top
from Writer.Models import ChapterOutput

import Writer.Scene.ChapterByScene

# Helper method declarations (skeletons initially, will be filled)


def _get_pydantic_format_instructions_if_enabled(Interface, _Logger, Config_module):
    """
    Get Pydantic format instructions if enabled in config.

    Uses language-aware format instructions from Interface._build_format_instruction().

    Returns:
        str: Format instructions or empty string
    """
    if not Config_module.USE_PYDANTIC_PARSING:
        return ""

    try:
        # Import here to avoid circular imports
        from Writer.Models import ChapterOutput

        # Use language-aware format instruction builder from Interface
        schema = ChapterOutput.model_json_schema()
        return Interface._build_format_instruction(schema)
    except Exception as e:
        _Logger.Log(f"Failed to generate Pydantic format instructions: {e}", 4)
        return ""


def _extract_chapter_summary(summary_json: dict) -> str:
    """Extract chapter summary from JSON response with fallback options.

    Handles multiple possible JSON structures from different LLM responses.
    Pattern: SafeGenerateJSON with fallback extraction (as used in ChapterGenSummaryCheck).

    Args:
        summary_json: Dictionary from SafeGenerateJSON response

    Returns:
        str: Extracted summary text, empty string if not found

    Extraction priority:
    1. Direct 'text' or 'summary' field (Qwen/new prompt style)
    2. Prompt-structured format "Bab Sebelumnya" / "Previous Chapter" (Gemma/old prompt style)
    3. Any string field longer than 10 chars (fallback)
    """
    if not isinstance(summary_json, dict):
        return ""

    # Priority 1: Direct text/summary field (Qwen style, new prompt)
    if 'text' in summary_json:
        text_val = summary_json.get('text', '')
        if isinstance(text_val, str) and len(text_val) > 0:
            return text_val
    if 'summary' in summary_json:
        summary_val = summary_json.get('summary', '')
        if isinstance(summary_val, str) and len(summary_val) > 0:
            return summary_val

    # Priority 2: Prompt-structured format (Gemma style, old prompt)
    if 'Bab Sebelumnya' in summary_json or 'Previous Chapter' in summary_json:
        return _format_structured_summary(summary_json)

    # Priority 3: Fallback to any string field
    for value in summary_json.values():
        if isinstance(value, str) and len(value) > 10:
            return value

    return ""


def _format_structured_summary(data: dict) -> str:
    """Format structured summary from prompt-style JSON response.

    Handles both Indonesian ("Bab Sebelumnya") and English ("Previous Chapter") formats.

    Args:
        data: Dictionary with structured summary data

    Returns:
        str: Formatted summary as string
    """
    sections = []

    # Indonesian format
    for key in ['Bab Sebelumnya']:
        if key in data and isinstance(data[key], dict):
            sections.append(f"{key}:")
            for subkey, values in data[key].items():
                if isinstance(values, list):
                    sections.append(f"- {subkey}: {', '.join(str(v) for v in values)}")
                elif isinstance(values, str):
                    sections.append(f"- {subkey}: {values}")

    # English format
    for key in ['Previous Chapter']:
        if key in data and isinstance(data[key], dict):
            sections.append(f"{key}:")
            for subkey, values in data[key].items():
                if isinstance(values, list):
                    sections.append(f"- {subkey}: {', '.join(str(v) for v in values)}")
                elif isinstance(values, str):
                    sections.append(f"- {subkey}: {values}")

    # Indonesian "Hal yang Perlu Diingat"
    for key in ['Hal yang Perlu Diingat']:
        if key in data and isinstance(data[key], list):
            sections.append(f"{key}:")
            for item in data[key]:
                sections.append(f"- {item}")

    # English "Things to Remember"
    for key in ['Things to Remember']:
        if key in data and isinstance(data[key], list):
            sections.append(f"{key}:")
            for item in data[key]:
                sections.append(f"- {item}")

    return "\n".join(sections)


def _generate_reasoning_for_stage(Interface, _Logger, Config_module, reasoning_type: str,
                                  ThisChapterOutline: str, FormattedLastChapterSummary: str = "",
                                  _BaseContext: str = "", _ChapterNum: int = None,  # type: ignore[assignment]
                                  existing_content: str = "") -> str:
    """
    Generate reasoning for a specific chapter generation stage.

    Args:
        Interface: LLM interface
        _Logger: Logger instance
        Config_module: Configuration module
        reasoning_type: Type of reasoning (plot, character, dialogue)
        ThisChapterOutline: Current chapter outline
        FormattedLastChapterSummary: Previous chapter summary
        _BaseContext: Base context
        _ChapterNum: Chapter number
        existing_content: Existing content for enhancement stages

    Returns:
        str: Generated reasoning text
    """
    if not Config_module.USE_REASONING_CHAIN:
        _Logger.Log("Skipping reasoning (USE_REASONING_CHAIN=False)", 6)
        return ""

    # Log reasoning request
    _Logger.Log(
        f"Requesting {reasoning_type} reasoning from {Config_module.REASONING_MODEL} for Chapter {_ChapterNum or 'N/A'}",
        5
    )

    # Import ReasoningChain here to avoid circular imports
    from Writer.ReasoningChain import ReasoningChain

    # Create or get the reasoning chain from a global cache
    # For now, create a new instance each time (could be optimized later)
    reasoning_chain = ReasoningChain(Interface, Config_module, _Logger)

    # Prepare context
    context = f"""
CHAPTER OUTLINE:
{ThisChapterOutline}

BASE CONTEXT:
{_BaseContext}
"""

    if FormattedLastChapterSummary:
        context += f"\nPREVIOUS CHAPTER SUMMARY:\n{FormattedLastChapterSummary}"

    # Generate reasoning based on type
    if reasoning_type == "plot":
        reasoning = reasoning_chain.reason(context, "plot", None, _ChapterNum)
    elif reasoning_type == "character":
        reasoning = reasoning_chain.reason(context, "character", existing_content, _ChapterNum)
    elif reasoning_type == "dialogue":
        reasoning = reasoning_chain.reason(context, "dialogue", existing_content, _ChapterNum)
    else:
        reasoning = ""

    return reasoning


def _prepare_initial_generation_context(Interface, _Logger, ActivePrompts, _Outline, _Chapters, _ChapterNum, _TotalChapters, Config_module):
    """Prepares initial context, chapter-specific outline, and last chapter summary."""
    _Logger.Log(f"Stage 0: Preparing initial generation context for Chapter {_ChapterNum}/{_TotalChapters}", 3)

    MessageHistory = [Interface.BuildSystemQuery(ActivePrompts.CHAPTER_GENERATION_INTRO)]  # Corrected variable name
    ContextHistoryInsert = ""

    if _Chapters:  # Check if list is not empty
        ContextHistoryInsert += ActivePrompts.CHAPTER_HISTORY_INSERT.format(_Outline=_Outline)

    # Extract ThisChapterOutline
    _Logger.Log(f"Extracting Chapter Specific Outline for Chapter {_ChapterNum}/{_TotalChapters}", 4)
    ChapterSegmentMessages = [
        Interface.BuildSystemQuery(ActivePrompts.CHAPTER_GENERATION_INTRO),
        Interface.BuildUserQuery(
            ActivePrompts.CHAPTER_GENERATION_PROMPT.format(_Outline=_Outline, _ChapterNum=_ChapterNum)
        )
    ]
    ChapterSegmentMessages, chapter_obj, _ = Interface.SafeGeneratePydantic(
        _Logger, ChapterSegmentMessages, Config_module.CHAPTER_STAGE1_WRITER_MODEL,
        ChapterOutput
    )
    ThisChapterOutline = chapter_obj.text
    _Logger.Log(f"Created Chapter Specific Outline for Chapter {_ChapterNum}/{_TotalChapters}", 4)

    # Generate Summary of Last Chapter If Applicable
    FormattedLastChapterSummary = ""
    if _Chapters:  # Check if list is not empty
        _Logger.Log(f"Creating Summary Of Last Chapter Info for Chapter {_ChapterNum}/{_TotalChapters}", 3)
        ChapterSummaryMessages = [
            Interface.BuildSystemQuery(ActivePrompts.CHAPTER_SUMMARY_INTRO),
            Interface.BuildUserQuery(
                ActivePrompts.CHAPTER_SUMMARY_PROMPT.format(
                    _ChapterNum=_ChapterNum - 1, _TotalChapters=_TotalChapters,
                    _Outline=_Outline, _LastChapter=_Chapters[-1].get("text", "")
                )
            )
        ]
        ChapterSummaryMessages, summary_json, _ = Interface.SafeGenerateJSON(
            _Logger, ChapterSummaryMessages, Config_module.CHAPTER_STAGE1_WRITER_MODEL
        )
        FormattedLastChapterSummary = _extract_chapter_summary(summary_json)
        _Logger.Log("Created Summary Of Last Chapter Info", 3)

    # DetailedChapterOutline combines ThisChapterOutline and FormattedLastChapterSummary (as per original logic)
    # The original logic was:
    # DetailedChapterOutline: str = ThisChapterOutline
    # if FormattedLastChapterSummary != "":
    #    DetailedChapterOutline = ThisChapterOutline # This seems like a bug, should it combine?
    # For now, replicating the original logic. If it's a bug, it's an existing one.
    # Let's assume the intention was to use ThisChapterOutline as the primary detailed outline for the current chapter,
    # and FormattedLastChapterSummary is part of the broader context.
    # The variable DetailedChapterOutline in the original code was used in LLMSummaryCheck.
    # Let's return both ThisChapterOutline and FormattedLastChapterSummary,
    # and the calling stages can format them into prompts as needed.
    # The original DetailedChapterOutline was used by LLMSummaryCheck.
    # Let's reconstruct it as it was:
    _ = ThisChapterOutline  # DetailedChapterOutlineForCheck (not used, kept for compatibility)
    if FormattedLastChapterSummary != "":
        # This was the original logic for DetailedChapterOutline, which seems to just be ThisChapterOutline
        # It was then used in LLMSummaryCheck.
        # For clarity, we will pass ThisChapterOutline and FormattedLastChapterSummary separately to stages,
        # and they can construct their prompts. LLMSummaryCheck will need the combined version.
        # The original code was:
        # DetailedChapterOutline: str = ThisChapterOutline
        # if FormattedLastChapterSummary != "":
        #    DetailedChapterOutline = ThisChapterOutline # This line seems to make DetailedChapterOutline always ThisChapterOutline
        # This was likely a bug. A more logical DetailedChapterOutline for checking would be:
        # DetailedChapterOutlineForCheck = f"{ThisChapterOutline}\n\n{FormattedLastChapterSummary}"
        # However, to maintain original behavior first, I will stick to the direct assignment.
        # The variable `DetailedChapterOutline` was directly passed to `LLMSummaryCheck`.
        # The prompt for stages used `ThisChapterOutline` and `FormattedLastChapterSummary` separately.
        pass  # No change to ThisChapterOutline based on FormattedLastChapterSummary for DetailedChapterOutlineForCheck

    _Logger.Log(f"Stage 0: Initial generation context prepared for Chapter {_ChapterNum}", 3)
    return MessageHistory, ContextHistoryInsert, ThisChapterOutline, FormattedLastChapterSummary, ThisChapterOutline  # Returning ThisChapterOutline as DetailedChapterOutlineForCheck


def _generate_stage1_plot(Interface, _Logger, ActivePrompts, _ChapterNum, _TotalChapters, MessageHistory, ContextHistoryInsert, ThisChapterOutline, FormattedLastChapterSummary, _BaseContext, DetailedChapterOutlineForCheck, Config_module, ChapterGenSummaryCheck_module):
    """Generates Stage 1: Initial Plot, including feedback loop."""
    _Logger.Log(f"Stage 1: Generating Initial Plot for Chapter {_ChapterNum}/{_TotalChapters}", 3)
    IterCounter = 0
    Feedback = ""
    Stage1Chapter = ""

    # Get Pydantic format instructions if enabled
    PydanticFormatInstructions = _get_pydantic_format_instructions_if_enabled(Interface, _Logger, Config_module)

    # Generate reasoning if reasoning chain is enabled
    ReasoningContent = ""
    if Config_module.USE_REASONING_CHAIN:
        ReasoningContent = _generate_reasoning_for_stage(
            Interface, _Logger, Config_module, "plot",
            ThisChapterOutline, FormattedLastChapterSummary, _BaseContext, _ChapterNum
        )

    while True:
        # Build enhanced base context with reasoning
        EnhancedBaseContext = _BaseContext
        if ReasoningContent:
            EnhancedBaseContext = f"{_BaseContext}\n\n### Reasoning Guidance:\n{ReasoningContent}"

        Prompt = ActivePrompts.CHAPTER_GENERATION_STAGE1.format(
            ContextHistoryInsert=ContextHistoryInsert,
            _ChapterNum=_ChapterNum,
            _TotalChapters=_TotalChapters,
            ThisChapterOutline=ThisChapterOutline,
            FormattedLastChapterSummary=FormattedLastChapterSummary,
            Feedback=Feedback,
            _BaseContext=EnhancedBaseContext,
            PydanticFormatInstructions=PydanticFormatInstructions,
        )
        _Logger.Log(f"Generating Initial Chapter (Stage 1: Plot) {_ChapterNum}/{_TotalChapters} (Iteration {IterCounter}/{Config_module.CHAPTER_MAX_REVISIONS})", 5)

        CurrentMessages = MessageHistory[:]  # Use a copy for each iteration
        CurrentMessages.append(Interface.BuildUserQuery(Prompt))

        # Use Pydantic model for structured output
        from Writer.Models import ChapterOutput
        CurrentMessages, pydantic_result, _ = Interface.SafeGeneratePydantic(
            _Logger, CurrentMessages, Config_module.CHAPTER_STAGE1_WRITER_MODEL,
            ChapterOutput, _SeedOverride=IterCounter + Config_module.SEED
        )
        Stage1Chapter = pydantic_result.text if hasattr(pydantic_result, 'text') else str(pydantic_result)

        IterCounter += 1
        _Logger.Log(f"Finished Initial Generation For Initial Chapter (Stage 1: Plot)  {_ChapterNum}/{_TotalChapters}", 5)

        if IterCounter > Config_module.CHAPTER_MAX_REVISIONS:
            _Logger.Log(f"Chapter Summary-Based Revision Seems Stuck (Stage 1: Plot) - Forcefully Exiting after {IterCounter}/{Config_module.CHAPTER_MAX_REVISIONS} iterations.", 7)
            break
        Result, Feedback = ChapterGenSummaryCheck_module.LLMSummaryCheck(
            Interface, _Logger, DetailedChapterOutlineForCheck, Stage1Chapter
        )
        if Result:
            _Logger.Log(f"Done Generating Initial Chapter (Stage 1: Plot) {_ChapterNum}/{_TotalChapters} after {IterCounter} iteration(s).", 5)
            break
    return Stage1Chapter


def _generate_stage2_character_dev(Interface, _Logger, ActivePrompts, _ChapterNum, _TotalChapters, MessageHistory, ContextHistoryInsert, ThisChapterOutline, FormattedLastChapterSummary, Stage1Chapter, _BaseContext, DetailedChapterOutlineForCheck, Config_module, ChapterGenSummaryCheck_module):
    """Generates Stage 2: Character Development, including feedback loop."""
    _Logger.Log(f"Stage 2: Generating Character Development for Chapter {_ChapterNum}/{_TotalChapters}", 3)
    IterCounter = 0
    Feedback = ""
    Stage2Chapter = ""

    # Get Pydantic format instructions if enabled
    PydanticFormatInstructions = _get_pydantic_format_instructions_if_enabled(Interface, _Logger, Config_module)

    # Generate reasoning if reasoning chain is enabled
    ReasoningContent = ""
    if Config_module.USE_REASONING_CHAIN:
        ReasoningContent = _generate_reasoning_for_stage(
            Interface, _Logger, Config_module, "character",
            ThisChapterOutline, FormattedLastChapterSummary, _BaseContext, _ChapterNum, Stage1Chapter
        )

    while True:
        # Build enhanced base context with reasoning
        EnhancedBaseContext = _BaseContext
        if ReasoningContent:
            EnhancedBaseContext = f"{_BaseContext}\n\n### Character Development Reasoning:\n{ReasoningContent}"

        Prompt = ActivePrompts.CHAPTER_GENERATION_STAGE2.format(
            ContextHistoryInsert=ContextHistoryInsert,
            _ChapterNum=_ChapterNum,
            _TotalChapters=_TotalChapters,
            ThisChapterOutline=ThisChapterOutline,
            FormattedLastChapterSummary=FormattedLastChapterSummary,
            Stage1Chapter=Stage1Chapter,  # Output from previous stage
            Feedback=Feedback,
            _BaseContext=EnhancedBaseContext,
            PydanticFormatInstructions=PydanticFormatInstructions,
        )
        _Logger.Log(f"Generating Character Development (Stage 2) {_ChapterNum}/{_TotalChapters} (Iteration {IterCounter}/{Config_module.CHAPTER_MAX_REVISIONS})", 5)

        CurrentMessages = MessageHistory[:]  # Use a copy
        CurrentMessages.append(Interface.BuildUserQuery(Prompt))

        # Use Pydantic model for structured output
        from Writer.Models import ChapterOutput
        CurrentMessages, pydantic_result, _ = Interface.SafeGeneratePydantic(
            _Logger, CurrentMessages, Config_module.CHAPTER_STAGE2_WRITER_MODEL,
            ChapterOutput, _SeedOverride=IterCounter + Config_module.SEED
        )
        Stage2Chapter = pydantic_result.text if hasattr(pydantic_result, 'text') else str(pydantic_result)

        IterCounter += 1
        _Logger.Log(f"Finished Character Development Generation (Stage 2) for Chapter {_ChapterNum}/{_TotalChapters}", 5)

        if IterCounter > Config_module.CHAPTER_MAX_REVISIONS:
            _Logger.Log(f"Chapter Summary-Based Revision Seems Stuck (Stage 2: Character Dev) - Forcefully Exiting after {IterCounter}/{Config_module.CHAPTER_MAX_REVISIONS} iterations.", 7)
            break
        Result, Feedback = ChapterGenSummaryCheck_module.LLMSummaryCheck(
            Interface, _Logger, DetailedChapterOutlineForCheck, Stage2Chapter
        )
        if Result:
            _Logger.Log(f"Done Generating Character Development (Stage 2) for Chapter {_ChapterNum}/{_TotalChapters} after {IterCounter} iteration(s).", 5)
            break
    return Stage2Chapter


def _generate_stage3_dialogue(Interface, _Logger, ActivePrompts, _ChapterNum, _TotalChapters, MessageHistory, ContextHistoryInsert, ThisChapterOutline, FormattedLastChapterSummary, Stage2Chapter, _BaseContext, DetailedChapterOutlineForCheck, Config_module, ChapterGenSummaryCheck_module):
    """Generates Stage 3: Dialogue, including feedback loop."""
    _Logger.Log(f"Stage 3: Generating Dialogue for Chapter {_ChapterNum}/{_TotalChapters}", 3)
    IterCounter = 0
    Feedback = ""
    Stage3Chapter = ""

    # Get Pydantic format instructions if enabled
    PydanticFormatInstructions = _get_pydantic_format_instructions_if_enabled(Interface, _Logger, Config_module)

    # Generate reasoning if reasoning chain is enabled
    ReasoningContent = ""
    if Config_module.USE_REASONING_CHAIN:
        ReasoningContent = _generate_reasoning_for_stage(
            Interface, _Logger, Config_module, "dialogue",
            ThisChapterOutline, FormattedLastChapterSummary, _BaseContext, _ChapterNum, Stage2Chapter
        )

    while True:
        # Build enhanced base context with reasoning
        EnhancedBaseContext = _BaseContext
        if ReasoningContent:
            EnhancedBaseContext = f"{_BaseContext}\n\n### Dialogue Enhancement Reasoning:\n{ReasoningContent}"

        Prompt = ActivePrompts.CHAPTER_GENERATION_STAGE3.format(
            ContextHistoryInsert=ContextHistoryInsert,
            _ChapterNum=_ChapterNum,
            _TotalChapters=_TotalChapters,
            ThisChapterOutline=ThisChapterOutline,
            FormattedLastChapterSummary=FormattedLastChapterSummary,
            Stage2Chapter=Stage2Chapter,  # Output from previous stage
            Feedback=Feedback,
            _BaseContext=EnhancedBaseContext,
            PydanticFormatInstructions=PydanticFormatInstructions,
        )
        _Logger.Log(f"Generating Dialogue (Stage 3) {_ChapterNum}/{_TotalChapters} (Iteration {IterCounter}/{Config_module.CHAPTER_MAX_REVISIONS})", 5)

        CurrentMessages = MessageHistory[:]  # Use a copy
        CurrentMessages.append(Interface.BuildUserQuery(Prompt))

        # Use Pydantic model for structured output
        from Writer.Models import ChapterOutput
        CurrentMessages, pydantic_result, _ = Interface.SafeGeneratePydantic(
            _Logger, CurrentMessages, Config_module.CHAPTER_STAGE3_WRITER_MODEL,
            ChapterOutput, _SeedOverride=IterCounter + Config_module.SEED
        )
        Stage3Chapter = pydantic_result.text if hasattr(pydantic_result, 'text') else str(pydantic_result)

        IterCounter += 1
        _Logger.Log(f"Finished Dialogue Generation (Stage 3) for Chapter {_ChapterNum}/{_TotalChapters}", 5)

        if IterCounter > Config_module.CHAPTER_MAX_REVISIONS:
            _Logger.Log(f"Chapter Summary-Based Revision Seems Stuck (Stage 3: Dialogue) - Forcefully Exiting after {IterCounter}/{Config_module.CHAPTER_MAX_REVISIONS} iterations.", 7)
            break
        Result, Feedback = ChapterGenSummaryCheck_module.LLMSummaryCheck(
            Interface, _Logger, DetailedChapterOutlineForCheck, Stage3Chapter
        )
        if Result:
            _Logger.Log(f"Done Generating Dialogue (Stage 3) for Chapter {_ChapterNum}/{_TotalChapters} after {IterCounter} iteration(s).", 5)
            break
    return Stage3Chapter


def _run_final_chapter_revision_loop(Interface, _Logger, ActivePrompts, _ChapterNum, _TotalChapters, ChapterToRevise, OverallOutline, MessageHistoryForRevision, Config_module, LLMEditor_module, ReviseChapter_func_local):
    """Runs the final chapter revision loop (Stage 5)."""
    _Logger.Log(f"Stage 5: Entering Feedback/Revision Loop For Chapter {_ChapterNum}/{_TotalChapters}", 4)

    CurrentChapterContent = ChapterToRevise
    CurrentWritingHistory = MessageHistoryForRevision[:]  # Use a copy
    Rating = False  # Original code implies boolean, though it was assigned int later. Let's use False.
    Iterations = 0
    RevisionLoopExitReason = "Unknown"

    while True:
        Iterations += 1
        Feedback = LLMEditor_module.GetFeedbackOnChapter(
            Interface, _Logger, CurrentChapterContent, OverallOutline  # OverallOutline is _Outline from GenerateChapter
        )
        Rating = LLMEditor_module.GetChapterRating(Interface, _Logger, CurrentChapterContent)

        if Iterations > Config_module.CHAPTER_MAX_REVISIONS:
            RevisionLoopExitReason = "Max Revisions Reached"
            break
        # Original code used Rating as boolean for this check
        if (Iterations > Config_module.CHAPTER_MIN_REVISIONS) and Rating:  # Rating should be boolean True if good
            RevisionLoopExitReason = "Quality Standard Met"
            break

        CurrentChapterContent, CurrentWritingHistory = ReviseChapter_func_local(
            Interface,
            _Logger,
            _ChapterNum,
            _TotalChapters,
            CurrentChapterContent,
            Feedback,
            CurrentWritingHistory,  # Pass the potentially modified history
            _Iteration=Iterations,
            # ActivePrompts is implicitly handled by ReviseChapter_func_local as it imports it.
        )

    _Logger.Log(f"{RevisionLoopExitReason}, Exiting Feedback/Revision Loop (Stage 5) For Chapter {_ChapterNum}/{_TotalChapters} after {Iterations}/{Config_module.CHAPTER_MAX_REVISIONS} iteration(s). Final Rating: {Rating}", 4)
    return CurrentChapterContent


def _run_scene_generation_pipeline_for_initial_plot(Interface, _Logger, ActivePrompts, _ChapterNum, _TotalChapters, ThisChapterOutline, _FullOutlineForSceneGen, _BaseContext, Config_module, _ExpandedChapterOutline=None):
    """Generates initial plot using scene-by-scene pipeline."""
    _Logger.Log(f"Stage 1 (Alternative): Running Scene Generation Pipeline for Chapter {_ChapterNum}/{_TotalChapters}", 3)
    # Note: Writer.Scene.ChapterByScene is imported in the main GenerateChapter or at file top.
    # Ensure it's available here if this structure changes.
    Stage1Chapter = Writer.Scene.ChapterByScene.ChapterByScene(
        Interface,
        _Logger,
        _ChapterNum,
        _TotalChapters,
        ThisChapterOutline,  # This is the chapter-specific outline
        _FullOutlineForSceneGen,  # This is the overall story outline
        _BaseContext,
        _ExpandedChapterOutline,  # type: ignore # Pass expanded chapter outline with scenes
        # Config_module is implicitly used by ChapterByScene if it imports Writer.Config directly
    )
    _Logger.Log(f"Stage 1 (Alternative): Scene Generation Pipeline COMPLETE for Chapter {_ChapterNum}/{_TotalChapters}", 3)
    return Stage1Chapter


def GenerateChapter(
    Interface,
    _Logger,
    _ChapterNum: int,
    _TotalChapters: int,
    _Outline: str,
    _Chapters: list = [],
    # _QualityThreshold: int = 85, # Removed as it's unused
    _BaseContext: str = "",
    _FullOutlineForSceneGen: str = "",  # Added to pass the full outline if needed by scene gen
    _ExpandedChapterOutline: dict = None  # type: ignore[assignment]  # Added to pass expanded chapter outline with scenes
):
    from Writer.PromptsHelper import get_prompts
    ActivePrompts = get_prompts()  # Use language-aware import
    import Writer.Config as Config  # Import Config
    import Writer.Chapter.ChapterGenSummaryCheck as ChapterGenSummaryCheck  # Import for helpers
    import Writer.LLMEditor as LLMEditor  # Import for helpers
    # Scene.ChapterByScene is imported where _run_scene_generation_pipeline_for_initial_plot is defined/called

    # Stage 0: Prepare initial context, chapter-specific outline, and last chapter summary
    (
        MessageHistory,
        ContextHistoryInsert,
        ThisChapterOutline,
        FormattedLastChapterSummary,
        DetailedChapterOutlineForCheck
    ) = _prepare_initial_generation_context(
        Interface, _Logger, ActivePrompts, _Outline, _Chapters,
        _ChapterNum, _TotalChapters, Config
    )
    _Logger.Log(f"Done with base langchain setup for Chapter {_ChapterNum}/{_TotalChapters}", 2)

    # Stage 1: Create Initial Plot (either via scene pipeline or direct generation)
    Stage1Chapter = ""
    if Config.SCENE_GENERATION_PIPELINE:  # Use Config from import
        Stage1Chapter = _run_scene_generation_pipeline_for_initial_plot(
            Interface, _Logger, ActivePrompts, _ChapterNum, _TotalChapters,
            ThisChapterOutline, _FullOutlineForSceneGen, _BaseContext, Config,  # Pass Config module
            _ExpandedChapterOutline  # Pass expanded chapter outline with scenes
        )
    else:
        Stage1Chapter = _generate_stage1_plot(
            Interface, _Logger, ActivePrompts, _ChapterNum, _TotalChapters, MessageHistory,  # Pass MessageHistory
            ContextHistoryInsert, ThisChapterOutline, FormattedLastChapterSummary,
            _BaseContext, DetailedChapterOutlineForCheck, Config, ChapterGenSummaryCheck  # Pass Config and ChapterGenSummaryCheck modules
        )

    # Stage 2: Add Character Development
    Stage2Chapter = _generate_stage2_character_dev(
        Interface, _Logger, ActivePrompts, _ChapterNum, _TotalChapters, MessageHistory,
        ContextHistoryInsert, ThisChapterOutline, FormattedLastChapterSummary,
        Stage1Chapter, _BaseContext, DetailedChapterOutlineForCheck, Config, ChapterGenSummaryCheck
    )

    # Stage 3: Add Dialogue
    Stage3Chapter = _generate_stage3_dialogue(
        Interface, _Logger, ActivePrompts, _ChapterNum, _TotalChapters, MessageHistory,
        ContextHistoryInsert, ThisChapterOutline, FormattedLastChapterSummary,
        Stage2Chapter, _BaseContext, DetailedChapterOutlineForCheck, Config, ChapterGenSummaryCheck
    )

    Chapter = Stage3Chapter

    # Stage 5: Revision Cycle
    if Config.CHAPTER_NO_REVISIONS:  # Use Config from import
        _Logger.Log("Chapter Revision Disabled In Config, Exiting Now", 5)
    else:
        Chapter = _run_final_chapter_revision_loop(
            Interface, _Logger, ActivePrompts, _ChapterNum, _TotalChapters,
            Chapter, _Outline, MessageHistory, Config, LLMEditor, ReviseChapter  # Pass imported modules and local ReviseChapter
        )

    return Chapter


def ReviseChapter(
    Interface,
    _Logger,
    _ChapterNum: int,
    _TotalChapters: int,
    _Chapter,
    _Feedback,
    _History: list = [],
    _Iteration: int = 0,
):  # Tambahkan _ChapterNum, _TotalChapters
    from Writer.PromptsHelper import get_prompts
    ActivePrompts = get_prompts()  # Use language-aware import

    # Get original word count before revising
    OriginalWordCount = Writer.Statistics.GetWordCount(_Chapter)

    RevisionPrompt = ActivePrompts.CHAPTER_REVISION.format(
        _Chapter=_Chapter, _Feedback=_Feedback
    )

    # Gunakan _ChapterNum dan _TotalChapters yang diteruskan sebagai parameter
    _Logger.Log(
        f"Revising Chapter {_ChapterNum}/{_TotalChapters} (Stage 5, Iteration {_Iteration}/{Writer.Config.CHAPTER_MAX_REVISIONS})",
        5,
    )
    Messages = _History
    Messages.append(Interface.BuildUserQuery(RevisionPrompt))
    Messages, revision_obj, _ = Interface.SafeGeneratePydantic(  # Use Pydantic model
        _Logger,
        Messages,
        Writer.Config.CHAPTER_REVISION_WRITER_MODEL,
        ChapterOutput
    )
    # Use .text attribute from ChapterOutput
    SummaryText: str = revision_obj.text
    NewWordCount = Writer.Statistics.GetWordCount(SummaryText)
    # Gunakan _ChapterNum dan _TotalChapters yang diteruskan sebagai parameter
    _Logger.Log(
        f"Done Revising Chapter {_ChapterNum}/{_TotalChapters} (Stage 5, Iteration {_Iteration}/{Writer.Config.CHAPTER_MAX_REVISIONS}). Word Count Change: {OriginalWordCount} -> {NewWordCount}",
        5,
    )

    return SummaryText, Messages
