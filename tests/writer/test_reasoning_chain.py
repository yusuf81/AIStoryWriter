# tests/writer/test_reasoning_chain.py
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

# Import the module we're testing
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestReasoningChain:
    """Test suite for ReasoningChain following TDD London School approach"""

    @pytest.fixture
    def mock_interface(self):
        """Create mock interface for testing"""
        from Writer.Interface.Wrapper import Interface

        interface = Interface()
        interface.Clients = {}
        return interface

    @pytest.fixture
    def mock_config(self):
        """Create mock config"""
        config = Mock()
        config.REASONING_MODEL = "test_model"
        config.REASONING_CACHE_RESULTS = False
        config.REASONING_LOG_SEPARATE = False
        return config

    @pytest.fixture
    def mock_logger(self):
        """Create mock logger"""
        logger = Mock()
        return logger

    @pytest.fixture
    def reasoning_chain(self, mock_interface, mock_config, mock_logger):
        """Create ReasoningChain instance for testing"""
        from Writer.ReasoningChain import ReasoningChain
        return ReasoningChain(mock_interface, mock_config, mock_logger)

    def test_reasoning_chain_initialization(self, reasoning_chain):
        """Test ReasoningChain initializes correctly"""
        assert reasoning_chain.interface is not None
        assert reasoning_chain.config is not None
        assert reasoning_chain.logger is not None
        assert reasoning_chain.reasoning_cache is None  # Caching disabled by default

    def test_reasoning_chain_with_caching_enabled(self, mock_interface, mock_config, mock_logger):
        """Test ReasoningChain with caching enabled"""
        mock_config.REASONING_CACHE_RESULTS = True
        from Writer.ReasoningChain import ReasoningChain

        chain = ReasoningChain(mock_interface, mock_config, mock_logger)
        assert chain.reasoning_cache == {}

    def test_reason_about_plot(self, reasoning_chain):
        """Test plot reasoning generation"""
        context = "Chapter 1: The hero begins their journey"
        chapter_num = 1

        with patch.object(reasoning_chain.interface, 'SafeGenerateText') as mock_generate:
            mock_generate.return_value = (
                [{"role": "assistant", "content": "Plot reasoning here"}],
                {"tokens": 100}
            )
            with patch.object(reasoning_chain.interface, 'GetLastMessageText') as mock_text:
                mock_text.return_value = "The hero's journey should start with a clear motivation..."

                result = reasoning_chain._reason_about_plot(context, None, chapter_num)

                assert result == "The hero's journey should start with a clear motivation..."
                mock_generate.assert_called_once()
                mock_text.assert_called_once()

    def test_reason_about_character(self, reasoning_chain):
        """Test character reasoning generation"""
        context = "Character Alice is brave but hesitant"
        chapter_num = 2

        with patch.object(reasoning_chain.interface, 'SafeGenerateText') as mock_generate:
            mock_generate.return_value = ([], {"tokens": 100})
            with patch.object(reasoning_chain.interface, 'GetLastMessageText') as mock_text:
                mock_text.return_value = "Alice's character development should show her overcoming hesitation..."

                result = reasoning_chain._reason_about_character(context, "Existing content", chapter_num)

                assert "overcoming hesitation" in result
                mock_generate.assert_called_once()

    def test_reason_about_dialogue(self, reasoning_chain):
        """Test dialogue reasoning generation"""
        context = "Scene with two characters meeting"
        chapter_num = 3

        with patch.object(reasoning_chain.interface, 'SafeGenerateText') as mock_generate:
            mock_generate.return_value = ([], {"tokens": 100})
            with patch.object(reasoning_chain.interface, 'GetLastMessageText') as mock_text:
                mock_text.return_value = "The dialogue should reveal character motivations..."

                result = reasoning_chain._reason_about_dialogue(context, "Existing text", chapter_num)

                assert "character motivations" in result

    def test_reason_about_outline(self, reasoning_chain):
        """Test outline reasoning generation"""
        context = "Story about a magical quest"

        with patch.object(reasoning_chain.interface, 'SafeGenerateText') as mock_generate:
            mock_generate.return_value = ([], {"tokens": 100})
            with patch.object(reasoning_chain.interface, 'GetLastMessageText') as mock_text:
                mock_text.return_value = "The outline should follow a three-act structure..."

                result = reasoning_chain._reason_about_outline(context)

                assert "three-act" in result

    def test_reason_general(self, reasoning_chain):
        """Test general reasoning for unknown task types"""
        context = "Some context for testing"
        task_type = "custom_task"
        chapter_num = 5

        with patch.object(reasoning_chain.interface, 'SafeGenerateText') as mock_generate:
            mock_generate.return_value = ([], {"tokens": 50})
            with patch.object(reasoning_chain.interface, 'GetLastMessageText') as mock_text:
                mock_text.return_value = "General reasoning approach..."

                result = reasoning_chain._reason_general(context, task_type, None, chapter_num)

                assert result == "General reasoning approach..."

    def test_reason_method_with_plot_task(self, reasoning_chain):
        """Test main reason method dispatches to correct type"""
        with patch.object(reasoning_chain, '_reason_about_plot') as mock_plot:
            mock_plot.return_value = "Plot reasoning result"

            result = reasoning_chain.reason("context", "plot", None, 1)

            assert result == "Plot reasoning result"
            mock_plot.assert_called_once_with("context", None, 1)

    def test_reason_method_with_character_task(self, reasoning_chain):
        """Test reason method with character task"""
        with patch.object(reasoning_chain, '_reason_about_character') as mock_char:
            mock_char.return_value = "Character reasoning result"

            result = reasoning_chain.reason("context", "character", "Additional", 2)

            assert result == "Character reasoning result"
            mock_char.assert_called_once_with("context", "Additional", 2)

    def test_reason_method_with_dialogue_task(self, reasoning_chain):
        """Test reason method with dialogue task"""
        with patch.object(reasoning_chain, '_reason_about_dialogue') as mock_dialogue:
            mock_dialogue.return_value = "Dialogue reasoning result"

            result = reasoning_chain.reason("context", "dialogue")

            assert result == "Dialogue reasoning result"
            mock_dialogue.assert_called_once_with("context", None, None)

    def test_reason_method_with_outline_task(self, reasoning_chain):
        """Test reason method with outline task"""
        with patch.object(reasoning_chain, '_reason_about_outline') as mock_outline:
            mock_outline.return_value = "Outline reasoning result"

            result = reasoning_chain.reason("prompt", "outline")

            assert result == "Outline reasoning result"
            mock_outline.assert_called_once_with("prompt")

    def test_reason_method_with_unknown_task(self, reasoning_chain):
        """Test reason method with unknown task type falls back to general"""
        with patch.object(reasoning_chain, '_reason_general') as mock_general:
            mock_general.return_value = "General reasoning result"

            result = reasoning_chain.reason("context", "unknown_task", "Extra", 3)

            assert result == "General reasoning result"
            mock_general.assert_called_once_with("context", "unknown_task", "Extra", 3)

    def test_caching_functionality(self, mock_interface, mock_config, mock_logger):
        """Test reasoning caching works correctly"""
        mock_config.REASONING_CACHE_RESULTS = True
        from Writer.ReasoningChain import ReasoningChain

        chain = ReasoningChain(mock_interface, mock_config, mock_logger)

        # First call should cache the result
        with patch.object(chain, '_reason_about_plot') as mock_reason:
            mock_reason.return_value = "Cached result"

            result1 = chain.reason("context", "plot", None, 1)
            result2 = chain.reason("context", "plot", None, 1)  # Should use cache

            # Should only call the reasoning method once due to caching
            mock_reason.assert_called_once()
            assert result1 == "Cached result"
            assert result2 == "Cached result"

    def test_separate_logging_enabled(self, mock_interface, mock_config, mock_logger, tmp_path):
        """Test separate logging functionality"""
        mock_config.REASONING_LOG_SEPARATE = True
        from Writer.ReasoningChain import ReasoningChain

        with patch('os.makedirs') as mock_makedirs:
            with patch('builtins.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file

                chain = ReasoningChain(mock_interface, mock_config, mock_logger)

                with patch.object(chain, '_reason_about_plot') as mock_reason:
                    mock_reason.return_value = "Log this reasoning"

                    chain.reason("context", "plot", None, 1)

                    # Should have created the log file and written to it
                    mock_makedirs.assert_called_once_with("Logs/Reasoning", exist_ok=True)
                    mock_open.assert_called()
                    mock_file.write.assert_called()

    def test_get_stats_no_caching(self, reasoning_chain):
        """Test get_stats returns correct information when caching disabled"""
        stats = reasoning_chain.get_stats()
        assert stats["cache_enabled"] is False
        assert stats["cached_items"] == 0
        assert stats["separate_logging"] is False

    def test_get_stats_with_caching(self, mock_interface, mock_config, mock_logger):
        """Test get_stats returns correct information when caching enabled"""
        mock_config.REASONING_CACHE_RESULTS = True
        from Writer.ReasoningChain import ReasoningChain

        chain = ReasoningChain(mock_interface, mock_config, mock_logger)
        chain.reasoning_cache["key1"] = "value1"
        chain.reasoning_cache["key2"] = "value2"

        stats = chain.get_stats()
        assert stats["cache_enabled"] is True
        assert stats["cached_items"] == 2

    def test_clear_cache_when_enabled(self, mock_interface, mock_config, mock_logger):
        """Test clear cache works when caching is enabled"""
        mock_config.REASONING_CACHE_RESULTS = True
        from Writer.ReasoningChain import ReasoningChain

        chain = ReasoningChain(mock_interface, mock_config, mock_logger)
        chain.reasoning_cache["key"] = "value"

        chain.clear_cache()

        assert len(chain.reasoning_cache) == 0
        mock_logger.Log.assert_called_with("Reasoning cache cleared", 4)

    def test_clear_cache_when_disabled(self, reasoning_chain):
        """Test clear cache does nothing when caching is disabled"""
        # Should not raise error when cache is None
        reasoning_chain.clear_cache()
        # No assertion needed - just ensuring no exception

    def test_integration_with_actual_interface(self, mock_config, mock_logger):
        """Integration test with actual interface methods"""
        from Writer.ReasoningChain import ReasoningChain
        from Writer.Interface.Wrapper import Interface

        interface = Interface()
        chain = ReasoningChain(interface, mock_config, mock_logger)

        # Mock the actual SafeGenerateText to avoid real LLM calls
        with patch.object(interface, 'SafeGenerateText') as mock_generate:
            mock_generate.return_value = ([], {"tokens": 100})
            with patch.object(interface, 'GetLastMessageText') as mock_text:
                with patch.object(interface, 'BuildSystemQuery') as mock_system:
                    with patch.object(interface, 'BuildUserQuery') as mock_user:
                        mock_text.return_value = "AI reasoning response"
                        mock_system.return_value = {"role": "system", "content": "system"}
                        mock_user.return_value = {"role": "user", "content": "user"}

                        result = chain.reason("test context", "plot", None, 1)

                        assert result == "AI reasoning response"
                        mock_generate.assert_called_once()

                        # Check the correct system message was used
                        mock_system.assert_called_with("You are a skilled story analyst providing structured reasoning for plot development.")

    def test_prompt_contains_required_elements(self, reasoning_chain):
        """Test that generated prompts contain expected elements"""
        # Test plot reasoning prompt
        with patch.object(reasoning_chain.interface, 'SafeGenerateText') as mock_generate:
            with patch.object(reasoning_chain.interface, 'GetLastMessageText') as mock_text:
                with patch.object(reasoning_chain.interface, 'BuildSystemQuery') as mock_system:
                    with patch.object(reasoning_chain.interface, 'BuildUserQuery') as mock_user:
                        mock_text.return_value = "Reasoning"
                        mock_system.return_value = {"role": "system", "content": "system"}
                        # Fix the mock to return proper tuple for SafeGenerateText
                        mock_generate.return_value = ([], {"tokens": 100})

                        # Capture the user prompt
                        captured_prompt = None
                        def capture_user_query(content):
                            nonlocal captured_prompt
                            captured_prompt = content
                            return {"role": "user", "content": content}
                        mock_user.side_effect = capture_user_query

                        reasoning_chain._reason_about_plot("Chapter context", None, 5)

                        # Verify important elements are in the prompt
                        assert "Chapter 5" in captured_prompt
                        assert "plot points" in captured_prompt
                        assert "pacing" in captured_prompt
                        assert "narrative structure" in captured_prompt