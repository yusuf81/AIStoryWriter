import pytest
from unittest.mock import MagicMock, call, patch
import Writer.OutlineGenerator as OutlineGenerator # Module to test
from Writer.Interface.Wrapper import Interface # Needed for type hinting if Interface instance is passed
import Writer.Config
import Writer.LLMEditor # To mock its functions
import Writer.Outline.StoryElements # To mock GenerateStoryElements
# Writer.Prompts will be patched directly where imported in OutlineGenerator

@pytest.fixture
def mock_interface(mocker):
    mock_iface = mocker.MagicMock(spec=Interface)

    def mock_safe_generate_text_logic(_logger, messages, _model, _seed_override=None, _format_schema=None, _min_word_count=1):
        assistant_response_content = "mocked LLM response from default SafeGenerateText mock"
        if hasattr(mock_iface.SafeGenerateText, 'custom_side_effect_list') and mock_iface.SafeGenerateText.custom_side_effect_list:
            val = mock_iface.SafeGenerateText.custom_side_effect_list.pop(0)
            if isinstance(val, Exception):
                raise val
            if isinstance(val, tuple) and len(val) == 2 and isinstance(val[0], list) and isinstance(val[1], dict):
                 return val
        messages_copy = messages[:]
        messages_copy.append({"role": "assistant", "content": assistant_response_content})
        return messages_copy, {"prompt_tokens": 5, "completion_tokens": 5}

    mock_iface.SafeGenerateText = MagicMock(side_effect=mock_safe_generate_text_logic)

    mock_iface.GetLastMessageText = MagicMock(side_effect=lambda msgs: msgs[-1]["content"] if msgs and msgs[-1] else "")
    mock_iface.BuildUserQuery = MagicMock(side_effect=lambda q: {"role": "user", "content": q})
    mock_iface.BuildSystemQuery = MagicMock(side_effect=lambda q: {"role": "system", "content": q})
    return mock_iface

@pytest.fixture
def mock_logger(mocker):
    logger = MagicMock()
    logger.Log = MagicMock()
    return logger

@patch('Writer.OutlineGenerator.Writer.Outline.StoryElements.GenerateStoryElements')
@patch('Writer.OutlineGenerator.Writer.LLMEditor.GetOutlineRating')
@patch('Writer.OutlineGenerator.Writer.LLMEditor.GetFeedbackOnOutline')
@patch('Writer.OutlineGenerator.Writer.Prompts')
def test_generate_outline_no_revisions(
    mock_writer_prompts, mock_get_feedback, mock_get_rating, mock_gen_story_elements,
    mock_interface, mock_logger, mocker
):
    mock_active_prompts = mock_writer_prompts

    mocker.patch.object(Writer.Config, 'INITIAL_OUTLINE_WRITER_MODEL', 'test_initial_model')
    mocker.patch.object(Writer.Config, 'MIN_WORDS_INITIAL_OUTLINE', 10)
    mocker.patch.object(Writer.Config, 'OUTLINE_MAX_REVISIONS', 3)
    mocker.patch.object(Writer.Config, 'OUTLINE_MIN_REVISIONS', 0)

    mock_active_prompts.GET_IMPORTANT_BASE_PROMPT_INFO = "BaseContextPrompt: {_Prompt}"
    mock_active_prompts.INITIAL_OUTLINE_PROMPT = "InitialOutlinePrompt: {StoryElements} {_OutlinePrompt}"

    mock_gen_story_elements.return_value = "Mocked Story Elements"

    base_context_msg_history = [{"role":"user", "content":"BaseContextPrompt: Test Prompt"}, {"role":"assistant", "content":"Mocked Base Context"}]
    initial_outline_msg_history = [{"role":"user", "content":"InitialOutlinePrompt: Mocked Story Elements Test Prompt"}, {"role":"assistant", "content":"Mocked Initial Outline"}]

    mock_interface.SafeGenerateText.side_effect = [
        (base_context_msg_history, {"prompt_tokens":1,"completion_tokens":1}),
        (initial_outline_msg_history, {"prompt_tokens":1,"completion_tokens":1})
    ]

    mock_get_rating.return_value = True

    final_outline, story_elements, outline, base_context = OutlineGenerator.GenerateOutline(
        mock_interface, mock_logger, "Test Prompt", _QualityThreshold=85
    )

    assert base_context == "Mocked Base Context"
    assert story_elements == "Mocked Story Elements"
    assert outline == "Mocked Initial Outline"
    assert "Mocked Base Context" in final_outline
    assert "Mocked Story Elements" in final_outline
    assert "Mocked Initial Outline" in final_outline

    calls = mock_interface.SafeGenerateText.call_args_list
    assert len(calls) == 2
    args_base_ctx, _ = calls[0]
    assert args_base_ctx[1] == [{"role":"user", "content":"BaseContextPrompt: Test Prompt"}]
    assert args_base_ctx[2] == 'test_initial_model'
    args_initial_outline, _ = calls[1]
    assert args_initial_outline[1] == [{"role":"user", "content":"InitialOutlinePrompt: Mocked Story Elements Test Prompt"}]
    assert args_initial_outline[2] == 'test_initial_model'
    assert args_initial_outline[5] == 10

    mock_gen_story_elements.assert_called_once_with(mock_interface, mock_logger, "Test Prompt")
    mock_get_rating.assert_called_once_with(mock_interface, mock_logger, "Mocked Initial Outline")
    mock_get_feedback.assert_called_once_with(mock_interface, mock_logger, "Mocked Initial Outline", "Mocked Story Elements", "Mocked Base Context")


