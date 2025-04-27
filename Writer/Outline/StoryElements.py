import Writer.LLMEditor
import Writer.PrintUtils
import Writer.Config
import Writer.Prompts


def GenerateStoryElements(Interface, _Logger, _OutlinePrompt):

    Prompt: str = Writer.Prompts.GENERATE_STORY_ELEMENTS.format(
        _OutlinePrompt=_OutlinePrompt
    )  # Menggunakan prompt terpusat

    # Generate Initial Story Elements
    _Logger.Log(f"Generating Main Story Elements", 4)
    Messages = [Interface.BuildUserQuery(Prompt)]
    Messages = Interface.SafeGenerateText(
        _Logger,
        Messages,
        Writer.Config.INITIAL_OUTLINE_WRITER_MODEL,
        _MinWordCount=Writer.Config.MIN_WORDS_STORY_ELEMENTS,  # Menggunakan Config
    )
    Elements: str = Interface.GetLastMessageText(Messages)
    _Logger.Log(f"Done Generating Main Story Elements", 4)

    return Elements
