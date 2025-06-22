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
    mock_prompts.CHAPTER_GENERATION_STAGE1 = "Stage 1: Outline={_ThisChapterOutline}, SummaryPrevCh={_FormattedLastChapterSummary}, Feedback={_Feedback}, BaseContext={_BaseContext}"
    mock_prompts.CHAPTER_GENERATION_STAGE2 = "Stage 2: Outline={_ThisChapterOutline}, SummaryPrevCh={_FormattedLastChapterSummary}, S1Content={_Stage1Chapter}, Feedback={_Feedback}, BaseContext={_BaseContext}"
    mock_prompts.CHAPTER_GENERATION_STAGE3 = "Stage 3: Outline={_ThisChapterOutline}, SummaryPrevCh={_FormattedLastChapterSummary}, S2Content={_Stage2Chapter}, Feedback={_Feedback}, BaseContext={_BaseContext}"

    mock_prompts.CRITIC_CHAPTER_INTRO = "System: Critic Chapter Intro"
    mock_prompts.CRITIC_CHAPTER_PROMPT = "Critique Chapter: {_Chapter} with Outline: {_Outline}"
    mock_prompts.CHAPTER_COMPLETE_INTRO = "System: Chapter Complete Intro"
    mock_prompts.CHAPTER_COMPLETE_PROMPT = "Is chapter complete (True/False)?: {_Chapter}"

    mock_prompts.CHAPTER_REVISION = "Revise Chapter: {_Chapter} with Feedback: {_Feedback}"

    # Use mocker.patch.dict for sys.modules, it handles cleanup.
    mocker.patch.dict(sys.modules, {"Writer.Prompts": mock_prompts})
    yield # Cleanup is handled by pytest-mock

class MockLogger:
    def __init__(self): self.logs = []
    def Log(self, msg, lvl):
        # print(f"LOG L{lvl}: {msg}")
        self.logs.append((lvl, msg))
    def SaveLangchain(self, s, m): pass

@pytest.fixture
def mock_logger(mocker):
    return MockLogger()