@patch('Writer.OutlineGenerator.Writer.Outline.StoryElements.GenerateStoryElements')
@patch('Writer.OutlineGenerator.ReviseOutline')
@patch('Writer.OutlineGenerator.Writer.LLMEditor.GetOutlineRating')
@patch('Writer.OutlineGenerator.Writer.LLMEditor.GetFeedbackOnOutline')
@patch('Writer.OutlineGenerator.Writer.Prompts')
def test_generate_outline_with_one_revision(
    mock_writer_prompts, mock_get_feedback, mock_get_rating, mock_revise_outline, mock_gen_story_elements,
    mock_interface, mock_logger, mocker
):
    mock_active_prompts = mock_writer_prompts

    mocker.patch.object(Writer.Config, 'INITIAL_OUTLINE_WRITER_MODEL', 'test_initial_model')
    mocker.patch.object(Writer.Config, 'MIN_WORDS_INITIAL_OUTLINE', 10)
    mocker.patch.object(Writer.Config, 'OUTLINE_MAX_REVISIONS', 3)
    mocker.patch.object(Writer.Config, 'OUTLINE_MIN_REVISIONS', 0)

    mock_active_prompts.GET_IMPORTANT_BASE_PROMPT_INFO = "BasePrompt: {_Prompt}"
    mock_active_prompts.INITIAL_OUTLINE_PROMPT = "InitialPrompt: {StoryElements} {_OutlinePrompt}"

    mock_gen_story_elements.return_value = "Mocked SE"
    base_ctx_content = "Mocked BaseCtx"
    initial_outline_content = "Initial Outline"
    base_ctx_history = [{"role":"system", "content":"System Base"}, {"role":"user", "content":"BasePrompt: TestP"}, {"role":"assistant", "content":base_ctx_content}]
    initial_outline_system_prompt = "System prompt for outline"
    mock_active_prompts.INITIAL_OUTLINE_SYSTEM_PROMPT = initial_outline_system_prompt
    initial_outline_user_query = f"InitialPrompt: Mocked SE TestP"
    initial_outline_history_after_gen = [
        {"role":"system", "content": initial_outline_system_prompt },
        {"role":"user", "content": initial_outline_user_query},
        {"role":"assistant", "content": initial_outline_content}
    ]
    mock_interface.SafeGenerateText.side_effect = [
        (base_ctx_history, {"p":1,"c":1}),
        (initial_outline_history_after_gen, {"p":1,"c":1})
    ]
    mock_get_rating.side_effect = [False, True]
    mock_get_feedback.return_value = "Some feedback"
    revised_outline_text = "Revised Outline Content"
    history_after_revise = initial_outline_history_after_gen + [{"role": "user", "content": "Revision User Prompt"}, {"role": "assistant", "content": revised_outline_text}]
    mock_revise_outline.return_value = (revised_outline_text, history_after_revise)

    final_outline, _, outline, _ = OutlineGenerator.GenerateOutline(mock_interface, mock_logger, "TestP")

    assert outline == revised_outline_text
    assert revised_outline_text in final_outline
    assert mock_get_rating.call_count == 2
    mock_revise_outline.assert_called_once_with(
        mock_interface, mock_logger, initial_outline_content, "Some feedback",
        initial_outline_history_after_gen,
        _Iteration=1
    )

