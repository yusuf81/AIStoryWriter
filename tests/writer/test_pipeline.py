import pytest
from pytest_mock import MockerFixture
import sys
import types # For creating mock modules

from Writer.Pipeline import StoryPipeline
# from Writer.Pipeline import save_state_pipeline # Not needed if we mock _save_state_wrapper
import Writer.Config

# Mock ActivePrompts for the Test Module
@pytest.fixture(autouse=True)
def mock_active_prompts_for_pipeline(mocker: MockerFixture):
    mock_prompts = types.ModuleType("Writer.Prompts")
    mock_prompts.EXPAND_OUTLINE_CHAPTER_BY_CHAPTER = "Refine outline: {_Outline}"
    mock_prompts.MEGA_OUTLINE_PREAMBLE = "Mega Preamble"
    mock_prompts.MEGA_OUTLINE_CHAPTER_FORMAT = "Chapter {chapter_num}:\n{prefix}{chapter_outline_text}"
    mock_prompts.PREVIOUS_CHAPTER_CONTEXT_FORMAT = "Prev Ch {chapter_num}: {previous_chapter_text}"
    mock_prompts.CURRENT_CHAPTER_OUTLINE_FORMAT = "Curr Ch {chapter_num}: {chapter_outline_text}"
    mock_prompts.GET_CHAPTER_TITLE_PROMPT = "Title for ch {chapter_num} of text: {chapter_text} with context {base_story_context}"

    mocker.patch.dict(sys.modules, {"Writer.Prompts": mock_prompts})
    yield

class MockLogger:
    def __init__(self):
        self.logs = []
    def Log(self, msg, lvl):
        # print(f"LOG L{lvl}: {msg}")
        self.logs.append((lvl, msg))
    def SaveLangchain(self, s, m): pass

@pytest.fixture
def mock_logger():
    return MockLogger()

@pytest.fixture
def mock_interface(mocker: MockerFixture):
    mock = mocker.Mock()
    # Add mock methods that might be called directly by pipeline logic if any (though unlikely)
    # For instance, if run_pipeline itself called Interface.BuildUserQuery, etc.
    # However, most interface calls should be within stages, which are mocked.
    return mock

@pytest.fixture
def mock_pipeline_dependencies(mocker: MockerFixture):
    mocks = {
        '_generate_outline_stage': mocker.patch.object(StoryPipeline, '_generate_outline_stage'),
        '_detect_chapters_stage': mocker.patch.object(StoryPipeline, '_detect_chapters_stage'),
        '_expand_chapter_outlines_stage': mocker.patch.object(StoryPipeline, '_expand_chapter_outlines_stage'),
        '_write_chapters_stage': mocker.patch.object(StoryPipeline, '_write_chapters_stage'),
        '_perform_post_processing_stage': mocker.patch.object(StoryPipeline, '_perform_post_processing_stage'),
        '_save_state_wrapper': mocker.patch.object(StoryPipeline, '_save_state_wrapper'),
        # _get_outline_for_chapter is a method of StoryPipeline, used by _write_chapters_stage.
        # If _write_chapters_stage is fully mocked, this might not need separate mocking here.
        # However, if we want to ensure it's available for a less-mocked _write_chapters_stage in other tests:
        '_get_outline_for_chapter': mocker.patch.object(StoryPipeline, '_get_outline_for_chapter', return_value="dummy_chapter_specific_outline_via_fixture_if_needed"),
    }

    def update_step_side_effect(new_step_name):
        def side_effect(current_state, *args, **kwargs):
            # Simulate the stage updating the current_state
            current_state['last_completed_step'] = new_step_name
            # Simulate stages returning essential data for the next step in run_pipeline's direct logic
            if new_step_name == "outline":
                current_state.update({
                    "full_outline": "Mocked Outline",
                    "story_elements": "Mocked Elements",
                    "rough_chapter_outline": "Mocked Rough Outline",
                    "base_context": "Mocked Base Context"
                })
                return "Mocked Outline", "Mocked Elements", "Mocked Rough Outline", "Mocked Base Context"
            if new_step_name == "detect_chapters":
                current_state["total_chapters"] = 3 # Example number of chapters
                return 3
            if new_step_name == "expand_chapters": # This includes refine_chapters step
                current_state["expanded_chapter_outlines"] = ["Ch1 Outline", "Ch2 Outline", "Ch3 Outline"]
                current_state["full_outline"] = "Refined Mocked Outline" # Simulate outline refinement
                return ["Ch1 Outline", "Ch2 Outline", "Ch3 Outline"], "Refined Mocked Outline"
            if new_step_name == "chapter_generation_complete":
                current_state["completed_chapters"] = ["Chapter 1 Text", "Chapter 2 Text", "Chapter 3 Text"]
                return ["Chapter 1 Text", "Chapter 2 Text", "Chapter 3 Text"]
            if new_step_name == "complete": # For post-processing
                # Post-processing modifies current_state directly and returns it
                current_state.update({
                    "status": "completed",
                    "final_story_path": "final.md",
                    "final_json_path": "final.json"
                })
                return current_state
            return None
        return side_effect

    mocks['_generate_outline_stage'].side_effect = update_step_side_effect("outline")
    mocks['_detect_chapters_stage'].side_effect = update_step_side_effect("detect_chapters")
    mocks['_expand_chapter_outlines_stage'].side_effect = update_step_side_effect("expand_chapters")
    mocks['_write_chapters_stage'].side_effect = update_step_side_effect("chapter_generation_complete")
    mocks['_perform_post_processing_stage'].side_effect = update_step_side_effect("complete")

    return mocks

