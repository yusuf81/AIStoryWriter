import pytest
from unittest.mock import MagicMock, call, patch
import Writer.Interface.Wrapper
import Writer.Config

@pytest.fixture(autouse=True)
def mock_load_models(mocker):
    mocker.patch.object(Writer.Interface.Wrapper.Interface, "LoadModels", return_value=None)

@pytest.fixture
def mock_logger(mocker):
    logger = MagicMock()
    logger.Log = MagicMock()
    return logger

def test_get_model_and_provider(mocker):
    mocker.patch.object(Writer.Config, 'OLLAMA_HOST', 'default_ollama_host_for_test')
    interface_instance = Writer.Interface.Wrapper.Interface(Models=[])

    provider, model_name, host, options = interface_instance.GetModelAndProvider("llama3")
    assert provider == "ollama"
    assert model_name == "llama3"
    assert host == 'default_ollama_host_for_test'
    assert options == {}

    provider, model_name, host, options = interface_instance.GetModelAndProvider("ollama://custommodel@myhost:12345")
    assert provider == "ollama"
    assert model_name == "custommodel"
    assert host == "myhost:12345"
    assert options == {}

    provider, model_name, host, options = interface_instance.GetModelAndProvider("ollama://mistral?temperature=0.5&num_ctx=4096")
    assert provider == "ollama"
    assert model_name == "mistral"
    assert host == 'default_ollama_host_for_test'
    assert options == {"temperature": 0.5, "num_ctx": 4096.0}

    provider, model_name, host, options = interface_instance.GetModelAndProvider("ollama://modelnamepart@hostpart:1234?temperature=0.6")
    assert provider == "ollama"
    assert model_name == "modelnamepart"
    assert host == "hostpart:1234"
    assert options == {"temperature": 0.6}

    provider, model_name, host, options = interface_instance.GetModelAndProvider("ollama://thenetlocmodel/pathpart@thepathhost:5678?temp=0.1")
    assert provider == "ollama"
    assert model_name == "thenetlocmodel/pathpart"
    assert host == "thepathhost:5678"
    assert options == {"temp": 0.1}

    provider, model_name, host, options = interface_instance.GetModelAndProvider("google://gemini-1.5-flash")
    assert provider == "google"
    assert model_name == "gemini-1.5-flash"
    assert host is None
    assert options == {}

    provider, model_name, host, options = interface_instance.GetModelAndProvider("google://gemini-pro?temperature=0.8")
    assert provider == "google"
    assert model_name == "gemini-pro"
    assert host is None
    assert options == {"temperature": 0.8}

    provider, model_name, host, options = interface_instance.GetModelAndProvider("openrouter://anthropic/claude-3-haiku")
    assert provider == "openrouter"
    assert model_name == "anthropic/claude-3-haiku"
    assert host is None
    assert options == {}

    provider, model_name, host, options = interface_instance.GetModelAndProvider("openrouter://google/gemini-flash-1.5?temperature=0.7")
    assert provider == "openrouter"
    assert model_name == "google/gemini-flash-1.5"
    assert host is None
    assert options == {"temperature": 0.7}

    provider, model_name, host, options = interface_instance.GetModelAndProvider("myprovider://modelA@hostB?paramC=1.0")
    assert provider == "myprovider"
    assert model_name == "modelA"
    assert host == "hostB"
    assert options == {"paramC": 1.0}

    provider, model_name, host, options = interface_instance.GetModelAndProvider("anotherprovider://modelX?paramZ=2")
    assert provider == "anotherprovider"
    assert model_name == "modelX"
    assert host is None
    assert options == {"paramZ": 2.0}

def test_safe_generate_text_valid_response(mocker, mock_logger):
    mocker.patch.object(Writer.Config, 'MAX_TEXT_RETRIES', 1)
    interface_instance = Writer.Interface.Wrapper.Interface(Models=[])

    mock_chat_response_tuple = ([{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}], {"prompt_tokens":1, "completion_tokens":1}, 10, 2)
    mock_chatandstream_method = mocker.patch.object(interface_instance, "ChatAndStreamResponse", return_value=mock_chat_response_tuple)

    messages_history = [{"role": "user", "content": "Hello"}]
    result_messages, token_usage = interface_instance.SafeGenerateText(mock_logger, messages_history, "mock_model_key", _MinWordCount=1)

    assert len(result_messages) == 2
    assert result_messages[-1]["content"] == "Hi there!"
    assert token_usage == {"prompt_tokens":1, "completion_tokens":1}
    mock_chatandstream_method.assert_called_once()

