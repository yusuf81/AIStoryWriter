"""
Tests for auto-retry on repetition detection

Phase: RED - These tests will fail initially because auto-retry logic
in ChatResponse() hasn't been implemented yet.
"""
import pytest
from unittest.mock import Mock, MagicMock
from Writer.Interface.Wrapper import Interface


class TestRepetitionAutoRetry:
    """Test auto-retry mechanism when repetition detected"""

    @pytest.fixture
    def mock_logger(self):
        """Standard mock logger"""
        logger = Mock()
        logger.Log = Mock()
        return logger

    def test_structured_output_minor_repetition_no_retry(self, mock_logger):
        """Structured output with minor repetition (below threshold) should not retry"""
        interface = Interface()  # Don't pass Models to avoid initialization

        schema = {"type": "object", "properties": {"title": {"type": "string"}}}

        # Mock Ollama client
        mock_client = Mock()
        mock_response = {
            "message": {"content": '{"title": "aaaaaaaaaaaaa"}'},  # 13 consecutive a's - below threshold of 20
            "prompt_eval_count": 10,
            "eval_count": 5
        }
        mock_client.chat = Mock(return_value=mock_response)
        interface.Clients["ollama://qwen:32b"] = mock_client

        # Mock GetModelAndProvider to return the right info
        interface.GetModelAndProvider = Mock(return_value=("ollama", "qwen:32b", None, {}))

        # Act - Call ChatResponse with structured output
        result, usage, _, _ = interface.ChatResponse(
            mock_logger,
            [{"role": "user", "content": "Generate"}],
            "ollama://qwen:32b",
            -1,
            schema  # Structured output
        )

        # Assert - Should NOT retry (13 a's is below structured threshold of 20)
        assert mock_client.chat.call_count == 1
        logged_messages = [str(call[0][0]) for call in mock_logger.Log.call_args_list]
        assert not any("repetition detected" in msg.lower() for msg in logged_messages)
        assert not any("auto-retry" in msg.lower() for msg in logged_messages)

    def test_normal_text_no_retry(self, mock_logger):
        """Normal text without repetition should not trigger retry"""
        interface = Interface()  # Don't pass Models to avoid initialization

        # Mock Ollama client with normal response
        mock_client = Mock()
        mock_response = {
            "message": {"content": "This is a normal chapter about adventure and exploration."},
            "prompt_eval_count": 10,
            "eval_count": 20
        }
        mock_client.chat = Mock(return_value=mock_response)
        interface.Clients["ollama://qwen:32b"] = mock_client

        # Mock GetModelAndProvider to return the right info
        interface.GetModelAndProvider = Mock(return_value=("ollama", "qwen:32b", None, {}))

        # Act
        result, usage, _, _ = interface.ChatResponse(
            mock_logger,
            [{"role": "user", "content": "Generate chapter"}],
            "ollama://qwen:32b",
            -1,
            None  # Non-structured output
        )

        # Assert - Should NOT retry
        assert mock_client.chat.call_count == 1
        logged_messages = [str(call[0][0]) for call in mock_logger.Log.call_args_list]
        assert not any("repetition detected" in msg.lower() for msg in logged_messages)

    def test_structured_output_with_character_explosion_retries(self, mock_logger):
        """Structured output with severe character explosion should trigger retry"""
        interface = Interface()

        schema = {"type": "object", "properties": {"title": {"type": "string"}}}

        # Mock Ollama client
        mock_client = Mock()

        # First response: character explosion in JSON value
        mock_response_bad = {
            "message": {"content": '{"title": "aaaaaaaaaaaaaaaaaaaaaaaaaaaa"}'},  # 28 consecutive 'a's
            "prompt_eval_count": 10,
            "eval_count": 5
        }

        # Second response: normal JSON
        mock_response_good = {
            "message": {"content": '{"title": "A Valid Title"}'},
            "prompt_eval_count": 10,
            "eval_count": 5
        }

        mock_client.chat = Mock(side_effect=[mock_response_bad, mock_response_good])

        # Replace Clients dict with MagicMock that returns mock_client for any key
        # This handles the case where retry modifies the model URL
        mock_clients_dict = MagicMock()
        mock_clients_dict.__getitem__.return_value = mock_client
        # Support membership test (key in dict) for _get_client()
        mock_clients_dict.__contains__.return_value = True
        interface.Clients = mock_clients_dict

        # Mock GetModelAndProvider to always return consistent values
        def mock_get_model(model_str):
            # Extract temperature from URL if present, otherwise use default
            temp = 0.7
            if '?' in model_str and 'temperature=' in model_str:
                import urllib.parse
                params = urllib.parse.parse_qs(model_str.split('?')[1])
                temp = float(params.get('temperature', [0.7])[0])
            return ("ollama", "qwen:32b", None, {'temperature': temp})

        interface.GetModelAndProvider = Mock(side_effect=mock_get_model)

        # Act
        result, usage, _, _ = interface.ChatResponse(
            mock_logger,
            [{"role": "user", "content": "Generate"}],
            "ollama://qwen:32b",
            -1,
            schema  # Structured output
        )

        # Assert - Should have retried once due to character explosion
        assert mock_client.chat.call_count == 2
        logged_messages = [str(call[0][0]) for call in mock_logger.Log.call_args_list]
        assert any("repetition detected" in msg.lower() for msg in logged_messages)
        assert any("charexplosion" in msg.lower() for msg in logged_messages)


class TestClientLookupWithQueryParameters:
    """Test _get_client() helper handles query parameters correctly"""

    def test_get_client_exact_match(self):
        """Test _get_client() with exact match (no query params)"""
        from Writer.Interface.Wrapper import Interface

        interface = Interface()
        mock_client = Mock()
        interface.Clients["ollama://qwen:32b"] = mock_client

        # Act
        result = interface._get_client("ollama://qwen:32b")

        # Assert
        assert result is mock_client

    def test_get_client_with_query_parameters(self):
        """Test _get_client() strips query parameters for lookup"""
        from Writer.Interface.Wrapper import Interface

        interface = Interface()
        mock_client = Mock()
        # Client registered WITHOUT query params
        interface.Clients["grok://grok-4-1-fast-reasoning"] = mock_client

        # Act - Lookup WITH query params (from auto-retry)
        result = interface._get_client("grok://grok-4-1-fast-reasoning?temperature=0.8999999999999999")

        # Assert - Should find client using base key
        assert result is mock_client

    def test_get_client_not_found_raises_descriptive_error(self):
        """Test _get_client() raises descriptive KeyError when client not found"""
        from Writer.Interface.Wrapper import Interface

        interface = Interface()
        interface.Clients["ollama://qwen:32b"] = Mock()

        # Act & Assert - Should raise KeyError with helpful message
        with pytest.raises(KeyError) as exc_info:
            interface._get_client("grok://nonexistent-model")

        error_msg = str(exc_info.value)
        assert "nonexistent-model" in error_msg
        assert "Available keys" in error_msg
