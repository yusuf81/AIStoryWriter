"""Test LangChain deprecation warnings are handled properly."""

import warnings
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

def test_lorebook_imports_chroma_without_deprecation():
    """Test that Lorebook initializes without LangChain deprecation warnings."""
    # Import warnings to capture them
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Import the module first
        import Writer.Lorebook

        # Mock the dependencies to avoid actual initialization
        with patch('Writer.Lorebook.LANGCHAIN_AVAILABLE', True):
            with patch('Writer.Config.USE_LOREBOOK', True):
                with patch('Writer.Config.EMBEDDING_MODEL', 'test://model'):
                    with patch('Writer.Interface.Wrapper.Interface'):
                        from Writer.Lorebook import LorebookManager
                        lorebook = LorebookManager(persist_dir="./test_lorebook_db")

                            # Check that no deprecation warnings were raised
        deprecation_warnings = [warning for warning in w
                              if issubclass(warning.category, DeprecationWarning)]
        langchain_warnings = [warning for warning in deprecation_warnings
                            if 'langchain' in str(warning.message).lower()]

        assert len(langchain_warnings) == 0, \
            f"LangChain deprecation warnings found: {[str(w.message) for w in langchain_warnings]}"

def test_lorebook_uses_langchain_chroma_preferentially():
    """Test that Lorebook uses Chroma correctly when imported."""
    # Import the module first
    import Writer.Lorebook

    # Mock to check which Chroma import is used
    with patch('Writer.Lorebook.Chroma') as mock_chroma:
        with patch('Writer.Lorebook.LANGCHAIN_AVAILABLE', True):
            with patch('Writer.Config.USE_LOREBOOK', True):
                with patch('Writer.Config.EMBEDDING_MODEL', 'test://model'):
                    with patch('Writer.Interface.Wrapper.Interface'):
                        from Writer.Lorebook import LorebookManager
                        lorebook = LorebookManager(persist_dir="./test_lorebook_db")

                        # Verify Chroma was called with correct parameters
                        mock_chroma.assert_called_once()
                        call_args = mock_chroma.call_args

                        # Check that the Chroma instance was created correctly
                        assert 'collection_name' in call_args.kwargs
                        assert call_args.kwargs['collection_name'] == 'story_lore'
                        assert 'embedding_function' in call_args.kwargs
                        assert 'persist_directory' in call_args.kwargs