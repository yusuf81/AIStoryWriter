"""
vLLM Provider Compliance Tests

TDD London School approach: Tests written first (RED phase)
to document expected behavior before implementation.

These tests verify that vLLM provider follows
the same patterns as existing OpenAI-compatible providers (Synthetic, OpenRouter).
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock

import Writer.Config
from Writer.Interface.Wrapper import Interface


class TestVLLMCompliance:
    """
    Test vLLM provider compliance with existing patterns.

    Following London School TDD:
    - RED: Tests fail initially because feature is not implemented
    - GREEN: Implement minimum code to make tests pass
    - REFACTOR: Clean up while keeping tests green
    """

    def test_vllm_max_retries_config_exists(self):
        """
        RED: Test fails because MAX_VLLM_RETRIES is not defined in Config.py

        Expected: After fix, Config should have MAX_VLLM_RETRIES = 2
        Actual: Currently not defined
        """
        assert hasattr(Writer.Config, 'MAX_VLLM_RETRIES'), \
            "MAX_VLLM_RETRIES should be defined in Config"
        assert getattr(Writer.Config, 'MAX_VLLM_RETRIES') == 2, \
            "MAX_VLLM_RETRIES should be 2"

    def test_vllm_api_url_config_exists(self):
        """
        RED: Test fails because VLLM_API_URL is not defined

        Expected: After fix, Config should have VLLM_API_URL with correct value
        """
        assert hasattr(Writer.Config, 'VLLM_API_URL'), \
            "VLLM_API_URL should be defined in Config"
        assert 'localhost:8000' in getattr(Writer.Config, 'VLLM_API_URL', ''), \
            "VLLM_API_URL should contain localhost:8000"

    def test_vllm_host_config_exists(self):
        """
        RED: Test fails because VLLM_HOST is not defined

        Expected: After fix, Config should have VLLM_HOST with correct value
        """
        assert hasattr(Writer.Config, 'VLLM_HOST'), \
            "VLLM_HOST should be defined in Config"
        assert 'localhost:8000' in getattr(Writer.Config, 'VLLM_HOST', ''), \
            "VLLM_HOST should contain localhost:8000"

    def test_vllm_timeout_config_exists(self):
        """
        RED: Test fails because VLLM_TIMEOUT is not defined

        Expected: After fix, Config should have VLLM_TIMEOUT = 300 (5 minutes)
        Note: Quantized models with structured output need longer timeout
        """
        assert hasattr(Writer.Config, 'VLLM_TIMEOUT'), \
            "VLLM_TIMEOUT should be defined in Config"
        assert getattr(Writer.Config, 'VLLM_TIMEOUT') >= 300, \
            "VLLM_TIMEOUT should be at least 300 seconds for quantized models"

    def test_vllm_frequency_penalty_config_exists(self):
        """
        RED: Test fails because VLLM_FREQUENCY_PENALTY is not defined

        Expected: After fix, Config should have VLLM_FREQUENCY_PENALTY = 0.5
        """
        assert hasattr(Writer.Config, 'VLLM_FREQUENCY_PENALTY'), \
            "VLLM_FREQUENCY_PENALTY should be defined in Config"

    def test_vllm_presence_penalty_config_exists(self):
        """
        RED: Test fails because VLLM_PRESENCE_PENALTY is not defined

        Expected: After fix, Config should have VLLM_PRESENCE_PENALTY = 0.3
        """
        assert hasattr(Writer.Config, 'VLLM_PRESENCE_PENALTY'), \
            "VLLM_PRESENCE_PENALTY should be defined in Config"

    def test_vllm_chat_handler_exists(self):
        """
        RED: Test fails because _vllm_chat method is not implemented

        Expected: After fix, Interface should have _vllm_chat method
        """
        interface = Interface([])
        assert hasattr(interface, '_vllm_chat'), \
            "_vllm_chat method should exist on Interface"
        assert callable(getattr(interface, '_vllm_chat')), \
            "_vllm_chat should be callable"

    def test_loadmodels_creates_vllm_client(self):
        """
        RED: Test fails because LoadModels doesn't handle 'vllm' provider

        Expected: After fix, LoadModels should create OpenAI client with vLLM base_url
        """
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            interface = Interface(Models=["vllm://meta-llama/Llama-3.1-8B-Instruct"])

            # Verify client was created and stored
            assert "vllm://meta-llama/Llama-3.1-8B-Instruct" in interface.Clients, \
                "Client should be stored in Clients dict"

    def test_vllm_uses_openai_library_with_correct_base_url(self):
        """
        RED: Test fails because LoadModels doesn't initialize OpenAI with vLLM base_url

        Expected: After fix, OpenAI should be called with base_url='http://localhost:8000/v1'
        """
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            interface = Interface([])
            interface.LoadModels(["vllm://meta-llama/Llama-3.1-8B-Instruct"])

            # Verify OpenAI was called with correct parameters
            assert mock_openai.called, \
                "OpenAI class should be instantiated"
            call_kwargs = mock_openai.call_args[1]
            assert 'base_url' in call_kwargs, \
                "base_url should be passed to OpenAI"
            assert 'localhost:8000' in call_kwargs['base_url'], \
                "base_url should point to vLLM API"
            assert call_kwargs['api_key'] == os.environ.get('VLLM_API_KEY', 'dummy'), \
                "api_key should use 'dummy' fallback for local vLLM"

    def test_vllm_uses_openai_library_with_timeout_and_retries(self):
        """
        RED: Test fails because OpenAI initialization doesn't include timeout/max_retries

        Expected: After fix, OpenAI should be configured with timeout and max_retries from Config
        """
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            interface = Interface([])
            interface.LoadModels(["vllm://test-model"])

            call_kwargs = mock_openai.call_args[1]
            assert 'timeout' in call_kwargs, \
                "timeout should be configured"
            assert 'max_retries' in call_kwargs, \
                "max_retries should be configured"

    def test_vllm_uses_custom_host_when_specified(self):
        """
        RED: Test fails because LoadModels doesn't handle custom host from environment

        Expected: After fix, should use VLLM_API_URL from config when Host is None
        Note: For vLLM, custom hosts should be specified via VLLM_API_URL config,
        not in the model URL. The model URL format is vllm://model-name.
        """
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            interface = Interface([])
            interface.LoadModels(["vllm://model-name"])

            call_kwargs = mock_openai.call_args[1]
            assert 'localhost:8000' in call_kwargs['base_url'], \
                "base_url should use VLLM_API_URL from config"

    def test_getmodeland_provider_parses_vllm_url(self):
        """
        RED: May fail if GetModelAndProvider doesn't handle 'vllm' scheme

        Expected: Should parse vllm://model-name correctly
        """
        interface = Interface([])
        provider, model, host, params = interface.GetModelAndProvider(
            "vllm://meta-llama/Llama-3.1-8B-Instruct"
        )
        assert provider == "vllm", \
            f"Provider should be 'vllm', got '{provider}'"
        assert model == "meta-llama/Llama-3.1-8B-Instruct", \
            f"Model should be 'meta-llama/Llama-3.1-8B-Instruct', got '{model}'"
        assert host is None, \
            f"Host should be None for vllm:// URLs without @, got {host}"
        assert params is None, \
            f"Params should be None for URLs without query string, got {params}"

    def test_getmodeland_provider_parses_vllm_url_with_host(self):
        """
        RED: May fail if GetModelAndProvider doesn't parse host from vllm:// URLs

        Expected: Should parse vllm://host/model correctly (host in netloc, model in path)
        """
        interface = Interface([])
        provider, model, host, params = interface.GetModelAndProvider(
            "vllm://10.0.0.1:8000/meta-llama/Llama-3.1-8B-Instruct"
        )
        assert provider == "vllm", \
            f"Provider should be 'vllm', got '{provider}'"
        assert model == "10.0.0.1:8000/meta-llama/Llama-3.1-8B-Instruct", \
            f"Model should be '10.0.0.1:8000/meta-llama/Llama-3.1-8B-Instruct', got '{model}'"
        # Host is None because @ format is not used
        assert host is None, \
            f"Host should be None for vllm:// URLs without @, got {host}"
        assert params is None, \
            f"Params should be None for URLs without query string, got {params}"

    def test_getmodeland_provider_parses_vllm_url_with_path(self):
        """
        RED: May fail if GetModelAndProvider doesn't parse path correctly

        Expected: Should combine netloc and path for model name
        """
        interface = Interface([])
        provider, model, host, params = interface.GetModelAndProvider(
            "vllm://org/model-name/fine-tune"
        )
        assert provider == "vllm", \
            f"Provider should be 'vllm', got '{provider}'"
        assert model == "org/model-name/fine-tune", \
            f"Model should be 'org/model-name/fine-tune', got '{model}'"

    def test_getmodeland_provider_parses_vllm_with_temperature(self):
        """
        RED: May fail if GetModelAndProvider doesn't parse query parameters

        Expected: Should parse query parameters from vllm:// URLs
        """
        interface = Interface([])
        provider, model, host, params = interface.GetModelAndProvider(
            "vllm://meta-llama/Llama-3.1-8B-Instruct?temperature=0.8"
        )
        assert provider == "vllm"
        assert model == "meta-llama/Llama-3.1-8B-Instruct"
        assert params is not None, \
            "Params should not be None when query string present"
        assert 'temperature' in params, \
            f"Params should contain 'temperature', got {params}"
        assert params['temperature'] == 0.8, \
            f"temperature should be 0.8, got {params['temperature']}"

    def test_vllm_loadmodels_works_without_api_key(self):
        """
        RED: Test fails because LoadModels requires VLLM_API_KEY

        Expected: Should work without API key (local vLLM doesn't need it)
        """
        # Ensure API key is not set
        with patch.dict(os.environ, {}, clear=False):
            if 'VLLM_API_KEY' in os.environ:
                del os.environ['VLLM_API_KEY']

            with patch('openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client

                interface = Interface([])
                interface.LoadModels(["vllm://test-model"])

                # Should succeed without API key
                assert "vllm://test-model" in interface.Clients


class TestVLLMChatHandler:
    """
    Test _vllm_chat method implementation.
    """

    @pytest.fixture
    def mock_logger(self):
        """Factory for creating mock Logger"""
        logger = MagicMock(name='mock_logger')
        logger.Log = MagicMock()
        logger.logs = []

        def log_side_effect(msg, lvl):
            logger.logs.append((lvl, msg))

        logger.Log.side_effect = log_side_effect
        return logger

    def test_vllm_chat_calls_openai_completions(self, mock_logger):
        """
        RED: Test fails because _vllm_chat doesn't use OpenAI client correctly

        Expected: Should call client.chat.completions.create with correct parameters
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            # Mock the completion response
            mock_response = Mock()
            mock_choice = Mock()
            mock_choice.message.content = "Test response content"
            mock_response.choices = [mock_choice]
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5
            mock_response.usage.total_tokens = 15
            mock_openai.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.Clients["vllm://test-model"] = mock_openai

            messages, usage = interface._vllm_chat(
                _Logger=mock_logger,
                _Model_key="vllm://test-model",
                ProviderModel_name="test-model",
                _Messages_list=[{"role": "user", "content": "test message"}],
                ModelOptions_dict={},
                Seed_int=42,
                _FormatSchema_dict=None
            )

            # Verify OpenAI API was called
            assert mock_openai.chat.completions.create.called, \
                "OpenAI chat.completions.create should be called"

            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            assert call_kwargs['model'] == "test-model", \
                f"model should be 'test-model', got {call_kwargs.get('model')}"
            assert 'messages' in call_kwargs, \
                "messages should be in call parameters"
            assert call_kwargs['messages'] == [{"role": "user", "content": "test message"}], \
                "messages should match input"

    def test_vllm_chat_has_retry_logic(self, mock_logger):
        """
        RED: Test fails because _vllm_chat doesn't have retry logic

        Expected: Should retry on failure and succeed after retries
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            # Mock first call to fail, second to succeed
            mock_response = Mock()
            mock_choice = Mock()
            mock_choice.message.content = "Success after retry"
            mock_response.choices = [mock_choice]
            mock_response.usage.prompt_tokens = 5
            mock_response.usage.completion_tokens = 3

            mock_openai.chat.completions.create.side_effect = [
                Exception("API Error - temporary"),
                mock_response
            ]

            interface = Interface([])
            interface.Clients["vllm://test"] = mock_openai

            # Should succeed after retry
            messages, usage = interface._vllm_chat(
                _Logger=mock_logger,
                _Model_key="vllm://test",
                ProviderModel_name="test",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},
                Seed_int=42,
                _FormatSchema_dict=None
            )

            assert mock_openai.chat.completions.create.call_count == 2, \
                f"Should retry once (2 calls total), got {mock_openai.chat.completions.create.call_count}"

    def test_vllm_chat_returns_correct_format(self, mock_logger):
        """
        RED: Test fails because _vllm_chat doesn't return correct format

        Expected: Should return (FullResponseMessages, TokenUsage) tuple
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            mock_response = Mock()
            mock_choice = Mock()
            mock_choice.message.content = "Response content"
            mock_response.choices = [mock_choice]
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5
            mock_openai.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.Clients["vllm://test"] = mock_openai

            messages, usage = interface._vllm_chat(
                _Logger=mock_logger,
                _Model_key="vllm://test",
                ProviderModel_name="test",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},
                Seed_int=42,
                _FormatSchema_dict=None
            )

            # Check return format
            assert isinstance(messages, list), \
                f"First return value should be list, got {type(messages)}"
            assert messages[-1]["role"] == "assistant", \
                f"Last message should be assistant, got {messages[-1]['role']}"
            assert messages[-1]["content"] == "Response content", \
                "Content should match response"

            assert isinstance(usage, dict), \
                f"Second return value should be dict, got {type(usage)}"
            assert 'prompt_tokens' in usage, \
                f"usage should have prompt_tokens, got {list(usage.keys())}"
            assert 'completion_tokens' in usage, \
                f"usage should have completion_tokens, got {list(usage.keys())}"

    def test_vllm_chat_handles_format_schema(self, mock_logger):
        """
        RED: Test fails because _vllm_chat doesn't handle structured output

        Expected: Should use response_format parameter for JSON output
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            mock_response = Mock()
            mock_choice = Mock()
            mock_choice.message.content = '{"result": "json"}'
            mock_response.choices = [mock_choice]
            mock_response.usage.prompt_tokens = 5
            mock_response.usage.completion_tokens = 3
            mock_openai.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.Clients["vllm://test"] = mock_openai

            # Call with FormatSchema (structured output)
            format_schema = {
                "type": "object",
                "properties": {
                    "result": {"type": "string"}
                }
            }

            messages, usage = interface._vllm_chat(
                _Logger=mock_logger,
                _Model_key="vllm://test",
                ProviderModel_name="test",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},
                Seed_int=42,
                _FormatSchema_dict=format_schema
            )

            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            assert 'response_format' in call_kwargs, \
                "response_format should be set for structured output"

    def test_vllm_uses_json_schema_name_wrapper(self, mock_logger):
        """
        RED: Test fails because _build_response_format doesn't wrap vLLM schemas

        Expected: vLLM should use {name, schema} wrapper format for structured output
        (OpenAI-compatible format requires 'name' field in json_schema)
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            mock_response = Mock()
            mock_choice = Mock()
            mock_choice.message.content = '{"result": "json"}'
            mock_response.choices = [mock_choice]
            mock_response.usage.prompt_tokens = 5
            mock_response.usage.completion_tokens = 3
            mock_openai.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.Clients["vllm://test"] = mock_openai

            # Call with FormatSchema (structured output)
            format_schema = {
                "type": "object",
                "properties": {
                    "result": {"type": "string"}
                }
            }

            messages, usage = interface._vllm_chat(
                _Logger=mock_logger,
                _Model_key="vllm://test",
                ProviderModel_name="test",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},
                Seed_int=42,
                _FormatSchema_dict=format_schema
            )

            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            response_format = call_kwargs.get('response_format', {})

            # vLLM requires OpenAI-compatible format with {name, schema} wrapper
            assert response_format.get('type') == 'json_schema', \
                "response_format type should be json_schema"
            json_schema = response_format.get('json_schema', {})
            assert 'name' in json_schema, \
                "json_schema must have 'name' field (OpenAI-compatible format)"
            assert 'schema' in json_schema, \
                "json_schema must have 'schema' field wrapping the actual schema"
            assert json_schema['schema'] == format_schema, \
                "Wrapped schema should match original format_schema"

    def test_vllm_chat_non_streaming(self, mock_logger):
        """
        RED: Test fails if _vllm_chat uses streaming

        Expected: Should NOT pass stream=True (use default non-streaming)
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            mock_response = Mock()
            mock_choice = Mock()
            mock_choice.message.content = "Response"
            mock_response.choices = [mock_choice]
            mock_response.usage.prompt_tokens = 5
            mock_response.usage.completion_tokens = 3
            mock_openai.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.Clients["vllm://test"] = mock_openai

            messages, usage = interface._vllm_chat(
                _Logger=mock_logger,
                _Model_key="vllm://test",
                ProviderModel_name="test",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},
                Seed_int=42,
                _FormatSchema_dict=None
            )

            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            # stream should NOT be True (default is False)
            assert call_kwargs.get('stream') is not True, \
                "stream should not be True (should use non-streaming mode)"

    def test_vllm_chat_applies_frequency_penalty(self, mock_logger):
        """
        RED: Test fails because _vllm_chat doesn't apply repetition penalties

        Expected: Should apply frequency_penalty from Config for free-form generation
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            mock_response = Mock()
            mock_choice = Mock()
            mock_choice.message.content = "Response"
            mock_response.choices = [mock_choice]
            mock_response.usage.prompt_tokens = 5
            mock_response.usage.completion_tokens = 3
            mock_openai.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.Clients["vllm://test"] = mock_openai

            # Call without FormatSchema (free-form generation)
            messages, usage = interface._vllm_chat(
                _Logger=mock_logger,
                _Model_key="vllm://test",
                ProviderModel_name="test",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},  # No frequency_penalty specified
                Seed_int=42,
                _FormatSchema_dict=None  # Free-form generation
            )

            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            assert 'frequency_penalty' in call_kwargs, \
                "frequency_penalty should be applied for free-form generation"

    def test_vllm_chat_raises_after_max_retries(self, mock_logger):
        """
        RED: Test fails because _vllm_chat doesn't raise after max retries

        Expected: Should raise Exception after all retries exhausted
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            # All calls fail
            mock_openai.chat.completions.create.side_effect = Exception("Persistent error")

            interface = Interface([])
            interface.Clients["vllm://test"] = mock_openai

            with pytest.raises(Exception) as exc_info:
                interface._vllm_chat(
                    _Logger=mock_logger,
                    _Model_key="vllm://test",
                    ProviderModel_name="test",
                    _Messages_list=[{"role": "user", "content": "test"}],
                    ModelOptions_dict={},
                    Seed_int=42,
                    _FormatSchema_dict=None
                )

            assert "vLLM" in str(exc_info.value) or "chat failed" in str(exc_info.value), \
                "Exception should mention vLLM or chat failed"

    def test_vllm_chat_applies_repetition_penalty(self, mock_logger):
        """
        RED: Test fails because _vllm_chat doesn't apply vLLM-native repetition_penalty

        Expected: Should apply repetition_penalty from Config (>1.0 reduces repetition)
        Note: vLLM-native parameters are passed via extra_body, not directly to create()
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            mock_response = Mock()
            mock_choice = Mock()
            mock_choice.message.content = "Response"
            mock_response.choices = [mock_choice]
            mock_response.usage.prompt_tokens = 5
            mock_response.usage.completion_tokens = 3
            mock_openai.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.Clients["vllm://test"] = mock_openai

            messages, usage = interface._vllm_chat(
                _Logger=mock_logger,
                _Model_key="vllm://test",
                ProviderModel_name="test",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},  # No repetition_penalty specified
                Seed_int=42,
                _FormatSchema_dict=None
            )

            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            assert 'extra_body' in call_kwargs, \
                "vLLM-native parameters should be passed via extra_body"
            assert call_kwargs['extra_body']['repetition_penalty'] > 1.0, \
                f"repetition_penalty should be > 1.0, got {call_kwargs['extra_body']['repetition_penalty']}"

    def test_vllm_chat_applies_top_p_sampling(self, mock_logger):
        """
        RED: Test fails because _vllm_chat doesn't apply top_p sampling

        Expected: Should apply top_p from Config (nucleus sampling)
        Note: vLLM-native parameters are passed via extra_body
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            mock_response = Mock()
            mock_choice = Mock()
            mock_choice.message.content = "Response"
            mock_response.choices = [mock_choice]
            mock_response.usage.prompt_tokens = 5
            mock_response.usage.completion_tokens = 3
            mock_openai.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.Clients["vllm://test"] = mock_openai

            messages, usage = interface._vllm_chat(
                _Logger=mock_logger,
                _Model_key="vllm://test",
                ProviderModel_name="test",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},  # No top_p specified
                Seed_int=42,
                _FormatSchema_dict=None
            )

            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            assert 'extra_body' in call_kwargs, \
                "vLLM-native parameters should be passed via extra_body"
            assert 0 < call_kwargs['extra_body']['top_p'] <= 1.0, \
                f"top_p should be in (0, 1], got {call_kwargs['extra_body']['top_p']}"

    def test_vllm_chat_applies_top_k_sampling(self, mock_logger):
        """
        RED: Test fails because _vllm_chat doesn't apply top_k sampling

        Expected: Should apply top_k from Config (limits vocabulary)
        Note: vLLM-native parameters are passed via extra_body
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            mock_response = Mock()
            mock_choice = Mock()
            mock_choice.message.content = "Response"
            mock_response.choices = [mock_choice]
            mock_response.usage.prompt_tokens = 5
            mock_response.usage.completion_tokens = 3
            mock_openai.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.Clients["vllm://test"] = mock_openai

            messages, usage = interface._vllm_chat(
                _Logger=mock_logger,
                _Model_key="vllm://test",
                ProviderModel_name="test",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},  # No top_k specified
                Seed_int=42,
                _FormatSchema_dict=None
            )

            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            assert 'extra_body' in call_kwargs, \
                "vLLM-native parameters should be passed via extra_body"
            assert call_kwargs['extra_body']['top_k'] > 0, \
                f"top_k should be > 0, got {call_kwargs['extra_body']['top_k']}"

    def test_vllm_chat_applies_stop_tokens(self, mock_logger):
        """
        RED: Test fails because _vllm_chat doesn't apply stop tokens

        Expected: Should apply stop tokens from Config (prevent character explosion)
        Note: stop IS OpenAI-compatible, so it goes directly in ReqOptions
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            mock_response = Mock()
            mock_choice = Mock()
            mock_choice.message.content = "Response"
            mock_response.choices = [mock_choice]
            mock_response.usage.prompt_tokens = 5
            mock_response.usage.completion_tokens = 3
            mock_openai.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.Clients["vllm://test"] = mock_openai

            messages, usage = interface._vllm_chat(
                _Logger=mock_logger,
                _Model_key="vllm://test",
                ProviderModel_name="test",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},  # No stop specified
                Seed_int=42,
                _FormatSchema_dict=None
            )

            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            # stop tokens ARE OpenAI-compatible, so they go directly in call_kwargs
            assert 'stop' in call_kwargs, \
                "stop tokens should be applied from VLLM_STOP_TOKENS config"
            assert isinstance(call_kwargs['stop'], list), \
                f"stop should be a list, got {type(call_kwargs['stop'])}"

    def test_vllm_dynamic_max_tokens_reduces_when_context_limited(self, mock_logger):
        """
        RED: Test fails because _vllm_chat doesn't calculate dynamic max_tokens

        Expected: When input tokens + requested max_tokens > context length,
        max_tokens should be reduced to fit within context window.

        Example: context=16384, input=12625, requested=4096
        Available = 16384 - 12625 - 100 (buffer) = 3659
        max_tokens should be min(4096, 3659) = 3659
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            mock_response = Mock()
            mock_choice = Mock()
            mock_choice.message.content = "Response"
            mock_response.choices = [mock_choice]
            mock_response.usage.prompt_tokens = 12625
            mock_response.usage.completion_tokens = 100
            mock_openai.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.Clients["vllm://test"] = mock_openai

            # Create a large message list to simulate high input token count
            # Each message ~100 chars = ~22 tokens (using 4.5 chars/token estimate)
            # Need ~12625 tokens = ~56812 chars
            large_content = "x" * 56000  # ~12444 tokens estimated

            messages, usage = interface._vllm_chat(
                _Logger=mock_logger,
                _Model_key="vllm://test",
                ProviderModel_name="test",
                _Messages_list=[{"role": "user", "content": large_content}],
                ModelOptions_dict={},
                Seed_int=42,
                _FormatSchema_dict={"type": "object"}  # Structured output triggers 4096 default
            )

            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            max_tokens = call_kwargs.get('max_tokens', 0)

            # With 16384 context, ~12444 input tokens, and 100 buffer:
            # Available = 16384 - 12444 - 100 = 3840
            # max_tokens should be <= available (not the default 4096)
            assert max_tokens < 4096, \
                f"max_tokens should be reduced from 4096 when context is limited, got {max_tokens}"
            assert max_tokens >= 256, \
                f"max_tokens should be at least 256 (minimum), got {max_tokens}"

    def test_vllm_dynamic_max_tokens_uses_full_when_context_sufficient(self, mock_logger):
        """
        RED: Test that max_tokens stays at requested value when context is sufficient

        Expected: When input tokens + requested max_tokens < context length,
        max_tokens should use the full requested value.
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            mock_response = Mock()
            mock_choice = Mock()
            mock_choice.message.content = "Response"
            mock_response.choices = [mock_choice]
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50
            mock_openai.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.Clients["vllm://test"] = mock_openai

            # Small message - plenty of context available
            messages, usage = interface._vllm_chat(
                _Logger=mock_logger,
                _Model_key="vllm://test",
                ProviderModel_name="test",
                _Messages_list=[{"role": "user", "content": "short message"}],
                ModelOptions_dict={},
                Seed_int=42,
                _FormatSchema_dict={"type": "object"}  # Structured output
            )

            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            max_tokens = call_kwargs.get('max_tokens', 0)

            # With small input, should use full requested max_tokens (4096 for structured)
            assert max_tokens == 4096, \
                f"max_tokens should be 4096 when context is sufficient, got {max_tokens}"
