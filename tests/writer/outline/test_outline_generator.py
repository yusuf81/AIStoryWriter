import pytest
from pytest_mock import MockerFixture
import sys
import types # For creating mock modules

# Functions to test
from Writer.OutlineGenerator import GenerateOutline, ReviseOutline, GeneratePerChapterOutline

# Modules to mock or use
import Writer.Config
# import Writer.LLMEditor # Will be mocked via mocker.patch
# import Writer.Outline.StoryElements # Will be mocked via mocker.patch

# Mock ActivePrompts for the Test Module
@pytest.fixture(autouse=True)
def mock_active_prompts(mocker: MockerFixture):
    mock_prompts_module = types.ModuleType("Writer.Prompts")
    mock_prompts_module.GET_IMPORTANT_BASE_PROMPT_INFO = "Base Context Prompt: {_Prompt}"
    mock_prompts_module.INITIAL_OUTLINE_PROMPT = "Initial Outline Prompt: {StoryElements} based on {_OutlinePrompt}"
    mock_prompts_module.OUTLINE_REVISION_PROMPT = "Revise Outline: {_Outline} with feedback: {_Feedback}"
    mock_prompts_module.CHAPTER_OUTLINE_PROMPT = "Chapter Outline for Chapter {_ChapterNum}/{_TotalChapters} based on Outline: {_Outline}" # Adjusted to match expected usage

    # Prompts for LLMEditor functions if they are called (might be better to mock the functions directly)
    mock_prompts_module.CRITIC_OUTLINE_INTRO = "System: Critic Intro for Outline"
    mock_prompts_module.CRITIC_OUTLINE_PROMPT = "Criticize Outline: {_Outline}"
    mock_prompts_module.OUTLINE_COMPLETE_INTRO = "System: Outline Rating Intro"
    mock_prompts_module.OUTLINE_COMPLETE_PROMPT = "Rate Outline (True/False for good): {_Outline}" # Assuming boolean for simplicity

    # Patch sys.modules to ensure the mock is used by the OutlineGenerator functions.
    # pytest-mock's mocker.patch.dict handles restoration automatically.
    mocker.patch.dict(sys.modules, {"Writer.Prompts": mock_prompts_module})
    yield # No explicit cleanup needed for sys.modules when using mocker.patch.dict


# Mock Logger Utility
class MockLogger:
    def __init__(self):
        self.logs = []
    def Log(self, message, level):
        # print(f"MockLog L{level}: {message}") # For debug during test writing
        self.logs.append((level, message))
    def SaveLangchain(self, stack, messages): pass

@pytest.fixture
def mock_logger():
    return MockLogger()

# Tests for GenerateOutline
def test_generate_outline_success_first_pass(mocker: MockerFixture, mock_logger):
    # Mock dependencies
    mock_interface = mocker.Mock()
    mock_story_elements_gen = mocker.patch("Writer.Outline.StoryElements.GenerateStoryElements")
    mock_llm_editor_get_feedback = mocker.patch("Writer.LLMEditor.GetFeedbackOnOutline")
    mock_llm_editor_get_rating = mocker.patch("Writer.LLMEditor.GetOutlineRating")

    # Configure mocks
    # Call 1: GetImportantBasePromptInfo
    # Call 2: GenerateInitialOutline
    mock_interface.SafeGenerateText.side_effect = [
        ([{"role": "system", "content": "Base Context Prompt: Test Prompt"}, {"role": "assistant", "content": "Mocked Base Context"}], {"tokens": 1}),
        ([{"role": "system", "content": "Initial Outline Prompt: Mocked Story Elements based on Test Prompt"}, {"role": "assistant", "content": "Mocked Initial Outline"}], {"tokens": 1}),
    ]

    # Correctly mock GetLastMessageText to reflect the 'content' of the last message from SafeGenerateText's tuple output
    def get_last_message_text_side_effect(*args, **kwargs):
        message_list = args[0] if args else kwargs.get('_Messages', [])
        if message_list:
            # Check if the last message is a dict and has 'content'
            last_msg = message_list[-1]
            if isinstance(last_msg, dict) and 'content' in last_msg:
                return last_msg['content']
        return "" # Fallback or raise error if structure is unexpected

    mocker.patch.object(mock_interface, 'GetLastMessageText', side_effect=get_last_message_text_side_effect)


    mock_story_elements_gen.return_value = "Mocked Story Elements"

    mocker.patch("Writer.Config.OUTLINE_MIN_REVISIONS", 1)
    mocker.patch("Writer.Config.OUTLINE_MAX_REVISIONS", 5)
    mock_llm_editor_get_feedback.return_value = "No feedback needed." # Feedback for the first outline
    mock_llm_editor_get_rating.return_value = True # Outline is good on the first try after min_revisions

    final_outline_str, story_elements_str, final_outline_variable, base_context_str = GenerateOutline(
        mock_interface, mock_logger, "Test Prompt", _QualityThreshold=85 # _QualityThreshold is unused
    )

    assert base_context_str == "Mocked Base Context"
    assert story_elements_str == "Mocked Story Elements"
    assert final_outline_variable == "Mocked Initial Outline"

    assert "Mocked Base Context" in final_outline_str
    assert "Mocked Story Elements" in final_outline_str
    assert "Mocked Initial Outline" in final_outline_str

    mock_story_elements_gen.assert_called_once_with(mock_interface, mock_logger, "Test Prompt")
    assert mock_interface.SafeGenerateText.call_count == 2
    mock_llm_editor_get_feedback.assert_called_once_with(mock_interface, mock_logger, "Mocked Initial Outline")
    mock_llm_editor_get_rating.assert_called_once_with(mock_interface, mock_logger, "Mocked Initial Outline")


