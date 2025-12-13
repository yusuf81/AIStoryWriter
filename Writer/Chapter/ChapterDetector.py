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

    # Use SafeGeneratePydantic with existing ChapterCountSchema (already a Pydantic model)
    _, count_obj, _ = Interface.SafeGeneratePydantic(
        _Logger,
        Messages,
        Writer.Config.EVAL_MODEL,
        ChapterCountSchema
    )
    # Access field via Pydantic object attribute instead of dict key
    TotalChapters = count_obj.TotalChapters
    _Logger.Log(
        f"Finished Getting ChapterCount JSON. Found {TotalChapters} chapters.", 5
    )
    return TotalChapters
