from pydantic import BaseModel # Ditambahkan
import Writer.Config
import json

# Definisikan Skema Pydantic
class StoryInfoSchema(BaseModel):
    Title: str
    Summary: str
    Tags: str
    OverallRating: int


def GetStoryInfo(Interface, _Logger, _Messages: list):

    Prompt: str = Writer.Prompts.STATS_PROMPT

    _Logger.Log("Prompting LLM To Generate Stats", 5)
    Messages = _Messages
    Messages.append(Interface.BuildUserQuery(Prompt))
    # Menggunakan SafeGenerateJSON dengan skema
    Messages, JSONResponse = Interface.SafeGenerateJSON(
        _Logger, Messages, Writer.Config.INFO_MODEL, _FormatSchema=StoryInfoSchema.model_json_schema()
    )
    _Logger.Log("Finished Getting Stats Feedback", 5)
    return JSONResponse
