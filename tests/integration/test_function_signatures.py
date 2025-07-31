"""
Integration tests to verify function signatures match usage.
These tests call real functions with minimal mocking to catch signature mismatches.
"""
import pytest
import inspect
from unittest.mock import Mock, MagicMock

# Import the modules we want to test
import Writer.Chapter.ChapterDetector as ChapterDetector
import Writer.OutlineGenerator as OutlineGenerator
import Writer.NovelEditor as NovelEditor
import Writer.Scrubber as Scrubber
import Writer.Translator as Translator
import Writer.StoryInfo as StoryInfo


class TestFunctionSignatures:
    """Test that function signatures match their actual usage patterns."""

    @pytest.fixture
    def mock_interface(self):
        """Create a mock interface that provides required methods."""
        interface = Mock()
        interface.BuildUserQuery.return_value = {"role": "user", "content": "test"}
        interface.SafeGenerateJSON.return_value = (None, {"TotalChapters": 3}, None)
        interface.SafeGenerateText.return_value = ([{"role": "assistant", "content": "test"}], {"tokens": 100})
        interface.GetLastMessageText.return_value = "test response"
        return interface

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        logger = Mock()
        logger.Log = Mock()
        return logger

    def test_llm_count_chapters_signature(self, mock_interface, mock_logger):
        """Test that LLMCountChapters can be called with correct arguments."""
        outline = "Test story outline"
        
        # This should not raise a TypeError
        result = ChapterDetector.LLMCountChapters(mock_interface, mock_logger, outline)
        
        # Verify it returns an integer
        assert isinstance(result, int)
        assert result > 0

    def test_revise_outline_signature(self, mock_interface, mock_logger):
        """Test that ReviseOutline can be called with correct arguments."""
        outline = "Test outline"
        feedback = "Test feedback"
        
        # Mock SafeGenerateText to return proper format
        mock_interface.SafeGenerateText.return_value = (
            [{"role": "assistant", "content": "Revised outline"}], 
            {"tokens": 100}
        )
        
        # This should not raise a TypeError
        result_outline, result_history = OutlineGenerator.ReviseOutline(
            mock_interface, mock_logger, outline, feedback
        )
        
        # Verify it returns expected types
        assert isinstance(result_outline, str)
        assert isinstance(result_history, list)

    def test_generate_per_chapter_outline_signature(self, mock_interface, mock_logger):
        """Test that GeneratePerChapterOutline can be called with correct arguments."""
        chapter_num = 1
        total_chapters = 3
        outline = "Test outline"
        
        # This should not raise a TypeError
        result = OutlineGenerator.GeneratePerChapterOutline(
            mock_interface, mock_logger, chapter_num, total_chapters, outline
        )
        
        # Verify it returns a string
        assert isinstance(result, str)

    def test_novel_editor_signature(self, mock_interface, mock_logger):
        """Test that NovelEditor.EditNovel can be called with correct arguments."""
        chapters = ["Chapter 1: Test content"]  # Should be list of strings
        outline = "Test outline"
        total_chapters = 1
        
        # This should not raise a TypeError
        result = NovelEditor.EditNovel(mock_interface, mock_logger, chapters, outline, total_chapters)
        
        # Verify it returns a list
        assert isinstance(result, list)

    def test_scrubber_signature(self, mock_interface, mock_logger):
        """Test that Scrubber.ScrubNovel can be called with correct arguments."""
        chapters = ["Chapter 1: Test content"]  # Should be list of strings
        total_chapters = 1
        
        # This should not raise a TypeError
        result = Scrubber.ScrubNovel(mock_interface, mock_logger, chapters, total_chapters)
        
        # Verify it returns a list
        assert isinstance(result, list)

    def test_translator_signature(self, mock_interface, mock_logger):
        """Test that Translator.TranslateNovel can be called with correct arguments."""
        chapters = ["Chapter 1: Test content"]  # Should be list of strings
        total_chapters = 1
        target_language = "French"
        source_language = "English"
        
        # This should not raise a TypeError
        result = Translator.TranslateNovel(
            mock_interface, mock_logger, chapters, total_chapters, target_language, source_language
        )
        
        # Verify it returns a list
        assert isinstance(result, list)

    def test_story_info_signature(self, mock_interface, mock_logger):
        """Test that StoryInfo.GetStoryInfo can be called with correct arguments."""
        messages = [{"role": "user", "content": "Test story"}]
        
        # Mock SafeGenerateJSON to return proper format
        mock_interface.SafeGenerateJSON.return_value = (
            None, 
            {"title": "Test Story", "genre": "Fantasy", "summary": "Test summary"}, 
            None
        )
        
        # This should not raise a TypeError
        result_info, result_messages = StoryInfo.GetStoryInfo(
            mock_interface, mock_logger, messages
        )
        
        # Verify it returns expected types
        assert isinstance(result_info, dict)
        assert isinstance(result_messages, (list, type(None)))  # Can be None or int (token count)


class TestContractValidation:
    """Test that our understanding of function contracts is correct."""

    def test_function_signatures_match_expected(self):
        """Verify that function signatures match what we expect."""
        
        # Test LLMCountChapters signature
        sig = inspect.signature(ChapterDetector.LLMCountChapters)
        assert len(sig.parameters) == 3
        param_names = list(sig.parameters.keys())
        assert param_names == ['Interface', '_Logger', '_Summary']

        # Test ReviseOutline signature
        sig = inspect.signature(OutlineGenerator.ReviseOutline)
        assert len(sig.parameters) == 6  # Including defaults
        param_names = list(sig.parameters.keys())
        expected = ['Interface', '_Logger', '_Outline', '_Feedback', '_History', '_Iteration']
        assert param_names == expected

        # Test GeneratePerChapterOutline signature
        sig = inspect.signature(OutlineGenerator.GeneratePerChapterOutline)
        assert len(sig.parameters) == 5
        param_names = list(sig.parameters.keys())
        expected = ['Interface', '_Logger', '_Chapter', '_TotalChapters', '_Outline']
        assert param_names == expected

        # Test NovelEditor.EditNovel signature
        sig = inspect.signature(NovelEditor.EditNovel)
        assert len(sig.parameters) == 5
        param_names = list(sig.parameters.keys())
        expected = ['Interface', '_Logger', '_Chapters', '_Outline', '_TotalChapters']
        assert param_names == expected

        # Test Scrubber.ScrubNovel signature
        sig = inspect.signature(Scrubber.ScrubNovel)
        assert len(sig.parameters) == 4
        param_names = list(sig.parameters.keys())
        expected = ['Interface', '_Logger', '_Chapters', '_TotalChapters']
        assert param_names == expected

        # Test Translator.TranslateNovel signature
        sig = inspect.signature(Translator.TranslateNovel)
        assert len(sig.parameters) == 6
        param_names = list(sig.parameters.keys())
        expected = ['Interface', '_Logger', '_Chapters', '_TotalChapters', '_TargetLanguage', '_SourceLanguage']
        assert param_names == expected

        # Test StoryInfo.GetStoryInfo signature
        sig = inspect.signature(StoryInfo.GetStoryInfo)
        assert len(sig.parameters) == 4
        param_names = list(sig.parameters.keys())
        expected = ['Interface', '_Logger', '_Messages', '_Model']
        assert param_names == expected

    def test_mock_return_types_match_real_functions(self):
        """Verify that our mock return types match what real functions actually return."""
        # This is a placeholder for more comprehensive contract testing
        # In a real implementation, we'd capture actual function returns and compare
        pass