#!/usr/bin/env python3
"""
TDD tests for LLMEditor Pydantic model assignments.
Tests that critique/feedback functions use the correct Pydantic models.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from Writer.Models import ReviewOutput, ChapterOutput


class TestLLMEditorModelAssignments:
    """Test that LLMEditor functions use correct Pydantic models"""

    def test_get_feedback_on_outline_uses_review_output_after_fix(self, mock_logger):
        """Test that GetFeedbackOnOutline now uses correct model (ReviewOutput) after fix"""
        from Writer.LLMEditor import GetFeedbackOnOutline

        # Create mock interface and mock SafeGeneratePydantic method
        mock_interface = Mock()

        # Mock SafeGeneratePydantic to capture the model parameter
        mock_interface.SafeGeneratePydantic.return_value = (
            [{"role": "user", "content": "test"}],
            Mock(),  # Mock ReviewOutput object
            {'prompt_tokens': 10, 'completion_tokens': 20}
        )

        # Call the function (after fix)
        result = GetFeedbackOnOutline(mock_interface, mock_logger(), "Test outline content")

        # Verify SafeGeneratePydantic was called
        mock_interface.SafeGeneratePydantic.assert_called_once()
        call_args = mock_interface.SafeGeneratePydantic.call_args

        # Check the model parameter (should be correct: ReviewOutput)
        called_model = call_args[0][3]  # [Logger, Messages, Config.REVISION_MODEL, MODEL]
        assert called_model == ReviewOutput, f"After fix uses ReviewOutput: {called_model}"
        assert called_model != ChapterOutput, "Should NOT use ChapterOutput (after fix)"

    def test_get_feedback_on_chapter_uses_review_output_after_fix(self, mock_logger):
        """Test that GetFeedbackOnChapter now uses correct model (ReviewOutput) after fix"""
        from Writer.LLMEditor import GetFeedbackOnChapter

        # Create mock interface and mock SafeGeneratePydantic method
        mock_interface = Mock()

        # Mock SafeGeneratePydantic to capture the model parameter
        mock_interface.SafeGeneratePydantic.return_value = (
            [{"role": "user", "content": "test"}],
            Mock(),  # Mock ReviewOutput object
            {'prompt_tokens': 10, 'completion_tokens': 20}
        )

        # Call the function (after fix)
        result = GetFeedbackOnChapter(mock_interface, mock_logger(), "Test chapter content", "Test outline content")

        # Verify SafeGeneratePydantic was called
        mock_interface.SafeGeneratePydantic.assert_called_once()
        call_args = mock_interface.SafeGeneratePydantic.call_args

        # Check the model parameter (should be correct: ReviewOutput)
        called_model = call_args[0][3]  # [Logger, Messages, Config.REVISION_MODEL, MODEL]
        assert called_model == ReviewOutput, f"After fix uses ReviewOutput: {called_model}"
        assert called_model != ChapterOutput, "Should NOT use ChapterOutput (after fix)"

    def test_get_feedback_on_outline_should_use_review_output(self, mock_logger):
        """Test that GetFeedbackOnOutline should use ReviewOutput after fix"""
        from Writer.LLMEditor import GetFeedbackOnOutline

        # Create a valid ReviewOutput instance to test return structure
        mock_review_output = ReviewOutput(
            feedback="Kritik konstruktif: Outline perlu perbaikan pada...",
            suggestions=["Tambah detail karakter", "Perbaiki alur"],
            rating=6
        )

        # Mock interface to return our ReviewOutput instance
        mock_interface = Mock()
        mock_interface.SafeGeneratePydantic.return_value = (
            [{"role": "user", "content": "test"}],
            mock_review_output,
            {'prompt_tokens': 10, 'completion_tokens': 20}
        )

        # Call the function (after fix - should use ReviewOutput)
        result = GetFeedbackOnOutline(mock_interface, mock_logger(), "Test outline content")

        # Verify result is the feedback text from ReviewOutput
        assert result == "Kritik konstruktif: Outline perlu perbaikan pada..."

        # Verify ReviewOutput was used after fix
        call_args = mock_interface.SafeGeneratePydantic.call_args
        called_model = call_args[0][3]
        assert called_model == ReviewOutput, f"After fix should use ReviewOutput: {called_model}"

    def test_get_feedback_on_chapter_should_use_review_output(self, mock_logger):
        """Test that GetFeedbackOnChapter should use ReviewOutput after fix"""
        from Writer.LLMEditor import GetFeedbackOnChapter

        # Create a valid ReviewOutput instance
        mock_review_output = ReviewOutput(
            feedback="Kritik konstruktif: Chapter perlu pengembangan...",
            suggestions=["Deepen character motivation", "Add more scene setting"],
            rating=7
        )

        # Mock interface to return our ReviewOutput instance
        mock_interface = Mock()
        mock_interface.SafeGeneratePydantic.return_value = (
            [{"role": "user", "content": "test"}],
            mock_review_output,
            {'prompt_tokens': 10, 'completion_tokens': 20}
        )

        # Call the function (after fix - should use ReviewOutput)
        result = GetFeedbackOnChapter(mock_interface, mock_logger(), "Test chapter content", "Test outline content")

        # Verify result is the feedback text from ReviewOutput
        assert result == "Kritik konstruktif: Chapter perlu pengembangan..."

        # Verify ReviewOutput was used after fix
        call_args = mock_interface.SafeGeneratePydantic.call_args
        called_model = call_args[0][3]
        assert called_model == ReviewOutput, f"After fix should use ReviewOutput: {called_model}"