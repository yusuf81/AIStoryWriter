import Writer.Config
from Writer.Models import SceneOutline
from typing import Union
# import Writer.Prompts # Dihapus untuk pemuatan dinamis


def SceneOutlineToScene(
    Interface,
    _Logger,
    _SceneNum: int,
    _TotalScenes: int,
    _ThisSceneOutline: Union[str, SceneOutline],  # Accept both string and SceneOutline object
    _Outline: str,
    _BaseContext: str = "",
):  # Added _SceneNum, _TotalScenes
    import Writer.Prompts as ActivePrompts  # Ditambahkan untuk pemuatan dinamis

    # Now we're finally going to go and write the scene provided.

    # Handle both SceneOutline object and string (backward compatibility)
    if isinstance(_ThisSceneOutline, SceneOutline):
        # NEW: Extract metadata and build enhanced prompt
        scene_action = _ThisSceneOutline.action
        scene_setting = _ThisSceneOutline.setting
        scene_characters = _ThisSceneOutline.characters_present
        scene_purpose = _ThisSceneOutline.purpose
        scene_word_target = _ThisSceneOutline.estimated_word_count

        # Enhanced scene outline with metadata
        scene_outline_text = f"""Scene Action: {scene_action}

Setting: {scene_setting}
Characters Present: {', '.join(scene_characters)}
Scene Purpose: {scene_purpose}
Target Word Count: {scene_word_target} words

Please write this scene with attention to the specified setting, characters, and purpose.
Aim for approximately {scene_word_target} words."""
    else:
        # OLD: String input (backward compatibility)
        scene_outline_text = _ThisSceneOutline

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
                _SceneOutline=scene_outline_text, _Outline=_Outline
            )
        )
    )

    Response, Scene_obj, _ = Interface.SafeGeneratePydantic(  # Use Pydantic model
        _Logger,
        MesssageHistory,
        Writer.Config.CHAPTER_STAGE1_WRITER_MODEL,
        SceneOutline
    )
    _Logger.Log(
        f"Finished SceneOutline->Scene Generation for Scene {_SceneNum}/{_TotalScenes}",
        5,
    )

    # Extract text from validated SceneOutline model
    return Scene_obj.action
