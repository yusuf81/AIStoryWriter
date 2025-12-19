import Writer.LLMEditor
import Writer.Config
from Writer.Models import OutlineOutput, StoryElements, BaseContext, ChapterOutlineOutput
# import Writer.Prompts # Dihapus untuk pemuatan dinamis


# We should probably do outline generation in stages, allowing us to go back and add foreshadowing, etc back to previous segments


def GenerateOutline(Interface, _Logger, _OutlinePrompt, _QualityThreshold: int = 85):
    from Writer.PromptsHelper import get_prompts
    ActivePrompts = get_prompts()  # Use language-aware import

    # Get any important info about the base prompt to pass along
    Prompt: str = ActivePrompts.GET_IMPORTANT_BASE_PROMPT_INFO.format(
        _Prompt=_OutlinePrompt
    )

    _Logger.Log("Extracting Important Base Context", 4)
    Messages = [Interface.BuildUserQuery(Prompt)]
    Messages, BaseContext_obj, _ = Interface.SafeGeneratePydantic(  # Use Pydantic model
        _Logger, Messages, Writer.Config.INITIAL_OUTLINE_WRITER_MODEL, BaseContext
    )
    BaseContext_str: str = BaseContext_obj.context
    _Logger.Log("Done Extracting Important Base Context", 4)

    # Generate Story Elements using Pydantic model
    from Writer.PromptsHelper import get_prompts
    ActivePrompts = get_prompts()

    Prompt: str = ActivePrompts.GENERATE_STORY_ELEMENTS.format(
        _OutlinePrompt=_OutlinePrompt
    )

    _Logger.Log("Generating Main Story Elements", 4)
    Messages = [Interface.BuildUserQuery(Prompt)]
    Messages, StoryElements_obj, _ = Interface.SafeGeneratePydantic(
        _Logger,
        Messages,
        Writer.Config.INITIAL_OUTLINE_WRITER_MODEL,
        StoryElements
    )

    # NEW: Use structured prompt generation from Pydantic model
    StoryElements_str = StoryElements_obj.to_prompt_string()

    _Logger.Log("Done Generating Main Story Elements", 4)

    # Now, Generate Initial Outline using Pydantic model
    Prompt: str = ActivePrompts.INITIAL_OUTLINE_PROMPT.format(
        StoryElements=StoryElements_str, _OutlinePrompt=_OutlinePrompt
    )

    _Logger.Log("Generating Initial Outline", 4)
    Messages = [Interface.BuildUserQuery(Prompt)]
    Messages, Outline_obj, _ = Interface.SafeGeneratePydantic(  # Use Pydantic model
        _Logger,
        Messages,
        Writer.Config.INITIAL_OUTLINE_WRITER_MODEL,
        OutlineOutput
    )
    # NEW: Use structured prompt generation from OutlineOutput model
    Outline: str = Outline_obj.to_prompt_string()
    _Logger.Log("Done Generating Initial Outline", 4)

    _Logger.Log("Entering Feedback/Revision Loop", 3)
    WritingHistory = Messages
    Rating: int = 0  # Seharusnya boolean
    Iterations: int = 0
    OutlineRevisionLoopExitReason = "Unknown"  # Tambahkan variabel ini
    while True:
        Iterations += 1
        Feedback = Writer.LLMEditor.GetFeedbackOnOutline(Interface, _Logger, Outline)
        Rating = Writer.LLMEditor.GetOutlineRating(Interface, _Logger, Outline)
        # Rating has been changed from a 0-100 int, to does it meet the standards (yes/no)?
        # Yes it has - the 0-100 int isn't actually good at all, LLM just returned a bunch of junk ratings

        if Iterations > Writer.Config.OUTLINE_MAX_REVISIONS:
            OutlineRevisionLoopExitReason = "Max Revisions Reached"  # Set alasan
            break
        if (Iterations > Writer.Config.OUTLINE_MIN_REVISIONS) and (Rating is True):
            OutlineRevisionLoopExitReason = "Quality Standard Met"  # Set alasan
            break

        # Perbaiki pemanggilan ReviseOutline agar sesuai dengan return value-nya (tuple)
        Outline, WritingHistory = ReviseOutline(
            Interface, _Logger, Outline, Feedback, WritingHistory, _Iteration=Iterations
        )  # Teruskan Iterations # Pastikan menangkap kedua nilai

    # Ganti pesan log ini:
    # _Logger.Log(f"Quality Standard Met, Exiting Feedback/Revision Loop", 4)

    # Dengan ini:
    _Logger.Log(
        f"{OutlineRevisionLoopExitReason}, Exiting Outline Feedback/Revision Loop after {Iterations}/{Writer.Config.OUTLINE_MAX_REVISIONS} iteration(s). Final Rating: {Rating}",
        4,
    )

    # Generate Final Outline
    FinalOutline: str = f"""
{BaseContext_str}

{StoryElements_str}

{Outline}
    """

    return FinalOutline, StoryElements_obj, Outline, BaseContext_str