@patch('Writer.OutlineGenerator.Writer.Outline.StoryElements.GenerateStoryElements')
@patch('Writer.OutlineGenerator.ReviseOutline')
@patch('Writer.OutlineGenerator.Writer.LLMEditor.GetOutlineRating')
@patch('Writer.OutlineGenerator.Writer.LLMEditor.GetFeedbackOnOutline')
@patch('Writer.OutlineGenerator.Writer.Prompts')
def test_generate_outline_max_revisions_reached(
    mock_writer_prompts, mock_get_feedback, mock_get_rating, mock_revise_outline, mock_gen_story_elements,
    mock_interface, mock_logger, mocker
):
    mock_active_prompts = mock_writer_prompts
    MAX_REVS = 2
    mocker.patch.object(Writer.Config, 'OUTLINE_MAX_REVISIONS', MAX_REVS)
    mocker.patch.object(Writer.Config, 'OUTLINE_MIN_REVISIONS', 0)
    mocker.patch.object(Writer.Config, 'MIN_WORDS_INITIAL_OUTLINE', 1)
    mocker.patch.object(Writer.Config, 'INITIAL_OUTLINE_WRITER_MODEL', 'test_model')

    mock_active_prompts.GET_IMPORTANT_BASE_PROMPT_INFO = "BasePrompt: {_Prompt}"
    mock_active_prompts.INITIAL_OUTLINE_PROMPT = "InitialPrompt: {StoryElements} {_OutlinePrompt}"
    mock_active_prompts.INITIAL_OUTLINE_SYSTEM_PROMPT = "System for outline"
    mock_gen_story_elements.return_value = "Mocked SE for max rev"

    initial_outline_content = "Initial Outline for max rev"
    base_ctx_history = [{"role":"assistant", "content":"Base Ctx"}]
    initial_gen_history = [{"role":"system", "content":"System for outline"}, {"role":"user", "content":f"InitialPrompt: Mocked SE for max rev TestMaxRev"}, {"role":"assistant", "content":initial_outline_content}]
    mock_interface.SafeGenerateText.side_effect = [(base_ctx_history, {}), (initial_gen_history, {})]
    mock_get_rating.return_value = False
    mock_get_feedback.return_value = "Feedback for max rev"

    def revise_side_effect(iface, logger, outline, feedback, history, _Iteration):
        new_text = f"Revised Outline {_Iteration}"
        history_copy = history[:]
        history_copy.append({"role":"user", "content": f"Revision prompt for iter {_Iteration}"})
        history_copy.append({"role":"assistant", "content": new_text})
        return new_text, history_copy
    mock_revise_outline.side_effect = revise_side_effect

    final_outline_text, _, last_generated_outline, _ = OutlineGenerator.GenerateOutline(mock_interface, mock_logger, "TestMaxRev")

    assert mock_get_rating.call_count == MAX_REVS +1
    assert mock_get_feedback.call_count == MAX_REVS +1
    assert mock_revise_outline.call_count == MAX_REVS
    assert last_generated_outline == f"Revised Outline {MAX_REVS}"
    assert f"Revised Outline {MAX_REVS}" in final_outline_text

    for i in range(MAX_REVS):
        call_args = mock_revise_outline.call_args_list[i][0]
        assert call_args[5] == i + 1
        expected_outline_for_this_revise_call = initial_outline_content if i == 0 else f"Revised Outline {i}"
        assert call_args[2] == expected_outline_for_this_revise_call
    mock_logger.Log.assert_any_call(f"Max Outline Revisions ({MAX_REVS}) reached. Proceeding with the current outline.", 6)

