import pytest
from pytest_mock import MockerFixture # For type hinting mocker
from Writer.Interface.Wrapper import Interface
import Writer.Config # To access config values like retry limits
import json_repair # To potentially mock it
import Writer.PrintUtils # For potential logger mocking if needed

class TestGetModelAndProvider:
    def setup_method(self):
        self.interface = Interface(Models=[]) # No models needed for GetModelAndProvider

    @pytest.mark.parametrize(
        "model_str, expected_provider, expected_model_name, expected_host, expected_params",
        [
            ("llama3", "ollama", "llama3", Writer.Config.OLLAMA_HOST, None),
            ("ollama://my-model", "ollama", "my-model", Writer.Config.OLLAMA_HOST, None),
            ("ollama://custom-model@myhost.com:12345", "ollama", "custom-model", "myhost.com:12345", None),
            ("ollama://another/model@otherhost?temperature=0.5&seed=42", "ollama", "another/model", "otherhost", {"temperature": 0.5, "seed": 42.0}),
            ("google://gemini-pro", "google", "gemini-pro", None, None),
            ("openrouter://google/gemini-flash-1.5", "openrouter", "google/gemini-flash-1.5", None, None),
            ("openrouter://anthropic/claude-3-opus?temperature=0.8", "openrouter", "anthropic/claude-3-opus", None, {"temperature": 0.8}),
        ],
    )
    def test_get_model_and_provider_valid(
        self, model_str, expected_provider, expected_model_name, expected_host, expected_params
    ):
        provider, model_name, host, params = self.interface.GetModelAndProvider(model_str)
        assert provider == expected_provider
        assert model_name == expected_model_name
        assert host == expected_host
        assert params == expected_params

    def test_get_model_and_provider_ollama_with_path_and_host(self):
        # This tests a specific case from the original code for ollama with path and host
        model_str = "ollama://models/ollama/mistral@localhost:11434"
        # urlparse(model_str) gives:
        # scheme='ollama', netloc='models', path='/ollama/mistral@localhost:11434', query=''
        # Original GetModelAndProvider logic for "ollama" with "@" in path:
        # Model = parsed.netloc + parsed.path.split("@")[0] -> "models" + "/ollama/mistral"
        # Host = parsed.path.split("@")[1] -> "localhost:11434"
        provider, model_name, host, params = self.interface.GetModelAndProvider(model_str)
        assert provider == "ollama"
        assert model_name == "models/ollama/mistral"
        assert host == "localhost:11434"
        assert params is None

    @pytest.mark.parametrize(
        "model_str, expected_provider, expected_model_name, expected_host, expected_params",
        [
            ("ollama://microsoft%2Fphi-3", "ollama", "microsoft/phi-3", Writer.Config.OLLAMA_HOST, None),
            ("openrouter://google%2Fgemini-flash-1.5", "openrouter", "google/gemini-flash-1.5", None, None),
            ("openrouter://anthropic%2Fclaude-3-opus", "openrouter", "anthropic/claude-3-opus", None, None),
            ("ollama://model%20with%20spaces", "ollama", "model with spaces", Writer.Config.OLLAMA_HOST, None),
            ("ollama://model%20name?temperature=0.7", "ollama", "model name", Writer.Config.OLLAMA_HOST, {"temperature": 0.7}),
            ("ollama://test%3Fmodel%3Dtrue", "ollama", "test?model=true", Writer.Config.OLLAMA_HOST, None),
        ],
    )
    def test_get_model_and_provider_url_encoded(
        self, model_str, expected_provider, expected_model_name, expected_host, expected_params
    ):
        """Test URL encoded characters in model names are properly decoded."""
        provider, model_name, host, params = self.interface.GetModelAndProvider(model_str)
        assert provider == expected_provider
        assert model_name == expected_model_name
        assert host == expected_host
        assert params == expected_params

