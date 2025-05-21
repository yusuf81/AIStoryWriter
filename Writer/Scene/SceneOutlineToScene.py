import Writer.LLMEditor
import Writer.PrintUtils
import Writer.Config
import Writer.Chapter.ChapterGenSummaryCheck
# import Writer.Prompts # Dihapus untuk pemuatan dinamis


def SceneOutlineToScene(
    Interface,
    _Logger,
    _SceneNum: int,
    _TotalScenes: int,
    _ThisSceneOutline: str,
    _Outline: str,
    _BaseContext: str = "",
):  # Added _SceneNum, _TotalScenes
    import Writer.Prompts as ActivePrompts # Ditambahkan untuk pemuatan dinamis

    # Now we're finally going to go and write the scene provided.

    _Logger.Log(
        f"Starting SceneOutline->Scene Generation for Scene {_SceneNum}/{_TotalScenes}",
        2,
    )
    MesssageHistory: list = []
    MesssageHistory.append(
        Interface.BuildSystemQuery(ActivePrompts.DEFAULT_SYSTEM_PROMPT)
    )
    MesssageHistory.append(
        Interface.BuildUserQuery(
            ActivePrompts.SCENE_OUTLINE_TO_SCENE.format(
                _SceneOutline=_ThisSceneOutline, _Outline=_Outline
            )
        )
    )

    Response, _ = Interface.SafeGenerateText(  # Unpack tuple, ignore token usage
        _Logger,
        MesssageHistory,
        Writer.Config.CHAPTER_STAGE1_WRITER_MODEL,
        _MinWordCount=Writer.Config.MIN_WORDS_SCENE_WRITE,  # Menggunakan Config
    )
    _Logger.Log(
        f"Finished SceneOutline->Scene Generation for Scene {_SceneNum}/{_TotalScenes}",
        5,
    )

    return Interface.GetLastMessageText(Response)
