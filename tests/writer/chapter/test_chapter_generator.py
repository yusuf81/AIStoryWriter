import pytest
from pytest_mock import MockerFixture
import sys
import types # For creating mock modules

# Functions/classes to test or mock
from Writer.Chapter.ChapterGenerator import (
    GenerateChapter,
    ReviseChapter, # Also in this file
    _prepare_initial_generation_context,
    _generate_stage1_plot,
    _generate_stage2_character_dev,
    _generate_stage3_dialogue,
    _run_scene_generation_pipeline_for_initial_plot,
    _run_final_chapter_revision_loop
)
import Writer.Config
# These will be mocked using mocker.patch where needed
# import Writer.Chapter.ChapterGenSummaryCheck
# import Writer.LLMEditor
# import Writer.Scene.ChapterByScene


# Mock ActivePrompts for the Test Module
@pytest.fixture(autouse=True)
def mock_active_prompts_for_chapter(mocker: MockerFixture):
    mock_prompts = types.ModuleType("Writer.Prompts")
    mock_prompts.CHAPTER_GENERATION_INTRO = "System: Chapter Gen Intro"
    mock_prompts.CHAPTER_HISTORY_INSERT = "History: {_Outline}"
    mock_prompts.CHAPTER_GENERATION_PROMPT = "Extract for chapter {_ChapterNum} from {_Outline}"
    mock_prompts.CHAPTER_SUMMARY_INTRO = "System: Summary Intro"
    mock_prompts.CHAPTER_SUMMARY_PROMPT = "Summarize {_LastChapter} for chapter {_ChapterNum}/{_TotalChapters} based on {_Outline}"
    mock_prompts.CHAPTER_GENERATION_STAGE1 = "Stage 1: Context={ContextHistoryInsert}, Chapter={_ChapterNum}/{_TotalChapters}, Outline={ThisChapterOutline}, Summary={FormattedLastChapterSummary}, Base={_BaseContext}, Feedback={Feedback}"
    mock_prompts.CHAPTER_GENERATION_STAGE2 = "Stage 2: Context={ContextHistoryInsert}, Chapter={_ChapterNum}/{_TotalChapters}, Outline={ThisChapterOutline}, Summary={FormattedLastChapterSummary}, S1={Stage1Chapter}, Base={_BaseContext}, Feedback={Feedback}"
    mock_prompts.CHAPTER_GENERATION_STAGE3 = "Stage 3: Context={ContextHistoryInsert}, Chapter={_ChapterNum}/{_TotalChapters}, Outline={ThisChapterOutline}, Summary={FormattedLastChapterSummary}, S2={Stage2Chapter}, Base={_BaseContext}, Feedback={Feedback}"

    mock_prompts.CRITIC_CHAPTER_INTRO = "System: Critic Chapter Intro"
    mock_prompts.CRITIC_CHAPTER_PROMPT = "Critique Chapter: {_Chapter} with Outline: {_Outline}"
    mock_prompts.CHAPTER_COMPLETE_INTRO = "System: Chapter Complete Intro"
    mock_prompts.CHAPTER_COMPLETE_PROMPT = "Is chapter complete (True/False)?: {_Chapter}"

    mock_prompts.CHAPTER_REVISION = "Revise Chapter: {_Chapter} with Feedback: {_Feedback}"

    # Use mocker.patch.dict for sys.modules, it handles cleanup.
    mocker.patch.dict(sys.modules, {"Writer.Prompts": mock_prompts})
    yield # Cleanup is handled by pytest-mock


# --- Tests for _prepare_initial_generation_context ---
def test_prepare_initial_context_no_prev_chapters(mocker: MockerFixture, mock_logger):
    mock_interface = mocker.Mock()
    # Mock the required Interface methods
    mock_interface.BuildSystemQuery = mocker.Mock(side_effect=lambda x: {"role": "system", "content": x})
    mock_interface.BuildUserQuery = mocker.Mock(side_effect=lambda x: {"role": "user", "content": x})
    # Simulate SafeGenerateText for ThisChapterOutline extraction
    mock_interface.SafeGenerateText.return_value = ([{"role": "assistant", "content": "Extracted Chapter Outline"}], {})
    mock_interface.GetLastMessageText = mocker.Mock(return_value="Extracted Chapter Outline")

    active_prompts_mock = sys.modules["Writer.Prompts"]

    history, ctx_insert, this_outline, last_summary, detail_check = _prepare_initial_generation_context(
        mock_interface, mock_logger(), active_prompts_mock,
        _Outline="Main chapter outline section", _Chapters=[], _ChapterNum=1, _TotalChapters=5,
        Config_module=Writer.Config
    )
    assert len(history) == 1 # Only system prompt from CHAPTER_GENERATION_INTRO
    assert history[0]["content"] == "System: Chapter Gen Intro"
    assert ctx_insert == "" # No previous chapters
    assert this_outline == "Extracted Chapter Outline"
    assert last_summary == ""
    assert detail_check == "Extracted Chapter Outline"
    assert mock_interface.SafeGenerateText.call_count == 1


