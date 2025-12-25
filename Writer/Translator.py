import Writer.Config
# Writer.Prompts akan diimpor sebagai ActivePrompts di dalam fungsi
import Writer.Statistics  # Add this import
from Writer.Models import ChapterOutput


def TranslatePrompt(Interface, _Logger, _Prompt: str, _SourceLanguage: str, TargetLang: str = "English"):  # Tambahkan TargetLang
    import Writer.Prompts as ActivePrompts  # Impor ulang untuk memastikan kita mendapatkan yang di-patch

    translation_prompt_template = ActivePrompts.TRANSLATE_PROMPT

    PromptFormatted: str = translation_prompt_template.format(
        _Prompt=_Prompt, _Language=_SourceLanguage, TargetLang=TargetLang
    )
    _Logger.Log(f"Prompting LLM To Translate User Prompt from {_SourceLanguage} to {TargetLang}", 5)
    Messages = []
    Messages.append(Interface.BuildUserQuery(PromptFormatted))
    Messages, Chapter_obj, _ = Interface.SafeGeneratePydantic(  # Use Pydantic model
        _Logger,
        Messages,
        Writer.Config.TRANSLATOR_MODEL,
        ChapterOutput
    )
    _Logger.Log(f"Finished Prompt Translation to {TargetLang}", 5)

    # Extract text from validated ChapterOutput model
    return Chapter_obj.text


def TranslateNovel(
    Interface, _Logger, _Chapters: list, _TotalChapters: int, _TargetLanguage: str, _SourceLanguage: str = "English"  # Tambahkan _SourceLanguage
):
    import Writer.Prompts as ActivePrompts  # Impor ulang untuk memastikan kita mendapatkan yang di-patch
    translation_chapter_prompt_template = ActivePrompts.CHAPTER_TRANSLATE_PROMPT

    EditedChapters = _Chapters[:]  # Salin list

    for i in range(_TotalChapters):

        # Get original word count before translating
        OriginalWordCount = Writer.Statistics.GetWordCount(EditedChapters[i])

        PromptFormatted: str = translation_chapter_prompt_template.format(
            _Chapter=EditedChapters[i], _Language=_TargetLanguage
        )
        _Logger.Log(
            f"Prompting LLM To Perform Chapter {i+1}/{_TotalChapters} Translation from {_SourceLanguage} to {_TargetLanguage}", 5
        )
        Messages = []
        Messages.append(Interface.BuildUserQuery(PromptFormatted))
        Messages, Chapter_obj, _ = Interface.SafeGeneratePydantic(  # Use Pydantic model
            _Logger, Messages, Writer.Config.TRANSLATOR_MODEL, ChapterOutput
        )
        _Logger.Log(f"Finished Chapter {i+1} Translation to {_TargetLanguage}", 5)

        # Extract text from validated ChapterOutput model
        NewChapter = Chapter_obj.text
        EditedChapters[i] = NewChapter
        NewWordCount = Writer.Statistics.GetWordCount(NewChapter)
        _Logger.Log(
            f"Word Count Change (Translate): Chapter {i+1} {OriginalWordCount} -> {NewWordCount}",
            3,
        )

    return EditedChapters