def test_run_pipeline_new_run_full_flow(mocker: MockerFixture, mock_logger, mock_interface, mock_pipeline_dependencies):
    # Mock ActivePrompts again locally if necessary, or ensure autouse=True is effective.
    # For this test, rely on autouse fixture.
    active_prompts_mock = sys.modules["Writer.Prompts"]
    pipeline = StoryPipeline(mock_interface, mock_logger, Writer.Config, active_prompts_mock)

    initial_state = {"last_completed_step": "init"}
    state_filepath = "dummy_state.json"
    prompt = "Test prompt for outline"

    mocker.patch.object(Writer.Config, 'EXPAND_OUTLINE', True)

    final_state = pipeline.run_pipeline(initial_state, state_filepath, prompt, Args=mocker.Mock(),
                                        original_prompt_content_for_post_processing="orig_prompt",
                                        translated_prompt_content_for_post_processing="trans_prompt",
                                        start_time_for_post_processing=0.0,
                                        log_directory_for_post_processing="logs/",
                                        input_prompt_file_for_post_processing="prompt.txt")

    mock_pipeline_dependencies['_generate_outline_stage'].assert_called_once()
    mock_pipeline_dependencies['_detect_chapters_stage'].assert_called_once()
    mock_pipeline_dependencies['_expand_chapter_outlines_stage'].assert_called_once()
    mock_pipeline_dependencies['_write_chapters_stage'].assert_called_once()
    mock_pipeline_dependencies['_perform_post_processing_stage'].assert_called_once()

    assert mock_pipeline_dependencies['_save_state_wrapper'].call_count >= 5
    assert final_state['last_completed_step'] == 'complete'


def test_run_pipeline_resume_from_detect_chapters(mocker: MockerFixture, mock_logger, mock_interface, mock_pipeline_dependencies):
    active_prompts_mock = sys.modules["Writer.Prompts"]
    pipeline = StoryPipeline(mock_interface, mock_logger, Writer.Config, active_prompts_mock)

    initial_state = {
        "last_completed_step": "detect_chapters", # Start after this step
        "full_outline": "Existing Outline", # Needed by expand_chapter_outlines
        "total_chapters": 3                 # Needed by expand_chapter_outlines
    }
    state_filepath = "dummy_state.json"
    prompt = "This prompt won't be used for outline gen"
    mocker.patch.object(Writer.Config, 'EXPAND_OUTLINE', True)

    final_state = pipeline.run_pipeline(initial_state, state_filepath, prompt, Args=mocker.Mock())

    mock_pipeline_dependencies['_generate_outline_stage'].assert_not_called()
    # _detect_chapters_stage itself is not called again, but the logic proceeds from its completion.
    # The run_pipeline logic checks last_completed_step. If "detect_chapters", it moves to expand/write.
    mock_pipeline_dependencies['_detect_chapters_stage'].assert_not_called()

    mock_pipeline_dependencies['_expand_chapter_outlines_stage'].assert_called_once()
    mock_pipeline_dependencies['_write_chapters_stage'].assert_called_once()
    mock_pipeline_dependencies['_perform_post_processing_stage'].assert_called_once()
    assert final_state['last_completed_step'] == 'complete'

def test_run_pipeline_skip_expand_outline_if_disabled(mocker: MockerFixture, mock_logger, mock_interface, mock_pipeline_dependencies):
    active_prompts_mock = sys.modules["Writer.Prompts"]
    pipeline = StoryPipeline(mock_interface, mock_logger, Writer.Config, active_prompts_mock)

    initial_state = {
        "last_completed_step": "detect_chapters", # Start after this step
        "full_outline": "Existing Outline",
        "total_chapters": 3,
        "base_context": "Mocked Base Context" # Needed for _write_chapters_stage
    }
    state_filepath = "dummy_state.json"
    prompt = "N/A"
    mocker.patch.object(Writer.Config, 'EXPAND_OUTLINE', False) # Disable expansion

    final_state = pipeline.run_pipeline(initial_state, state_filepath, prompt, Args=mocker.Mock())

    mock_pipeline_dependencies['_generate_outline_stage'].assert_not_called()
    mock_pipeline_dependencies['_detect_chapters_stage'].assert_not_called()
    mock_pipeline_dependencies['_expand_chapter_outlines_stage'].assert_not_called()

    # Check that _write_chapters_stage was called, indicating expand was skipped correctly
    mock_pipeline_dependencies['_write_chapters_stage'].assert_called_once()
    # And post-processing as well
    mock_pipeline_dependencies['_perform_post_processing_stage'].assert_called_once()
    assert final_state['last_completed_step'] == 'complete'

    # Check logs for skipping message
    assert any("Skipping Per-Chapter Outline Expansion (disabled in config)" in log[1] for log in mock_logger.logs)
