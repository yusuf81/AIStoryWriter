"""
Tests for Phase 6: Scene Pipeline Integration

Verifies that ChapterByScene can reuse scenes from expanded chapter outlines
when available, falling back to ChapterOutlineToScenes when not.
"""

import sys
sys.path.insert(0, '/var/www/AIStoryWriter')

from Writer.Models import SceneOutline


def test_can_use_expanded_scenes_with_dict():
    """Verify _can_use_expanded_scenes returns True for dict with scenes"""
    from Writer.Scene.ChapterByScene import _can_use_expanded_scenes

    # Mock logger
    class MockLogger:
        def Log(self, msg, level):
            pass

    expanded_outline = {
        "text": "Chapter summary",
        "scenes": [
            {"action": "Scene 1"},
            {"action": "Scene 2"}
        ]
    }

    result = _can_use_expanded_scenes(expanded_outline, MockLogger())
    assert result is True, "Should return True for dict with scenes"


def test_can_use_expanded_scenes_with_empty_scenes():
    """Verify _can_use_expanded_scenes returns False for empty scenes array"""
    from Writer.Scene.ChapterByScene import _can_use_expanded_scenes

    class MockLogger:
        def Log(self, msg, level):
            pass

    expanded_outline = {
        "text": "Chapter summary",
        "scenes": []
    }

    result = _can_use_expanded_scenes(expanded_outline, MockLogger())
    assert result is False, "Should return False for empty scenes array"


def test_can_use_expanded_scenes_with_non_dict():
    """Verify _can_use_expanded_scenes returns False for non-dict"""
    from Writer.Scene.ChapterByScene import _can_use_expanded_scenes

    class MockLogger:
        def Log(self, msg, level):
            pass

    result = _can_use_expanded_scenes("Not a dict", MockLogger())
    assert result is False, "Should return False for non-dict"


def test_extract_scenes_from_dict():
    """Verify _extract_scenes_from_expanded_outline converts dicts to SceneOutline"""
    from Writer.Scene.ChapterByScene import _extract_scenes_from_expanded_outline

    class MockLogger:
        def Log(self, msg, level):
            pass

    expanded_outline = {
        "text": "Chapter summary",
        "scenes": [
            {
                "scene_number": 1,
                "setting": "Forest",
                "characters_present": ["Hero"],
                "action": "Hero enters forest",
                "purpose": "Setup",
                "estimated_word_count": 250
            }
        ]
    }

    scenes = _extract_scenes_from_expanded_outline(expanded_outline, MockLogger())

    assert len(scenes) == 1, "Should extract one scene"
    assert isinstance(scenes[0], SceneOutline), "Should be SceneOutline object"
    assert scenes[0].setting == "Forest", "Should preserve setting"
    assert scenes[0].action == "Hero enters forest", "Should preserve action"


def test_extract_scenes_from_strings():
    """Verify _extract_scenes_from_expanded_outline handles string scenes"""
    from Writer.Scene.ChapterByScene import _extract_scenes_from_expanded_outline

    class MockLogger:
        def Log(self, msg, level):
            pass

    expanded_outline = {
        "text": "Chapter summary",
        "scenes": [
            "First scene description",
            "Second scene description"
        ]
    }

    scenes = _extract_scenes_from_expanded_outline(expanded_outline, MockLogger())

    assert len(scenes) == 2, "Should extract two scenes"
    assert all(isinstance(s, SceneOutline) for s in scenes), "All should be SceneOutline objects"
    assert scenes[0].action == "First scene description", "Should use string as action"
    assert scenes[1].action == "Second scene description", "Should use string as action"


def test_extract_scenes_from_scene_outline_objects():
    """Verify _extract_scenes_from_expanded_outline handles SceneOutline objects"""
    from Writer.Scene.ChapterByScene import _extract_scenes_from_expanded_outline

    class MockLogger:
        def Log(self, msg, level):
            pass

    scene_obj = SceneOutline(
        scene_number=1,
        setting="Castle",
        characters_present=["King", "Queen"],
        action="Royal meeting",
        purpose="Establish conflict",
        estimated_word_count=300
    )

    expanded_outline = {
        "text": "Chapter summary",
        "scenes": [scene_obj]
    }

    scenes = _extract_scenes_from_expanded_outline(expanded_outline, MockLogger())

    assert len(scenes) == 1, "Should extract one scene"
    assert scenes[0] is scene_obj, "Should use the same SceneOutline object"
    assert scenes[0].setting == "Castle", "Should preserve all fields"


def test_chapter_by_scene_signature_accepts_expanded_outline():
    """Verify ChapterByScene function accepts _ExpandedChapterOutline parameter"""
    from Writer.Scene import ChapterByScene
    import inspect

    sig = inspect.signature(ChapterByScene.ChapterByScene)
    params = list(sig.parameters.keys())

    assert '_ExpandedChapterOutline' in params, \
        "ChapterByScene should have _ExpandedChapterOutline parameter"
    assert sig.parameters['_ExpandedChapterOutline'].default is None, \
        "_ExpandedChapterOutline should default to None"


def test_chapter_generator_signature_accepts_expanded_outline():
    """Verify GenerateChapter function accepts _ExpandedChapterOutline parameter"""
    # Check file content instead of importing to avoid dependency issues
    with open('/var/www/AIStoryWriter/Writer/Chapter/ChapterGenerator.py', 'r') as f:
        content = f.read()

    assert '_ExpandedChapterOutline: dict = None' in content, \
        "GenerateChapter should have _ExpandedChapterOutline parameter with default None"
    assert 'def GenerateChapter(' in content, \
        "File should contain GenerateChapter function"


def test_pipeline_extracts_expanded_outline():
    """Verify Pipeline.py contains logic to extract expanded outline dict"""
    with open('/var/www/AIStoryWriter/Writer/Pipeline.py', 'r') as f:
        content = f.read()

    assert 'expanded_chapter_outline_dict' in content, \
        "Pipeline should have expanded_chapter_outline_dict variable"
    assert 'expanded_chapter_outlines' in content, \
        "Pipeline should access expanded_chapter_outlines from state"
    assert 'Passing expanded outline dict for Chapter' in content, \
        "Pipeline should log when passing expanded outline"
