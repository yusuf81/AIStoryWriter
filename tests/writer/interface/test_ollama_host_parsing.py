"""Test OLLAMA host parsing and fallback to config."""

import pytest  # type: ignore # Needed for pytest fixtures
from Writer.Interface.Wrapper import Interface


def test_ollama_host_fallback_to_config():
    """Test model string without host uses OLLAMA_HOST from config."""
    # Create interface instance
    interface = Interface([])

    # Test model string without host should use OLLAMA_HOST
    result = interface.GetModelAndProvider("ollama://llama3:70b")

    # Should return provider, model, and host from config
    assert result[0] == "ollama"  # provider
    assert result[1] == "llama3:70b"  # model
    # Host should be from OLLAMA_HOST config if no host in model
    from Writer import Config
    expected_host = getattr(Config, 'OLLAMA_HOST', None)
    assert result[2] == expected_host


def test_ollama_host_in_model_string():
    """Test model string with host should use that host, not OLLAMA_HOST."""
    interface = Interface([])
    result = interface.GetModelAndProvider("ollama://llama3:70b@custom.host:1234")

    # Should return the custom host, overriding config
    assert result[0] == "ollama"  # provider
    assert result[1] == "llama3:70b"  # model
    assert result[2] == "custom.host:1234"  # host from model string


def test_ollama_model_without_provider():
    """Test that plain model name defaults to ollama and uses config host."""
    interface = Interface([])
    result = interface.GetModelAndProvider("llama3:70b")

    assert result[0] == "ollama"  # Default provider
    assert result[1] == "llama3:70b"
    # Should use OLLAMA_HOST from config
    from Writer import Config
    expected_host = getattr(Config, 'OLLAMA_HOST', None)
    assert result[2] == expected_host


def test_ollama_host_with_config_override():
    """Test that model string host overrides OLLAMA_HOST config."""
    interface = Interface([])
    result = interface.GetModelAndProvider("ollama://model@test.com")

    assert result[0] == "ollama"
    assert result[1] == "model"
    assert result[2] == "test.com"  # Should NOT be from config
