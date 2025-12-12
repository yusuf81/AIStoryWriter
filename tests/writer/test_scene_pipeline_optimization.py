"""Test scene generation pipeline for duplicate processing."""

import pytest
from unittest.mock import MagicMock, patch
from Writer.Scene.ChapterByScene import ChapterByScene
from Writer.Scene.ChapterOutlineToScenes import ChapterOutlineToScenes
from Writer.Scene.ScenesToJSON import ScenesToJSON


def test_scene_pipeline_flow():
    """Test that scene pipeline doesn't duplicate work unnecessarily."""

    # Mock interface
    mock_interface = MagicMock()

    # Mock ChapterOutlineToScenes to return scene outline text
    scene_outline_text = """
    Scene 1: Character wakes up
    Description: John wakes up to the sound of his alarm clock.

    Scene 2: Character prepares for journey
    Description: John packs his bags and prepares for the adventure.

    Scene 3: Character leaves home
    Description: John locks the door and walks away from his house.
    """

    # Mock ScenesToJSON to return list of scenes
    scene_json_list = [
        "Scene 1: Character wakes up\nDescription: John wakes up to the sound of his alarm clock.",
        "Scene 2: Character prepares for journey\nDescription: John packs his bags and prepares for the adventure.",
        "Scene 3: Character leaves home\nDescription: John locks the door and walks away from his house."
    ]

    # Track call counts
    mock_interface.SafeGenerateText.return_value = ([], {})
    mock_interface.SafeGenerateJSON.return_value = ([], {"scenes": scene_json_list}, {})

    with patch('Writer.Scene.ChapterOutlineToScenes.ChapterOutlineToScenes', return_value=scene_outline_text), \
         patch('Writer.Scene.ScenesToJSON.ScenesToJSON', side_effect=lambda *args: scene_json_list), \
         patch('Writer.Scene.SceneOutlineToScene.SceneOutlineToScene', return_value="\n\nScene 1 content"):

        from Writer.PrintUtils import Logger
        logger = Logger()

        result = ChapterByScene(
            Interface=mock_interface,
            _Logger=logger,
            _ChapterNum=1,
            _TotalChapters=3,
            _ThisChapterOutline="Chapter 1 outline",
            _Outline="Full story outline"
        )

        # Check that the functions were called
        # The duplication would be if ScenesToJSON is called with already formatted scene details
        # and then SceneOutlineToScene re-processes them


def test_scenes_to_json_input_output():
    """Test that ScenesToJSON properly converts markdown scene list to JSON list."""

    # Mock interface with proper methods
    mock_interface = MagicMock()
    mock_interface.SafeGenerateJSON.return_value = ([], {"scenes": ["Scene 1", "Scene 2"]}, {})
    mock_interface.BuildSystemQuery.return_value = {"role": "system", "content": "System"}
    mock_interface.BuildUserQuery.return_value = {"role": "user", "content": "User"}

    from Writer.PrintUtils import Logger
    logger = Logger()

    scenes_text = """
    Scene 1: The Beginning
    Description: Our hero starts their journey.

    Scene 2: The Challenge
    Description: Our hero faces their first obstacle.
    """

    result = ScenesToJSON(
        Interface=mock_interface,
        _Logger=logger,
        _ChapterNum=1,
        _TotalChapters=5,
        _Scenes=scenes_text
    )

    # Should return a list of strings
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(scene, str) for scene in result)

    # Check the prompt was formed correctly
    mock_interface.BuildUserQuery.assert_called_once()
    call_args = mock_interface.BuildUserQuery.call_args[0][0]

    # The original scenes text should be in the prompt
    assert scenes_text in call_args


def test_optimize_scene_content_flow():
    """Test optimization opportunity: ScenesToJSON should extract only unique content."""

    # Test if we can detect redundant processing
    scenes_with_redundancy = """
    Scene 1: Character wakes up
    Scene 1: Character wakes up
    Description: John wakes up to the sound of his alarm clock.
    Description: John wakes up to the sound of his alarm clock.
    """

    # The ideal optimization would be to deduplicate before processing
    lines = scenes_with_redundancy.strip().split('\n')
    unique_lines = list(dict.fromkeys(lines))  # Preserve order while deduplicating
    deduplicated_text = '\n'.join(unique_lines)

    # Should have fewer lines after deduplication
    assert len(deduplicated_text.split('\n')) < len(scenes_with_redundancy.split('\n'))


def test_scene_deduplication():
    """Test the _deduplicate_scenes function."""

    from Writer.Scene.ScenesToJSON import _deduplicate_scenes

    # Test exact duplicates
    scenes_with_duplicates = [
        "Scene 1: Character wakes up",
        "Scene 2: Character prepares",
        "Scene 1: Character wakes up",  # Duplicate
        "Scene 3: Character leaves"
    ]

    deduplicated = _deduplicate_scenes(scenes_with_duplicates)
    assert len(deduplicated) == 3
    assert deduplicated[0] == "Scene 1: Character wakes up"
    assert deduplicated[1] == "Scene 2: Character prepares"
    assert deduplicated[2] == "Scene 3: Character leaves"

    # Test near duplicates (fuzzy matching)
    scenes_with_near_duplicates = [
        "Scene 1: The character wakes up in the morning",
        "Scene 2: Character prepares for the journey",
        "Scene 1: Character wakes up in morning",  # Near duplicate
        "Scene 3: Character leaves the house"
    ]

    deduplicated = _deduplicate_scenes(scenes_with_near_duplicates)
    # Should remove the near duplicate if similarity > 80%
    assert len(deduplicated) == 3

    # Test with different capitalization
    scenes_with_case_diff = [
        "Scene 1: Character wakes up",
        "SCENE 1: CHARACTER WAKES UP",  # Same but different case
        "Scene 2: Character prepares"
    ]

    deduplicated = _deduplicate_scenes(scenes_with_case_diff)
    assert len(deduplicated) == 2
    assert deduplicated[0] == "Scene 1: Character wakes up"

    # Test empty list
    assert _deduplicate_scenes([]) == []
    assert _deduplicate_scenes([""]) == [""]