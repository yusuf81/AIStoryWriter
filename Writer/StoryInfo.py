from pydantic import BaseModel  # Ditambahkan
import Writer.Config
# import Writer.Prompts  # Dihapus untuk pemuatan dinamis
import json


# Definisikan Skema Pydantic
class StoryInfoSchema(BaseModel):
    Title: str
    Summary: str
    Tags: str
    OverallRating: int


def GetStoryInfo(
    Interface, _Logger, _Messages: list, _Model: str = None
):  # Tambahkan parameter _Model opsional
    import Writer.Prompts as ActivePrompts # Ditambahkan untuk pemuatan dinamis

    Prompt: str = ActivePrompts.STATS_PROMPT

    # Tentukan model yang akan digunakan: parameter _Model jika ada, jika tidak fallback ke Config
    ModelToUse = _Model if _Model is not None else Writer.Config.INFO_MODEL

    _Logger.Log(
        f"Prompting LLM ({ModelToUse}) To Generate Stats", 5
    )  # Log model yang digunakan
    Messages = _Messages
    Messages.append(Interface.BuildUserQuery(Prompt))
    # Menggunakan SafeGenerateJSON dengan skema dan model yang benar (ModelToUse)
    # Modify the call to SafeGenerateJSON to unpack three values
    # Instead of: Messages, JSONResponse = Interface.SafeGenerateJSON(...)
    Messages, JSONResponse, TokenUsage = Interface.SafeGenerateJSON(
        _Logger,
        Messages,
        ModelToUse,  # Gunakan model yang sudah ditentukan
        _FormatSchema=StoryInfoSchema.model_json_schema(),
    )
    _Logger.Log("Finished Getting Stats Feedback", 5)
    # Modify the return statement
    # Instead of: return JSONResponse
    return JSONResponse, TokenUsage  # Return JSON and tokens
