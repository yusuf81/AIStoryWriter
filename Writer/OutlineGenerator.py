import Writer.LLMEditor
import Writer.PrintUtils
import Writer.Config
import Writer.Outline.StoryElements
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
    Messages, _ = Interface.SafeGenerateText(  # Unpack tuple, ignore token usage
        _Logger, Messages, Writer.Config.INITIAL_OUTLINE_WRITER_MODEL
    )
    BaseContext: str = Interface.GetLastMessageText(Messages)
    _Logger.Log(f"Done Extracting Important Base Context", 4)

    # Generate Story Elements
    StoryElements: str = Writer.Outline.StoryElements.GenerateStoryElements(
        Interface, _Logger, _OutlinePrompt
    )

    # Now, Generate Initial Outline
    Prompt: str = ActivePrompts.INITIAL_OUTLINE_PROMPT.format(
        StoryElements=StoryElements, _OutlinePrompt=_OutlinePrompt
    )

    _Logger.Log(f"Generating Initial Outline", 4)
    Messages = [Interface.BuildUserQuery(Prompt)]
    Messages, _ = Interface.SafeGenerateText(  # Unpack tuple, ignore token usage
        _Logger,
        Messages,
        Writer.Config.INITIAL_OUTLINE_WRITER_MODEL,
        _MinWordCount=Writer.Config.MIN_WORDS_INITIAL_OUTLINE,  # Menggunakan Config
    )
    Outline: str = Interface.GetLastMessageText(Messages)
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
{BaseContext}

{StoryElements}

{Outline}
    """

    return FinalOutline, StoryElements, Outline, BaseContext


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
    )  # Tambahkan Max Revisions
    Messages = _History
    Messages.append(Interface.BuildUserQuery(RevisionPrompt))
    Messages, _ = Interface.SafeGenerateText(  # Unpack tuple, ignore token usage
        _Logger,
        Messages,
        Writer.Config.INITIAL_OUTLINE_WRITER_MODEL,
        _MinWordCount=Writer.Config.MIN_WORDS_REVISE_OUTLINE,  # Menggunakan Config
    )
    SummaryText: str = Interface.GetLastMessageText(Messages)
    _Logger.Log(
        f"Done Revising Outline (Iteration {_Iteration}/{Writer.Config.OUTLINE_MAX_REVISIONS})",
        2,
    )  # Tambahkan Max Revisions

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
    Messages, _ = Interface.SafeGenerateText(  # Unpack tuple, ignore token usage
        _Logger,
        Messages,
        Writer.Config.CHAPTER_OUTLINE_WRITER_MODEL,
        _MinWordCount=Writer.Config.MIN_WORDS_PER_CHAPTER_OUTLINE,  # Menggunakan Config
    )
    SummaryText: str = Interface.GetLastMessageText(Messages)
    # Modifikasi pesan log ini
    _Logger.Log(
        f"Done Generating Outline For Chapter {_Chapter} from {_TotalChapters}", 5
    )

    return SummaryText  # Hanya kembalikan teks outline
