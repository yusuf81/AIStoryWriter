"""
Synthetic.dev Provider Compliance Tests

TDD London School approach: Tests written first (RED phase)
to document expected behavior before implementation.

These tests verify that Synthetic.dev provider follows
the same patterns as existing providers (Google, OpenRouter, Grok, Ollama).
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock

import Writer.Config
from Writer.Interface.Wrapper import Interface


class TestSyntheticCompliance:
    """
    Test Synthetic.dev provider compliance with existing patterns.

    Following London School TDD:
    - RED: Tests fail initially because feature is not implemented
    - GREEN: Implement minimum code to make tests pass
    - REFACTOR: Clean up while keeping tests green
    """

    def test_synthetic_max_retries_config_exists(self):
        """
        RED: Test fails because MAX_SYNTHETIC_RETRIES is not defined in Config.py

        Expected: After fix, Config should have MAX_SYNTHETIC_RETRIES = 2
        Actual: Currently not defined
        """
        assert hasattr(Writer.Config, 'MAX_SYNTHETIC_RETRIES'), \
            "MAX_SYNTHETIC_RETRIES should be defined in Config"
        assert getattr(Writer.Config, 'MAX_SYNTHETIC_RETRIES') == 2, \
            "MAX_SYNTHETIC_RETRIES should be 2"

    def test_synthetic_frequency_penalty_config_exists(self):
        """
        RED: Test fails because SYNTHETIC_FREQUENCY_PENALTY is not defined

        Expected: After fix, Config should have SYNTHETIC_FREQUENCY_PENALTY = 0.5
        """
        assert hasattr(Writer.Config, 'SYNTHETIC_FREQUENCY_PENALTY'), \
            "SYNTHETIC_FREQUENCY_PENALTY should be defined in Config"

    def test_synthetic_presence_penalty_config_exists(self):
        """
        RED: Test fails because SYNTHETIC_PRESENCE_PENALTY is not defined

        Expected: After fix, Config should have SYNTHETIC_PRESENCE_PENALTY = 0.3
        """
        assert hasattr(Writer.Config, 'SYNTHETIC_PRESENCE_PENALTY'), \
            "SYNTHETIC_PRESENCE_PENALTY should be defined in Config"

    def test_synthetic_api_url_config_exists(self):
        """
        RED: Test fails because SYNTHETIC_API_URL is not defined

        Expected: After fix, Config should have SYNTHETIC_API_URL with correct value
        """
        assert hasattr(Writer.Config, 'SYNTHETIC_API_URL'), \
            "SYNTHETIC_API_URL should be defined in Config"
        assert 'synthetic.new' in getattr(Writer.Config, 'SYNTHETIC_API_URL', ''), \
            "SYNTHETIC_API_URL should contain synthetic.new"

    def test_synthetic_chat_handler_exists(self):
        """
        RED: Test fails because _synthetic_chat method is not implemented

        Expected: After fix, Interface should have _synthetic_chat method
        """
        interface = Interface([])
        assert hasattr(interface, '_synthetic_chat'), \
            "_synthetic_chat method should exist on Interface"
        assert callable(getattr(interface, '_synthetic_chat')), \
            "_synthetic_chat should be callable"

    def test_synthetic_embedding_handler_exists(self):
        """
        RED: Test fails because _synthetic_embedding method is not implemented

        Expected: After fix, Interface should have _synthetic_embedding method
        """
        interface = Interface([])
        assert hasattr(interface, '_synthetic_embedding'), \
            "_synthetic_embedding method should exist on Interface"
        assert callable(getattr(interface, '_synthetic_embedding')), \
            "_synthetic_embedding should be callable"

    @patch.dict(os.environ, {'SYNTHETIC_API_KEY': 'test-key-synthetic'})
    def test_loadmodels_creates_synthetic_client(self):
        """
        RED: Test fails because LoadModels doesn't handle 'synthetic' provider

        Expected: After fix, LoadModels should create OpenAI client with synthetic base_url
        """
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            interface = Interface(Models=["synthetic://qwen/qwen-2.5-32b-instruct"])

            # Verify client was created and stored
            assert "synthetic://qwen/qwen-2.5-32b-instruct" in interface.Clients, \
                "Client should be stored in Clients dict"

    @patch.dict(os.environ, {'SYNTHETIC_API_KEY': 'test-key-synthetic'})
    def test_synthetic_uses_openai_library_with_correct_base_url(self):
        """
        RED: Test fails because LoadModels doesn't initialize OpenAI with synthetic base_url

        Expected: After fix, OpenAI should be called with base_url='https://api.synthetic.new/openai/v1'
        """
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            interface = Interface([])
            interface.LoadModels(["synthetic://qwen/qwen-2.5-32b-instruct"])

            # Verify OpenAI was called with correct parameters
            assert mock_openai.called, \
                "OpenAI class should be instantiated"
            call_kwargs = mock_openai.call_args[1]
            assert 'base_url' in call_kwargs, \
                "base_url should be passed to OpenAI"
            assert 'synthetic.new' in call_kwargs['base_url'], \
                "base_url should point to synthetic.new API"
            assert call_kwargs['api_key'] == os.environ.get('SYNTHETIC_API_KEY'), \
                "api_key from environment should be passed to OpenAI"

    @patch.dict(os.environ, {'SYNTHETIC_API_KEY': 'test-key-synthetic'})
    def test_synthetic_uses_openai_library_with_timeout_and_retries(self):
        """
        RED: Test fails because OpenAI initialization doesn't include timeout/max_retries

        Expected: After fix, OpenAI should be configured with timeout and max_retries from Config
        """
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            interface = Interface([])
            interface.LoadModels(["synthetic://test-model"])

            call_kwargs = mock_openai.call_args[1]
            assert 'timeout' in call_kwargs, \
                "timeout should be configured"
            assert 'max_retries' in call_kwargs, \
                "max_retries should be configured"

    def test_getmodeland_provider_parses_synthetic_url(self):
        """
        RED: May fail if GetModelAndProvider doesn't handle 'synthetic' scheme

        Expected: Should parse synthetic://model-name correctly
        """
        interface = Interface([])
        provider, model, host, params = interface.GetModelAndProvider(
            "synthetic://qwen/qwen-2.5-32b-instruct"
        )
        assert provider == "synthetic", \
            f"Provider should be 'synthetic', got '{provider}'"
        assert model == "qwen/qwen-2.5-32b-instruct", \
            f"Model should be 'qwen/qwen-2.5-32b-instruct', got '{model}'"
        assert host is None, \
            f"Host should be None for synthetic:// URLs, got {host}"
        assert params is None, \
            f"Params should be None for URLs without query string, got {params}"

    def test_getmodeland_provider_parses_synthetic_with_temperature(self):
        """
        RED: May fail if GetModelAndProvider doesn't parse query parameters

        Expected: Should parse query parameters from synthetic:// URLs
        """
        interface = Interface([])
        provider, model, host, params = interface.GetModelAndProvider(
            "synthetic://qwen/qwen-2.5-32b-instruct?temperature=0.8"
        )
        assert provider == "synthetic"
        assert model == "qwen/qwen-2.5-32b-instruct"
        assert params is not None, \
            "Params should not be None when query string present"
        assert 'temperature' in params, \
            f"Params should contain 'temperature', got {params}"
        assert params['temperature'] == 0.8, \
            f"temperature should be 0.8, got {params['temperature']}"

    def test_synthetic_loadmodels_raises_without_api_key(self):
        """
        RED: Test fails because LoadModels doesn't check for SYNTHETIC_API_KEY

        Expected: Should raise Exception with clear message when API key is missing
        """
        # Ensure API key is not set
        with patch.dict(os.environ, {}, clear=False):
            if 'SYNTHETIC_API_KEY' in os.environ:
                del os.environ['SYNTHETIC_API_KEY']

            interface = Interface([])
            with pytest.raises(Exception) as exc_info:
                interface.LoadModels(["synthetic://test-model"])

            assert "SYNTHETIC_API_KEY" in str(exc_info.value), \
                "Exception should mention SYNTHETIC_API_KEY"


class TestSyntheticChatHandler:
    """
    Test _synthetic_chat method implementation.
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

    def test_synthetic_chat_calls_openai_completions(self, mock_logger):
        """
        RED: Test fails because _synthetic_chat doesn't use OpenAI client correctly

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
            interface.Clients["synthetic://test-model"] = mock_openai

            messages, usage = interface._synthetic_chat(
                _Logger=mock_logger,
                _Model_key="synthetic://test-model",
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

    def test_synthetic_chat_has_retry_logic(self, mock_logger):
        """
        RED: Test fails because _synthetic_chat doesn't have retry logic

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
            interface.Clients["synthetic://test"] = mock_openai

            # Should succeed after retry
            messages, usage = interface._synthetic_chat(
                _Logger=mock_logger,
                _Model_key="synthetic://test",
                ProviderModel_name="test",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},
                Seed_int=42,
                _FormatSchema_dict=None
            )

            assert mock_openai.chat.completions.create.call_count == 2, \
                f"Should retry once (2 calls total), got {mock_openai.chat.completions.create.call_count}"

    def test_synthetic_chat_applies_frequency_penalty(self, mock_logger):
        """
        RED: Test fails because _synthetic_chat doesn't apply repetition penalties

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
            interface.Clients["synthetic://test"] = mock_openai

            # Call without FormatSchema (free-form generation)
            messages, usage = interface._synthetic_chat(
                _Logger=mock_logger,
                _Model_key="synthetic://test",
                ProviderModel_name="test",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},  # No frequency_penalty specified
                Seed_int=42,
                _FormatSchema_dict=None  # Free-form generation
            )

            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            assert 'frequency_penalty' in call_kwargs, \
                "frequency_penalty should be applied for free-form generation"

    def test_synthetic_chat_handles_response_format(self, mock_logger):
        """
        RED: Test fails because _synthetic_chat doesn't handle structured output

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
            interface.Clients["synthetic://test"] = mock_openai

            # Call with FormatSchema (structured output)
            format_schema = {
                "type": "json_schema",
                "json_schema": {"type": "object"},
                "strict": True
            }

            messages, usage = interface._synthetic_chat(
                _Logger=mock_logger,
                _Model_key="synthetic://test",
                ProviderModel_name="test",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},
                Seed_int=42,
                _FormatSchema_dict=format_schema
            )

            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            assert 'response_format' in call_kwargs, \
                "response_format should be set for structured output"

    def test_synthetic_chat_wraps_json_schema_for_synthetic_provider(self, mock_logger):
        """
        Test that _synthetic_chat wraps json_schema in {name, schema} format for Synthetic.dev.

        Synthetic.dev requires the format:
        {
            "type": "json_schema",
            "json_schema": {
                "name": "...",
                "schema": {...actual schema...},
                "strict": True
            }
        }

        This is different from OpenAI's format which uses the schema directly.
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            mock_response = Mock()
            mock_choice = Mock()
            mock_choice.message.content = '{"title": "Test"}'
            mock_response.choices = [mock_choice]
            mock_response.usage.prompt_tokens = 5
            mock_response.usage.completion_tokens = 3
            mock_openai.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.Clients["synthetic://test"] = mock_openai

            # Schema dengan properties (full structured output)
            format_schema = {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "genre": {"type": "string"}
                },
                "required": ["title", "genre"]
            }

            messages, usage = interface._synthetic_chat(
                _Logger=mock_logger,
                _Model_key="synthetic://test",
                ProviderModel_name="test",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},
                Seed_int=42,
                _FormatSchema_dict=format_schema
            )

            # Verifikasi response_format yang dikirim
            call_kwargs = mock_openai.chat.completions.create.call_args[1]
            assert 'response_format' in call_kwargs, \
                "response_format should be set"

            response_format = call_kwargs['response_format']
            assert response_format['type'] == 'json_schema', \
                f"response_format type should be json_schema, got {response_format.get('type')}"

            # VERIFIKASI KUNCI: Synthetic.dev membutuhkan format {name, schema}
            assert 'json_schema' in response_format, \
                "response_format should contain json_schema"
            json_schema = response_format['json_schema']
            assert 'name' in json_schema, \
                f"json_schema should have 'name' key for Synthetic.dev, got {list(json_schema.keys())}"
            assert 'schema' in json_schema, \
                f"json_schema should have 'schema' key for Synthetic.dev, got {list(json_schema.keys())}"
            assert json_schema['schema'] == format_schema, \
                "json_schema['schema'] should contain the actual FormatSchema_dict"
            assert json_schema.get('strict') is True, \
                "json_schema should have strict=True"

            # Verifikasi bahwa FormatSchema_dict asli DIBUNGKUS, bukan langsung
            # Note: In Python, two dicts with same values are equal (==), but we verify wrapping
            assert json_schema['schema'] == format_schema, \
                "json_schema['schema'] should contain the actual FormatSchema_dict"
            # The key check is that 'schema' is wrapped in another dict, not used directly
            assert response_format['json_schema'] is not format_schema, \
                "FormatSchema_dict should be wrapped inside response_format, not used directly"


class TestSyntheticEmbeddingHandler:
    """
    Test _synthetic_embedding method implementation.
    """

    @pytest.fixture
    def mock_logger(self):
        """Factory for creating mock Logger"""
        logger = MagicMock(name='mock_logger')
        logger.Log = MagicMock()
        return logger

    def test_synthetic_embedding_generates_embeddings(self, mock_logger):
        """
        RED: Test fails because _synthetic_embedding is not implemented

        Expected: Should generate embeddings using OpenAI client.embeddings.create
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            # Mock embedding response
            mock_response = Mock()
            mock_embedding_obj = Mock()
            mock_embedding_obj.embedding = [0.1, 0.2, 0.3, 0.4]
            mock_response.data = [mock_embedding_obj]
            mock_response.usage.prompt_tokens = 5
            mock_openai.embeddings.create.return_value = mock_response

            interface = Interface([])
            interface.Clients["synthetic://embedding-model"] = mock_openai

            embeddings, usage = interface._synthetic_embedding(
                _Logger=mock_logger,
                _Model_key="synthetic://embedding-model",
                ProviderModel_name="embedding-model",
                _Texts=["test text"]
            )

            assert len(embeddings) == 1, \
                f"Should generate 1 embedding, got {len(embeddings)}"
            assert embeddings[0] == [0.1, 0.2, 0.3, 0.4], \
                f"Embedding values should match, got {embeddings[0]}"
            assert mock_openai.embeddings.create.called, \
                "OpenAI embeddings.create should be called"

    def test_synthetic_embedding_handles_multiple_texts(self, mock_logger):
        """
        RED: Test fails because _synthetic_embedding doesn't handle multiple texts

        Expected: Should generate embeddings for all texts in input list
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            # Mock embedding response
            def create_embedding(model, input):
                mock_response = Mock()
                mock_embedding_obj = Mock()
                # Different embedding for different input
                mock_embedding_obj.embedding = [len(input) * 0.1]
                mock_response.data = [mock_embedding_obj]
                mock_response.usage.prompt_tokens = len(input.split())
                return mock_response

            mock_openai.embeddings.create.side_effect = create_embedding

            interface = Interface([])
            interface.Clients["synthetic://embedding-model"] = mock_openai

            embeddings, usage = interface._synthetic_embedding(
                _Logger=mock_logger,
                _Model_key="synthetic://embedding-model",
                ProviderModel_name="embedding-model",
                _Texts=["first text", "second text"]
            )

            assert len(embeddings) == 2, \
                f"Should generate 2 embeddings, got {len(embeddings)}"
            assert mock_openai.embeddings.create.call_count == 2, \
                f"Should call embeddings.create twice, got {mock_openai.embeddings.create.call_count}"

    def test_synthetic_embedding_raises_on_api_error(self, mock_logger):
        """
        RED: Test fails because _synthetic_embedding doesn't handle errors properly

        Expected: Should raise Exception with clear message on API error
        """
        from unittest.mock import patch
        with patch('openai.OpenAI') as mock_openai_class:
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai

            # Mock API error
            mock_openai.embeddings.create.side_effect = Exception("Embedding API error")

            interface = Interface([])
            interface.Clients["synthetic://embedding-model"] = mock_openai

            with pytest.raises(Exception) as exc_info:
                interface._synthetic_embedding(
                    _Logger=mock_logger,
                    _Model_key="synthetic://embedding-model",
                    ProviderModel_name="embedding-model",
                    _Texts=["test"]
                )

            assert "Embedding" in str(exc_info.value) or "embedding" in str(exc_info.value), \
                "Exception should mention embedding"
