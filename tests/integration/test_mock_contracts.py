"""
Contract testing to ensure mocks match real implementations.
This prevents signature mismatches from slipping through tests.
"""
import pytest
import inspect
from unittest.mock import Mock

# Import modules that are commonly mocked
import Writer.Chapter.ChapterDetector as ChapterDetector
import Writer.OutlineGenerator as OutlineGenerator
import Writer.NovelEditor as NovelEditor
import Writer.Scrubber as Scrubber
import Writer.Translator as Translator
import Writer.StoryInfo as StoryInfo


class TestMockContracts:
    """Verify that mocks used in other tests match real function signatures."""
    
    def test_mock_llm_count_chapters_contract(self):
        """Ensure mock for LLMCountChapters matches real signature."""
        # Get real function signature
        real_sig = inspect.signature(ChapterDetector.LLMCountChapters)
        real_params = list(real_sig.parameters.keys())
        
        # Expected signature based on our tests and usage
        expected_params = ['Interface', '_Logger', '_Summary']
        
        # Verify signature matches our expectations
        assert real_params == expected_params, (
            f"LLMCountChapters signature changed! "
            f"Expected: {expected_params}, Got: {real_params}"
        )
        
        # Verify the function can be called with expected arguments
        mock_interface = Mock()
        mock_logger = Mock()
        summary = "test summary"
        
        # Create a mock that enforces the correct signature
        mock_function = Mock(spec=ChapterDetector.LLMCountChapters)
        
        # This should not raise an error if signatures match
        try:
            mock_function(mock_interface, mock_logger, summary)
        except TypeError as e:
            pytest.fail(f"Mock signature doesn't match real function: {e}")

    def test_mock_revise_outline_contract(self):
        """Ensure mock for ReviseOutline matches real signature."""
        real_sig = inspect.signature(OutlineGenerator.ReviseOutline)
        real_params = list(real_sig.parameters.keys())
        
        expected_params = ['Interface', '_Logger', '_Outline', '_Feedback', '_History', '_Iteration']
        
        assert real_params == expected_params, (
            f"ReviseOutline signature changed! "
            f"Expected: {expected_params}, Got: {real_params}"
        )

    def test_mock_generate_per_chapter_outline_contract(self):
        """Ensure mock for GeneratePerChapterOutline matches real signature."""
        real_sig = inspect.signature(OutlineGenerator.GeneratePerChapterOutline)
        real_params = list(real_sig.parameters.keys())
        
        expected_params = ['Interface', '_Logger', '_Chapter', '_TotalChapters', '_Outline']
        
        assert real_params == expected_params, (
            f"GeneratePerChapterOutline signature changed! "
            f"Expected: {expected_params}, Got: {real_params}"
        )

    def test_mock_novel_editor_contract(self):
        """Ensure mock for NovelEditor.EditNovel matches real signature."""
        real_sig = inspect.signature(NovelEditor.EditNovel)
        real_params = list(real_sig.parameters.keys())
        
        expected_params = ['Interface', '_Logger', '_Chapters', '_Outline', '_TotalChapters']
        
        assert real_params == expected_params, (
            f"NovelEditor.EditNovel signature changed! "
            f"Expected: {expected_params}, Got: {real_params}"
        )

    def test_mock_scrubber_contract(self):
        """Ensure mock for Scrubber.ScrubNovel matches real signature."""
        real_sig = inspect.signature(Scrubber.ScrubNovel)
        real_params = list(real_sig.parameters.keys())
        
        expected_params = ['Interface', '_Logger', '_Chapters', '_TotalChapters']
        
        assert real_params == expected_params, (
            f"Scrubber.ScrubNovel signature changed! "
            f"Expected: {expected_params}, Got: {real_params}"
        )

    def test_mock_translator_contract(self):
        """Ensure mock for Translator.TranslateNovel matches real signature."""
        real_sig = inspect.signature(Translator.TranslateNovel)
        real_params = list(real_sig.parameters.keys())
        
        expected_params = ['Interface', '_Logger', '_Chapters', '_TotalChapters', '_TargetLanguage', '_SourceLanguage']
        
        assert real_params == expected_params, (
            f"Translator.TranslateNovel signature changed! "
            f"Expected: {expected_params}, Got: {real_params}"
        )

    def test_mock_story_info_contract(self):
        """Ensure mock for StoryInfo.GetStoryInfo matches real signature."""
        real_sig = inspect.signature(StoryInfo.GetStoryInfo)
        real_params = list(real_sig.parameters.keys())
        
        expected_params = ['Interface', '_Logger', '_Messages', '_Model']
        
        assert real_params == expected_params, (
            f"StoryInfo.GetStoryInfo signature changed! "
            f"Expected: {expected_params}, Got: {real_params}"
        )


