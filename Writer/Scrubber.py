import Writer.PrintUtils
# import Writer.Prompts # Dihapus untuk pemuatan dinamis
import Writer.Config  # Add this
import Writer.Statistics  # Add this import


def ScrubNovel(Interface, _Logger, _Chapters: list, _TotalChapters: int):
    import Writer.Prompts as ActivePrompts # Ditambahkan untuk pemuatan dinamis

    EditedChapters = _Chapters

    for i in range(_TotalChapters):

        # Get original word count before scrubbing
        OriginalWordCount = Writer.Statistics.GetWordCount(EditedChapters[i])

        Prompt: str = ActivePrompts.CHAPTER_SCRUB_PROMPT.format(
            _Chapter=EditedChapters[i]
        )
        _Logger.Log(
            f"Prompting LLM To Perform Chapter {i+1}/{_TotalChapters} Scrubbing Edit", 5
        )
        Messages = []
        Messages.append(Interface.BuildUserQuery(Prompt))
        Messages, _ = Interface.SafeGenerateText(  # Unpack tuple, ignore token usage
            _Logger,
            Messages,
            Writer.Config.SCRUB_MODEL,
            _MinWordCount=Writer.Config.MIN_WORDS_SCRUB_CHAPTER,  # Menggunakan Config
        )
        _Logger.Log(f"Finished Chapter {i+1}/{_TotalChapters} Scrubbing Edit", 5)

        NewChapter = Interface.GetLastMessageText(Messages)
        EditedChapters[i] = NewChapter
        NewWordCount = Writer.Statistics.GetWordCount(NewChapter)
        _Logger.Log(
            f"Word Count Change (Scrub): Chapter {i+1} {OriginalWordCount} -> {NewWordCount}",
            3,
        )

    return EditedChapters
