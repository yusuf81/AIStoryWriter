from pydantic import BaseModel  # Ditambahkan
# import Writer.Prompts # Dihapus untuk pemuatan dinamis
import Writer.Config as Config

from Writer.Models import ReviewOutput


# Definisikan Skema Pydantic
class OutlineCompleteSchema(BaseModel):
    IsComplete: bool


class ChapterCompleteSchema(BaseModel):
    IsComplete: bool


def GetFeedbackOnOutline(Interface, _Logger, _Outline: str):
    import Writer.Prompts as ActivePrompts # Ditambahkan untuk pemuatan dinamis

    # Setup Initial Context History
    History = []
    History.append(Interface.BuildSystemQuery(ActivePrompts.CRITIC_OUTLINE_INTRO))

    StartingPrompt: str = ActivePrompts.CRITIC_OUTLINE_PROMPT.format(_Outline=_Outline)

    _Logger.Log("Prompting LLM To Critique Outline", 5)
    History.append(Interface.BuildUserQuery(StartingPrompt))
    History, Review_obj, _ = Interface.SafeGeneratePydantic(  # Use ReviewOutput model
        _Logger,
        History,
        Config.REVISION_MODEL,
        ReviewOutput
    )
    _Logger.Log("Finished Getting Outline Feedback", 5)

    # Extract feedback from validated ReviewOutput model
    return Review_obj.feedback


def GetOutlineRating(
    Interface,
    _Logger,
    _Outline: str,
):
    import Writer.Prompts as ActivePrompts # Ditambahkan untuk pemuatan dinamis

    # Setup Initial Context History
    History = []
    History.append(Interface.BuildSystemQuery(ActivePrompts.OUTLINE_COMPLETE_INTRO))

    StartingPrompt: str = ActivePrompts.OUTLINE_COMPLETE_PROMPT.format(
        _Outline=_Outline
    )

    _Logger.Log("Prompting LLM To Get Review JSON", 5)

    History.append(Interface.BuildUserQuery(StartingPrompt))
    # Use SafeGeneratePydantic with existing OutlineCompleteSchema (already a Pydantic model)
    _, review_obj, _ = Interface.SafeGeneratePydantic(
        _Logger,
        History,
        Config.EVAL_MODEL,
        OutlineCompleteSchema
    )
    # Access field via Pydantic object attribute instead of dict key
    Rating = review_obj.IsComplete
    _Logger.Log(f"Editor Determined IsComplete: {Rating}", 5)
    return Rating


def GetFeedbackOnChapter(Interface, _Logger, _Chapter: str, _Outline: str):
    import Writer.Prompts as ActivePrompts # Ditambahkan untuk pemuatan dinamis

    # Setup Initial Context History
    History = []
    History.append(Interface.BuildSystemQuery(ActivePrompts.CRITIC_CHAPTER_INTRO))

    # Disabled seeing the outline too.
    StartingPrompt: str = ActivePrompts.CRITIC_CHAPTER_PROMPT.format(
        _Chapter=_Chapter, _Outline=_Outline
    )

    _Logger.Log("Prompting LLM To Critique Chapter", 5)
    History.append(Interface.BuildUserQuery(StartingPrompt))
    Messages, Review_obj, _ = Interface.SafeGeneratePydantic(  # Use ReviewOutput model
        _Logger, History, Config.REVISION_MODEL, ReviewOutput
    )
    _Logger.Log("Finished Getting Chapter Feedback", 5)

    # Extract feedback from validated ReviewOutput model
    return Review_obj.feedback


# Switch this to iscomplete true/false (similar to outline)
def GetChapterRating(Interface, _Logger, _Chapter: str):
    import Writer.Prompts as ActivePrompts # Ditambahkan untuk pemuatan dinamis

    # Setup Initial Context History
    History = []
    History.append(Interface.BuildSystemQuery(ActivePrompts.CHAPTER_COMPLETE_INTRO))

    StartingPrompt: str = ActivePrompts.CHAPTER_COMPLETE_PROMPT.format(
        _Chapter=_Chapter
    )

    _Logger.Log("Prompting LLM To Get Review JSON", 5)
    History.append(Interface.BuildUserQuery(StartingPrompt))
    # Use SafeGeneratePydantic with existing ChapterCompleteSchema (already a Pydantic model)
    _, review_obj, _ = Interface.SafeGeneratePydantic(
        _Logger,
        History,
        Config.EVAL_MODEL,
        ChapterCompleteSchema
    )
    # Access field via Pydantic object attribute instead of dict key
    Rating = review_obj.IsComplete
    _Logger.Log(f"Editor Determined IsComplete: {Rating}", 5)
    return Rating