def test_prepare_initial_context_with_prev_chapters(mocker: MockerFixture, mock_logger):
    mock_interface = mocker.Mock()
    # Mock the required Interface methods
    mock_interface.BuildSystemQuery = mocker.Mock(side_effect=lambda x: {"role": "system", "content": x})
    mock_interface.BuildUserQuery = mocker.Mock(side_effect=lambda x: {"role": "user", "content": x})
    mock_interface.SafeGenerateText.side_effect = [
        ([{"role": "assistant", "content": "Extracted Chapter Outline"}], {}),
        ([{"role": "assistant", "content": "Mocked Last Chapter Summary"}], {}),
    ]
    get_last_text_mock = mocker.patch.object(mock_interface, "GetLastMessageText")
    get_last_text_mock.side_effect = ["Extracted Chapter Outline", "Mocked Last Chapter Summary"]

    active_prompts_mock = sys.modules["Writer.Prompts"]
    prev_chapters = [{"number": 1, "title": "Chapter 1", "text": "Chapter 1 content"}]
    history, ctx_insert, this_outline, last_summary, detail_check = _prepare_initial_generation_context(
        mock_interface, mock_logger(), active_prompts_mock,
        _Outline="Main outline part for ch2", _Chapters=prev_chapters, _ChapterNum=2, _TotalChapters=5,
        Config_module=Writer.Config
    )
    assert len(history) == 1
    assert "History: Main outline part for ch2" in ctx_insert
    assert this_outline == "Extracted Chapter Outline"
    assert last_summary == "Mocked Last Chapter Summary"
    assert detail_check == "Extracted Chapter Outline" # As per current logic in _prepare_initial_generation_context
    assert mock_interface.SafeGenerateText.call_count == 2

# --- Tests for _generate_stageX_plot (example for stage1) ---
def test_generate_stage1_plot_success_first_try(mocker: MockerFixture, mock_logger):
    mock_interface = mocker.Mock()
    # Mock the required Interface methods
    mock_interface.BuildUserQuery = mocker.Mock(side_effect=lambda x: {"role": "user", "content": x})
    # Mock the ChapterGenSummaryCheck module itself, then its function
    mock_chapter_gen_summary_check_module = types.ModuleType("Writer.Chapter.ChapterGenSummaryCheck")
    mock_summary_check_func = mocker.Mock(return_value=(True, "")) # Success, no feedback
    mock_chapter_gen_summary_check_module.LLMSummaryCheck = mock_summary_check_func

    # Mock SafeGeneratePydantic to return a tuple with 3 elements
    mock_pydantic_result = mocker.Mock()
    mock_pydantic_result.text = "Generated S1 Plot"
    mock_interface.SafeGeneratePydantic.return_value = (
        [{"role": "assistant", "content": "Generated S1 Plot"}],
        mock_pydantic_result,
        {"prompt_tokens": 100, "completion_tokens": 150}
    )
    # Also mock SafeGenerateText as fallback
    mock_interface.SafeGenerateText.return_value = ([{"role": "assistant", "content": "Generated S1 Plot"}], {})
    mocker.patch.object(mock_interface, "GetLastMessageText", return_value="Generated S1 Plot")
    active_prompts_mock = sys.modules["Writer.Prompts"]

    result = _generate_stage1_plot(
        mock_interface, mock_logger(), active_prompts_mock,
        _ChapterNum=1, _TotalChapters=3, MessageHistory=[], ContextHistoryInsert="",
        ThisChapterOutline="Specific outline for Ch1", FormattedLastChapterSummary="Summary of prev",
        _BaseContext="Base story context", DetailedChapterOutlineForCheck="Detailed outline for check",
        Config_module=Writer.Config, ChapterGenSummaryCheck_module=mock_chapter_gen_summary_check_module
    )
    assert result == "Generated S1 Plot"
    mock_interface.SafeGenerateText.assert_called_once()
    mock_summary_check_func.assert_called_once()

