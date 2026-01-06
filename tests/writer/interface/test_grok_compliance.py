"""
xAI Grok API Compliance Tests

This test suite follows London School TDD methodology to ensure
xAI Grok integration complies with API standards and project patterns.

Phase 1 - RED: All tests should fail initially to verify implementation is missing.
Phase 2 - GREEN: Tests will pass after minimal implementation.
Phase 3 - REFACTOR: Tests will continue passing with improved code.
"""

import pytest
import inspect
import os
from unittest.mock import Mock
import Writer.Config


class TestGrokCompliance:
    """Test xAI Grok API compliance for configuration, client patterns, and SDK usage."""

    @pytest.fixture(autouse=True)
    def setup_grok_env(self):
        """Setup test environment with xAI API key if needed"""
        if not os.environ.get("XAI_API_KEY"):
            os.environ["XAI_API_KEY"] = "test_key_for_pytest"

    def test_grok_max_retries_config_exists(self):
        """
        RED: Test fails because MAX_GROK_RETRIES is not defined in Config.py

        Expected: After fix, Config should have MAX_GROK_RETRIES = 2
        Actual: Currently not defined
        """
        # Act & Assert - Check config exists
        assert hasattr(Writer.Config, 'MAX_GROK_RETRIES'), "MAX_GROK_RETRIES should be defined in Config"
        assert getattr(Writer.Config, 'MAX_GROK_RETRIES') == 2, "MAX_GROK_RETRIES should be 2"

        # Verify fallback is not used in source code
        from Writer.Interface.Wrapper import Interface
        interface = Interface()
        source = inspect.getsource(interface._grok_chat)
        assert 'getattr(Writer.Config, "MAX_GROK_RETRIES"' not in source, \
            "Should use direct Config.MAX_GROK_RETRIES, not getattr fallback"

    def test_grok_client_initialization(self):
        """
        RED: Test fails because grok provider is not implemented in LoadModels()

        Expected: After fix, should initialize xai_sdk.Client with API key
        Actual: Currently raises NotImplementedError or no grok branch exists
        """
        from Writer.Interface.Wrapper import Interface

        # Arrange - Set API key
        os.environ["XAI_API_KEY"] = "test_key"

        # Act - Initialize interface with grok model
        interface = Interface(Models=["grok://grok-3"])

        # Assert - Client should be initialized
        assert "grok://grok-3" in interface.Clients, "Grok client should be initialized"
        # Verify it's the correct client type
        assert interface.Clients["grok://grok-3"] is not None

    def test_grok_message_transformation(self):
        """
        RED: Test fails because _transform_messages_for_grok() doesn't exist

        Expected: After fix, should transform messages using xAI SDK helpers
        Actual: Currently no transformation method exists
        """
        from Writer.Interface.Wrapper import Interface

        # Arrange
        interface = Interface()
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]

        # Act - Transform messages
        transformed = interface._transform_messages_for_grok(messages)

        # Assert - Should return list of transformed messages
        assert isinstance(transformed, list)
        assert len(transformed) == 3

    def test_grok_chat_completion(self, mock_logger):
        """
        RED: Test fails because _grok_chat() method doesn't exist

        Expected: After fix, should handle chat completion with token usage
        Actual: Currently no _grok_chat method exists
        """
        from Writer.Interface.Wrapper import Interface

        # Arrange
        interface = Interface()
        mock_client = Mock()
        interface.Clients["grok://grok-3"] = mock_client

        # Mock chat.create() and chat.sample()
        mock_chat = Mock()
        mock_response = Mock()
        mock_response.content = "Test response"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5

        mock_chat.sample.return_value = mock_response
        mock_client.chat.create.return_value = mock_chat

        # Act - Execute chat
        messages = [{"role": "user", "content": "Test"}]
        result, usage = interface._grok_chat(
            _Logger=mock_logger,
            _Model_key="grok://grok-3",
            ProviderModel_name="grok-3",
            _Messages_list=messages,
            ModelOptions_dict=None,
            Seed_int=None,
            _FormatSchema_dict=None
        )

        # Assert - Verify response and token usage
        assert result[-1]["content"] == "Test response"
        assert usage is not None
        assert usage["prompt_tokens"] == 10
        assert usage["completion_tokens"] == 5

    def test_grok_chat_retries_on_failure(self, mock_logger):
        """
        RED: Test fails because retry logic doesn't exist in _grok_chat()

        Expected: After fix, should retry on failure using _execute_with_retry()
        Actual: Currently no retry implementation
        """
        from Writer.Interface.Wrapper import Interface

        # Arrange
        interface = Interface()
        mock_client = Mock()
        interface.Clients["grok://grok-3"] = mock_client

        # Mock: first call fails, second succeeds
        mock_chat = Mock()
        mock_response = Mock()
        mock_response.content = "Success after retry"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5

        mock_chat.sample.side_effect = [
            Exception("API Error"),
            mock_response
        ]
        mock_client.chat.create.return_value = mock_chat

        # Act - Execute with retry
        result, usage = interface._grok_chat(
            _Logger=mock_logger,
            _Model_key="grok://grok-3",
            ProviderModel_name="grok-3",
            _Messages_list=[{"role": "user", "content": "Test"}],
            ModelOptions_dict=None,
            Seed_int=None,
            _FormatSchema_dict=None
        )

        # Assert - Should succeed on second attempt
        assert result[-1]["content"] == "Success after retry"
        assert mock_chat.sample.call_count == 2

    def test_grok_embedding_not_implemented(self, mock_logger):
        """
        RED: Test fails because _grok_embedding() doesn't exist

        Expected: After fix, should raise NotImplementedError with helpful message
        Actual: Currently no _grok_embedding method exists
        """
        from Writer.Interface.Wrapper import Interface

        # Arrange
        interface = Interface()
        interface.Clients["grok://grok-3"] = Mock()

        # Act & Assert - Should raise NotImplementedError
        with pytest.raises(NotImplementedError) as exc_info:
            interface._grok_embedding(
                _Logger=mock_logger,
                _Model_key="grok://grok-3",
                ProviderModel_name="grok-3",
                _Texts=["test text"]
            )

        # Assert - Error message should be helpful
        error_msg = str(exc_info.value)
        assert "Collections API" in error_msg
        assert "gemini-embedding-001" in error_msg or "ollama" in error_msg

    def test_grok_structured_output_warning(self, mock_logger):
        """
        RED: Test fails because structured output handling doesn't exist

        Expected: After fix, should log warning for structured output mode
        Actual: Currently no FormatSchema handling in _grok_chat
        """
        from Writer.Interface.Wrapper import Interface

        # Arrange
        interface = Interface()
        mock_client = Mock()
        interface.Clients["grok://grok-3"] = mock_client

        # Mock response
        mock_chat = Mock()
        mock_response = Mock()
        mock_response.content = '{"test": "data"}'
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 3
        mock_chat.sample.return_value = mock_response
        mock_client.chat.create.return_value = mock_chat

        # Act - Execute with FormatSchema
        schema = {"type": "object", "properties": {"test": {"type": "string"}}}
        result, usage = interface._grok_chat(
            _Logger=mock_logger,
            _Model_key="grok://grok-3",
            ProviderModel_name="grok-3",
            _Messages_list=[{"role": "user", "content": "Test"}],
            ModelOptions_dict=None,
            Seed_int=None,
            _FormatSchema_dict=schema
        )

        # Assert - Warning should be logged (schema not in registry fallback)
        mock_logger.Log.assert_any_call(
            "Warning: xAI Grok structured output uses basic JSON mode (schema not in registry)", 6
        )
        # Temperature should be set to 0.0
        call_args = mock_client.chat.create.call_args
        assert call_args[1].get('temperature') == 0.0


