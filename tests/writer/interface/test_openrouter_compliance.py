"""
OpenRouter API Compliance Tests

This test suite follows London School TDD methodology to ensure
OpenRouter integration complies with the latest API standards.

Phase 1 - RED: All tests should fail initially to verify issues exist.
Phase 2 - GREEN: Tests will pass after minimal fixes.
Phase 3 - REFACTOR: Tests will continue passing with improved code.
"""

import pytest
import inspect
from unittest.mock import Mock, patch
import Writer.Config


class TestOpenRouterCompliance:
    """Test OpenRouter API compliance for parameter naming and structured outputs."""

    def test_openrouter_uses_correct_max_tokens_parameter(self, mock_interface, mock_logger):
        """
        RED: Test fails because OpenRouter uses 'max_token' instead of 'max_tokens'

        Expected: After fix, OpenRouter should send 'max_tokens' parameter to API
        Actual: Currently sends 'max_token' which is incorrect per OpenRouter API spec
        """
        from Writer.Interface.Wrapper import Interface

        # Arrange
        with patch('Writer.Interface.OpenRouter.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "test response"}}],
                "usage": {"total_tokens": 10}
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            interface = Interface()

            # Mock the OpenRouter client
            mock_client = Mock()
            # Create proper response object structure
            mock_choice = Mock()
            mock_choice.message.content = "test response"
            mock_response.choices = [mock_choice]
            mock_response.usage = {"total_tokens": 10}
            mock_client.chat.return_value = mock_response
            interface.Clients["openrouter_test"] = mock_client

            # Parse model with max_tokens parameter
            provider, model, host, params = interface.GetModelAndProvider(
                "openrouter://anthropic/claude-3-sonnet?max_tokens=1000"
            )

            # Act - This should call OpenRouter API
            interface._openrouter_chat(
                _Logger=mock_logger,
                _Model_key="openrouter_test",
                ProviderModel_name=model,
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict=params,
                Seed_int=42,
                _FormatSchema_dict=None
            )

            # Assert - Check what parameters were actually sent
            # Note: We need to check the OpenRouter client's chat method call
            mock_client.chat.assert_called_once()
            call_args = mock_client.chat.call_args
            assert 'stream' in call_args.kwargs
            assert call_args.kwargs['stream'] == False

            # Check that max_tokens was properly passed from ModelOptions
            assert 'max_tokens' in call_args.kwargs
            assert call_args.kwargs['max_tokens'] == 1000

    def test_openrouter_structured_outputs_with_json_schema(self, mock_interface, mock_logger):
        """
        RED: Test fails because OpenRouter doesn't support full JSON Schema in response_format

        Expected: After fix, OpenRouter should accept full JSON Schema like:
        {
            "type": "json_schema",
            "json_schema": {...},
            "strict": True
        }
        Actual: Only supports {"type": "json_object"}
        """
        from Writer.Interface.Wrapper import Interface

        # Arrange
        json_schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "chapters": {"type": "array", "items": {"type": "object"}}
            },
            "required": ["title", "chapters"]
        }

        interface = Interface()

        # Mock the OpenRouter client
        mock_client = Mock()
        mock_response = Mock()
        # Create proper response object structure
        mock_choice = Mock()
        mock_choice.message.content = '{"title": "Test Story", "chapters": []}'
        mock_response.choices = [mock_choice]
        mock_response.usage = {"total_tokens": 10}
        mock_client.chat.return_value = mock_response
        interface.Clients["openrouter_test"] = mock_client

        # Act - Call with full JSON Schema
        interface._openrouter_chat(
            _Logger=mock_logger,
            _Model_key="openrouter_test",
            ProviderModel_name="anthropic/claude-3-sonnet",
            _Messages_list=[{"role": "user", "content": "生成故事大纲"}],
            ModelOptions_dict=None,
            Seed_int=None,
            _FormatSchema_dict=json_schema  # Full schema, not just empty dict
        )

        # Assert - Check if JSON Schema is properly passed to OpenRouter
        mock_client.chat.assert_called_once()
        call_args = mock_client.chat.call_args
        call_kwargs = call_args.kwargs

        # RED: This will FAIL because current code doesn't support full JSON Schema
        response_format = call_kwargs.get('response_format')
        assert response_format is not None, "response_format should be set"
        assert response_format.get('type') == 'json_schema', "Should use json_schema type"
        assert 'json_schema' in response_format, "Should contain json_schema field"
        assert response_format['json_schema'] == json_schema, "JSON Schema should match input"
        assert response_format.get('strict') == True, "Should enforce strict mode"

    def test_openrouter_max_retries_config_exists(self):
        """
        RED: Test fails because MAX_OPENROUTER_RETRIES is not defined in Config.py

        Expected: Config should have MAX_OPENROUTER_RETRIES = 2 like other providers
        Actual: Currently uses fallback getattr() with default value
        """
        from Writer.Interface.Wrapper import Interface

        # Act & Assert - Check config exists
        assert hasattr(Writer.Config, 'MAX_OPENROUTER_RETRIES'), "MAX_OPENROUTER_RETRIES should be defined in Config"
        assert getattr(Writer.Config, 'MAX_OPENROUTER_RETRIES') == 2, "MAX_OPENROUTER_RETRIES should be 2"

        # Verify the fallback is no longer needed in source code
        interface = Interface()
        source = inspect.getsource(interface._openrouter_chat)

        # RED: This will FAIL because fallback code still exists
        assert 'getattr(Writer.Config, "MAX_OPENROUTER_RETRIES", 2)' not in source, \
            "Fallback getattr should be removed now that config is properly defined"

    def test_openrouter_backward_compatibility_basic_json(self, mock_interface, mock_logger):
        """
        RED-TO-GREEN: Test ensures backward compatibility for basic JSON format

        This should pass both before and after fixes to ensure we don't break existing functionality
        """
        from Writer.Interface.Wrapper import Interface

        # Arrange
        interface = Interface()

        # Mock the OpenRouter client
        mock_client = Mock()
        mock_response = Mock()
        # Create proper response object structure
        mock_choice = Mock()
        mock_choice.message.content = '{"result": "success"}'
        mock_response.choices = [mock_choice]
        mock_response.usage = {"total_tokens": 10}
        mock_client.chat.return_value = mock_response
        interface.Clients["openrouter_test"] = mock_client

        # Act - Call with empty dict (should result in basic JSON mode)
        interface._openrouter_chat(
            _Logger=mock_logger,
            _Model_key="openrouter_test",
            ProviderModel_name="anthropic/claude-3-sonnet",
            _Messages_list=[{"role": "user", "content": "test"}],
            ModelOptions_dict=None,
            Seed_int=None,
            _FormatSchema_dict={}  # Empty dict should trigger basic JSON mode
        )

        # Assert - Should still work with basic format
        mock_client.chat.assert_called_once()
        call_args = mock_client.chat.call_args
        call_kwargs = call_args.kwargs

        # This should PASS even in current implementation
        response_format = call_kwargs.get('response_format')
        assert response_format is not None, "response_format should be set for basic JSON"
        assert response_format.get('type') == 'json_object', "Basic mode should use json_object type"


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing"""
    logger = Mock()
    logger.Log = Mock()
    return logger
