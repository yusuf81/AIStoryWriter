"""Test configurable max_tokens and anti-repetition settings for Synthetic.dev."""

from unittest.mock import Mock, patch, MagicMock
from Writer.Interface.Wrapper import Interface


class TestSyntheticMaxTokensConfig:
    """Test that Synthetic uses configured max_tokens values."""

    @patch.dict('os.environ', {'SYNTHETIC_API_KEY': 'test-key'})
    def test_synthetic_uses_configured_max_tokens_structured(self):
        """Structured output should use MAX_SYNTHETIC_TOKENS_STRUCTURED."""
        with patch('openai.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            # Mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"text": "test", "chapter_number": 1}'
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 100
            mock_client.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.LoadModels(["synthetic://hf:test-model"])

            # Call with structured output (FormatSchema provided)
            from Writer.Models import ChapterOutput
            schema = ChapterOutput.model_json_schema()

            interface._synthetic_chat(
                _Logger=Mock(),
                _Model_key="synthetic://hf:test-model",
                ProviderModel_name="test-model",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},
                Seed_int=42,
                _FormatSchema_dict=schema
            )

            # Verify max_tokens was set from config
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert 'max_tokens' in call_kwargs
            assert call_kwargs['max_tokens'] == 4096  # From config

    @patch.dict('os.environ', {'SYNTHETIC_API_KEY': 'test-key'})
    def test_synthetic_uses_higher_temperature_for_structured(self):
        """Structured output should use higher temperature for LLaMA."""
        with patch('openai.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"text": "test"}'
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 100
            mock_client.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.LoadModels(["synthetic://hf:test-model"])

            from Writer.Models import ChapterOutput
            schema = ChapterOutput.model_json_schema()

            interface._synthetic_chat(
                _Logger=Mock(),
                _Model_key="synthetic://hf:test-model",
                ProviderModel_name="test-model",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},
                Seed_int=None,
                _FormatSchema_dict=schema
            )

            # Verify temperature is set higher for LLaMA
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs.get('temperature') == 0.8

    @patch.dict('os.environ', {'SYNTHETIC_API_KEY': 'test-key'})
    def test_synthetic_uses_stronger_penalties_for_structured(self):
        """Structured output should use stronger repetition penalties for LLaMA."""
        with patch('openai.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"text": "test"}'
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 100
            mock_client.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.LoadModels(["synthetic://hf:test-model"])

            from Writer.Models import ChapterOutput
            schema = ChapterOutput.model_json_schema()

            interface._synthetic_chat(
                _Logger=Mock(),
                _Model_key="synthetic://hf:test-model",
                ProviderModel_name="test-model",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={},
                Seed_int=None,
                _FormatSchema_dict=schema
            )

            # Verify stronger penalties
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs.get('frequency_penalty') == 1.0
            assert call_kwargs.get('presence_penalty') == 0.6

    @patch.dict('os.environ', {'SYNTHETIC_API_KEY': 'test-key'})
    def test_synthetic_respects_max_tokens_from_model_options(self):
        """max_tokens from ModelOptions_dict should override config."""
        with patch('openai.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"text": "test"}'
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 100
            mock_client.chat.completions.create.return_value = mock_response

            interface = Interface([])
            interface.LoadModels(["synthetic://hf:test-model"])

            from Writer.Models import ChapterOutput
            schema = ChapterOutput.model_json_schema()

            # Pass custom max_tokens via ModelOptions
            interface._synthetic_chat(
                _Logger=Mock(),
                _Model_key="synthetic://hf:test-model",
                ProviderModel_name="test-model",
                _Messages_list=[{"role": "user", "content": "test"}],
                ModelOptions_dict={"max_tokens": 8000},
                Seed_int=None,
                _FormatSchema_dict=schema
            )

            # Should use ModelOptions value, not config
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs['max_tokens'] == 8000
