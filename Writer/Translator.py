import Writer.PrintUtils
import Writer.Config
import Writer.Prompts
import Writer.Statistics  # Add this import


def TranslatePrompt(Interface, _Logger, _Prompt: str, _Language: str = "French"):

    Prompt: str = Writer.Prompts.TRANSLATE_PROMPT.format(
        _Prompt=_Prompt, _Language=_Language
    )
    _Logger.Log(f"Prompting LLM To Translate User Prompt", 5)
    Messages = []
    Messages.append(Interface.BuildUserQuery(Prompt))
    Messages, _ = Interface.SafeGenerateText(  # Unpack tuple, ignore token usage
        _Logger,
        Messages,
        Writer.Config.TRANSLATOR_MODEL,
        _MinWordCount=Writer.Config.MIN_WORDS_TRANSLATE_PROMPT,  # Menggunakan Config
    )
    _Logger.Log(f"Finished Prompt Translation", 5)

    return Interface.GetLastMessageText(Messages)


def TranslateNovel(
    Interface, _Logger, _Chapters: list, _TotalChapters: int, _Language: str = "French"
):

    EditedChapters = _Chapters

    for i in range(_TotalChapters):

        # Get original word count before translating
        OriginalWordCount = Writer.Statistics.GetWordCount(EditedChapters[i])

        Prompt: str = Writer.Prompts.CHAPTER_TRANSLATE_PROMPT.format(
            _Chapter=EditedChapters[i], _Language=_Language
        )
        _Logger.Log(
            f"Prompting LLM To Perform Chapter {i+1}/{_TotalChapters} Translation", 5
        )
        Messages = []
        Messages.append(Interface.BuildUserQuery(Prompt))
        Messages, _ = Interface.SafeGenerateText(  # Unpack tuple, ignore token usage
            _Logger, Messages, Writer.Config.TRANSLATOR_MODEL
        )
        _Logger.Log(f"Finished Chapter {i+1} Translation", 5)

        NewChapter = Interface.GetLastMessageText(Messages)
        EditedChapters[i] = NewChapter
        NewWordCount = Writer.Statistics.GetWordCount(NewChapter)
        _Logger.Log(
            f"Word Count Change (Translate): Chapter {i+1} {OriginalWordCount} -> {NewWordCount}",
            3,
        )

    return EditedChapters
