"""
Test suite for lorebook state persistence functionality - TDD RED Phase

This test suite follows the TDD London School methodology where tests are written
to fail first (RED), then implemented to pass (GREEN), then refactored for clarity.
"""

from unittest.mock import Mock, patch
import tempfile
import json
from pathlib import Path


class TestLorebookStatePersistence:
    """TDD RED Tests for lorebook state persistence functionality"""

    def test_save_entries_to_state_should_store_text_and_metadata(self):
        """GREEN: Lorebook entries should be saved to state and can be retrieved

        Tests the implemented functionality - should now pass.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock state file path
            state_file = Path(temp_dir) / "run.state.json"

            # Create mock lorebook with entries
            mock_lorebook = Mock()
            mock_lorebook.get_all_entries.return_value = [
                {
                    "id": "uuid-1",
                    "text": "Rian adalah karakter utama yang penasaran dengan legenda gua harta karun.",
                    "metadata": {"type": "character", "name": "Rian", "source": "outline"}
                },
                {
                    "id": "uuid-2",
                    "text": "Desa terletak di tepi sungai yang jernih, dikelilingi hutan lebat.",
                    "metadata": {"type": "location", "name": "Desa", "source": "outline"}
                }
            ]

            # Save entries to state (method should now work)
            from Writer.Lorebook import LorebookManager
            LorebookManager.save_entries_to_state(mock_lorebook, str(state_file))

            # Verify the state file was created and содержит correct data
            assert state_file.exists(), "State file should be created"

            with open(state_file, 'r', encoding='utf-8') as f:
                saved_state = json.load(f)

            assert "lorebook_entries" in saved_state["other_data"], "State should contain lorebook_entries"
            assert len(saved_state["other_data"]["lorebook_entries"]) == 2, "Should have 2 entries"

            first_entry = saved_state["other_data"]["lorebook_entries"][0]
            assert first_entry["text"] == "Rian adalah karakter utama yang penasaran dengan legenda gua harta karun."
            assert first_entry["metadata"]["type"] == "character"

    def test_load_entries_from_state_should_restore_to_chromadb(self):
        """GREEN: State entries should be restored to ChromaDB

        Tests the implemented functionality - should now pass.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test state file with lorebook entries
            state_file = Path(temp_dir) / "run.state.json"
            state_data = {
                "pydantic_objects": {},
                "other_data": {
                    "status": "in_progress",
                    "chapters_completed": 2,
                    "lorebook_entries": [
                        {
                            "id": "uuid-1",
                            "text": "Rian adalah karakter utama yang penasaran dengan legenda gua harta karun.",
                            "metadata": {
                                "type": "character",
                                "name": "Rian",
                                "source": "outline",
                                "added_at": "2025-12-15T10:30:00"
                            }
                        }
                    ]
                }
            }
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)

            # Create mock lorebook
            mock_lorebook = Mock()
            mock_lorebook.clear = Mock()

            # Load entries from state (method should now work)
            from Writer.Lorebook import LorebookManager
            LorebookManager.load_entries_from_state(mock_lorebook, str(state_file))

            # Verify clear was called first
            mock_lorebook.clear.assert_called_once()

            # Verify add_entry was called with correct data
            mock_lorebook.add_entry.assert_called_once_with(
                "Rian adalah karakter utama yang penasaran dengan legenda gua harta karun.",
                {
                    "type": "character",
                    "name": "Rian",
                    "source": "outline",
                    "added_at": "2025-12-15T10:30:00"
                }
            )

    def test_pipeline_should_save_lorebook_entries_on_checkpoint(self):
        """RED: Pipeline should save lorebook entries during checkpoints

        This will FAIL initially - pipeline doesn't save lorebook state.
        """
        with patch('Writer.Pipeline.StateManager') as mock_state_manager:
            mock_state_manager.save_state = Mock()

            # Create pipeline with lorebook
            with patch('Writer.Lorebook.LorebookManager') as mock_lorebook_class:
                mock_lorebook = Mock()
                mock_lorebook.get_all_entries.return_value = [
                    {
                        "id": "uuid-1",
                        "text": "Rian mendengar legenda dari tetua desa.",
                        "metadata": {"type": "plot_point", "name": "Legenda Gua"}
                    }
                ]
                mock_lorebook_class.return_value = mock_lorebook

                from Writer.Pipeline import StoryPipeline
                pipeline = StoryPipeline(Mock(), Mock(), Mock(), Mock(), is_fresh_run=True)

                # This should save lorebook entries to state but won't initially
                pipeline._save_state_wrapper({"test": "data"}, "test_file.json")

                # Verify StateManager.save_state was called
                mock_state_manager.save_state.assert_called_once()

                # Verify lorebook entries were included in saved state
                call_args = mock_state_manager.save_state.call_args[0][0]
                assert "lorebook_entries" in call_args.get("other_data", {}), \
                    "Pipeline should include lorebook entries in saved state"

    def test_pipeline_should_restore_lorebook_on_resume(self):
        """GREEN: Pipeline should restore lorebook when is_fresh_run=False

        Tests the restored functionality - should now pass.
        """
        with patch('Writer.Lorebook.LorebookManager') as mock_lorebook_class:
            mock_lorebook = Mock()
            mock_lorebook.load_entries_from_state = Mock()
            mock_lorebook_class.return_value = mock_lorebook

            # Create a fake log directory with state file
            with tempfile.TemporaryDirectory() as temp_dir:
                log_dir = Path(temp_dir) / "Logs" / "Generation_2025-12-15_19-47-56"
                log_dir.mkdir(parents=True)

                state_file = log_dir / "run.state.json"
                state_data = {
                    "other_data": {
                        "lorebook_entries": [
                            {
                                "id": "uuid-1",
                                "text": "Test entry for resume",
                                "metadata": {"type": "test", "name": "Resume Test"}
                            }
                        ]
                    }
                }
                with open(state_file, 'w') as f:
                    json.dump(state_data, f)

                # Mock glob to return our temp Logs directory (with Generation_*/ pattern)
                with patch('glob.glob') as mock_glob:
                    mock_glob.return_value = [str(log_dir)]

                    # Create pipeline for resume
                    from Writer.Pipeline import StoryPipeline
                    pipeline = StoryPipeline(Mock(), Mock(), Mock(), Mock(), is_fresh_run=False)

                    # This should restore lorebook entries
                    mock_lorebook.load_entries_from_state.assert_called_once_with(str(state_file))

    def test_get_all_entries_should_return_serializable_data(self):
        """GREEN: LorebookManager should provide all entries in serializable format

        Tests the implemented functionality - should now pass.
        """
        # Create lorebook manager (mock the ChromaDB part)
        with patch('Writer.Lorebook.Chroma') as mock_chroma:
            mock_db = Mock()
            mock_db.get.return_value = {
                "ids": ["char_rian", "loc_desa"],
                "documents": [
                    "Rian adalah karakter utama yang penasaran.",
                    "Desa terletak di tepi sungai."
                ],
                "metadatas": [
                    {"type": "character", "name": "Rian"},
                    {"type": "location", "name": "Desa"}
                ]
            }
            mock_chroma.return_value = mock_db

            from Writer.Lorebook import LorebookManager
            from Writer import Config

            # Create temporary directory for test
            with tempfile.TemporaryDirectory() as temp_dir:
                lorebook = LorebookManager(persist_dir=temp_dir, config=Config)

                # This method should now work
                entries = lorebook.get_all_entries()
                assert len(entries) == 2
                assert entries[0]["id"] == "char_rian"
                assert entries[0]["text"] == "Rian adalah karakter utama yang penasaran."
                assert entries[0]["metadata"]["type"] == "character"
                assert entries[1]["id"] == "loc_desa"
                assert entries[1]["text"] == "Desa terletak di tepi sungai."
                assert entries[1]["metadata"]["type"] == "location"

    def test_add_entry_should_include_timestamp(self):
        """RED: add_entry should add timestamp to metadata for tracking

        This test checks existing functionality but ensures our enhancement works.
        """
        from Writer.Lorebook import LorebookManager
        from Writer import Config

        # Create lorebook manager
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the embedding interface to avoid real LLM calls
            with patch('Writer.Interface.Wrapper.Interface') as mock_interface_class:
                mock_interface = Mock()
                mock_interface.LoadModels = Mock()
                mock_interface_class.return_value = mock_interface

                # Mock embedding function
                with patch('Writer.Lorebook.LorebookManager._create_provider_embeddings') as mock_embeddings:
                    mock_embeddings.return_value = Mock()

                    # Mock ChromaDB
                    with patch('Writer.Lorebook.Chroma') as mock_chroma:
                        mock_db = Mock()
                        mock_db.add_documents.return_value = ["test_id"]
                        mock_chroma.return_value = mock_db

                        lorebook = LorebookManager(persist_dir=temp_dir, config=Config)

                        # Add entry
                        doc_id = lorebook.add_entry(
                            "Test character",
                            {"type": "character", "name": "TestChar"}
                        )

                        # Verify add_documents was called with timestamped metadata
                        mock_db.add_documents.assert_called_once()
                        call_args = mock_db.add_documents.call_args[0][0]
                        assert len(call_args) == 1

                        metadata = call_args[0].metadata
                        assert "added_at" in metadata, "add_entry should include timestamp in metadata"

    def test_static_helper_methods_should_exist(self):
        """GREEN: Static helper methods should exist for external access

        Tests the implemented functionality - should now pass.
        """
        from Writer.Lorebook import LorebookManager

        mock_lorebook = Mock()
        mock_lorebook.save_entries_to_state = Mock()
        mock_lorebook.load_entries_from_state = Mock()
        state_filepath = "/fake/path/state.json"

        # These static methods should now work
        LorebookManager.save_lorebook_state(mock_lorebook, state_filepath)
        mock_lorebook.save_entries_to_state.assert_called_once_with(state_filepath)

        LorebookManager.load_lorebook_state(mock_lorebook, state_filepath)
        mock_lorebook.load_entries_from_state.assert_called_once_with(state_filepath)

    def test_state_persistence_should_handle_empty_lorebook(self):
        """GREEN: State persistence should handle empty lorebook gracefully

        Tests edge cases for the new functionality.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "run.state.json"

            # Create mock empty lorebook
            mock_lorebook = Mock()
            mock_lorebook.get_all_entries.return_value = []

            from Writer.Lorebook import LorebookManager

            # This should handle empty lorebook without errors
            LorebookManager.save_entries_to_state(mock_lorebook, str(state_file))

            # Should create state with empty list
            assert state_file.exists(), "State file should be created"
            with open(state_file, 'r') as f:
                saved_state = json.load(f)
                assert saved_state["other_data"]["lorebook_entries"] == []

    def test_load_from_missing_state_should_gracefully_fail(self):
        """GREEN: Loading from missing state file should handle gracefully

        Tests error handling for missing state files.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "nonexistent_state.json"

            mock_lorebook = Mock()
            mock_lorebook.SysLogger = Mock()  # Mock logger to capture log calls

            from Writer.Lorebook import LorebookManager

            # This should handle missing file gracefully
            LorebookManager.load_entries_from_state(mock_lorebook, str(state_file))

            # Should not crash and should not call clear (since file doesn't exist)
            mock_lorebook.clear.assert_not_called()
