from pydantic import BaseModel  # Ditambahkan
import Writer.Config
# import Writer.Prompts # Dihapus untuk pemuatan dinamis

import re
import json


# Definisikan Skema Pydantic
class ChapterCountSchema(BaseModel):
    TotalChapters: int


def LLMCountChapters(Interface, _Logger, _Summary):
    import Writer.Prompts as ActivePrompts # Ditambahkan untuk pemuatan dinamis

    Prompt = ActivePrompts.CHAPTER_COUNT_PROMPT.format(_Summary=_Summary)

    _Logger.Log("Prompting LLM To Get ChapterCount JSON", 5)
    Messages = []
    Messages.append(Interface.BuildUserQuery(Prompt))

    # Menggunakan SafeGenerateJSON dengan skema
    # Unpack 3 values, ignore messages and tokens
    _, JSONResponse, _ = Interface.SafeGenerateJSON(
        _Logger,
        Messages,
        Writer.Config.EVAL_MODEL,
        _FormatSchema=ChapterCountSchema.model_json_schema(),
    )
    TotalChapters = JSONResponse["TotalChapters"]
    _Logger.Log(
        f"Finished Getting ChapterCount JSON. Found {TotalChapters} chapters.", 5
    )
    return TotalChapters
