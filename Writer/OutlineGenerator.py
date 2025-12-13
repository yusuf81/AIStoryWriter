import Writer.LLMEditor
import Writer.PrintUtils
import Writer.Config
from Writer.Models import OutlineOutput, StoryElements, BaseContext, ChapterOutput
# import Writer.Prompts # Dihapus untuk pemuatan dinamis


# We should probably do outline generation in stages, allowing us to go back and add foreshadowing, etc back to previous segments


def GenerateOutline(Interface, _Logger, _OutlinePrompt, _QualityThreshold: int = 85):
    from Writer.PromptsHelper import get_prompts
    ActivePrompts = get_prompts() # Use language-aware import

    # Get any important info about the base prompt to pass along
    Prompt: str = ActivePrompts.GET_IMPORTANT_BASE_PROMPT_INFO.format(
        _Prompt=_OutlinePrompt
    )

    _Logger.Log(f"Extracting Important Base Context", 4)
    Messages = [Interface.BuildUserQuery(Prompt)]
    Messages, BaseContext_obj, _ = Interface.SafeGeneratePydantic(  # Use Pydantic model
        _Logger, Messages, Writer.Config.INITIAL_OUTLINE_WRITER_MODEL, BaseContext
    )
    BaseContext_str: str = BaseContext_obj.context
    _Logger.Log(f"Done Extracting Important Base Context", 4)

    # Generate Story Elements using Pydantic model
    from Writer.PromptsHelper import get_prompts
    ActivePrompts = get_prompts()

    Prompt: str = ActivePrompts.GENERATE_STORY_ELEMENTS.format(
        _OutlinePrompt=_OutlinePrompt
    )

    _Logger.Log(f"Generating Main Story Elements", 4)
    Messages = [Interface.BuildUserQuery(Prompt)]
    Messages, StoryElements_obj, _ = Interface.SafeGeneratePydantic(
        _Logger,
        Messages,
        Writer.Config.INITIAL_OUTLINE_WRITER_MODEL,
        StoryElements
    )

    # Convert StoryElements object to string for use in prompts
    StoryElements_str = f"""Characters:
{chr(10).join([f"- {name}: {desc}" for name, desc in StoryElements_obj.characters.items()])}

Locations:
{chr(10).join([f"- {name}: {desc}" for name, desc in StoryElements_obj.locations.items()])}

Themes: {', '.join(StoryElements_obj.themes)}

Conflict: {StoryElements_obj.conflict or 'Not specified'}
Resolution: {StoryElements_obj.resolution or 'Not specified'}"""

    _Logger.Log(f"Done Generating Main Story Elements", 4)

    # Now, Generate Initial Outline using Pydantic model
    Prompt: str = ActivePrompts.INITIAL_OUTLINE_PROMPT.format(
        StoryElements=StoryElements_str, _OutlinePrompt=_OutlinePrompt
    )

    _Logger.Log(f"Generating Initial Outline", 4)
    Messages = [Interface.BuildUserQuery(Prompt)]
    Messages, Outline_obj, _ = Interface.SafeGeneratePydantic(  # Use Pydantic model
        _Logger,
        Messages,
        Writer.Config.INITIAL_OUTLINE_WRITER_MODEL,
        OutlineOutput
    )
    # Extract text from OutlineOutput model
    Outline: str = Outline_obj.title + "\n\n" + "\n\n".join(Outline_obj.chapters)
    _Logger.Log(f"Done Generating Initial Outline", 4)

    _Logger.Log(f"Entering Feedback/Revision Loop", 3)
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
        if (Iterations > Writer.Config.OUTLINE_MIN_REVISIONS) and (Rating == True):
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
    ActivePrompts = get_prompts() # Use language-aware import

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
    ActivePrompts = get_prompts() # Use language-aware import

    RevisionPrompt: str = ActivePrompts.CHAPTER_OUTLINE_PROMPT.format(
        _Chapter=_Chapter, _Outline=_Outline
    )
    # Modifikasi pesan log ini
    _Logger.Log(f"Generating Outline For Chapter {_Chapter} from {_TotalChapters}", 5)
    Messages = []  # Inisialisasi Messages sebagai list kosong di dalam fungsi
    Messages.append(Interface.BuildUserQuery(RevisionPrompt))
    Messages, Chapter_obj, _ = Interface.SafeGeneratePydantic(  # Use Pydantic model
        _Logger,
        Messages,
        Writer.Config.CHAPTER_OUTLINE_WRITER_MODEL,
        ChapterOutput
    )
    SummaryText: str = Chapter_obj.text  # Extract text from ChapterOutput model (minimum 100 chars)
    # Modifikasi pesan log ini
    _Logger.Log(
        f"Done Generating Outline For Chapter {_Chapter} from {_TotalChapters}", 5
    )

    return SummaryText  # Hanya kembalikan teks outline
