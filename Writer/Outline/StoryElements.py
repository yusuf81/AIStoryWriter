import Writer.LLMEditor
import Writer.PrintUtils
import Writer.Config
# import Writer.Prompts # Dihapus untuk pemuatan dinamis


def GenerateStoryElements(Interface, _Logger, _OutlinePrompt):
    import Writer.Prompts as ActivePrompts # Ditambahkan untuk pemuatan dinamis

    Prompt: str = ActivePrompts.GENERATE_STORY_ELEMENTS.format(
        _OutlinePrompt=_OutlinePrompt
    )  # Menggunakan prompt terpusat

    # Generate Initial Story Elements
    _Logger.Log(f"Generating Main Story Elements", 4)
    Messages = [Interface.BuildUserQuery(Prompt)]
    Messages, _ = Interface.SafeGenerateText(  # Unpack tuple, ignore token usage
        _Logger,
        Messages,
        Writer.Config.INITIAL_OUTLINE_WRITER_MODEL,
        _MinWordCount=Writer.Config.MIN_WORDS_STORY_ELEMENTS,  # Menggunakan Config
    )
    Elements: str = Interface.GetLastMessageText(Messages)
    _Logger.Log(f"Done Generating Main Story Elements", 4)

    return Elements