def test_safe_generate_text_retry_on_empty(mocker, mock_logger):
    mocker.patch.object(Writer.Config, 'MAX_TEXT_RETRIES', 2)
    interface_instance = Writer.Interface.Wrapper.Interface(Models=[])

    empty_response_tuple = ([{"role": "user", "content": "Q"}, {"role": "assistant", "content": "  "}], None, 5, 1)
    valid_response_tuple = ([{"role": "user", "content": "Q"}, {"role": "assistant", "content": "Valid"}], {"prompt_tokens":1, "completion_tokens":1}, 10, 2)

    mock_chat_stream_method = mocker.patch.object(interface_instance, "ChatAndStreamResponse")
    mock_chat_stream_method.side_effect = [empty_response_tuple, valid_response_tuple]

    messages_history = [{"role": "user", "content": "Q"}]
    result_messages, token_usage = interface_instance.SafeGenerateText(mock_logger, messages_history, "mock_model_key", _MinWordCount=1)

    assert result_messages[-1]["content"] == "Valid"
    assert mock_chat_stream_method.call_count == 2
    found_log = False
    for call_args in mock_logger.Log.call_args_list:
        expected_log_msg_part = "Failed Due To Empty Response"
        expected_retry_count_part = "Retry 1/2" # max_retries is 2 for this test
        if expected_log_msg_part in call_args[0][0] and \
           expected_retry_count_part in call_args[0][0] and \
           call_args[0][1] == 7:
            found_log = True # This line was causing the error due to dedent
            break            # This line was also dedented
    assert found_log, f"Log message for '{expected_log_msg_part} with {expected_retry_count_part}' not found."


def test_safe_generate_text_retry_on_short(mocker, mock_logger):
    mocker.patch.object(Writer.Config, 'MAX_TEXT_RETRIES', 2)
    interface_instance = Writer.Interface.Wrapper.Interface(Models=[])

    short_response_tuple = ([{"role": "user", "content": "Q"}, {"role": "assistant", "content": "Short"}], None, 5, 1)
    valid_response_tuple = ([{"role": "user", "content": "Q"}, {"role": "assistant", "content": "Valid and long enough"}], {"prompt_tokens":1,"completion_tokens":1}, 10,2)

    mock_chat_stream_method = mocker.patch.object(interface_instance, "ChatAndStreamResponse")
    mock_chat_stream_method.side_effect = [short_response_tuple, valid_response_tuple]

    messages_history = [{"role": "user", "content": "Q"}]
    result_messages, token_usage = interface_instance.SafeGenerateText(mock_logger, messages_history, "mock_model_key", _MinWordCount=3)

    assert result_messages[-1]["content"] == "Valid and long enough"
    assert mock_chat_stream_method.call_count == 2
    found_log = False
    for call_args in mock_logger.Log.call_args_list:
        # Corrected log check for this test
        expected_log_msg_part = "Failed Due To Short Response"
        expected_retry_count_part = "Retry 1/2"
        if expected_log_msg_part in call_args[0][0] and \
           expected_retry_count_part in call_args[0][0] and \
           call_args[0][1] == 7:
            found_log = True
            break
    assert found_log, f"Log message for '{expected_log_msg_part} with {expected_retry_count_part}' not found."

def test_safe_generate_text_max_retries_exceeded(mocker, mock_logger):
    max_retries_config = 2
    mocker.patch.object(Writer.Config, 'MAX_TEXT_RETRIES', max_retries_config)
    interface_instance = Writer.Interface.Wrapper.Interface(Models=[])

    empty_response_tuple = ([{"role": "user", "content": "Q"}, {"role": "assistant", "content": "  "}], None, 0, 0)
    mock_chat_stream_method = mocker.patch.object(interface_instance, "ChatAndStreamResponse", return_value=empty_response_tuple)

    messages_history = [{"role": "user", "content": "Q"}]
    with pytest.raises(Exception, match=f"Failed to generate valid text after {max_retries_config} retries"):
        interface_instance.SafeGenerateText(mock_logger, messages_history, "mock_model_key", _MinWordCount=1, _max_retries_override=max_retries_config)

    assert mock_chat_stream_method.call_count == max_retries_config


def test_safe_generate_json_valid_response(mocker, mock_logger):
    mocker.patch.object(Writer.Config, 'MAX_JSON_RETRIES', 1)
    interface_instance = Writer.Interface.Wrapper.Interface(Models=[])

    valid_json_str = '{"key": "value", "num": 123}'
    mock_chat_response_tuple = ([{"role": "user", "content": "Q"}, {"role": "assistant", "content": valid_json_str}], {"prompt_tokens":1,"completion_tokens":1}, 10,2)
    mock_chatandstream_method = mocker.patch.object(interface_instance, "ChatAndStreamResponse", return_value=mock_chat_response_tuple)

    messages_history = [{"role": "user", "content": "Q"}]
    result_messages, json_obj, token_usage = interface_instance.SafeGenerateJSON(mock_logger, messages_history, "mock_model_key")

    assert json_obj == {"key": "value", "num": 123}
    mock_chatandstream_method.assert_called_once()

