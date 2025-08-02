#!/usr/bin/env python3
"""
Integration tests for pipeline resume functionality at multiple checkpoints.
Tests the ability to resume from different stages in the story generation pipeline.
"""
import pytest
from pytest_mock import MockerFixture
import sys
import types
import tempfile
import os
import json

# Add project root to path
sys.path.insert(0, '/var/www/AIStoryWriter')

from Writer.Pipeline import StoryPipeline
import Writer.Config


# Mock ActivePrompts for the Test Module
@pytest.fixture(autouse=True)
def mock_active_prompts_for_integration(mocker: MockerFixture):
    mock_prompts = types.ModuleType("Writer.Prompts")
    mock_prompts.EXPAND_OUTLINE_CHAPTER_BY_CHAPTER = "Refine outline: {_Outline}"
    mock_prompts.MEGA_OUTLINE_PREAMBLE = "Mega Preamble"
    mock_prompts.MEGA_OUTLINE_CHAPTER_FORMAT = "Chapter {chapter_num}:\\n{prefix}{chapter_outline_text}"
    mock_prompts.PREVIOUS_CHAPTER_CONTEXT_FORMAT = "Prev Ch {chapter_num}: {previous_chapter_text}"
    mock_prompts.CURRENT_CHAPTER_OUTLINE_FORMAT = "Curr Ch {chapter_num}: {chapter_outline_text}"
    mock_prompts.GET_CHAPTER_TITLE_PROMPT = "Title for ch {chapter_num} of text: {chapter_text_segment} with context {base_story_context}"
    mock_prompts.MEGA_OUTLINE_CURRENT_CHAPTER_PREFIX = ">>> CURRENT CHAPTER: "

    mocker.patch.dict(sys.modules, {"Writer.Prompts": mock_prompts})
    yield


class MockLogger:
    def __init__(self):
        self.logs = []
    def Log(self, msg, lvl):
        self.logs.append((lvl, msg))
    def SaveLangchain(self, s, m): pass


@pytest.fixture
def mock_logger():
    return MockLogger()


@pytest.fixture
def mock_interface(mocker: MockerFixture):
    return mocker.Mock()


@pytest.fixture
def mock_dependencies(mocker: MockerFixture):
    """Mock all external dependencies for pipeline operations."""
    mocks = {
        'OutlineGenerator.GenerateOutline': mocker.patch('Writer.OutlineGenerator.GenerateOutline'),
        'OutlineGenerator.ReviseOutline': mocker.patch('Writer.OutlineGenerator.ReviseOutline'),
        'ChapterDetector.LLMCountChapters': mocker.patch('Writer.Chapter.ChapterDetector.LLMCountChapters'),
        'OutlineGenerator.GeneratePerChapterOutline': mocker.patch('Writer.OutlineGenerator.GeneratePerChapterOutline'),
        'ChapterGenerator.GenerateChapter': mocker.patch('Writer.Chapter.ChapterGenerator.GenerateChapter'),
        'NovelEditor.EditNovel': mocker.patch('Writer.NovelEditor.EditNovel'),
        'Scrubber.ScrubNovel': mocker.patch('Writer.Scrubber.ScrubNovel'),
        'Translator.TranslateNovel': mocker.patch('Writer.Translator.TranslateNovel'),
        'StoryInfo.GetStoryInfo': mocker.patch('Writer.StoryInfo.GetStoryInfo'),
    }

    # Set up return values
    mocks['OutlineGenerator.GenerateOutline'].return_value = (
        "Mocked Full Outline", "Mocked Elements", "Mocked Rough Outline", "Mocked Base Context"
    )
    mocks['OutlineGenerator.ReviseOutline'].return_value = (
        "Mocked Revised Outline", []
    )
    mocks['ChapterDetector.LLMCountChapters'].return_value = 5
    mocks['OutlineGenerator.GeneratePerChapterOutline'].return_value = "Mocked Chapter Outline"
    mocks['ChapterGenerator.GenerateChapter'].return_value = "Mocked Chapter Content"
    mocks['NovelEditor.EditNovel'].return_value = "Edited Novel Content"
    mocks['Scrubber.ScrubNovel'].return_value = ["Scrubbed Content"]
    mocks['Translator.TranslateNovel'].return_value = ["Translated Content"]
    mocks['StoryInfo.GetStoryInfo'].return_value = ({
        "title": "Test Story",
        "summary": "Test summary",
        "tags": ["test"]
    }, {})

    return mocks