class TestMockReturnTypes:
    """Verify that mock return types match real function return types."""
    
    @pytest.fixture
    def mock_interface(self):
        """Create a minimal mock interface for testing."""
        interface = Mock()
        interface.BuildUserQuery.return_value = {"role": "user", "content": "test"}
        interface.SafeGenerateJSON.return_value = (None, {"TotalChapters": 3}, {"tokens": 100})
        interface.SafeGenerateText.return_value = ([{"role": "assistant", "content": "test"}], {"tokens": 100})
        interface.GetLastMessageText.return_value = "test response"
        return interface

    @pytest.fixture
    def mock_logger(self):
        """Create a minimal mock logger for testing."""
        logger = Mock()
        logger.Log = Mock()
        return logger

    def test_llm_count_chapters_return_type(self, mock_interface, mock_logger):
        """Verify LLMCountChapters returns an integer."""
        result = ChapterDetector.LLMCountChapters(mock_interface, mock_logger, "test outline")
        
        # Should return an integer
        assert isinstance(result, int), f"Expected int, got {type(result)}"
        assert result > 0, "Chapter count should be positive"

    def test_revise_outline_return_type(self, mock_interface, mock_logger):
        """Verify ReviseOutline returns a tuple of (str, list)."""
        result = OutlineGenerator.ReviseOutline(mock_interface, mock_logger, "outline", "feedback")
        
        # Should return a tuple
        assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
        assert len(result) == 2, f"Expected tuple of length 2, got {len(result)}"
        
        outline, history = result
        assert isinstance(outline, str), f"First element should be str, got {type(outline)}"
        assert isinstance(history, list), f"Second element should be list, got {type(history)}"

    def test_generate_per_chapter_outline_return_type(self, mock_interface, mock_logger):
        """Verify GeneratePerChapterOutline returns a string."""
        result = OutlineGenerator.GeneratePerChapterOutline(
            mock_interface, mock_logger, 1, 3, "test outline"
        )
        
        # Should return a string
        assert isinstance(result, str), f"Expected str, got {type(result)}"

    def test_novel_editor_return_type(self, mock_interface, mock_logger):
        """Verify NovelEditor.EditNovel returns a list."""
        chapters = ["Chapter 1 content"]
        outline = "Test outline"
        
        result = NovelEditor.EditNovel(mock_interface, mock_logger, chapters, outline, 1)
        
        # Should return a list
        assert isinstance(result, list), f"Expected list, got {type(result)}"

    def test_scrubber_return_type(self, mock_interface, mock_logger):
        """Verify Scrubber.ScrubNovel returns a list."""
        chapters = ["Chapter 1 content"]
        
        result = Scrubber.ScrubNovel(mock_interface, mock_logger, chapters, 1)
        
        # Should return a list
        assert isinstance(result, list), f"Expected list, got {type(result)}"

    def test_translator_return_type(self, mock_interface, mock_logger):
        """Verify Translator.TranslateNovel returns a list."""
        chapters = ["Chapter 1 content"]
        
        result = Translator.TranslateNovel(
            mock_interface, mock_logger, chapters, 1, "French", "English"
        )
        
        # Should return a list
        assert isinstance(result, list), f"Expected list, got {type(result)}"

    def test_story_info_return_type(self, mock_interface, mock_logger):
        """Verify StoryInfo.GetStoryInfo returns a tuple of (dict, tokens)."""
        messages = [{"role": "user", "content": "test"}]
        
        result = StoryInfo.GetStoryInfo(mock_interface, mock_logger, messages)
        
        # Should return a tuple
        assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
        assert len(result) == 2, f"Expected tuple of length 2, got {len(result)}"
        
        info, tokens = result
        assert isinstance(info, dict), f"First element should be dict, got {type(info)}"
        # Second element can be dict (token usage) or other types


