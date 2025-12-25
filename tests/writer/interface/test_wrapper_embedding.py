# tests/writer/interface/test_wrapper_embedding.py
"""Test embedding functionality in Interface Wrapper"""
from Writer.Interface.Wrapper import Interface
import os
import sys
import pytest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TestGenerateEmbedding:
    """Test embedding generation through unified provider system"""

    def setup_method(self):
        self.interface = Interface(Models=[])
        self.mock_logger = Mock()
        self.mock_logger.Log = Mock()

    def test_get_model_and_provider_parsing_embedding(self):
        """Test that embedding model strings are parsed correctly"""
        test_cases = [
            ("ollama://nomic-embed-text", "ollama", "nomic-embed-text", "10.23.82.116:11434", None),
            ("google://gemini-embedding-001", "google", "gemini-embedding-001", None, None),
            ("openrouter://text-embedding-3-small", "openrouter", "text-embedding-3-small", None, None),
            ("ollama://nomic-embed-text@localhost:11434", "ollama", "nomic-embed-text", "localhost:11434", None),
        ]

        for model_str, expected_provider, expected_model, expected_host, expected_params in test_cases:
            provider, model, host, params = self.interface.GetModelAndProvider(model_str)
            assert provider == expected_provider
            assert model == expected_model
            assert host == expected_host
            assert params == expected_params

    @pytest.mark.parametrize("provider", ["ollama", "google", "openrouter"])
    def test_embedding_method_exists(self, provider):
        """Test that each provider has an embedding method"""
        method_name = f"_{provider}_embedding"
        # Methods should now exist after implementation (GREEN phase)
        assert hasattr(self.interface, method_name), f"Method {method_name} should exist"
        assert callable(getattr(self.interface, method_name, None)), f"Method {method_name} should be callable"

    def test_generate_embedding_method_exists(self):
        """Test that GenerateEmbedding method exists - GREEN phase"""
        assert hasattr(self.interface, 'GenerateEmbedding'), "GenerateEmbedding method should exist"
        assert callable(getattr(self.interface, 'GenerateEmbedding', None)), "GenerateEmbedding should be callable"

    @patch('ollama.Client')
    def test_ollama_embedding_with_mock(self, mock_ollama_client):
        """Test Ollama embedding generation with mocked client - GREEN phase"""
        # Mock the ollama client
        mock_client = Mock()
        mock_client.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}
        self.interface.Clients["ollama://nomic-embed-text"] = mock_client

        # Test embedding generation
        embeddings, usage = self.interface.GenerateEmbedding(
            self.mock_logger, ["test text"], "ollama://nomic-embed-text"
        )

        assert embeddings == [[0.1, 0.2, 0.3]]
        assert usage["completion_tokens"] == 0  # Check that completion tokens is 0
        mock_client.embeddings.assert_called_with(
            model="nomic-embed-text",
            prompt="test text"
        )

    def test_generate_embedding_unsupported_provider(self):
        """Test that unsupported providers raise an error - GREEN phase"""
        with pytest.raises(Exception):
            self.interface.GenerateEmbedding(
                self.mock_logger, ["test"], "unsupported://model"
            )


class TestEmbeddingConfig:
    """Test embedding configuration in Config"""

    def test_embedding_config_vars_exist(self):
        """Test that embedding config variables exist"""
        from Writer import Config

        # These should all exist after implementation
        config_vars = [
            'EMBEDDING_MODEL',
            'EMBEDDING_DIMENSIONS',
            'EMBEDDING_CTX',
            'EMBEDDING_FALLBACK_ENABLED'
        ]

        # Now they should exist after adding to Config.py
        for var in config_vars:
            assert hasattr(Config, var), f"{var} should exist in Config"

        # Check default values - use whatever is configured in Config.py
        from Writer.Config import EMBEDDING_MODEL
        assert Config.EMBEDDING_MODEL == EMBEDDING_MODEL
        assert Config.EMBEDDING_DIMENSIONS == 768
        assert Config.EMBEDDING_CTX == 8192
        assert Config.EMBEDDING_FALLBACK_ENABLED == False
