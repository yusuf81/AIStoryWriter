from pydantic import BaseModel  # Ditambahkan
from typing import List  # Ditambahkan
import Writer.LLMEditor
import Writer.PrintUtils
import Writer.Config
import Writer.Chapter.ChapterGenSummaryCheck
import Writer.Prompts


# Definisikan Skema Pydantic
class SceneListSchema(BaseModel):
    scenes: List[str]


def ScenesToJSON(Interface, _Logger, _ChapterNum: int, _TotalChapters: int, _Scenes: str): # Added chapter context

    # This function converts the given scene list (from markdown format, to a specified JSON format).

    _Logger.Log(f"Starting ChapterScenes->JSON for Chapter {_ChapterNum}/{_TotalChapters}", 2)
    MesssageHistory: list = []
    MesssageHistory.append(
        Interface.BuildSystemQuery(Writer.Prompts.DEFAULT_SYSTEM_PROMPT)
    )
    MesssageHistory.append(
        Interface.BuildUserQuery(Writer.Prompts.SCENES_TO_JSON.format(_Scenes=_Scenes))
    )

    # Menggunakan SafeGenerateJSON dengan skema
    Response, SceneJSONResponse = Interface.SafeGenerateJSON(
        _Logger,
        MesssageHistory,
        Writer.Config.CHECKER_MODEL,
        _FormatSchema=SceneListSchema.model_json_schema(),
    )
    SceneList = SceneJSONResponse["scenes"]  # Ekstrak list dari dictionary
    _Logger.Log(f"Finished ChapterScenes->JSON for Chapter {_ChapterNum}/{_TotalChapters} ({len(SceneList)} Scenes Found)", 5)

    return SceneList
