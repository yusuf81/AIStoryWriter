"""Test OLLAMA host parsing and fallback to config."""

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


def test_ollama_local_model_with_query_params():
    """RED: Local Ollama model string with query params should parse correctly

    Bug: "huihui_ai/qwen3-abliterated:30b?temperature=0.9" was returning
    ProviderModelName with query params attached, causing Ollama API error "model is required".
    """
    import Writer.Config
    interface = Interface([])
    result = interface.GetModelAndProvider("huihui_ai/qwen3-abliterated:30b?temperature=0.9")

    # Should return provider, model (CLEAN without query), host from config, params
    assert result[0] == "ollama"  # provider
    assert result[1] == "huihui_ai/qwen3-abliterated:30b"  # model WITHOUT query params
    assert result[2] == getattr(Writer.Config, "OLLAMA_HOST", None)  # host from config

    # Should parse query params correctly (converted from list to dict values)
    assert result[3] is not None  # params should exist
    assert isinstance(result[3], dict)
    assert "temperature" in result[3]
    assert result[3]["temperature"] == 0.9  # Converted to float value


def test_ollama_local_model_with_multiple_query_params():
    """RED: Local model string with multiple query params should parse correctly."""
    interface = Interface([])
    result = interface.GetModelAndProvider("llama3:70b?temperature=0.8&top_p=0.9&num_ctx=4096")

    assert result[0] == "ollama"
    assert result[1] == "llama3:70b"  # model WITHOUT query params

    # All params should be parsed (converted from list to dict values)
    assert result[3] is not None
    assert result[3]["temperature"] == 0.8
    assert result[3]["top_p"] == 0.9
    assert result[3]["num_ctx"] == 4096.0


def test_ollama_local_model_without_query_params():
    """Green: Local model string without query params should work as before."""
    import Writer.Config
    interface = Interface([])
    result = interface.GetModelAndProvider("huihui_ai/qwen3-abliterated:30b")

    assert result[0] == "ollama"
    assert result[1] == "huihui_ai/qwen3-abliterated:30b"
    assert result[2] == getattr(Writer.Config, "OLLAMA_HOST", None)
    assert result[3] is None  # No params when no query string
