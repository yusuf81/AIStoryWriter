from pydantic import BaseModel  # Ditambahkan
import Writer.PrintUtils
import Writer.Prompts

import json


# Definisikan Skema Pydantic
class OutlineCompleteSchema(BaseModel):
    IsComplete: bool


class ChapterCompleteSchema(BaseModel):
    IsComplete: bool


def GetFeedbackOnOutline(Interface, _Logger, _Outline: str):

    # Setup Initial Context History
    History = []
    History.append(Interface.BuildSystemQuery(Writer.Prompts.CRITIC_OUTLINE_INTRO))

    StartingPrompt: str = Writer.Prompts.CRITIC_OUTLINE_PROMPT.format(_Outline=_Outline)

    _Logger.Log("Prompting LLM To Critique Outline", 5)
    History.append(Interface.BuildUserQuery(StartingPrompt))
    History, _ = Interface.SafeGenerateText( # Unpack tuple, ignore token usage
        _Logger,
        History,
        Writer.Config.REVISION_MODEL,
        _MinWordCount=Writer.Config.MIN_WORDS_OUTLINE_FEEDBACK,  # Menggunakan Config
    )
    _Logger.Log("Finished Getting Outline Feedback", 5)

    return Interface.GetLastMessageText(History)


def GetOutlineRating(
    Interface,
    _Logger,
    _Outline: str,
):

    # Setup Initial Context History
    History = []
    History.append(Interface.BuildSystemQuery(Writer.Prompts.OUTLINE_COMPLETE_INTRO))

    StartingPrompt: str = Writer.Prompts.OUTLINE_COMPLETE_PROMPT.format(
        _Outline=_Outline
    )

    _Logger.Log("Prompting LLM To Get Review JSON", 5)

    History.append(Interface.BuildUserQuery(StartingPrompt))
    # Menggunakan SafeGenerateJSON dengan skema
    # Unpack 3 values, ignore messages and tokens
    _, JSONResponse, _ = Interface.SafeGenerateJSON(
        _Logger,
        History, # Pass the current history
        Writer.Config.EVAL_MODEL,
        _FormatSchema=OutlineCompleteSchema.model_json_schema(),
    )
    Rating = JSONResponse["IsComplete"]
    _Logger.Log(f"Editor Determined IsComplete: {Rating}", 5)
    return Rating


def GetFeedbackOnChapter(Interface, _Logger, _Chapter: str, _Outline: str):

    # Setup Initial Context History
    History = []
    History.append(Interface.BuildSystemQuery(Writer.Prompts.CRITIC_CHAPTER_INTRO))

    # Disabled seeing the outline too.
    StartingPrompt: str = Writer.Prompts.CRITIC_CHAPTER_PROMPT.format(
        _Chapter=_Chapter, _Outline=_Outline
    )

    _Logger.Log("Prompting LLM To Critique Chapter", 5)
    History.append(Interface.BuildUserQuery(StartingPrompt))
    Messages, _ = Interface.SafeGenerateText( # Unpack tuple, ignore token usage
        _Logger, History, Writer.Config.REVISION_MODEL
    )
    _Logger.Log("Finished Getting Chapter Feedback", 5)

    return Interface.GetLastMessageText(Messages)


# Switch this to iscomplete true/false (similar to outline)
def GetChapterRating(Interface, _Logger, _Chapter: str):

    # Setup Initial Context History
    History = []
    History.append(Interface.BuildSystemQuery(Writer.Prompts.CHAPTER_COMPLETE_INTRO))

    StartingPrompt: str = Writer.Prompts.CHAPTER_COMPLETE_PROMPT.format(
        _Chapter=_Chapter
    )

    _Logger.Log("Prompting LLM To Get Review JSON", 5)
    History.append(Interface.BuildUserQuery(StartingPrompt))
    # Menggunakan SafeGenerateJSON dengan skema
    History, JSONResponse = Interface.SafeGenerateJSON(
        _Logger,
        History,
        Writer.Config.EVAL_MODEL,
        _FormatSchema=ChapterCompleteSchema.model_json_schema(),
    )
    Rating = JSONResponse["IsComplete"]
    _Logger.Log(f"Editor Determined IsComplete: {Rating}", 5)
    return Rating