def test_generate_stage1_plot_retry_and_succeed(mocker: MockerFixture, mock_logger):
    mock_interface = mocker.Mock()
    # Mock the required Interface methods
    mock_interface.BuildUserQuery = mocker.Mock(side_effect=lambda x: {"role": "user", "content": x})
    mock_chapter_gen_summary_check_module = types.ModuleType("Writer.Chapter.ChapterGenSummaryCheck")
    mock_summary_check_func = mocker.Mock(side_effect=[(False, "Feedback: too short"), (True, "")])
    mock_chapter_gen_summary_check_module.LLMSummaryCheck = mock_summary_check_func

    mock_get_last_text = mocker.patch.object(mock_interface, "GetLastMessageText")

    # Mock SafeGeneratePydantic retries
    mock_pydantic_result_1 = mocker.Mock()
    mock_pydantic_result_1.text = "S1 Plot v1 (needs work)"
    mock_pydantic_result_2 = mocker.Mock()
    mock_pydantic_result_2.text = "S1 Plot v2 (good!)"

    mock_interface.SafeGeneratePydantic.side_effect = [
        ([{"role": "assistant", "content": "S1 Plot v1 (needs work)"},], mock_pydantic_result_1, {"prompt_tokens": 100, "completion_tokens": 150}),
        ([{"role": "assistant", "content": "S1 Plot v2 (good!)"}], mock_pydantic_result_2, {"prompt_tokens": 100, "completion_tokens": 150}),
    ]

    # Also mock SafeGenerateText as fallback
    mock_interface.SafeGenerateText.side_effect = [
        ([{"role": "assistant", "content": "S1 Plot v1 (needs work)"}], {}),
        ([{"role": "assistant", "content": "S1 Plot v2 (good!)"}], {}),
    ]

    mock_get_last_text.side_effect = ["S1 Plot v1 (needs work)", "S1 Plot v2 (good!)"]

    active_prompts_mock = sys.modules["Writer.Prompts"]
    mocker.patch("Writer.Config.CHAPTER_MAX_REVISIONS", 5)

    result = _generate_stage1_plot(
        mock_interface, mock_logger(), active_prompts_mock,
        _ChapterNum=1, _TotalChapters=3, MessageHistory=[], ContextHistoryInsert="",
        ThisChapterOutline="Specific outline for Ch1", FormattedLastChapterSummary="Summary of prev",
        _BaseContext="Base story context", DetailedChapterOutlineForCheck="Detailed outline for check",
        Config_module=Writer.Config, ChapterGenSummaryCheck_module=mock_chapter_gen_summary_check_module
    )
    assert result == "S1 Plot v2 (good!)"
    # Check which method was actually called based on the config
    if Writer.Config.USE_PYDANTIC_PARSING:
        assert mock_interface.SafeGeneratePydantic.call_count == 2
        second_call_prompt = mock_interface.SafeGeneratePydantic.call_args_list[1][0][1][-1]['content']
    else:
        assert mock_interface.SafeGenerateText.call_count == 2
        second_call_prompt = mock_interface.SafeGenerateText.call_args_list[1][0][1][-1]['content']
    assert mock_summary_check_func.call_count == 2
    assert "Feedback: too short" in second_call_prompt

# --- Test for _run_scene_generation_pipeline_for_initial_plot ---
def test_run_scene_generation_pipeline(mocker: MockerFixture, mock_logger):
    # Mock the ChapterByScene class/function itself from the Scene sub-module
    mock_chapter_by_scene_func = mocker.patch("Writer.Scene.ChapterByScene.ChapterByScene")
    mock_chapter_by_scene_func.return_value = "Chapter content from scenes"
    active_prompts_mock = sys.modules["Writer.Prompts"]

    # Create logger instance to use consistently
    logger = mock_logger()

    result = _run_scene_generation_pipeline_for_initial_plot(
        mocker.Mock(), logger, active_prompts_mock, # Interface mock can be simpler here
        _ChapterNum=1, _TotalChapters=1, ThisChapterOutline="Scene outline here",
        _FullOutlineForSceneGen="Full story outline", _BaseContext="Base",
        Config_module=Writer.Config
    )
    assert result == "Chapter content from scenes"
    mock_chapter_by_scene_func.assert_called_once_with(
        mocker.ANY, logger, 1, 1, "Scene outline here", "Full story outline", "Base" # Config is used internally by ChapterByScene
    )

# --- Test for _run_final_chapter_revision_loop ---
def test_run_final_chapter_revision_loop_success(mocker: MockerFixture, mock_logger):
    mock_interface = mocker.Mock()
    # Mock LLMEditor module and its functions
    mock_llm_editor_module = types.ModuleType("Writer.LLMEditor")
    mock_llm_editor_module.GetFeedbackOnChapter = mocker.Mock(return_value="Needs minor tweaks.")
    mock_llm_editor_module.GetChapterRating = mocker.Mock(side_effect=[False, True]) # Fail once, then succeed

    mock_revise_chapter_func = mocker.Mock(spec=ReviseChapter)
    mock_revise_chapter_func.return_value = ("Revised Chapter Content v2", [])

    active_prompts_mock = sys.modules["Writer.Prompts"]
    mocker.patch("Writer.Config.CHAPTER_MIN_REVISIONS", 1)
    mocker.patch("Writer.Config.CHAPTER_MAX_REVISIONS", 5)

    # Create logger instance to use consistently
    logger = mock_logger()

    initial_chapter_content = "Initial Chapter Content v1"
    result = _run_final_chapter_revision_loop(
        mock_interface, logger, active_prompts_mock,
        _ChapterNum=1, _TotalChapters=1, ChapterToRevise=initial_chapter_content,
        OverallOutline="Story outline", MessageHistoryForRevision=[],
        Config_module=Writer.Config, LLMEditor_module=mock_llm_editor_module, # Pass the mocked module
        ReviseChapter_func_local=mock_revise_chapter_func
    )

    assert result == "Revised Chapter Content v2"
    assert mock_llm_editor_module.GetChapterRating.call_count == 2
    mock_revise_chapter_func.assert_called_once_with(
        mock_interface, logger, 1, 1, initial_chapter_content, "Needs minor tweaks.", [], _Iteration=1
    )

