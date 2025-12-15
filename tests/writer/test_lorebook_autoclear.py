"""Test suite for lorebook auto-clear functionality - TDD RED Phase"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import shutil


class TestLorebookAutoClear:
    """TDD RED Tests for lorebook auto-clear functionality"""

    def test_fresh_run_should_clear_lorebook(self):
        """RED: Fresh runs should clear lorebook but currently don't

        This test demonstrates the problem: StoryPipeline doesn't clear lorebook
        for fresh runs, causing contamination from previous stories.
        """
        # This test will FAIL initially, proving the problem exists
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup existing lorebook directory to simulate contamination
            lorebook_dir = f"{temp_dir}/lorebook_db"
            os.makedirs(lorebook_dir, exist_ok=True)
            with open(f"{lorebook_dir}/test.txt", 'w') as f:
                f.write("existing lore data from previous story")

            # Mock config with auto-clear enabled
            mock_config = Mock()
            mock_config.USE_LOREBOOK = True
            mock_config.LOREBOOK_PERSIST_DIR = lorebook_dir
            mock_config.LOREBOOK_AUTO_CLEAR = True

            # Create pipeline for fresh run
            with patch('Writer.Lorebook.LorebookManager') as mock_lorebook_class:
                mock_lorebook = Mock()
                mock_lorebook_class.return_value = mock_lorebook

                from Writer.Pipeline import StoryPipeline
                pipeline = StoryPipeline(
                    interface=Mock(),
                    sys_logger=Mock(),
                    config=mock_config,
                    active_prompts=Mock(),
                    is_fresh_run=True  # Explicitly a fresh run
                )

                # Should call clear() but won't initially (RED test - EXPECTED TO FAIL)
                mock_lorebook.clear.assert_called_once()

    def test_resume_run_should_preserve_lorebook(self):
        """RED: Resume runs should preserve lorebook (will pass from start)

        This test confirms that resume runs don't clear lorebook,
        maintaining existing functionality.
        """
        with patch('Writer.Lorebook.LorebookManager') as mock_lorebook_class:
            mock_lorebook = Mock()
            mock_lorebook_class.return_value = mock_lorebook

            from Writer.Pipeline import StoryPipeline
            pipeline = StoryPipeline(
                interface=Mock(),
                sys_logger=Mock(),
                config=Mock(),
                active_prompts=Mock(),
                is_fresh_run=False  # Resume run
            )

            # Should NOT call clear() for resume
            mock_lorebook.clear.assert_not_called()

    def test_disabled_auto_clear_should_preserve_lorebook(self):
        """RED: When auto-clear is disabled, lorebook should be preserved even for fresh runs

        This test verifies that the configuration flag properly controls the behavior.
        """
        # Mock config with auto-clear disabled
        mock_config = Mock()
        mock_config.USE_LOREBOOK = True
        mock_config.LOREBOOK_AUTO_CLEAR = False  # Disabled

        with patch('Writer.Lorebook.LorebookManager') as mock_lorebook_class:
            mock_lorebook = Mock()
            mock_lorebook_class.return_value = mock_lorebook

            from Writer.Pipeline import StoryPipeline
            pipeline = StoryPipeline(
                interface=Mock(),
                sys_logger=Mock(),
                config=mock_config,
                active_prompts=Mock(),
                is_fresh_run=True  # Fresh run but auto-clear disabled
            )

            # Should NOT call clear() when disabled
            mock_lorebook.clear.assert_not_called()

    def test_lorebook_disabled_should_work_normally(self):
        """RED: When lorebook is disabled, pipeline should work normally"""
        mock_config = Mock()
        mock_config.USE_LOREBOOK = False  # Lorebook disabled

        from Writer.Pipeline import StoryPipeline
        pipeline = StoryPipeline(
            interface=Mock(),
            sys_logger=Mock(),
            config=mock_config,
            active_prompts=Mock(),
            is_fresh_run=True
        )

        # Should have lorebook as None
        assert pipeline.lorebook is None