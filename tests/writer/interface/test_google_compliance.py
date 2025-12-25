"""
Google Gemini API Compliance Tests

This test suite follows London School TDD methodology to ensure
Google Gemini integration complies with the latest API standards.

Phase 1 - RED: All tests should fail initially to verify issues exist.
Phase 2 - GREEN: Tests will pass after minimal fixes.
Phase 3 - REFACTOR: Tests will continue passing with improved code.
"""

import pytest
import inspect
import os
from unittest.mock import Mock
import Writer.Config


class TestGoogleCompliance:
    """Test Google Gemini API compliance for configuration, client patterns, and latest SDK usage."""

    @pytest.fixture(autouse=True)
    def setup_google_env(self):
        """Setup test environment with Google API key if needed"""
        if not os.environ.get("GOOGLE_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = "test_key_for_pytest"

    def test_google_max_retries_config_exists(self):
        """
        RED: Test fails because MAX_GOOGLE_RETRIES is not defined in Config.py

        Expected: After fix, Config should have MAX_GOOGLE_RETRIES = 2
        Actual: Currently uses fallback getattr() with default value
        """
        # Act & Assert - Check config exists
        assert hasattr(Writer.Config, 'MAX_GOOGLE_RETRIES'), "MAX_GOOGLE_RETRIES should be defined in Config"
        assert getattr(Writer.Config, 'MAX_GOOGLE_RETRIES') == 2, "MAX_GOOGLE_RETRIES should be 2"

        # Verify fallback is removed from source code
        from Writer.Interface.Wrapper import Interface
        interface = Interface()
        source = inspect.getsource(interface._google_chat)
        assert 'getattr(Writer.Config, "MAX_GOOGLE_RETRIES", 2)' not in source, \
            "Fallback getattr should be removed now that config is properly defined"

    def test_google_embedding_uses_client_pattern(self, mock_logger):
        """
        RED: Test fails because embedding uses deprecated genai.embed_content()

        Expected: After fix, should use client.models.embed_content() pattern from latest SDK
        Actual: Currently uses genai.embed_content() function-based approach
        """
        from Writer.Interface.Wrapper import Interface

        # Arrange
        interface = Interface()
        mock_client = Mock()
        interface.Clients["google_test"] = mock_client

        # Mock the embed_content response - using client.models.embed_content pattern
        mock_response = Mock()
        mock_response.embedding = [0.1, 0.2, 0.3]
        mock_client.models.embed_content.return_value = mock_response

        # Act - This should call client.models.embed_content, not genai.embed_content
        result, usage = interface._google_embedding(
            _Logger=mock_logger,
            _Model_key="google_test",
            ProviderModel_name="text-embedding-004",
            _Texts=["test text"]
        )

        # Assert - Verify client.models pattern is used
        mock_client.models.embed_content.assert_called_once()
        assert result == [[0.1, 0.2, 0.3]]

    def test_google_uses_current_models(self):
        """
        RED: Test fails because Config.py references deprecated Gemini 1.5 models

        Expected: After fix, should reference current Gemini 3 models
        Actual: Currently has gemini-1.5-pro in example URLs
        """
        # Act & Assert - Check no deprecated models in Config
        config_source = inspect.getsource(Writer.Config)
        assert 'gemini-1.5-pro' not in config_source, "Should not reference deprecated Gemini 1.5 models"
        assert 'gemini-3' in config_source, "Should reference current Gemini 3 models"

    def test_google_embedding_has_retry_logic(self, mock_logger):
        """
        RED: Test fails because embedding method has no retry logic

        Expected: After fix, embedding should retry on failure like chat method
        Actual: Currently has no retry loop, just raises exception immediately
        """
        from Writer.Interface.Wrapper import Interface

        # Arrange
        interface = Interface()
        mock_client = Mock()

        # Make first call fail, second succeed
        mock_response = Mock()
        mock_response.embedding = [0.1, 0.2, 0.3]
        mock_client.models.embed_content.side_effect = [
            Exception("API Error"),  # First call fails
            mock_response            # Second call succeeds
        ]
        interface.Clients["google_test"] = mock_client

        # Act - Should retry and succeed
        result, usage = interface._google_embedding(
            _Logger=mock_logger,
            _Model_key="google_test",
            ProviderModel_name="text-embedding-004",
            _Texts=["test text"]
        )

        # Assert - Should have retried and succeeded
        assert mock_client.models.embed_content.call_count == 2
        assert result == [[0.1, 0.2, 0.3]]

    def test_google_embedding_uses_object_attributes(self, mock_logger):
        """
        RED: Test fails because code uses dictionary access instead of object attributes

        Expected: After fix, should use result.embedding (object attribute)
        Actual: Currently uses result['embedding'] (dictionary access)
        """
        from Writer.Interface.Wrapper import Interface

        # Arrange
        interface = Interface()
        mock_client = Mock()

        # Mock response with object attributes (latest SDK pattern)
        mock_response = Mock()
        mock_response.embedding = [0.1, 0.2, 0.3]
        mock_client.models.embed_content.return_value = mock_response
        interface.Clients["google_test"] = mock_client

        # Act
        result, usage = interface._google_embedding(
            _Logger=mock_logger,
            _Model_key="google_test",
            ProviderModel_name="text-embedding-004",
            _Texts=["test text"]
        )

        # Assert - Should access object attributes, not dictionary keys
        assert hasattr(mock_response, 'embedding'), "Response should have embedding attribute"
        assert result == [[0.1, 0.2, 0.3]]

    def test_google_chat_optimizes_system_messages(self, mock_logger):
        """
        RED: Test fails because system message handling could be optimized

        Expected: After fix, system messages should be properly handled and preserved
        Actual: Current transformation works but could be optimized for better history
        """
        from Writer.Interface.Wrapper import Interface

        # Arrange
        interface = Interface()
        mock_client = Mock()

        # Mock response
        mock_response = Mock()
        mock_response.text = "Assistant response"
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 5
        mock_client.generate_content.return_value = mock_response
        interface.Clients["google_test"] = mock_client

        # Messages with system message
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"}
        ]

        # Act
        result, usage = interface._google_chat(
            _Logger=mock_logger,
            _Model_key="google_test",
            ProviderModel_name="gemini-3-flash-preview",
            _Messages_list=messages,
            ModelOptions_dict=None,
            Seed_int=None,
            _FormatSchema_dict=None
        )

        # Assert - System message should be preserved and handled correctly
        call_args = mock_client.generate_content.call_args
        transformed_messages = call_args[1]['contents']

        # System message should be converted to user message for Gemini compatibility
        assert len(transformed_messages) == 2
        assert transformed_messages[0]["role"] == "user"  # System converted to user
        assert transformed_messages[0]["parts"][0] == "You are a helpful assistant"
        assert transformed_messages[1]["role"] == "user"  # Original user message
        assert transformed_messages[1]["parts"][0] == "Hello"


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing"""
    logger = Mock()
    logger.Log = Mock()
    return logger
