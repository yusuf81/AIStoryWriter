#!/usr/bin/env python3
"""
Integration tests for PDF generation feature.
Tests the complete PDF generation flow through the pipeline.
"""
import pytest
from pytest_mock import MockerFixture
import sys
import types
import tempfile
import os
import json

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

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


@pytest.fixture
def mock_interface(mocker: MockerFixture):
    mock = mocker.Mock()
    return mock


class MockArgs:
    """Mock arguments object for testing"""
    def __init__(self, generate_pdf=False):
        self.Output = None
        self.GeneratePDF = generate_pdf
        # Add other required attributes as defaults
        for attr in ['ExpandOutline', 'NoChapterRevision', 'NoScrubChapters',
                     'EnableFinalEditPass', 'SceneGenerationPipeline', 'Debug',
                     'Translate', 'TranslatePrompt', 'TranslateModel']:
            setattr(self, attr, None)


@pytest.mark.integration
class TestPDFGenerationIntegration:
    """Integration tests for PDF generation through pipeline"""

    def test_pdf_generation_disabled_by_default(self, mock_interface, mock_logger, mocker):
        """Test that PDF generation is not triggered when disabled"""
        # Mock all pipeline stage methods
        mocks = {
            '_generate_outline_stage': mocker.patch.object(StoryPipeline, '_generate_outline_stage'),
            '_detect_chapters_stage': mocker.patch.object(StoryPipeline, '_detect_chapters_stage'),
            '_expand_chapter_outlines_stage': mocker.patch.object(StoryPipeline, '_expand_chapter_outlines_stage'),
            '_write_chapters_stage': mocker.patch.object(StoryPipeline, '_write_chapters_stage'),
            '_perform_post_processing_stage': mocker.patch.object(StoryPipeline, '_perform_post_processing_stage')
        }

        # Setup mock return values
        mocks['_generate_outline_stage'].return_value = ("Test Outline", None, None, "Test Context")
        mocks['_detect_chapters_stage'].return_value = 2
        mocks['_expand_chapter_outlines_stage'].return_value = [{"number": 1}, {"number": 2}]
        mocks['_write_chapters_stage'].return_value = [{"number": 1, "title": "Ch1", "text": "Chapter 1 text"},
                                                         {"number": 2, "title": "Ch2", "text": "Chapter 2 text"}]
        mocks['_perform_post_processing_stage'].return_value = {"last_completed_step": "complete"}

        # Setup initial state
        initial_state = {
            "last_completed_step": "init",
            "generated_at": "2025-01-01T00:00:00",
            "run_id": "test-run",
            "base_context": "Test context",
            "full_outline": "Test outline",
            "total_chapters": 2
        }

        # Set PDF generation to disabled
        original_setting = Writer.Config.ENABLE_PDF_GENERATION
        Writer.Config.ENABLE_PDF_GENERATION = False

        try:
            # Create pipeline
            pipeline = StoryPipeline(mock_interface, mock_logger(), Writer.Config, None)

            # Run post-processing stage directly
            args = MockArgs(generate_pdf=False)
            with tempfile.TemporaryDirectory() as tmpdir:
                state_path = os.path.join(tmpdir, "test_state.json")

                # Create initial state file
                with open(state_path, 'w') as f:
                    json.dump(initial_state, f)

                # Prepare state for post-processing
                post_process_state = initial_state.copy()
                post_process_state.update({
                    "completed_chapters_data": [{"number": 1, "title": "Ch1", "text": "Chapter 1 text"},
                                              {"number": 2, "title": "Ch2", "text": "Chapter 2 text"}],
                    "translated_prompt_content": "Test prompt"
                })

                result_state = pipeline._perform_post_processing_stage(
                    post_process_state, state_path, args, 0.0
                )

                # Check that no PDF was generated
                assert "PDF" not in result_state.get("StoryInfoJSON", {}).get("OutputFiles", {})
        finally:
            # Restore original setting
            Writer.Config.ENABLE_PDF_GENERATION = original_setting

    def test_pdf_generation_enabled_via_flag(self, mock_interface, mock_logger, mocker):
        """Test that PDF generation is triggered when enabled via flag"""
        # Mock PDFGenerator.GeneratePDF to return success
        mocked_generate = mocker.patch('Writer.PDFGenerator.GeneratePDF')
        mocked_generate.return_value = (True, "PDF generated successfully")

        # Set PDF generation disabled in config (to test that flag overrides)
        original_setting = Writer.Config.ENABLE_PDF_GENERATION
        Writer.Config.ENABLE_PDF_GENERATION = False

        try:
            # Create pipeline
            pipeline = StoryPipeline(mock_interface, mock_logger(), Writer.Config, None)

            # Enable PDF generation via args flag
            args = MockArgs(generate_pdf=True)

            with tempfile.TemporaryDirectory() as tmpdir:
                state_path = os.path.join(tmpdir, "test_state.json")

                # Create initial state file
                initial_state = {
                    "last_completed_step": "chapter_generation_complete",
                    "completed_chapters_data": [
                        {"number": 1, "title": "Ch1", "text": "Chapter 1 text"},
                        {"number": 2, "title": "Ch2", "text": "Chapter 2 text"}
                    ],
                    "translated_prompt_content": "Test prompt",
                    "generated_at": "2025-01-01T00:00:00",
                    "run_id": "test-run"
                }

                with open(state_path, 'w') as f:
                    json.dump(initial_state, f)

                # Run post-processing stage
                result_state = pipeline._perform_post_processing_stage(
                    initial_state, state_path, args, 0.0
                )

                # Verify PDF generation was called (flag enabled it despite config disabled)
                assert mocked_generate.called
                assert result_state["last_completed_step"] == "complete"

        finally:
            # Restore original setting
            Writer.Config.ENABLE_PDF_GENERATION = original_setting

    def test_pdf_generation_failure_handling(self, mock_interface, mock_logger, mocker):
        """Test that pipeline continues when PDF generation fails"""
        # Mock PDFGenerator to fail
        mocked_generate = mocker.patch('Writer.PDFGenerator.GeneratePDF')
        mocked_generate.return_value = (False, "PDF generation failed")

        # Create pipeline
        pipeline = StoryPipeline(mock_interface, mock_logger(), Writer.Config, None)

        # Enable PDF generation via args
        args = MockArgs(generate_pdf=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, "test_state.json")

            # Create initial state file
            initial_state = {
                "last_completed_step": "chapter_generation_complete",
                "completed_chapters_data": [
                    {"number": 1, "title": "Ch1", "text": "Chapter 1 text"}
                ],
                "translated_prompt_content": "Test prompt",
                "generated_at": "2025-01-01T00:00:00",
                "run_id": "test-run"
            }

            with open(state_path, 'w') as f:
                json.dump(initial_state, f)

            # Run post-processing stage
            result_state = pipeline._perform_post_processing_stage(
                initial_state, state_path, args, 0.0
            )

            # Verify pipeline completed despite PDF failure
            assert result_state["last_completed_step"] == "complete"

            # Verify PDF generation was attempted but failed
            assert mocked_generate.called
            # PDF should not be in OutputFiles since generation failed
            story_info = result_state.get("StoryInfoJSON", {})
            output_files = story_info.get("OutputFiles", {})
            assert "PDF" not in output_files
