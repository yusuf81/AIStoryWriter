import Writer.LLMEditor
import Writer.PrintUtils
import Writer.Config
import Writer.Chapter.ChapterGenSummaryCheck
from Writer.Models import SceneOutline
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
    import Writer.Prompts as ActivePrompts # Ditambahkan untuk pemuatan dinamis

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

    Response, Scene_obj, _ = Interface.SafeGeneratePydantic(  # Use Pydantic model
        _Logger,
        MesssageHistory,
        Writer.Config.CHAPTER_OUTLINE_WRITER_MODEL,
        SceneOutline
    )
    _Logger.Log(
        f"Finished Splitting Chapter {_ChapterNum}/{_TotalChapters} Into Scenes", 5
    )

    # Extract text from validated SceneOutline model
    return Scene_obj.action
