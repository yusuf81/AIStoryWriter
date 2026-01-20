# import Writer.Prompts # Dihapus untuk pemuatan dinamis
import Writer.Config  # Add this
import Writer.Statistics  # Add this import
from Writer.Models import ChapterOutput


def ScrubNovel(Interface, _Logger, _Chapters: list, _TotalChapters: int):
    import Writer.Prompts as ActivePrompts  # Ditambahkan untuk pemuatan dinamis

    EditedChapters = _Chapters

    for i in range(_TotalChapters):

        # Save original chapter for potential revert
        OriginalChapter = EditedChapters[i]

        # Get original word count before scrubbing
        OriginalWordCount = Writer.Statistics.GetWordCount(OriginalChapter)

        Prompt: str = ActivePrompts.CHAPTER_SCRUB_PROMPT.format(
            _Chapter=OriginalChapter
        )
        _Logger.Log(
            f"Prompting LLM To Perform Chapter {i+1}/{_TotalChapters} Scrubbing Edit", 5
        )
        Messages = []
        # FIX: Ensure proper role alternation for vLLM (OpenAI-compatible API)
        # Start with system message, then user message
        Messages.append(Interface.BuildSystemQuery(Interface._get_text('default_system_message')))
        Messages.append(Interface.BuildUserQuery(Prompt))
        Messages, Chapter_obj, _ = Interface.SafeGeneratePydantic(  # Use Pydantic model
            _Logger,
            Messages,
            Writer.Config.SCRUB_MODEL,
            ChapterOutput
        )
        _Logger.Log(f"Finished Chapter {i+1}/{_TotalChapters} Scrubbing Edit", 5)

        # Extract text from validated ChapterOutput model
        NewChapter = Chapter_obj.text
        NewWordCount = Writer.Statistics.GetWordCount(NewChapter)

        # Validate content shrinkage
        from Writer.ContentValidator import validate_content_shrinkage
        shrinkage_valid, _ = validate_content_shrinkage(
            OriginalChapter, NewChapter, _Logger, f"Scrubber Chapter {i+1}"
        )
        if not shrinkage_valid:
            _Logger.Log(f"Scrubber content shrinkage detected for Chapter {i+1}, keeping original", 5)
            NewChapter = OriginalChapter  # Revert to original
            NewWordCount = OriginalWordCount

        EditedChapters[i] = NewChapter
        _Logger.Log(
            f"Word Count Change (Scrub): Chapter {i+1} {OriginalWordCount} -> {NewWordCount}",
            3,
        )

    return EditedChapters