class TestRemoveThinkTagFromAssistantMessages:
    def setup_method(self):
        self.interface = Interface(Models=[])

    def test_remove_simple_thinking_tag(self):
        """Test basic thinking tag removal with simple content."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "<thinking>This is thinking</thinking>\n\nHello, how can I help?"}
        ]
        cleaned = self.interface.RemoveThinkTagFromAssistantMessages(messages)
        assert cleaned[0]["content"] == "Hello"
        assert cleaned[1]["content"] == "Hello, how can I help?"

    def test_remove_multiline_thinking_tag(self):
        """Test thinking tag removal with multiline content."""
        messages = [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "<thinking>\nLet me think about this step by step.\nFirst, I should consider...\n</thinking>\n\nThe answer is 42."}
        ]
        cleaned = self.interface.RemoveThinkTagFromAssistantMessages(messages)
        assert cleaned[1]["content"] == "The answer is 42."

    def test_handle_unpaired_tag(self):
        """Test removal when thinking tag is not closed."""
        messages = [
            {"role": "user", "content": "Ask"},
            {"role": "assistant", "content": "<thinking>I need to think but the tag is not closed\n\nStill thinking...\nFinal answer."}
        ]
        cleaned = self.interface.RemoveThinkTagFromAssistantMessages(messages)
        # Unpaired tags remove everything after the tag since we can't reliably determine boundaries
        assert cleaned[1]["content"] == ""

    def test_preserve_non_assistant_messages(self):
        """Test that messages without thinking tags are unchanged."""
        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "Normal message"},
            {"role": "assistant", "content": "<thinking>Think</thinking>Response"},
        ]
        cleaned = self.interface.RemoveThinkTagFromAssistantMessages(messages)
        # System and user messages unchanged
        assert cleaned[0]["content"] == "System message"
        assert cleaned[1]["content"] == "Normal message"
        # Assistant message cleaned
        assert cleaned[2]["content"] == "Response"

    def test_handle_malformed_messages(self):
        """Test handling of various malformed message structures."""
        # String message
        messages = ["just a string"]
        cleaned = self.interface.RemoveThinkTagFromAssistantMessages(messages)
        assert cleaned == messages

        # Empty list
        cleaned = self.interface.RemoveThinkTagFromAssistantMessages([])
        assert cleaned == []

        # None input
        cleaned = self.interface.RemoveThinkTagFromAssistantMessages(None)
        assert cleaned is None

        # Dict without role/content
        messages = [{"other": "data"}]
        cleaned = self.interface.RemoveThinkTagFromAssistantMessages(messages)
        assert cleaned == messages

    def test_multiple_assistant_messages(self):
        """Test thinking tag removal in multiple assistant messages."""
        messages = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "<thinking>Think 1</thinking>Answer 1"},
            {"role": "user", "content": "Second"},
            {"role": "assistant", "content": "<thinking>Think 2</thinking>Answer 2"},
        ]
        cleaned = self.interface.RemoveThinkTagFromAssistantMessages(messages)
        assert cleaned[1]["content"] == "Answer 1"
        assert cleaned[3]["content"] == "Answer 2"

    def test_no_thinking_tag_unchanged(self):
        """Test that messages without thinking tags pass through unchanged."""
        messages = [
            {"role": "assistant", "content": "Just a normal response without any thinking tags."}
        ]
        cleaned = self.interface.RemoveThinkTagFromAssistantMessages(messages)
        assert cleaned == messages

class TestSafeGenerateText:
    @pytest.fixture(autouse=True)
    def setup(self, mock_logger):
        self.interface = Interface(Models=[])
        self.mock_logger = mock_logger()

    def test_safegen_text_valid_first_try(self, mocker: MockerFixture):
        mock_chat_response = mocker.patch.object(self.interface, "ChatAndStreamResponse")
        valid_response_messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there this is a valid response."}]
        mock_chat_response.return_value = (valid_response_messages, {"prompt_tokens": 10, "completion_tokens": 5}, 50, 10)

        messages_in = [{"role": "user", "content": "Hello"}]
        result_messages, token_usage = self.interface.SafeGenerateText(self.mock_logger, messages_in, "mock_model", _MinWordCount=3)

        assert result_messages == valid_response_messages
        assert token_usage == {"prompt_tokens": 10, "completion_tokens": 5}
        mock_chat_response.assert_called_once()

    def test_safegen_text_retry_on_empty(self, mocker: MockerFixture):
        mock_chat_response = mocker.patch.object(self.interface, "ChatAndStreamResponse")
        empty_response = [{"role": "user", "content": "Q"}, {"role": "assistant", "content": " "}]
        valid_response = [{"role": "user", "content": "Q"}, {"role": "assistant", "content": "Valid answer."}]

        mock_chat_response.side_effect = [
            (empty_response, {"prompt_tokens": 1, "completion_tokens": 1}, 5, 1),
            (valid_response, {"prompt_tokens": 1, "completion_tokens": 2}, 5, 1)
        ]

        messages_in = [{"role": "user", "content": "Q"}]
        result_messages, _ = self.interface.SafeGenerateText(self.mock_logger, messages_in, "mock_model", _MinWordCount=2)

        assert self.interface.GetLastMessageText(result_messages) == "Valid answer."
        assert mock_chat_response.call_count == 2

    def test_safegen_text_retry_on_short(self, mocker: MockerFixture):
        mock_chat_response = mocker.patch.object(self.interface, "ChatAndStreamResponse")
        short_response = [{"role": "user", "content": "Q"}, {"role": "assistant", "content": "Too short."}] # 2 words
        valid_response = [{"role": "user", "content": "Q"}, {"role": "assistant", "content": "Now this is long enough."}] # 6 words

        mock_chat_response.side_effect = [
            (short_response, {}, 0, 0),
            (valid_response, {}, 0, 0)
        ]

        messages_in = [{"role": "user", "content": "Q"}]
        result_messages, _ = self.interface.SafeGenerateText(self.mock_logger, messages_in, "mock_model", _MinWordCount=5)

        assert self.interface.GetLastMessageText(result_messages) == "Now this is long enough."
        assert mock_chat_response.call_count == 2

    def test_safegen_text_max_retries_exceeded(self, mocker: MockerFixture):
        mock_chat_response = mocker.patch.object(self.interface, "ChatAndStreamResponse")

        # Store original value to restore it later
        original_max_text_retries = Writer.Config.MAX_TEXT_RETRIES
        Writer.Config.MAX_TEXT_RETRIES = 2 # Lower for test

        responses = [([{"role": "user", "content": "Q"}, {"role": "assistant", "content": " "}], {}, 0, 0) for _ in range(Writer.Config.MAX_TEXT_RETRIES)]
        mock_chat_response.side_effect = responses

        messages_in = [{"role": "user", "content": "Q"}]
        with pytest.raises(Exception, match="Failed to generate valid text after"):
            self.interface.SafeGenerateText(self.mock_logger, messages_in, "mock_model", _MinWordCount=1)

        assert mock_chat_response.call_count == Writer.Config.MAX_TEXT_RETRIES
        Writer.Config.MAX_TEXT_RETRIES = original_max_text_retries # Restore original value

class TestSafeGenerateJSON:
    @pytest.fixture(autouse=True)
    def setup(self, mock_logger):
        self.interface = Interface(Models=[])
        self.mock_logger = mock_logger()

    def test_safegen_json_valid_first_try(self, mocker: MockerFixture):
        mock_chat_response = mocker.patch.object(self.interface, "ChatAndStreamResponse")
        valid_json_str = '{"key": "value", "number": 123}'
        expected_json_obj = {"key": "value", "number": 123}
        response_messages = [{"role": "user", "content": "Q"}, {"role": "assistant", "content": valid_json_str}]
        mock_chat_response.return_value = (response_messages, {"prompt_tokens":1, "completion_tokens":10}, 10, 2)

        messages_in = [{"role": "user", "content": "Q"}]
        _, result_json, _ = self.interface.SafeGenerateJSON(self.mock_logger, messages_in, "mock_model")

        assert result_json == expected_json_obj
        mock_chat_response.assert_called_once()

    def test_safegen_json_strips_markdown(self, mocker: MockerFixture):
        mock_chat_response = mocker.patch.object(self.interface, "ChatAndStreamResponse")
        json_with_markdown = '```json\n{"key": "value"}\n```'
        expected_json_obj = {"key": "value"}
        response_messages = [{"role": "user", "content": "Q"}, {"role": "assistant", "content": json_with_markdown}]
        mock_chat_response.return_value = (response_messages, {}, 0, 0)

        messages_in = [{"role": "user", "content": "Q"}]
        _, result_json, _ = self.interface.SafeGenerateJSON(self.mock_logger, messages_in, "mock_model")
        assert result_json == expected_json_obj

    def test_safegen_json_uses_json_repair(self, mocker: MockerFixture):
        mock_chat_response = mocker.patch.object(self.interface, "ChatAndStreamResponse")
        # We also need to mock json_repair.loads itself
        mock_json_repair_loads = mocker.patch("json_repair.loads")

        malformed_json_str = '{"key": "value", "error": True,}' # Trailing comma
        repaired_obj = {"key": "value", "error": True} # What json_repair should return
        mock_json_repair_loads.return_value = repaired_obj

        response_messages = [{"role": "user", "content": "Q"}, {"role": "assistant", "content": malformed_json_str}]
        mock_chat_response.return_value = (response_messages, {}, 0, 0)

        messages_in = [{"role": "user", "content": "Q"}]
        _, result_json, _ = self.interface.SafeGenerateJSON(self.mock_logger, messages_in, "mock_model")

        mock_json_repair_loads.assert_called_once_with(malformed_json_str)
        assert result_json == repaired_obj

    def test_safegen_json_retry_on_persistent_invalid(self, mocker: MockerFixture):
        mock_chat_response = mocker.patch.object(self.interface, "ChatAndStreamResponse")
        # Make json_repair.loads raise an error each time it's called
        mock_json_repair_loads = mocker.patch("json_repair.loads", side_effect=ValueError("parse error"))

        original_max_json_retries = Writer.Config.MAX_JSON_RETRIES
        Writer.Config.MAX_JSON_RETRIES = 2 # Lower for test

        # Prepare responses for ChatAndStreamResponse for each retry attempt
        invalid_json_responses = [
            ([{"role": "user", "content": "Q"}, {"role": "assistant", "content": "{invalid json}"}], {}, 0, 0) 
            for _ in range(Writer.Config.MAX_JSON_RETRIES)
        ]
        mock_chat_response.side_effect = invalid_json_responses

        messages_in = [{"role": "user", "content": "Q"}]
        with pytest.raises(Exception, match="Failed to generate valid JSON after"):
            self.interface.SafeGenerateJSON(self.mock_logger, messages_in, "mock_model")

        assert mock_chat_response.call_count == Writer.Config.MAX_JSON_RETRIES
        # json_repair.loads will be called for each response from ChatAndStreamResponse
        assert mock_json_repair_loads.call_count == Writer.Config.MAX_JSON_RETRIES
        Writer.Config.MAX_JSON_RETRIES = original_max_json_retries # Restore