class TestGrokStructuredOutputSupport:
    """
    TDD London School: Test xAI Grok response_format parameter support
    """

    @pytest.fixture(autouse=True)
    def setup_grok_env(self):
        """Setup test environment with xAI API key"""
        if not os.environ.get("XAI_API_KEY"):
            os.environ["XAI_API_KEY"] = "test_key_for_pytest"

    def test_grok_structured_output_passes_pydantic_model(self, mock_logger):
        """RED: Verify response_format passed to xAI SDK with Pydantic class"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        # Arrange
        interface = Interface()
        mock_client = Mock()
        interface.Clients["grok://grok-4"] = mock_client

        mock_chat = Mock()
        mock_response = Mock()
        mock_response.content = '{"text": "Valid chapter text", "chapter_number": 1}'
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_chat.sample.return_value = mock_response
        mock_client.chat.create.return_value = mock_chat

        # Act
        schema = ChapterOutput.model_json_schema()
        result, usage = interface._grok_chat(
            _Logger=mock_logger,
            _Model_key="grok://grok-4",
            ProviderModel_name="grok-4",
            _Messages_list=[{"role": "user", "content": "Generate chapter"}],
            ModelOptions_dict=None,
            Seed_int=None,
            _FormatSchema_dict=schema
        )

        # Assert
        call_args = mock_client.chat.create.call_args
        assert call_args is not None
        assert 'response_format' in call_args[1]
        assert call_args[1]['response_format'] == ChapterOutput

    def test_grok_structured_output_logs_enabled_message(self, mock_logger):
        """RED: Verify log message changed from 'basic JSON mode' to 'structured output enabled'"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import OutlineOutput

        # Arrange
        interface = Interface()
        mock_client = Mock()
        interface.Clients["grok://grok-4"] = mock_client

        mock_chat = Mock()
        mock_response = Mock()
        mock_response.content = '{"title": "Test", "chapters": ["Ch1"], "target_chapter_count": 1}'
        mock_response.usage = None
        mock_chat.sample.return_value = mock_response
        mock_client.chat.create.return_value = mock_chat

        # Act
        schema = OutlineOutput.model_json_schema()
        interface._grok_chat(
            _Logger=mock_logger,
            _Model_key="grok://grok-4",
            ProviderModel_name="grok-4",
            _Messages_list=[{"role": "user", "content": "Test"}],
            ModelOptions_dict=None,
            Seed_int=None,
            _FormatSchema_dict=schema
        )

        # Assert
        logged_messages = [call[0][0] for call in mock_logger.Log.call_args_list]
        assert any("structured output enabled" in msg.lower() for msg in logged_messages)
        assert not any("basic JSON mode" in msg for msg in logged_messages)

    def test_grok_structured_output_without_schema_no_response_format(self, mock_logger):
        """Test that response_format NOT passed when FormatSchema is None"""
        from Writer.Interface.Wrapper import Interface

        # Arrange
        interface = Interface()
        mock_client = Mock()
        interface.Clients["grok://grok-4"] = mock_client

        mock_chat = Mock()
        mock_response = Mock()
        mock_response.content = "Plain text"
        mock_response.usage = None
        mock_chat.sample.return_value = mock_response
        mock_client.chat.create.return_value = mock_chat

        # Act
        interface._grok_chat(
            _Logger=mock_logger,
            _Model_key="grok://grok-4",
            ProviderModel_name="grok-4",
            _Messages_list=[{"role": "user", "content": "Test"}],
            ModelOptions_dict=None,
            Seed_int=None,
            _FormatSchema_dict=None
        )

        # Assert
        call_args = mock_client.chat.create.call_args
        assert 'response_format' not in call_args[1]

    def test_grok_structured_output_schema_not_in_registry_fallback(self, mock_logger):
        """RED: Test fallback to basic JSON when schema not in registry"""
        from Writer.Interface.Wrapper import Interface

        # Arrange
        interface = Interface()
        mock_client = Mock()
        interface.Clients["grok://grok-4"] = mock_client

        mock_chat = Mock()
        mock_response = Mock()
        mock_response.content = '{"unknown": "data"}'
        mock_response.usage = None
        mock_chat.sample.return_value = mock_response
        mock_client.chat.create.return_value = mock_chat

        # Act
        custom_schema = {
            "title": "CustomUnknownModel",
            "type": "object",
            "properties": {"unknown": {"type": "string"}}
        }

        interface._grok_chat(
            _Logger=mock_logger,
            _Model_key="grok://grok-4",
            ProviderModel_name="grok-4",
            _Messages_list=[{"role": "user", "content": "Test"}],
            ModelOptions_dict=None,
            Seed_int=None,
            _FormatSchema_dict=custom_schema
        )

        # Assert - Should NOT pass response_format
        call_args = mock_client.chat.create.call_args
        assert 'response_format' not in call_args[1]

        # Should log fallback warning
        logged_messages = [call[0][0] for call in mock_logger.Log.call_args_list]
        assert any("basic" in msg.lower() for msg in logged_messages)

    def test_grok_structured_output_maintains_temperature_zero(self, mock_logger):
        """Test that temperature=0.0 set for structured output"""
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput

        # Arrange
        interface = Interface()
        mock_client = Mock()
        interface.Clients["grok://grok-4"] = mock_client

        mock_chat = Mock()
        mock_response = Mock()
        mock_response.content = '{"text": "Valid", "chapter_number": 1}'
        mock_response.usage = None
        mock_chat.sample.return_value = mock_response
        mock_client.chat.create.return_value = mock_chat

        # Act
        schema = ChapterOutput.model_json_schema()
        interface._grok_chat(
            _Logger=mock_logger,
            _Model_key="grok://grok-4",
            ProviderModel_name="grok-4",
            _Messages_list=[{"role": "user", "content": "Test"}],
            ModelOptions_dict=None,
            Seed_int=None,
            _FormatSchema_dict=schema
        )

        # Assert
        call_args = mock_client.chat.create.call_args
        assert call_args[1].get('temperature') == 0.0