# --- Tests for _prepare_initial_generation_context ---
def test_prepare_initial_context_no_prev_chapters(mocker: MockerFixture, mock_logger):
    mock_interface = mocker.Mock()
    # Simulate SafeGenerateText for ThisChapterOutline extraction
    mock_interface.SafeGenerateText.return_value = ([{"role": "assistant", "content": "Extracted Chapter Outline"}], {})
    mocker.patch.object(mock_interface, "GetLastMessageText", return_value="Extracted Chapter Outline")

    active_prompts_mock = sys.modules["Writer.Prompts"]

    history, ctx_insert, this_outline, last_summary, detail_check = _prepare_initial_generation_context(
        mock_interface, mock_logger, active_prompts_mock,
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
    mock_interface.SafeGenerateText.side_effect = [
        ([{"role": "assistant", "content": "Extracted Chapter Outline"}], {}),
        ([{"role": "assistant", "content": "Mocked Last Chapter Summary"}], {}),
    ]
    get_last_text_mock = mocker.patch.object(mock_interface, "GetLastMessageText")
    get_last_text_mock.side_effect = ["Extracted Chapter Outline", "Mocked Last Chapter Summary"]

    active_prompts_mock = sys.modules["Writer.Prompts"]
    prev_chapters = ["Chapter 1 content"]
    history, ctx_insert, this_outline, last_summary, detail_check = _prepare_initial_generation_context(
        mock_interface, mock_logger, active_prompts_mock,
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
    # Mock the ChapterGenSummaryCheck module itself, then its function
    mock_chapter_gen_summary_check_module = types.ModuleType("Writer.Chapter.ChapterGenSummaryCheck")
    mock_summary_check_func = mocker.Mock(return_value=(True, "")) # Success, no feedback
    mock_chapter_gen_summary_check_module.LLMSummaryCheck = mock_summary_check_func

    mock_interface.SafeGenerateText.return_value = ([{"role": "assistant", "content": "Generated S1 Plot"}], {})
    mocker.patch.object(mock_interface, "GetLastMessageText", return_value="Generated S1 Plot")
    active_prompts_mock = sys.modules["Writer.Prompts"]

    result = _generate_stage1_plot(
        mock_interface, mock_logger, active_prompts_mock,
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
    mock_chapter_gen_summary_check_module = types.ModuleType("Writer.Chapter.ChapterGenSummaryCheck")
    mock_summary_check_func = mocker.Mock(side_effect=[(False, "Feedback: too short"), (True, "")])
    mock_chapter_gen_summary_check_module.LLMSummaryCheck = mock_summary_check_func

    mock_get_last_text = mocker.patch.object(mock_interface, "GetLastMessageText")
    mock_interface.SafeGenerateText.side_effect = [
        ([{"role": "assistant", "content": "S1 Plot v1 (needs work)"}], {}),
        ([{"role": "assistant", "content": "S1 Plot v2 (good!)"}], {}),
    ]
    mock_get_last_text.side_effect = ["S1 Plot v1 (needs work)", "S1 Plot v2 (good!)"]

    active_prompts_mock = sys.modules["Writer.Prompts"]
    mocker.patch("Writer.Config.CHAPTER_MAX_REVISIONS", 5)

    result = _generate_stage1_plot(
        mock_interface, mock_logger, active_prompts_mock,
        _ChapterNum=1, _TotalChapters=3, MessageHistory=[], ContextHistoryInsert="",
        ThisChapterOutline="Specific outline for Ch1", FormattedLastChapterSummary="Summary of prev",
        _BaseContext="Base story context", DetailedChapterOutlineForCheck="Detailed outline for check",
        Config_module=Writer.Config, ChapterGenSummaryCheck_module=mock_chapter_gen_summary_check_module
    )
    assert result == "S1 Plot v2 (good!)"
    assert mock_interface.SafeGenerateText.call_count == 2
    assert mock_summary_check_func.call_count == 2
    second_call_prompt = mock_interface.SafeGenerateText.call_args_list[1][0][1][-1]['content']
    assert "Feedback: too short" in second_call_prompt

# --- Test for _run_scene_generation_pipeline_for_initial_plot ---
def test_run_scene_generation_pipeline(mocker: MockerFixture, mock_logger):
    # Mock the ChapterByScene class/function itself from the Scene sub-module
    mock_chapter_by_scene_func = mocker.patch("Writer.Scene.ChapterByScene.ChapterByScene")
    mock_chapter_by_scene_func.return_value = "Chapter content from scenes"
    active_prompts_mock = sys.modules["Writer.Prompts"]

    result = _run_scene_generation_pipeline_for_initial_plot(
        mocker.Mock(), mock_logger, active_prompts_mock, # Interface mock can be simpler here
        _ChapterNum=1, _TotalChapters=1, ThisChapterOutline="Scene outline here",
        _FullOutlineForSceneGen="Full story outline", _BaseContext="Base",
        Config_module=Writer.Config
    )
    assert result == "Chapter content from scenes"
    mock_chapter_by_scene_func.assert_called_once_with(
        mocker.ANY, mock_logger, 1, 1, "Scene outline here", "Full story outline", "Base" # Config is used internally by ChapterByScene
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

    initial_chapter_content = "Initial Chapter Content v1"
    result = _run_final_chapter_revision_loop(
        mock_interface, mock_logger, active_prompts_mock,
        _ChapterNum=1, _TotalChapters=1, ChapterToRevise=initial_chapter_content,
        OverallOutline="Story outline", MessageHistoryForRevision=[],
        Config_module=Writer.Config, LLMEditor_module=mock_llm_editor_module, # Pass the mocked module
        ReviseChapter_func_local=mock_revise_chapter_func
    )

    assert result == "Revised Chapter Content v2"
    assert mock_llm_editor_module.GetChapterRating.call_count == 2
    mock_revise_chapter_func.assert_called_once_with(
        mock_interface, mock_logger, 1, 1, initial_chapter_content, "Needs minor tweaks.", [], _Iteration=1
    )

# --- High-level test for GenerateChapter orchestrator ---
def test_generate_chapter_orchestration_no_scenes_no_revisions(mocker: MockerFixture, mock_logger):
    m_prepare_ctx = mocker.patch("Writer.Chapter.ChapterGenerator._prepare_initial_generation_context")
    m_stage1 = mocker.patch("Writer.Chapter.ChapterGenerator._generate_stage1_plot")
    m_stage2 = mocker.patch("Writer.Chapter.ChapterGenerator._generate_stage2_character_dev")
    m_stage3 = mocker.patch("Writer.Chapter.ChapterGenerator._generate_stage3_dialogue")
    m_run_revisions = mocker.patch("Writer.Chapter.ChapterGenerator._run_final_chapter_revision_loop")

    m_prepare_ctx.return_value = ([], "", "ChOutline", "LastSum", "DetailCheck")
    m_stage1.return_value = "S1_Content"
    m_stage2.return_value = "S2_Content"
    m_stage3.return_value = "S3_Content (Final)"

    mocker.patch("Writer.Config.SCENE_GENERATION_PIPELINE", False)
    mocker.patch("Writer.Config.CHAPTER_NO_REVISIONS", True)
    mock_interface_main = mocker.Mock() # For GenerateChapter's direct Interface use if any

    final_content = GenerateChapter(
        mock_interface_main, mock_logger, _ChapterNum=1, _TotalChapters=1,
        _Outline="Chapter specific outline provided by pipeline", _Chapters=[], _BaseContext="Base",
        _FullOutlineForSceneGen="Should not be used" # Added for completeness of signature
    )

    assert final_content == "S3_Content (Final)"
    m_prepare_ctx.assert_called_once()
    m_stage1.assert_called_once()
    m_stage2.assert_called_once()
    m_stage3.assert_called_once()
    m_run_revisions.assert_not_called()

def test_generate_chapter_orchestration_with_scenes_and_revisions(mocker: MockerFixture, mock_logger):
    m_prepare_ctx = mocker.patch("Writer.Chapter.ChapterGenerator._prepare_initial_generation_context")
    m_scene_pipeline = mocker.patch("Writer.Chapter.ChapterGenerator._run_scene_generation_pipeline_for_initial_plot")
    m_stage1_direct = mocker.patch("Writer.Chapter.ChapterGenerator._generate_stage1_plot")
    m_stage2 = mocker.patch("Writer.Chapter.ChapterGenerator._generate_stage2_character_dev")
    m_stage3 = mocker.patch("Writer.Chapter.ChapterGenerator._generate_stage3_dialogue")
    m_run_revisions = mocker.patch("Writer.Chapter.ChapterGenerator._run_final_chapter_revision_loop")

    m_prepare_ctx.return_value = (["SysMsg"], "CtxInsert", "ChOutline", "LastSum", "DetailCheck")
    m_scene_pipeline.return_value = "S1_From_Scenes"
    m_stage2.return_value = "S2_Content"
    m_stage3.return_value = "S3_Content"
    m_run_revisions.return_value = "S3_Content_Revised (Final)"

    mocker.patch("Writer.Config.SCENE_GENERATION_PIPELINE", True)
    mocker.patch("Writer.Config.CHAPTER_NO_REVISIONS", False)
    mock_interface_main = mocker.Mock()

    final_content = GenerateChapter(
        mock_interface_main, mock_logger, _ChapterNum=1, _TotalChapters=1,
        _Outline="Chapter specific outline", _Chapters=[], _BaseContext="Base", _FullOutlineForSceneGen="FullOutline"
    )

    assert final_content == "S3_Content_Revised (Final)"
    m_prepare_ctx.assert_called_once()
    m_scene_pipeline.assert_called_once()
    m_stage1_direct.assert_not_called()
    m_stage2.assert_called_once()
    m_stage3.assert_called_once()
    m_run_revisions.assert_called_once()

    # Check if _FullOutlineForSceneGen was passed to scene pipeline
    # The actual ActivePrompts module is sys.modules["Writer.Prompts"] due to the fixture
    active_prompts_mock = sys.modules["Writer.Prompts"]
    m_scene_pipeline.assert_called_with(
        mock_interface_main, mock_logger, active_prompts_mock,
        1, 1, "ChOutline", "FullOutline", "Base", Writer.Config
    )