def test_generate_outline_reaches_max_revisions(mocker: MockerFixture, mock_logger):
    mock_interface = mocker.Mock()
    mocker.patch("Writer.Outline.StoryElements.GenerateStoryElements", return_value="Elements")

    mock_revise_outline = mocker.patch("Writer.OutlineGenerator.ReviseOutline")

    mock_interface.SafeGenerateText.side_effect = [
        ([{"role": "assistant", "content": "Base Context"}], {}),
        ([{"role": "assistant", "content": "Initial Outline v1"}], {}),
    ]

    def get_last_message_text_side_effect_revisions(*args, **kwargs):
        # Simulate the sequence of "last messages" that GenerateOutline would see
        # This needs to align with how many times GetLastMessageText is called *outside* ReviseOutline
        # The call_count on a mock object is global for that mock.
        # We need to ensure this side_effect is only for this specific mock_interface.GetLastMessageText
        if mock_interface.GetLastMessageText.call_count == 1: return "Base Context"
        if mock_interface.GetLastMessageText.call_count == 2: return "Initial Outline v1"
        return "Unexpected call to GetLastMessageText in this test sequence"

    mocker.patch.object(mock_interface, 'GetLastMessageText', side_effect=get_last_message_text_side_effect_revisions)

    original_min_rev = Writer.Config.OUTLINE_MIN_REVISIONS
    original_max_rev = Writer.Config.OUTLINE_MAX_REVISIONS
    Writer.Config.OUTLINE_MIN_REVISIONS = 1
    Writer.Config.OUTLINE_MAX_REVISIONS = 2

    mock_llm_editor_get_feedback = mocker.patch("Writer.LLMEditor.GetFeedbackOnOutline", return_value="Needs work")
    mock_llm_editor_get_rating = mocker.patch("Writer.LLMEditor.GetOutlineRating", return_value=False)

    mock_revise_outline.side_effect = [
        ("Revised Outline v2", [{"role": "assistant", "content": "Revised Outline v2"}]),
        ("Revised Outline v3", [{"role": "assistant", "content": "Revised Outline v3"}]),
    ]

    _, _, outline_after_loop, _ = GenerateOutline(mock_interface, mock_logger, "Test")

    assert outline_after_loop == "Revised Outline v3"
    assert mock_interface.SafeGenerateText.call_count == 2
    assert mock_revise_outline.call_count == Writer.Config.OUTLINE_MAX_REVISIONS
    assert mock_llm_editor_get_rating.call_count == Writer.Config.OUTLINE_MAX_REVISIONS + 1
    assert mock_llm_editor_get_feedback.call_count == Writer.Config.OUTLINE_MAX_REVISIONS + 1
    assert any("Max Revisions Reached" in log[1] for log in mock_logger.logs if log[0] == 4)

    Writer.Config.OUTLINE_MIN_REVISIONS = original_min_rev
    Writer.Config.OUTLINE_MAX_REVISIONS = original_max_rev

