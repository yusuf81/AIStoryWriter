from pydantic import BaseModel
from typing import List
import Writer.Config
# import Writer.Prompts  # Dihapus untuk pemuatan dinamis


# Definisikan Skema Pydantic
class SceneListSchema(BaseModel):
    scenes: List[str]


def _deduplicate_scenes(scenes: List[str]) -> List[str]:
    """
    Remove duplicate scenes while preserving order.
    Uses fuzzy matching to detect similar-but-not-identical duplicates.

    Args:
        scenes: List of scene descriptions

    Returns:
        List with duplicates removed
    """
    if not scenes:
        return scenes

    unique_scenes = []
    seen = set()

    for scene in scenes:
        # Normalize by stripping and lowercasing for exact duplicate check
        normalized = scene.strip().lower()

        # Check for exact duplicate
        if normalized not in seen:
            # Additional fuzzy check for near-duplicates
            is_duplicate = False
            for existing_scene in unique_scenes:
                # Simple similarity check: if most words are the same, consider it a duplicate
                words1 = set(normalized.split())
                words2 = set(existing_scene.lower().split())

                # If both have more than 5 words and share 80%+ similarity, consider duplicate
                if len(words1) > 5 and len(words2) > 5:
                    intersection = words1.intersection(words2)
                    union = words1.union(words2)
                    similarity = len(intersection) / len(union) if union else 0

                    if similarity > 0.8:
                        is_duplicate = True
                        break

            if not is_duplicate:
                unique_scenes.append(scene)
                seen.add(normalized)

    return unique_scenes


def ScenesToJSON(
    Interface, _Logger, _ChapterNum: int, _TotalChapters: int, _Scenes: str
):  # Added chapter context
    import Writer.Prompts as ActivePrompts  # Ditambahkan untuk pemuatan dinamis

    # This function converts the given scene list (from markdown format, to a specified JSON format).

    _Logger.Log(
        f"Starting ChapterScenes->JSON for Chapter {_ChapterNum}/{_TotalChapters}", 2
    )
    MesssageHistory: list = []
    MesssageHistory.append(
        Interface.BuildSystemQuery(ActivePrompts.DEFAULT_SYSTEM_PROMPT)
    )
    MesssageHistory.append(
        Interface.BuildUserQuery(ActivePrompts.SCENES_TO_JSON.format(_Scenes=_Scenes))
    )

    # Menggunakan SafeGenerateJSON dengan skema
    # Unpack 3 values, ignore messages and tokens
    _, SceneJSONResponse, _ = (
        Interface.SafeGenerateJSON(  # Unpack 3 values, ignore messages and tokens
            # Response, SceneJSONResponse = Interface.SafeGenerateJSON( # Baris lama
            _Logger,
            MesssageHistory,
            Writer.Config.CHECKER_MODEL,
            _FormatSchema=SceneListSchema.model_json_schema(),
        )
    )
    SceneList = SceneJSONResponse["scenes"]  # Ekstrak list dari dictionary

    # Optimize: Remove duplicate scenes
    SceneList = _deduplicate_scenes(SceneList)

    _Logger.Log(
        f"Finished ChapterScenes->JSON for Chapter {_ChapterNum}/{_TotalChapters} ({len(SceneList)} Scenes Found after deduplication)",
        5,
    )

    return SceneList
