"""
Test Wrapper.py config fallback behavior - TDD London School Approach
Tests for MAX_JSON_RETRIES bug fix using MAX_PYDANTIC_RETRIES as fallback
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestWrapperConfigFallback:
    """Test SafeGenerateJSON uses proper config fallback"""

    def test_safe_generate_json_uses_max_pydantic_retries_as_fallback(self, mock_logger):
        """
        RED TEST: Verify SafeGenerateJSON uses MAX_PYDANTIC_RETRIES when _max_retries_override is None

        This test will FAIL initially because:
        - Line 157 references Writer.Config.MAX_JSON_RETRIES
        - MAX_JSON_RETRIES doesn't exist in Config
        - Will raise AttributeError

        After fix, this test will PASS because:
        - Will use getattr(Writer.Config, 'MAX_PYDANTIC_RETRIES', 5)
        - Safely falls back without AttributeError
        """
        # Arrange: Import real Interface class
        from Writer.Interface.Wrapper import Interface
        import Writer.Config

        # Verify MAX_JSON_RETRIES doesn't exist (current buggy state)
        assert not hasattr(Writer.Config, 'MAX_JSON_RETRIES'), "Test assumption violated: MAX_JSON_RETRIES should not exist"

        # Create real Interface instance (takes Models list)
        real_interface = Interface(Models=[])

        # Mock the ChatAndStreamResponse to return valid JSON response
        with patch.object(real_interface, 'ChatAndStreamResponse') as mock_chat:
            mock_chat.return_value = (
                [{'role': 'assistant', 'content': '{"result": "test"}'}],  # ResponseMessagesList
                {'prompt_tokens': 10, 'completion_tokens': 5},  # TokenUsage
                50,  # InputChars
                10   # EstInputTokens
            )

            # Mock GetLastMessageText to return valid JSON
            with patch.object(real_interface, 'GetLastMessageText', return_value='{"result": "test"}'):
                # Act: Call SafeGenerateJSON without retry override (triggers fallback to config)
                # RED: This will crash with AttributeError initially
                # GREEN: After fix, this should work without crashing
                result = real_interface.SafeGenerateJSON(
                    mock_logger(),
                    [{'role': 'user', 'content': 'test'}],
                    "ollama://test",
                    _max_retries_override=None  # Triggers config fallback
                )

                # Assert: Should return valid 3-tuple without crashing
                assert result is not None
                assert len(result) == 3  # (messages, json_response, token_usage)
                messages, json_response, token_usage = result
                assert isinstance(messages, list)
                assert isinstance(json_response, dict)
                assert isinstance(token_usage, dict)

    def test_safe_generate_json_respects_explicit_retry_override(self, mock_logger):
        """Verify SafeGenerateJSON uses _max_retries_override when provided"""
        from Writer.Interface.Wrapper import Interface

        # Create Interface instance
        real_interface = Interface(Models=[])

        with patch.object(real_interface, 'ChatAndStreamResponse') as mock_chat:
            # Mock to fail first, succeed second
            mock_chat.side_effect = [
                # First attempt - invalid JSON
                ([{'role': 'assistant', 'content': 'invalid json'}], {'prompt_tokens': 10}, 10, 10),
                # Second attempt - valid JSON
                ([{'role': 'assistant', 'content': '{"result": "success"}'}], {'prompt_tokens': 10}, 10, 10),
            ]

            # Use explicit override of 2 retries
            with patch.object(real_interface, 'GetLastMessageText', side_effect=['invalid json', '{"result": "success"}']):
                result = real_interface.SafeGenerateJSON(
                    mock_logger(),
                    [{'role': 'user', 'content': 'test'}],
                    "ollama://test",
                    _max_retries_override=2  # Explicit override - should NOT use config
                )

                # Should succeed on second attempt
                assert result is not None
                messages, json_response, token_usage = result
                assert json_response == {"result": "success"}