# Tests for ReviseOutline
def test_revise_outline(mocker: MockerFixture, mock_logger):
    mock_interface = mocker.Mock()

    # Expected history for SafeGenerateText call within ReviseOutline
    expected_messages_for_safe_generate = [
        {"role": "system", "content": "System prompt"}, # Initial history
        {"role": "user", "content": "Revise Outline: Original Outline with feedback: Feedback given"} # User query from ReviseOutline
    ]

    mock_interface.SafeGenerateText.return_value = (
        expected_messages_for_safe_generate + [{"role": "assistant", "content": "Revised Outline Content"}],
        {"tokens": 1} # Mock token usage
    )
    mocker.patch.object(mock_interface, 'GetLastMessageText', return_value="Revised Outline Content")
    # Mock BuildUserQuery specifically for this test to check its argument
    mock_build_user_query = mocker.patch.object(mock_interface, 'BuildUserQuery', return_value={"role": "user", "content": "Revise Outline: Original Outline with feedback: Feedback given"})


    initial_history = [{"role": "system", "content": "System prompt"}]
    revised_text, history = ReviseOutline(
        mock_interface, mock_logger, "Original Outline", "Feedback given", initial_history.copy(), _Iteration=1
    )

    assert revised_text == "Revised Outline Content"
    assert len(history) == 3
    assert history[-1]["content"] == "Revised Outline Content"
    assert history[-1]["role"] == "assistant"

    mock_interface.SafeGenerateText.assert_called_once()
    # Verify the messages sent to SafeGenerateText
    actual_messages_sent = mock_interface.SafeGenerateText.call_args[0][1]
    assert actual_messages_sent == expected_messages_for_safe_generate

    # Check that BuildUserQuery was called with the correct formatted prompt string
    # This relies on ActivePrompts.OUTLINE_REVISION_PROMPT being "Revise Outline: {_Outline} with feedback: {_Feedback}"
    expected_prompt_str = "Revise Outline: Original Outline with feedback: Feedback given"
    mock_build_user_query.assert_called_once_with(expected_prompt_str)

# Tests for GeneratePerChapterOutline
def test_generate_per_chapter_outline(mocker: MockerFixture, mock_logger):
    mock_interface = mocker.Mock()

    expected_messages_for_safe_generate = [
        {"role": "system", "content": Writer.Config.DEFAULT_SYSTEM_MSG}, # Assuming default system message
        {"role": "user", "content": "Chapter Outline for Chapter 1/5 based on Outline: Main Story Outline"}
    ]

    mock_interface.SafeGenerateText.return_value = (
        expected_messages_for_safe_generate + [{"role": "assistant", "content": "Detailed Chapter 1 Outline"}],
        {} # Mock token usage
    )
    mocker.patch.object(mock_interface, 'GetLastMessageText', return_value="Detailed Chapter 1 Outline")
    # Mock BuildUserQuery and BuildSystemQuery to check their arguments
    mock_build_user_query = mocker.patch.object(mock_interface, 'BuildUserQuery')
    mock_build_system_query = mocker.patch.object(mock_interface, 'BuildSystemQuery')

    # Set specific return values for mocked BuildUserQuery and BuildSystemQuery
    # This is important because these are used to construct the list passed to SafeGenerateText
    mock_build_system_query.return_value = {"role": "system", "content": Writer.Config.DEFAULT_SYSTEM_MSG}
    mock_build_user_query.return_value = {"role": "user", "content": "Chapter Outline for Chapter 1/5 based on Outline: Main Story Outline"}


    chapter_outline = GeneratePerChapterOutline(
        mock_interface, mock_logger, _ChapterNum=1, _TotalChapters=5, _Outline="Main Story Outline" # Corrected param name _Chapter to _ChapterNum
    )

    assert chapter_outline == "Detailed Chapter 1 Outline"
    mock_interface.SafeGenerateText.assert_called_once()

    # Assert that BuildUserQuery was called with the correctly formatted prompt string
    # This relies on ActivePrompts.CHAPTER_OUTLINE_PROMPT from the mock_active_prompts fixture
    expected_prompt_str = "Chapter Outline for Chapter 1/5 based on Outline: Main Story Outline"
    mock_build_user_query.assert_called_once_with(expected_prompt_str)
    mock_build_system_query.assert_called_once_with(Writer.Config.DEFAULT_SYSTEM_MSG)

    # Verify the messages sent to SafeGenerateText
    actual_messages_sent = mock_interface.SafeGenerateText.call_args[0][1]
    assert actual_messages_sent == expected_messages_for_safe_generate