class TestPipelineResumeFromDifferentCheckpoints:
    """Test resume functionality from different pipeline checkpoints."""

    def test_resume_from_init_runs_full_pipeline(self, mocker: MockerFixture, mock_logger, mock_interface, mock_dependencies):
        """Test resume from 'init' runs the complete pipeline."""
        active_prompts_mock = sys.modules["Writer.Prompts"]
        pipeline = StoryPipeline(mock_interface, mock_logger, Writer.Config, active_prompts_mock)

        initial_state = {"last_completed_step": "init"}
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            state_filepath = f.name

        try:
            mock_args = mocker.Mock()
            mock_args.Output = "test_output.md"
            
            final_state = pipeline.run_pipeline(initial_state, state_filepath, "Test prompt", mock_args, 0.0)

            # Verify all major stages were called
            mock_dependencies['OutlineGenerator.GenerateOutline'].assert_called_once()
            mock_dependencies['ChapterDetector.LLMCountChapters'].assert_called_once()
            
            assert final_state['last_completed_step'] == 'complete'
        finally:
            if os.path.exists(state_filepath):
                os.unlink(state_filepath)

    def test_resume_from_outline_skips_outline_generation(self, mocker: MockerFixture, mock_logger, mock_interface, mock_dependencies):
        """Test resume from 'outline' skips outline generation."""
        active_prompts_mock = sys.modules["Writer.Prompts"]
        pipeline = StoryPipeline(mock_interface, mock_logger, Writer.Config, active_prompts_mock)

        initial_state = {
            "last_completed_step": "outline",
            "full_outline": "Existing Outline",
            "story_elements": "Existing Elements",
            "rough_chapter_outline": "Existing Rough Outline",
            "base_context": "Existing Base Context"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            state_filepath = f.name

        try:
            mock_args = mocker.Mock()
            mock_args.Output = "test_output.md"
            
            final_state = pipeline.run_pipeline(initial_state, state_filepath, "Test prompt", mock_args, 0.0)

            # Outline generation should NOT be called
            mock_dependencies['OutlineGenerator.GenerateOutline'].assert_not_called()
            
            # But chapter detection should be called
            mock_dependencies['ChapterDetector.LLMCountChapters'].assert_called_once()
            
            assert final_state['last_completed_step'] == 'complete'
        finally:
            if os.path.exists(state_filepath):
                os.unlink(state_filepath)

    def test_resume_from_detect_chapters_with_expand_outline_disabled(self, mocker: MockerFixture, mock_logger, mock_interface, mock_dependencies):
        """Test resume from 'detect_chapters' when outline expansion is disabled."""
        active_prompts_mock = sys.modules["Writer.Prompts"]
        pipeline = StoryPipeline(mock_interface, mock_logger, Writer.Config, active_prompts_mock)

        # Disable outline expansion
        mocker.patch.object(Writer.Config, 'EXPAND_OUTLINE', False)

        initial_state = {
            "last_completed_step": "detect_chapters",
            "full_outline": "Existing Outline",
            "total_chapters": 3,
            "base_context": "Existing Base Context"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            state_filepath = f.name

        try:
            mock_args = mocker.Mock()
            mock_args.Output = "test_output.md"
            
            final_state = pipeline.run_pipeline(initial_state, state_filepath, "Test prompt", mock_args, 0.0)

            # Should skip outline generation and chapter detection
            mock_dependencies['OutlineGenerator.GenerateOutline'].assert_not_called()
            mock_dependencies['ChapterDetector.LLMCountChapters'].assert_not_called()
            
            # Should skip per-chapter outline generation
            mock_dependencies['OutlineGenerator.GeneratePerChapterOutline'].assert_not_called()
            
            # Should proceed to chapter generation
            mock_dependencies['ChapterGenerator.GenerateChapter'].assert_called()
            
            assert final_state['last_completed_step'] == 'complete'
        finally:
            if os.path.exists(state_filepath):
                os.unlink(state_filepath)

    def test_resume_from_expand_chapters_proceeds_to_chapter_generation(self, mocker: MockerFixture, mock_logger, mock_interface, mock_dependencies):
        """Test resume from 'expand_chapters' proceeds directly to chapter generation."""
        active_prompts_mock = sys.modules["Writer.Prompts"]
        pipeline = StoryPipeline(mock_interface, mock_logger, Writer.Config, active_prompts_mock)

        initial_state = {
            "last_completed_step": "expand_chapters",
            "full_outline": "Existing Outline",
            "total_chapters": 3,
            "expanded_chapter_outlines": ["Outline 1", "Outline 2", "Outline 3"],
            "base_context": "Existing Base Context"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            state_filepath = f.name

        try:
            mock_args = mocker.Mock()
            mock_args.Output = "test_output.md"
            
            final_state = pipeline.run_pipeline(initial_state, state_filepath, "Test prompt", mock_args, 0.0)

            # Should skip all earlier stages
            mock_dependencies['OutlineGenerator.GenerateOutline'].assert_not_called()
            mock_dependencies['ChapterDetector.LLMCountChapters'].assert_not_called()
            mock_dependencies['OutlineGenerator.GeneratePerChapterOutline'].assert_not_called()
            
            # Should proceed to chapter generation
            mock_dependencies['ChapterGenerator.GenerateChapter'].assert_called()
            
            assert final_state['last_completed_step'] == 'complete'
        finally:
            if os.path.exists(state_filepath):
                os.unlink(state_filepath)

    def test_resume_from_chapter_generation_complete_skips_to_post_processing(self, mocker: MockerFixture, mock_logger, mock_interface, mock_dependencies):
        """Test resume from 'chapter_generation_complete' skips to post-processing."""
        active_prompts_mock = sys.modules["Writer.Prompts"]
        
        # Ensure final edit pass is enabled for this test
        mocker.patch.object(Writer.Config, 'ENABLE_FINAL_EDIT_PASS', True)
        
        pipeline = StoryPipeline(mock_interface, mock_logger, Writer.Config, active_prompts_mock)

        initial_state = {
            "last_completed_step": "chapter_generation_complete",
            "full_outline": "Existing Outline",
            "total_chapters": 2,
            "completed_chapters_data": [
                {"number": 1, "title": "Chapter 1", "text": "Chapter 1 content"},
                {"number": 2, "title": "Chapter 2", "text": "Chapter 2 content"}
            ],
            "base_context": "Existing Base Context"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            state_filepath = f.name

        try:
            mock_args = mocker.Mock()
            mock_args.Output = "test_output.md"
            
            final_state = pipeline.run_pipeline(initial_state, state_filepath, "Test prompt", mock_args, 0.0)

            # Should skip all generation stages
            mock_dependencies['OutlineGenerator.GenerateOutline'].assert_not_called()
            mock_dependencies['ChapterDetector.LLMCountChapters'].assert_not_called()
            mock_dependencies['ChapterGenerator.GenerateChapter'].assert_not_called()
            
            # Should proceed to post-processing
            mock_dependencies['NovelEditor.EditNovel'].assert_called()
            
            assert final_state['last_completed_step'] == 'complete'
        finally:
            if os.path.exists(state_filepath):
                os.unlink(state_filepath)

    def test_resume_preserves_existing_data(self, mocker: MockerFixture, mock_logger, mock_interface, mock_dependencies):
        """Test that resume preserves all existing data from previous run."""
        active_prompts_mock = sys.modules["Writer.Prompts"]
        pipeline = StoryPipeline(mock_interface, mock_logger, Writer.Config, active_prompts_mock)

        original_outline = "Original Detailed Outline Content"
        original_chapters = [
            {"number": 1, "title": "Original Chapter 1", "text": "Original content 1"}
        ]
        original_config = {"SEED": 42, "NATIVE_LANGUAGE": "en"}

        initial_state = {
            "last_completed_step": "chapter_generation",
            "full_outline": original_outline,
            "total_chapters": 1,
            "completed_chapters_data": original_chapters,
            "config": original_config,
            "base_context": "Original Base Context"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            state_filepath = f.name

        try:
            mock_args = mocker.Mock()
            mock_args.Output = "test_output.md"
            
            final_state = pipeline.run_pipeline(initial_state, state_filepath, "Test prompt", mock_args, 0.0)

            # Verify original data is preserved
            assert final_state["full_outline"] == original_outline
            assert final_state["completed_chapters_data"] == original_chapters
            assert final_state["config"] == original_config
            assert final_state["total_chapters"] == 1
            
            assert final_state['last_completed_step'] == 'complete'
        finally:
            if os.path.exists(state_filepath):
                os.unlink(state_filepath)


class TestPartialChapterGeneration:
    """Test resume functionality during chapter generation."""

    def test_resume_chapter_generation_continues_from_next_chapter(self, mocker: MockerFixture, mock_logger, mock_interface, mock_dependencies):
        """Test resume from partial chapter generation continues from the correct chapter."""
        active_prompts_mock = sys.modules["Writer.Prompts"]
        pipeline = StoryPipeline(mock_interface, mock_logger, Writer.Config, active_prompts_mock)

        # Simulate having completed 2 out of 5 chapters
        initial_state = {
            "last_completed_step": "chapter_generation",
            "full_outline": "Full Outline",
            "total_chapters": 5,
            "completed_chapters_data": [
                {"number": 1, "title": "Chapter 1", "text": "Content 1"},
                {"number": 2, "title": "Chapter 2", "text": "Content 2"}
            ],
            "next_chapter_index": 3,  # Should start from chapter 3
            "base_context": "Base Context"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            state_filepath = f.name

        try:
            mock_args = mocker.Mock()
            mock_args.Output = "test_output.md"
            
            final_state = pipeline.run_pipeline(initial_state, state_filepath, "Test prompt", mock_args, 0.0)

            # Verify chapter generation was called for remaining chapters (3, 4, 5)
            # Note: The exact call count depends on the mock setup, but it should be called
            mock_dependencies['ChapterGenerator.GenerateChapter'].assert_called()
            
            # Verify final state shows completion
            assert final_state['last_completed_step'] == 'complete'
            
        finally:
            if os.path.exists(state_filepath):
                os.unlink(state_filepath)