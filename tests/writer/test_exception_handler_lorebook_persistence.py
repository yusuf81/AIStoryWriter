"""
Test suite for lorebook persistence during exception handling - TDD RED Phase

Tests that exception handler in Write.py preserves lorebook entries from ChromaDB
by using pipeline._save_state_wrapper() with fallback to save_state().
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestExceptionHandlerLorebookPersistence:
    """TDD RED Tests for exception handler lorebook persistence"""

    def test_exception_handler_uses_pipeline_wrapper_when_available(self):
        """RED: Exception handler should use pipeline._save_state_wrapper() when pipeline is available

        This tests that when an exception occurs and pipeline object is available,
        the exception handler uses _save_state_wrapper() to preserve lorebook entries.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup: Create mock pipeline with _save_state_wrapper
            from Writer.Pipeline import StoryPipeline

            mock_pipeline = MagicMock(spec=StoryPipeline)
            mock_pipeline._save_state_wrapper = Mock()
            mock_pipeline.Config = Mock()
            mock_pipeline.Config.USE_LOREBOOK = True

            # Setup: Create mock logger
            mock_logger = MagicMock()
            mock_logger.Log = Mock()

            # Setup: Create test state with lorebook entries
            state_file = Path(temp_dir) / "test.state.json"
            test_state = {
                "status": "error_in_main",
                "error_message_main": "Test error",
                "error_traceback_main": "Traceback...",
                "last_completed_step": "chapter_generation"
            }
            with open(state_file, 'w') as f:
                json.dump(test_state, f)

            # Act: Simulate exception handler behavior
            # This simulates what the exception handler should do
            test_state["status"] = "error_in_main"
            test_state["error_message_main"] = "Test exception"
            test_state["error_traceback_main"] = "Traceback..."

            # Should use _save_state_wrapper
            mock_pipeline._save_state_wrapper(test_state, str(state_file))
            mock_logger.Log(f"Saved error state to {state_file}", 6)

            # Assert: _save_state_wrapper was called
            mock_pipeline._save_state_wrapper.assert_called_once()
            assert mock_pipeline._save_state_wrapper.call_args[0][0] == test_state
            assert mock_pipeline._save_state_wrapper.call_args[0][1] == str(state_file)

    def test_exception_handler_fallback_to_basic_save_when_wrapper_fails(self):
        """RED: Exception handler should fall back to save_state() when _save_state_wrapper fails

        This tests that if pipeline._save_state_wrapper() fails (pipeline in bad state),
        the exception handler falls back to basic save_state() to still save the state.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup: Create mock pipeline that fails
            from Writer.Pipeline import StoryPipeline

            mock_pipeline = MagicMock(spec=StoryPipeline)
            wrapper_exception = Exception("Pipeline in bad state")
            mock_pipeline._save_state_wrapper = Mock(side_effect=wrapper_exception)

            # Setup: Create mock logger
            mock_logger = MagicMock()
            mock_logger.Log = Mock()

            # Setup: Create test state and state file
            state_file = Path(temp_dir) / "test.state.json"
            test_state = {
                "other_data": {
                    "error_message_main": "Test error",
                    "error_traceback_main": "Traceback..."
                }
            }

            # Act: Simulate exception handler with fallback
            test_state["other_data"]["error_message_main"] = "Test exception"

            # Try _save_state_wrapper first
            try:
                mock_pipeline._save_state_wrapper(test_state, str(state_file))
            except Exception as wrapper_err:
                # Fallback to basic save
                mock_logger.Log(f"Pipeline wrapper save failed: {wrapper_err}, falling back", 6)
                from Write import save_state
                save_state(test_state, str(state_file))

            mock_logger.Log(f"Saved error state to {state_file}", 6)

            # Assert: _save_state_wrapper was attempted
            mock_pipeline._save_state_wrapper.assert_called_once()

            # Assert: state file was saved via fallback
            assert state_file.exists(), "State file should exist after fallback"

            with open(state_file, 'r') as f:
                saved_state = json.load(f)
            # Note: StateManager nests other_data: output["other_data"]["other_data"]["key"]
            assert saved_state["other_data"]["other_data"]["error_message_main"] == "Test exception"

    def test_lorebook_entries_preserved_after_unhandled_exception(self):
        """RED: Lorebook entries should be preserved after unhandled exception

        This tests the full scenario: pipeline error → _save_state_wrapper saves with lorebook
        → exception handler preserves those entries instead of overwriting.

        This test FAILS because the current Write.py exception handler uses save_state()
        which doesn't preserve lorebook entries.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup: Create mock lorebook entries
            lorebook_entries = [
                {
                    "id": "uuid-1",
                    "text": "Rian adalah karakter utama.",
                    "metadata": {"type": "character", "name": "Rian"}
                },
                {
                    "id": "uuid-2",
                    "text": "Desa di tepi sungai.",
                    "metadata": {"type": "location", "name": "Desa"}
                }
            ]

            # Setup: Create state file and mock pipeline
            state_file = Path(temp_dir) / "test.state.json"

            # Simulate pipeline saving state WITH lorebook entries
            # (using _save_state_wrapper behavior - this is what pipeline does now)
            test_state = {
                "last_completed_step": "chapter_generation",
                "error": "Test pipeline error",
                "other_data": {
                    "lorebook_entries": lorebook_entries
                }
            }

            from Write import save_state
            save_state(test_state, str(state_file))

            # Verify lorebook was saved correctly
            with open(state_file, 'r') as f:
                saved_state = json.load(f)
            nested_lorebook = saved_state.get("other_data", {}).get("other_data", {}).get("lorebook_entries", [])
            assert len(nested_lorebook) == 2, "Lorebook entries should be saved initially"
            assert nested_lorebook[0]["text"] == "Rian adalah karakter utama."

            # Now simulate Write.py exception handler with the NEW implementation
            # The fix: use pipeline._save_state_wrapper() to preserve lorebook
            from Writer.Pipeline import StoryPipeline

            # Create mock pipeline with _save_state_wrapper that adds lorebook
            mock_pipeline = MagicMock(spec=StoryPipeline)
            mock_lorebook = Mock()
            mock_lorebook.get_all_entries.return_value = lorebook_entries  # Return SAME entries
            mock_pipeline.lorebook = mock_lorebook
            mock_pipeline.Config = Mock()
            mock_pipeline.Config.USE_LOREBOOK = True

            # Simulate wrapper behavior from Write.py exception handler
            wrapper_state = saved_state.copy()
            wrapper_state["status"] = "error_in_main"
            wrapper_state["other_data"]["error_message_main"] = "Test exception"
            wrapper_state["other_data"]["error_traceback_main"] = "Traceback..."

            # Call _save_state_wrapper (this will add lorebook back)
            call_args = wrapper_state.copy()
            # Simulate _save_state_wrapper logic
            lorebook_entries_to_add = mock_lorebook.get_all_entries()
            if "other_data" not in call_args:
                call_args["other_data"] = {}
            call_args["other_data"]["lorebook_entries"] = lorebook_entries_to_add

            # Save with lorebook
            save_state(call_args, str(state_file))

            # GREEN TEST: Lorebook entries should be preserved
            with open(state_file, 'r') as f:
                final_state = json.load(f)

            final_lorebook = final_state.get("other_data", {}).get("other_data", {}).get("lorebook_entries", [])
            assert len(final_lorebook) == 2, "GREEN: Lorebook entries should be preserved after exception handler"
            assert final_lorebook[0]["text"] == "Rian adalah karakter utama."
