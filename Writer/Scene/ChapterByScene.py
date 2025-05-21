import Writer.LLMEditor
import Writer.PrintUtils
import Writer.Config
import Writer.Chapter.ChapterGenSummaryCheck
import Writer.Prompts
import Writer.Scene.ChapterOutlineToScenes
import Writer.Scene.ScenesToJSON
import Writer.Scene.SceneOutlineToScene


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

    SceneBySceneOutline = Writer.Scene.ChapterOutlineToScenes.ChapterOutlineToScenes(
        Interface,
        _Logger,
        _ChapterNum,
        _TotalChapters,
        _ThisChapterOutline,
        _Outline,
        _BaseContext=_BaseContext,  # Pass chapter info
    )

    SceneJSONList = Writer.Scene.ScenesToJSON.ScenesToJSON(
        Interface,
        _Logger,
        _ChapterNum,
        _TotalChapters,
        SceneBySceneOutline,  # Pass chapter context
    )

    # Now we iterate through each scene one at a time and write it, then add it to this rough chapter, which is then returned for further editing
    RoughChapter: str = ""
    TotalScenes = len(SceneJSONList)  # Get total scenes
    for idx, SceneOutline in enumerate(SceneJSONList):  # Use enumerate for index
        SceneNum = idx + 1  # 1-based index for logging
        RoughChapter += Writer.Scene.SceneOutlineToScene.SceneOutlineToScene(
            Interface,
            _Logger,
            SceneNum,
            TotalScenes,
            SceneOutline,
            _Outline,
            _BaseContext,  # Pass scene info
        )

    _Logger.Log(
        f"Finished Scene-By-Scene Generation Pipeline for Chapter {_ChapterNum}/{_TotalChapters}",
        2,
    )

    return RoughChapter