def ReviseOutline(
    Interface, _Logger, _Outline, _Feedback, _History: list = [], _Iteration: int = 0
):  # Tambahkan _Iteration
    from Writer.PromptsHelper import get_prompts
    ActivePrompts = get_prompts()  # Use language-aware import

    RevisionPrompt: str = ActivePrompts.OUTLINE_REVISION_PROMPT.format(
        _Outline=_Outline, _Feedback=_Feedback
    )

    _Logger.Log(
        f"Revising Outline (Iteration {_Iteration}/{Writer.Config.OUTLINE_MAX_REVISIONS})",
        2,
    )
    Messages = _History
    Messages.append(Interface.BuildUserQuery(RevisionPrompt))
    Messages, Outline_obj, _ = Interface.SafeGeneratePydantic(  # Use Pydantic model
        _Logger,
        Messages,
        Writer.Config.INITIAL_OUTLINE_WRITER_MODEL,
        OutlineOutput
    )
    # Extract text from OutlineOutput model
    SummaryText: str = Outline_obj.title + "\n\n" + "\n\n".join(Outline_obj.chapters)
    _Logger.Log(
        f"Done Revising Outline (Iteration {_Iteration}/{Writer.Config.OUTLINE_MAX_REVISIONS})",
        2,
    )

    return SummaryText, Messages


def GeneratePerChapterOutline(
    Interface,
    _Logger,
    _Chapter,
    _TotalChapters: int,
    _Outline: str,
    # Parameter _History dihapus dari definisi fungsi
):  # Tambahkan _TotalChapters
    from Writer.PromptsHelper import get_prompts
    ActivePrompts = get_prompts()  # Use language-aware import

    RevisionPrompt: str = ActivePrompts.CHAPTER_OUTLINE_PROMPT.format(
        _Chapter=_Chapter, _Outline=_Outline
    )
    # Modifikasi pesan log ini
    _Logger.Log(f"Generating Outline For Chapter {_Chapter} from {_TotalChapters}", 5)
    Messages = []  # Inisialisasi Messages sebagai list kosong di dalam fungsi
    Messages.append(Interface.BuildUserQuery(RevisionPrompt))
    Messages, Chapter_obj, _ = Interface.SafeGeneratePydantic(  # Use ChapterOutlineOutput model
        _Logger,
        Messages,
        Writer.Config.CHAPTER_OUTLINE_WRITER_MODEL,
        ChapterOutlineOutput
    )
    # Extract full scenes content instead of just summary to avoid MegaOutline fallback
    if hasattr(Chapter_obj, 'scenes') and Chapter_obj.scenes:
        # Combine all scenes into comprehensive outline
        scenes_text = []
        for scene in Chapter_obj.scenes:
            if isinstance(scene, str):
                # Simple string scene
                scenes_text.append(scene)
            else:
                # EnhancedSceneOutline object - extract all fields
                scene_parts = []
                if hasattr(scene, 'title') and scene.title:
                    scene_parts.append(f"Scene: {scene.title}")
                if hasattr(scene, 'characters_and_setting') and scene.characters_and_setting:
                    scene_parts.append(f"Characters & Setting: {scene.characters_and_setting}")
                if hasattr(scene, 'conflict_and_tone') and scene.conflict_and_tone:
                    scene_parts.append(f"Conflict & Tone: {scene.conflict_and_tone}")
                if hasattr(scene, 'key_events') and scene.key_events:
                    scene_parts.append(f"Key Events: {scene.key_events}")
                if hasattr(scene, 'literary_devices') and scene.literary_devices:
                    scene_parts.append(f"Literary Devices: {scene.literary_devices}")
                if hasattr(scene, 'resolution') and scene.resolution:
                    scene_parts.append(f"Resolution: {scene.resolution}")

                # Join scene parts or use fallback
                scene_text = "\n".join(scene_parts) if scene_parts else str(scene)
                scenes_text.append(scene_text)

        SummaryText = "\n\n".join(scenes_text)
    else:
        # Fallback to outline_summary if scenes not available
        SummaryText = Chapter_obj.outline_summary  # Extract outline summary from ChapterOutlineOutput model
    # Modifikasi pesan log ini
    _Logger.Log(
        f"Done Generating Outline For Chapter {_Chapter} from {_TotalChapters}", 5
    )

    return SummaryText, Chapter_obj.chapter_title  # Return summary and title
