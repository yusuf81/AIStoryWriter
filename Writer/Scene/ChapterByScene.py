import Writer.Scene.ChapterOutlineToScenes
import Writer.Scene.SceneOutlineToScene
from Writer.Scene.ScenesToJSON import deduplicate_scene_objects


def ChapterByScene(
    Interface,
    _Logger,
    _ChapterNum: int,
    _TotalChapters: int,
    _ThisChapterOutline: str,
    _Outline: str,
    _BaseContext: str = "",
):  # Added _ChapterNum, _TotalChapters, renamed _ThisChapter

    # This function calls all other scene-by-scene generation functions and creates a full chapter based on the new scene pipeline.

    _Logger.Log(
        f"Starting Scene-By-Scene Generation Pipeline for Chapter {_ChapterNum}/{_TotalChapters}",
        2,
    )

    # Get full SceneOutline objects (not strings) - preserves metadata
    SceneOutlineObjects = Writer.Scene.ChapterOutlineToScenes.ChapterOutlineToScenes(
        Interface,
        _Logger,
        _ChapterNum,
        _TotalChapters,
        _ThisChapterOutline,
        _Outline,
        _BaseContext=_BaseContext,
    )

    # Deduplicate WITHOUT LLM call using utility function
    SceneOutlineList = deduplicate_scene_objects(SceneOutlineObjects)

    # Now we iterate through each scene one at a time and write it, then add it to this rough chapter, which is then returned for further editing
    RoughChapter: str = ""
    TotalScenes = len(SceneOutlineList)  # Get total scenes after deduplication
    for idx, SceneOutlineObj in enumerate(SceneOutlineList):  # SceneOutlineObj is SceneOutline object
        SceneNum = idx + 1  # 1-based index for logging
        RoughChapter += Writer.Scene.SceneOutlineToScene.SceneOutlineToScene(
            Interface,
            _Logger,
            SceneNum,
            TotalScenes,
            SceneOutlineObj,  # Pass SceneOutline object (not string) with all metadata
            _Outline,
            _BaseContext,
        )

    _Logger.Log(
        f"Finished Scene-By-Scene Generation Pipeline for Chapter {_ChapterNum}/{_TotalChapters}",
        2,
    )

    return RoughChapter