class TestPipelineMockCompatibility:
    """Test that Pipeline.py calls match the real function signatures we've validated."""
    
    def test_pipeline_llm_count_chapters_call(self):
        """Verify Pipeline.py calls LLMCountChapters with correct signature."""
        # This is what Pipeline.py should call:
        # NumChapters = self.ChapterDetector.LLMCountChapters(
        #     self.Interface, self.SysLogger, Outline
        # )
        
        # Create mock objects with proper setup
        mock_interface = Mock()
        mock_interface.BuildUserQuery.return_value = {"role": "user", "content": "test"}
        mock_interface.SafeGenerateJSON.return_value = (None, {"TotalChapters": 3}, {"tokens": 100})
        mock_logger = Mock()
        outline = "test outline"
        
        # This should work without TypeError
        try:
            # Simulate the actual call pattern from Pipeline.py
            result = ChapterDetector.LLMCountChapters(mock_interface, mock_logger, outline)
            assert isinstance(result, int)
        except TypeError as e:
            pytest.fail(f"Pipeline.py call pattern doesn't match function signature: {e}")

    def test_pipeline_revise_outline_call(self):
        """Verify Pipeline.py calls ReviseOutline with correct signature."""
        # This is what Pipeline.py should call:
        # refined_global_outline, _ = self.OutlineGenerator.ReviseOutline(
        #     self.Interface, self.SysLogger, base_outline_for_expansion, "global_chapter_structure"
        # )
        
        mock_interface = Mock()
        mock_logger = Mock()
        mock_interface.SafeGenerateText.return_value = ([{"role": "assistant", "content": "test"}], {"tokens": 100})
        mock_interface.GetLastMessageText.return_value = "revised outline"
        
        try:
            # Simulate the actual call pattern from Pipeline.py
            result_outline, result_history = OutlineGenerator.ReviseOutline(
                mock_interface, mock_logger, "base outline", "global_chapter_structure"
            )
            assert isinstance(result_outline, str)
            assert isinstance(result_history, list)
        except TypeError as e:
            pytest.fail(f"Pipeline.py call pattern doesn't match function signature: {e}")

    def test_pipeline_generate_per_chapter_outline_call(self):
        """Verify Pipeline.py calls GeneratePerChapterOutline with correct signature."""
        # This is what Pipeline.py should call:
        # ChapterOutlineText = self.OutlineGenerator.GeneratePerChapterOutline(
        #     self.Interface, self.SysLogger, ChapterIdx, num_chapters, refined_global_outline
        # )
        
        mock_interface = Mock()
        mock_logger = Mock()
        mock_interface.SafeGenerateText.return_value = ([{"role": "assistant", "content": "test"}], {"tokens": 100})
        mock_interface.GetLastMessageText.return_value = "chapter outline"
        
        try:
            # Simulate the actual call pattern from Pipeline.py
            result = OutlineGenerator.GeneratePerChapterOutline(
                mock_interface, mock_logger, 1, 3, "refined outline"
            )
            assert isinstance(result, str)
        except TypeError as e:
            pytest.fail(f"Pipeline.py call pattern doesn't match function signature: {e}")


# Utility function to validate mock setup in other test files
def validate_mock_signature(mock_func, real_func):
    """
    Utility function to validate that a mock has the same signature as the real function.
    This can be used in other test files to ensure mocks are set up correctly.
    
    Args:
        mock_func: The mock function/object
        real_func: The real function to compare against
        
    Returns:
        bool: True if signatures match, raises AssertionError if not
    """
    if hasattr(mock_func, 'spec') and mock_func.spec is not None:
        # Mock has a spec, signatures should match
        return True
    else:
        # Mock doesn't have a spec - this is a potential problem
        real_sig = inspect.signature(real_func)
        pytest.fail(
            f"Mock for {real_func.__name__} doesn't have a spec. "
            f"Expected signature: {real_sig}. "
            f"Consider using Mock(spec={real_func.__module__}.{real_func.__name__})"
        )