@patch('Writer.OutlineGenerator.Writer.Prompts')
def test_revise_outline(mock_writer_prompts, mock_interface, mock_logger, mocker):
    mock_active_prompts = mock_writer_prompts
    mocker.patch.object(Writer.Config, 'INITIAL_OUTLINE_WRITER_MODEL', 'test_revise_model')
    mocker.patch.object(Writer.Config, 'MIN_WORDS_REVISE_OUTLINE', 5)
    mock_active_prompts.OUTLINE_REVISION_PROMPT = "Revise: {_Outline} BasedOn: {_Feedback}"

    original_outline = "Original outline content"
    feedback_text = "Feedback for revision"
    initial_history = [{"role": "system", "content": "System msg"}, {"role":"user", "content":"Initial User Query"}]
    revised_content = "This is the revised outline."
    revision_user_query = f"Revise: {original_outline} BasedOn: {feedback_text}"
    final_history_from_llm = initial_history + [{"role":"user", "content": revision_user_query}, {"role":"assistant", "content": revised_content}]
    expected_messages_to_safe_generate_text = initial_history + [{"role":"user", "content": revision_user_query}]
    mock_interface.SafeGenerateText.return_value = (final_history_from_llm, {"prompt_tokens":1,"completion_tokens":1})

    new_outline, resulting_history = OutlineGenerator.ReviseOutline(
        mock_interface, mock_logger, original_outline, feedback_text, initial_history, _Iteration=1
    )

    assert new_outline == revised_content
    assert resulting_history == final_history_from_llm
    mock_interface.SafeGenerateText.assert_called_once_with(
        mock_logger, expected_messages_to_safe_generate_text,
        'test_revise_model', _MinWordCount=5
    )
    mocker.patch.object(Writer.Config, 'OUTLINE_MAX_REVISIONS', 3)
    mock_logger.Log.assert_any_call(mocker.string_matching(r"Revising Outline \(Iteration 1/3\)"), 2)

@patch('Writer.OutlineGenerator.Writer.Prompts')
def test_generate_per_chapter_outline(mock_writer_prompts, mock_interface, mock_logger, mocker):
    mock_active_prompts = mock_writer_prompts
    mocker.patch.object(Writer.Config, 'CHAPTER_OUTLINE_WRITER_MODEL', 'test_chapter_outline_model')
    mocker.patch.object(Writer.Config, 'MIN_WORDS_PER_CHAPTER_OUTLINE', 20)
    mock_active_prompts.CHAPTER_OUTLINE_PROMPT = "ChapterOutline: ChapterNo {_ChapterNum} of {_TotalChapters} FromMainOutline: {_Outline}"
    mock_active_prompts.CHAPTER_OUTLINE_SYSTEM_PROMPT = "You are an expert chapter outline generator."

    chapter_num = 1
    total_chapters = 5
    main_outline = "Main story outline."
    expected_chapter_outline_text = "Detailed outline for chapter 1."
    expected_user_query = f"ChapterOutline: ChapterNo {chapter_num} of {total_chapters} FromMainOutline: {main_outline}"
    expected_messages_to_llm = [{"role": "system", "content": "You are an expert chapter outline generator."}, {"role": "user", "content": expected_user_query}]
    final_messages_from_llm = expected_messages_to_llm + [{"role":"assistant", "content": expected_chapter_outline_text}]
    mock_interface.SafeGenerateText.return_value = (final_messages_from_llm, {"prompt_tokens":1,"completion_tokens":1})

    generated_text = OutlineGenerator.GeneratePerChapterOutline(
        mock_interface, mock_logger, chapter_num, total_chapters, main_outline
    )

    assert generated_text == expected_chapter_outline_text
    mock_interface.SafeGenerateText.assert_called_once_with(
        mock_logger, expected_messages_to_llm,
        'test_chapter_outline_model', _MinWordCount=20
    )
    mock_logger.Log.assert_any_call(f"Generating Outline For Chapter {chapter_num} from {total_chapters}", 5)
