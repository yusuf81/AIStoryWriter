# conftest.py for shared pytest fixtures

# Set environment variables to fix NumPy 2.0 compatibility with SciPy
import os
os.environ['NUMPY_EXPERIMENTAL_ARRAY_FUNCTION'] = '1'
os.environ['NPY_DISABLE_CPU_FEATURES'] = 'AVX2'

import pytest
import glob
from unittest.mock import Mock, patch


@pytest.fixture
def mock_document():
    """Factory for creating mock Document objects with standard interface"""
    def _create_mock_document(page_content, metadata=None):
        doc = Mock()
        doc.page_content = page_content
        doc.metadata = metadata or {}
        return doc
    return _create_mock_document


@pytest.fixture
def mock_interface():
    """Factory for creating mock Interface with properly formatted return values

    Each test gets a fresh mock to ensure isolation.
    """
    def _create_mock_interface():
        from unittest.mock import MagicMock

        # Create a fresh Mock with name for better debugging
        mock_int = MagicMock(name='mock_interface')

        # SafeGenerateText returns (messages, token_usage)
        mock_int.SafeGenerateText.return_value = (
            [{'role': 'assistant', 'content': 'Mock response'}],
            {'prompt_tokens': 100, 'completion_tokens': 50}
        )

        # SafeGenerateJSON returns (messages, json_response, token_usage)
        mock_int.SafeGenerateJSON.return_value = (
            [{'role': 'assistant', 'content': '{"result": "mock"}'}],
            {"result": "mock"},
            {'prompt_tokens': 100, 'completion_tokens': 50}
        )

        # SafeGeneratePydantic returns (messages, pydantic_result, token_usage)
        mock_pydantic = Mock(name='mock_pydantic_result')
        mock_pydantic.text = "mock"
        mock_pydantic.word_count = 5
        mock_int.SafeGeneratePydantic.return_value = (
            [{'role': 'assistant', 'content': '{"text": "mock", "word_count": 5}'}],
            mock_pydantic,
            {'prompt_tokens': 100, 'completion_tokens': 50}
        )

        # Common interface methods
        mock_int.BuildUserQuery.side_effect = lambda x: x
        mock_int.GetLastMessageText.side_effect = lambda msgs: msgs[-1]['content'] if msgs else ""

        # Reset side_effect to be clean for each test
        mock_int.reset_mock()

        return mock_int
    return _create_mock_interface


@pytest.fixture
def mock_logger():
    """Factory for creating mock Logger with standard interface"""
    def _create_mock_logger():
        from unittest.mock import MagicMock

        # Create a fresh Mock with name for better debugging
        logger = MagicMock(name='mock_logger')

        # Standard logger methods
        logger.Log = MagicMock()
        logger.SaveLangchain = MagicMock()

        # Track logs for assertions (format: [(lvl, msg), ...])
        logger.logs = []

        def log_side_effect(msg, lvl):
            logger.logs.append((lvl, msg))

        logger.Log.side_effect = log_side_effect

        return logger
    return _create_mock_logger


@pytest.fixture
def indonesian_language_config():
    """Set up Indonesian language configuration for tests"""
    with patch('Writer.Config.NATIVE_LANGUAGE', 'id'):
        yield


@pytest.fixture
def english_language_config():
    """Set up English language configuration for tests"""
    with patch('Writer.Config.NATIVE_LANGUAGE', 'en'):
        yield


@pytest.fixture(autouse=True)
def cleanup_test_artifacts():
    """Automatically cleanup test output files after each test."""
    # Setup: nothing to do before test
    yield

    # Teardown: cleanup after test
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_artifacts = [
        "test_output.md*",  # Will match test_output.md.md, test_output.md_info.json, etc.
        "dummy_state.json",
    ]

    for pattern in test_artifacts:
        for filepath in glob.glob(os.path.join(root_dir, pattern)):
            try:
                os.remove(filepath)
                print(f"Cleaned up test artifact: {filepath}")
            except Exception as e:
                print(f"Warning: Could not remove {filepath}: {e}")
