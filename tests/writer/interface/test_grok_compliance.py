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
from unittest.mock import Mock, patch
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

        # Assert - Warning should be logged
        mock_logger.Log.assert_any_call(
            "Warning: xAI Grok structured output uses basic JSON mode", 6
        )
        # Temperature should be set to 0.0
        call_args = mock_client.chat.create.call_args
        assert call_args[1].get('temperature') == 0.0


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing"""
    logger = Mock()
    logger.Log = Mock()
    return logger