class TestGrokFrequencyPenaltyAutoFallback:
    """Test auto-fallback when model doesn't support frequency_penalty"""

    @pytest.fixture(autouse=True)
    def setup_grok_env(self):
        """Setup test environment with xAI API key"""
        if not os.environ.get("XAI_API_KEY"):
            os.environ["XAI_API_KEY"] = "test_key_for_pytest"

    def test_grok_reasoning_model_auto_fallback_on_unsupported_param(self, mock_logger):
        """
        RED: Test auto-fallback when reasoning model rejects frequency_penalty

        Scenario:
        1. First call with frequency_penalty → Error "does not support parameter frequencyPenalty"
        2. Auto-retry without frequency_penalty → Success
        3. Log warning about unsupported parameter
        """
        from Writer.Interface.Wrapper import Interface

        # Arrange
        interface = Interface()
        mock_client = Mock()
        interface.Clients["grok://grok-4-1-fast-reasoning"] = mock_client

        # Mock: First call fails with parameter error, second succeeds
        mock_chat_fail = Mock()
        mock_chat_success = Mock()

        # Simulate gRPC error from xAI SDK
        grpc_error = Exception("Model grok-4-1-fast-reasoning does not support parameter frequencyPenalty.")

        mock_chat_fail.sample.side_effect = grpc_error

        # Second call succeeds
        mock_response = Mock()
        mock_response.content = "Valid response without frequency_penalty"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_chat_success.sample.return_value = mock_response

        # client.chat.create called twice: first fails, second succeeds
        mock_client.chat.create.side_effect = [mock_chat_fail, mock_chat_success]

        # Act - Execute chat (should auto-retry without frequency_penalty)
        result, usage = interface._grok_chat(
            _Logger=mock_logger,
            _Model_key="grok://grok-4-1-fast-reasoning",
            ProviderModel_name="grok-4-1-fast-reasoning",
            _Messages_list=[{"role": "user", "content": "Test"}],
            ModelOptions_dict=None,
            Seed_int=None,
            _FormatSchema_dict=None
        )

        # Assert - Should succeed on second attempt
        assert result[-1]["content"] == "Valid response without frequency_penalty"
        assert usage is not None
        assert usage["prompt_tokens"] == 10
        assert mock_client.chat.create.call_count == 2

        # Assert - Warning logged about unsupported parameter
        logged_messages = [str(call[0][0]) for call in mock_logger.Log.call_args_list]
        assert any("does not support frequency_penalty" in msg for msg in logged_messages)
        assert any("Retrying without it" in msg for msg in logged_messages)

    def test_grok_non_reasoning_model_uses_frequency_penalty_normally(self, mock_logger):
        """
        Test that non-reasoning models (grok-3, grok-3-mini) successfully use frequency_penalty
        """
        from Writer.Interface.Wrapper import Interface

        # Arrange
        interface = Interface()
        mock_client = Mock()
        interface.Clients["grok://grok-3"] = mock_client

        # Mock successful response
        mock_chat = Mock()
        mock_response = Mock()
        mock_response.content = "Response with frequency_penalty applied"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 8
        mock_response.usage.completion_tokens = 12
        mock_chat.sample.return_value = mock_response
        mock_client.chat.create.return_value = mock_chat

        # Act
        result, usage = interface._grok_chat(
            _Logger=mock_logger,
            _Model_key="grok://grok-3",
            ProviderModel_name="grok-3",
            _Messages_list=[{"role": "user", "content": "Test"}],
            ModelOptions_dict=None,
            Seed_int=None,
            _FormatSchema_dict=None
        )

        # Assert - Should succeed on first attempt
        assert result[-1]["content"] == "Response with frequency_penalty applied"
        assert mock_client.chat.create.call_count == 1

        # Assert - frequency_penalty passed in config
        call_args = mock_client.chat.create.call_args
        assert 'frequency_penalty' in call_args[1]


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing"""
    logger = Mock()
    logger.Log = Mock()
    return logger