def test_safe_generate_json_retry_on_invalid_json(mocker, mock_logger):
    mocker.patch.object(Writer.Config, 'MAX_JSON_RETRIES', 2)
    interface_instance = Writer.Interface.Wrapper.Interface(Models=[])

    invalid_json_response_messages = [{"role": "user", "content": "Q"}, {"role": "assistant", "content": "not json"}]
    invalid_json_response_tuple = (invalid_json_response_messages, None,0,0)

    valid_json_str = '{"key": "fixed"}'
    successful_messages_list = [
        {"role": "user", "content": "Q"},
        {"role": "assistant", "content": valid_json_str}
    ]
    valid_json_response_tuple = (successful_messages_list, {"prompt_tokens":1,"completion_tokens":1},10,2)

    mock_chat_stream_method = mocker.patch.object(interface_instance, "ChatAndStreamResponse")
    mock_chat_stream_method.side_effect = [invalid_json_response_tuple, valid_json_response_tuple]

    messages_history = [{"role": "user", "content": "Q"}]
    _, json_obj, _ = interface_instance.SafeGenerateJSON(mock_logger, messages_history, "mock_model_key", _max_retries_override=2)

    assert json_obj == {"key": "fixed"}
    assert mock_chat_stream_method.call_count == 2
    found_log = False
    for call_args in mock_logger.Log.call_args_list:
        # Corrected log check for this test (JSON error)
        expected_log_msg_part = "Error parsing JSON"
        expected_retry_count_part = "Retry 1/2"
        if expected_log_msg_part in call_args[0][0] and \
           expected_retry_count_part in call_args[0][0] and \
           call_args[0][1] == 7:
            found_log = True
            break
    assert found_log, f"Log message for '{expected_log_msg_part} with {expected_retry_count_part}' not found."


def test_safe_generate_json_repair_with_json_repair(mocker, mock_logger):
    mocker.patch.object(Writer.Config, 'MAX_JSON_RETRIES', 1)
    interface_instance = Writer.Interface.Wrapper.Interface(Models=[])

    malformed_json_str = '{"key": "value", "num": 123,}'
    mock_chat_response_tuple = ([{"role": "user", "content": "Q"}, {"role": "assistant", "content": malformed_json_str}], {"prompt_tokens":1,"completion_tokens":1},10,2)
    mocker.patch.object(interface_instance, "ChatAndStreamResponse", return_value=mock_chat_response_tuple)

    messages_history = [{"role": "user", "content": "Q"}]
    _, json_obj, _ = interface_instance.SafeGenerateJSON(mock_logger, messages_history, "mock_model_key")

    assert json_obj == {"key": "value", "num": 123}
    interface_instance.ChatAndStreamResponse.assert_called_once()

def test_safe_generate_json_cleans_markdown(mocker, mock_logger):
    mocker.patch.object(Writer.Config, 'MAX_JSON_RETRIES', 1)
    interface_instance = Writer.Interface.Wrapper.Interface(Models=[])

    json_with_markdown = '```json\n{"key": "value"}\n```'
    mock_chat_response_tuple = ([{"role": "user", "content": "Q"}, {"role": "assistant", "content": json_with_markdown}], {"prompt_tokens":1,"completion_tokens":1},10,2)
    mocker.patch.object(interface_instance, "ChatAndStreamResponse", return_value=mock_chat_response_tuple)

    messages_history = [{"role": "user", "content": "Q"}]
    _, json_obj, _ = interface_instance.SafeGenerateJSON(mock_logger, messages_history, "mock_model_key")

    assert json_obj == {"key": "value"}
    interface_instance.ChatAndStreamResponse.assert_called_once()

def test_safe_generate_json_max_retries_exceeded(mocker, mock_logger):
    max_json_retries_config = 2
    mocker.patch.object(Writer.Config, 'MAX_JSON_RETRIES', max_json_retries_config)
    interface_instance = Writer.Interface.Wrapper.Interface(Models=[])

    invalid_json_response_tuple = ([{"role": "user", "content": "Q"}, {"role": "assistant", "content": "not json"}], None,0,0)
    mock_chat_stream_method = mocker.patch.object(interface_instance, "ChatAndStreamResponse", return_value=invalid_json_response_tuple)

    messages_history = [{"role": "user", "content": "Q"}]
    with pytest.raises(Exception, match=f"Failed to generate valid JSON after {max_json_retries_config} retries"):
        interface_instance.SafeGenerateJSON(mock_logger, messages_history, "mock_model_key", _max_retries_override=max_json_retries_config)

    assert mock_chat_stream_method.call_count == max_json_retries_config

def test_get_last_message_text(mocker):
    interface_instance = Writer.Interface.Wrapper.Interface(Models=[])
    messages = [{"role":"user", "content":"Hi"}, {"role":"assistant", "content":"Hello there"}]
    assert interface_instance.GetLastMessageText(messages) == "Hello there"

def test_get_last_message_text_empty_list(mocker):
    interface_instance = Writer.Interface.Wrapper.Interface(Models=[])
    messages_empty = []
    assert interface_instance.GetLastMessageText(messages_empty) == ""
