import Writer.PrintUtils
import Writer.Config
import Writer.Prompts
import Writer.Statistics # Add this import


def EditNovel(Interface, _Logger, _Chapters: list, _Outline: str, _TotalChapters: int):

    EditedChapters = _Chapters

    for i in range(1, _TotalChapters + 1):

        NovelText: str = ""
        for Chapter in EditedChapters:
            NovelText += Chapter

        # Get original word count before editing
        OriginalWordCount = Writer.Statistics.GetWordCount(EditedChapters[i - 1])

        Prompt: str = Writer.Prompts.CHAPTER_EDIT_PROMPT.format(
            _Outline=_Outline, NovelText=NovelText, i=i
        )

        _Logger.Log(
            f"Prompting LLM To Perform Chapter {i} Second Pass In-Place Edit", 5
        )
        Messages = []
        Messages.append(Interface.BuildUserQuery(Prompt))
        Messages = Interface.SafeGenerateText(
            _Logger,
            Messages,
            Writer.Config.CHAPTER_STAGE4_WRITER_MODEL,  # Menggunakan model Stage 4 untuk edit pass
            _MinWordCount=Writer.Config.MIN_WORDS_EDIT_NOVEL,  # Menggunakan Config
        )
        _Logger.Log(f"Finished Chapter {i} Second Pass In-Place Edit", 5)

        NewChapter = Interface.GetLastMessageText(Messages)
        EditedChapters[i - 1] = NewChapter # Use 0-based index
        NewWordCount = Writer.Statistics.GetWordCount(NewChapter)
        _Logger.Log(f"Word Count Change (Edit): Chapter {i} {OriginalWordCount} -> {NewWordCount}", 3)

    return EditedChapters