# --- High-level test for GenerateChapter orchestrator ---
def test_generate_chapter_orchestration_no_scenes_no_revisions(mocker: MockerFixture, mock_logger):
    # Mock external dependencies only, NOT internal methods
    mock_interface = mocker.Mock()

    # Mock SafeGeneratePydantic for enabled Pydantic
    mock_pydantic_result = mocker.Mock()
    mock_pydantic_result.text = "Generated chapter content"
    mock_interface.SafeGeneratePydantic.return_value = (
        [{"role": "assistant", "content": "Generated chapter content"}],
        mock_pydantic_result,
        {"prompt_tokens": 100, "completion_tokens": 150}
    )

    # Also mock SafeGenerateText as fallback
    mock_interface.SafeGenerateText.return_value = (
        [{"role": "assistant", "content": "Generated chapter content"}], {"tokens": 100}
    )
    mock_interface.GetLastMessageText.return_value = "Generated chapter content"
    mock_interface.BuildUserQuery.side_effect = lambda x: {"role": "user", "content": x}
    mock_interface.BuildSystemQuery.side_effect = lambda x: {"role": "system", "content": x}

    # Mock config settings to disable scene generation and revisions
    mocker.patch("Writer.Config.SCENE_GENERATION_PIPELINE", False)
    mocker.patch("Writer.Config.CHAPTER_NO_REVISIONS", True)

    # Test the real GenerateChapter function
    result = GenerateChapter(
        mock_interface, mock_logger(), 1, 1, "ChOutline", [], "BaseCtx", "FullOutline"
    )

    # Verify the function completed and returned content
    assert result == "Generated chapter content"
    # Verify external dependencies were called
    assert mock_interface.SafeGenerateText.called

def test_generate_chapter_orchestration_with_scenes_and_revisions(mocker: MockerFixture, mock_logger):
    # Mock external dependencies only
    mock_interface_main = mocker.Mock()

    # Mock SafeGeneratePydantic for enabled Pydantic
    mock_pydantic_result = mocker.Mock()
    mock_pydantic_result.text = "Generated chapter with scenes"
    mock_interface_main.SafeGeneratePydantic.return_value = (
        [{"role": "assistant", "content": "Generated chapter with scenes"}],
        mock_pydantic_result,
        {"prompt_tokens": 150, "completion_tokens": 200}
    )

    # Also mock SafeGenerateText as fallback
    mock_interface_main.SafeGenerateText.return_value = (
        [{"role": "assistant", "content": "Generated chapter with scenes"}], {"tokens": 150}
    )
    mock_interface_main.GetLastMessageText.return_value = "Generated chapter with scenes"
    mock_interface_main.BuildUserQuery.side_effect = lambda x: {"role": "user", "content": x}
    mock_interface_main.BuildSystemQuery.side_effect = lambda x: {"role": "system", "content": x}
    
    # Mock scene generation dependencies
    mocker.patch("Writer.Scene.ScenesToJSON.ScenesToJSON", return_value=(
        "mock_logger", "mock_json_response", "mock_usage"
    ))
    mocker.patch("Writer.LLMEditor.GetFeedbackOnChapter", return_value="Good chapter")
    mocker.patch("Writer.LLMEditor.GetChapterRating", return_value=True)
    
    # Mock config settings to disable scene generation but enable revisions
    mocker.patch("Writer.Config.SCENE_GENERATION_PIPELINE", False)  # Disable to avoid complex scene dependencies
    mocker.patch("Writer.Config.CHAPTER_NO_REVISIONS", False)

    # Test the real GenerateChapter function with scenes and revisions enabled
    result = GenerateChapter(
        mock_interface_main, mock_logger(), 1, 1, "ChOutline", [], "BaseCtx", "FullOutline"
    )

    # Verify the function completed and returned content
    assert result == "Generated chapter with scenes"
    # Verify external dependencies were called
    assert mock_interface_main.SafeGenerateText.called
