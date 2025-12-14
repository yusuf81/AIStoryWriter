import Writer.Config
from Writer.Models import SceneOutlineList
# import Writer.Prompts # Dihapus untuk pemuatan dinamis


def ChapterOutlineToScenes(
    Interface,
    _Logger,
    _ChapterNum: int,
    _TotalChapters: int,
    _ThisChapterOutline: str,
    _Outline: str,
    _BaseContext: str = "",
):  # Added _ChapterNum, _TotalChapters, renamed _ThisChapter
    import Writer.Prompts as ActivePrompts  # Ditambahkan untuk pemuatan dinamis

    # We're now going to convert the chapter outline into a more detailed outline for each scene.
    # The scene by scene outline will be returned, JSONified, and then later converted into fully written scenes
    # These will then be concatenated into chapters and revised

    _Logger.Log(f"Splitting Chapter {_ChapterNum}/{_TotalChapters} Into Scenes", 2)
    MesssageHistory: list = []
    MesssageHistory.append(
        Interface.BuildSystemQuery(ActivePrompts.DEFAULT_SYSTEM_PROMPT)
    )
    MesssageHistory.append(
        Interface.BuildUserQuery(
            ActivePrompts.CHAPTER_TO_SCENES.format(
                _ThisChapter=_ThisChapterOutline,
                _Outline=_Outline,  # Use renamed variable
            )
        )
    )

    Response, SceneList_obj, _ = Interface.SafeGeneratePydantic(  # Use wrapper model for multiple scenes
        _Logger,
        MesssageHistory,
        Writer.Config.CHAPTER_OUTLINE_WRITER_MODEL,
        SceneOutlineList
    )
    _Logger.Log(
        f"Finished Splitting Chapter {_ChapterNum}/{_TotalChapters} Into Scenes", 5
    )

    # Return list of scene actions directly (no backward compatibility)
    return [scene.action for scene in SceneList_obj.scenes]
