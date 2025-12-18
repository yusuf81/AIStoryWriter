import Writer.Scene.ChapterOutlineToScenes
import Writer.Scene.SceneOutlineToScene
from Writer.Scene.ScenesToJSON import deduplicate_scene_objects
from Writer.Models import SceneOutline


def _can_use_expanded_scenes(expanded_outline, logger):
    """
    Check if expanded outline has usable scene data.

    Returns True if the expanded outline is a dict with a non-empty scenes array.
    """
    if not isinstance(expanded_outline, dict):
        return False

    scenes = expanded_outline.get('scenes', [])
    if not scenes or len(scenes) == 0:
        return False

    logger.Log(f"Expanded outline contains {len(scenes)} scene(s) - can reuse", 5)
    return True


def _extract_scenes_from_expanded_outline(expanded_outline, logger):
    """
    Extract SceneOutline objects from expanded outline.

    Converts various scene formats (SceneOutline objects, dicts, strings)
    into a list of SceneOutline objects with proper metadata.
    """
    scenes = expanded_outline.get('scenes', [])
    scene_objects = []

    for idx, scene in enumerate(scenes):
        scene_num = idx + 1

        if isinstance(scene, SceneOutline):
            # Already a SceneOutline object - use directly
            logger.Log(f"Scene {scene_num}: Using existing SceneOutline object", 6)
            scene_objects.append(scene)

        elif isinstance(scene, dict):
            # Dict format - convert to SceneOutline
            logger.Log(f"Scene {scene_num}: Converting dict to SceneOutline", 6)
            try:
                scene_obj = SceneOutline(
                    scene_number=scene.get('scene_number', scene_num),
                    setting=scene.get('setting', 'Unknown setting'),
                    characters_present=scene.get('characters_present', []),
                    action=scene.get('action', scene.get('description', 'Scene action')),
                    purpose=scene.get('purpose', 'Advance plot'),
                    estimated_word_count=scene.get('estimated_word_count', 200)
                )
                scene_objects.append(scene_obj)
            except Exception as e:
                logger.Log(f"Scene {scene_num}: Error converting dict to SceneOutline: {e}. Skipping.", 5)
                continue

        elif isinstance(scene, str):
            # String format - create minimal SceneOutline
            logger.Log(f"Scene {scene_num}: Converting string to SceneOutline", 6)
            scene_obj = SceneOutline(
                scene_number=scene_num,
                setting="Unknown setting",
                characters_present=[],
                action=scene,
                purpose="From expanded outline",
                estimated_word_count=200
            )
            scene_objects.append(scene_obj)
        else:
            logger.Log(f"Scene {scene_num}: Unknown scene type {type(scene)}. Skipping.", 5)
            continue

    logger.Log(f"Extracted {len(scene_objects)} scene(s) from expanded outline", 5)
    return scene_objects


def ChapterByScene(
    Interface,
    _Logger,
    _ChapterNum: int,
    _TotalChapters: int,
    _ThisChapterOutline: str,
    _Outline: str,
    _BaseContext: str = "",
    _ExpandedChapterOutline: dict = None,
):  # Added _ExpandedChapterOutline parameter

    # This function calls all other scene-by-scene generation functions and creates a full chapter based on the new scene pipeline.

    _Logger.Log(
        f"Starting Scene-By-Scene Generation Pipeline for Chapter {_ChapterNum}/{_TotalChapters}",
        2,
    )

    # NEW: Check if expanded outline has usable scenes
    SceneOutlineObjects = None

    if _ExpandedChapterOutline and _can_use_expanded_scenes(_ExpandedChapterOutline, _Logger):
        _Logger.Log("Using scenes from expanded chapter outline", 4)
        SceneOutlineObjects = _extract_scenes_from_expanded_outline(
            _ExpandedChapterOutline, _Logger
        )

    # FALLBACK: Generate scenes if not available from expanded outline
    if not SceneOutlineObjects:
        _Logger.Log("Generating scenes via ChapterOutlineToScenes", 4)
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
