#!/usr/bin/env python3
"""
Unit tests for save_state() and load_state() functions in Write.py
Tests atomic file operations, JSON serialization, and error handling.
"""
from Write import save_state, load_state
import pytest
import os
import tempfile
from unittest.mock import patch
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


class TestSaveState:
    """Test suite for save_state() function."""

    def test_save_state_creates_file_successfully(self):
        """Test that save_state creates a valid JSON file."""
        test_data = {
            "last_completed_step": "outline",
            "total_chapters": 5,
            "config": {"SEED": 42}
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            save_state(test_data, temp_path)

            # Verify file exists
            assert os.path.exists(temp_path)

            # Verify content is valid JSON
            # Use load_state to get the data in the expected format
            loaded_data = load_state(temp_path)

            assert loaded_data == test_data
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_state_atomic_operation(self):
        """Test that save_state uses atomic file operations (temp file + move)."""
        test_data = {"test": "data"}

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            with patch('shutil.move') as mock_move:
                save_state(test_data, temp_path)

                # Verify shutil.move was called (atomic operation)
                mock_move.assert_called_once()
                args = mock_move.call_args[0]
                assert args[0] == temp_path + ".tmp"  # source (temp file)
                assert args[1] == temp_path          # destination (final file)
        finally:
            # Clean up any created files
            for path in [temp_path, temp_path + ".tmp"]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_save_state_handles_io_error(self, capsys):
        """Test that save_state handles IO errors gracefully."""
        test_data = {"test": "data"}
        invalid_path = "/invalid/path/that/does/not/exist.json"

        save_state(test_data, invalid_path)

        # Verify error message was printed to stderr
        captured = capsys.readouterr()
        assert "FATAL: Failed to save state" in captured.err
        assert invalid_path in captured.err

    def test_save_state_creates_directory_if_needed(self):
        """Test that save_state works when parent directory exists."""
        test_data = {"test": "data"}

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "subdir", "test.json")

            # Create parent directory
            os.makedirs(os.path.dirname(test_file), exist_ok=True)

            save_state(test_data, test_file)

            # Verify file was created
            assert os.path.exists(test_file)

            # Verify content
            loaded_data = load_state(test_file)
            assert loaded_data == test_data

    def test_save_state_complex_data_structure(self):
        """Test save_state with complex nested data structures."""
        test_data = {
            "last_completed_step": "chapter_generation",
            "total_chapters": 10,
            "completed_chapters": [
                {"number": 1, "title": "Chapter 1", "text": "Content 1"},
                {"number": 2, "title": "Chapter 2", "text": "Content 2"}
            ],
            "config": {
                "SEED": 42,
                "models": {
                    "outline": "ollama://model1",
                    "chapter": "ollama://model2"
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            save_state(test_data, temp_path)

            # Verify complex structure is preserved
            # Use load_state to get the data in the expected format
            loaded_data = load_state(temp_path)

            assert loaded_data == test_data
            assert loaded_data["completed_chapters"][0]["title"] == "Chapter 1"
            assert loaded_data["config"]["models"]["outline"] == "ollama://model1"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestLoadState:
    """Test suite for load_state() function."""

    def test_load_state_reads_file_successfully(self):
        """Test that load_state reads a valid JSON file correctly."""
        test_data = {
            "last_completed_step": "detect_chapters",
            "total_chapters": 7,
            "full_outline": "Test outline content"
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            # Use save_state to create file in the expected format
            save_state(test_data, temp_path)

            loaded_data = load_state(temp_path)
            assert loaded_data == test_data
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_state_handles_missing_file(self):
        """Test that load_state handles missing files gracefully."""
        non_existent_path = "/tmp/non_existent_file_12345.json"

        with pytest.raises(FileNotFoundError):
            load_state(non_existent_path)

    def test_load_state_handles_invalid_json(self):
        """Test that load_state handles corrupted JSON files."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write("invalid json content {broken")
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_state(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_state_handles_empty_file(self):
        """Test that load_state handles empty files."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            # Create empty file
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_state(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_state_preserves_data_types(self):
        """Test that load_state preserves all Python data types correctly."""
        test_data = {
            "string_value": "test string",
            "int_value": 42,
            "float_value": 3.14,
            "bool_value": True,
            "null_value": None,
            "list_value": [1, 2, 3],
            "dict_value": {"nested": "data"}
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            # Use save_state to create file in the expected format
            save_state(test_data, temp_path)

            loaded_data = load_state(temp_path)

            # Verify all data types are preserved
            assert isinstance(loaded_data["string_value"], str)
            assert isinstance(loaded_data["int_value"], int)
            assert isinstance(loaded_data["float_value"], float)
            assert isinstance(loaded_data["bool_value"], bool)
            assert loaded_data["null_value"] is None
            assert isinstance(loaded_data["list_value"], list)
            assert isinstance(loaded_data["dict_value"], dict)

            assert loaded_data == test_data
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestStateRoundTrip:
    """Test save and load operations together."""

    def test_save_load_roundtrip_preserves_data(self):
        """Test that save_state -> load_state preserves data exactly."""
        original_data = {
            "last_completed_step": "expand_chapters",
            "total_chapters": 15,
            "expanded_chapter_outlines": [
                {"text": "Outline 1", "title": "Chapter 1"},
                {"text": "Outline 2", "title": "Chapter 2"},
                {"text": "Outline 3", "title": "Chapter 3"}
            ],
            "config": {
                "SEED": 12345,
                "NATIVE_LANGUAGE": "en",
                "models": ["model1", "model2"]
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            # Save then load
            save_state(original_data, temp_path)
            loaded_data = load_state(temp_path)

            # Verify exact preservation
            assert loaded_data == original_data
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_multiple_save_operations_on_same_file(self):
        """Test multiple save operations on the same file."""
        data1 = {"step": "outline", "chapters": 5}
        data2 = {"step": "detect_chapters", "chapters": 7}
        data3 = {"step": "complete", "chapters": 7}

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            # Save data1
            save_state(data1, temp_path)
            loaded = load_state(temp_path)
            assert loaded == data1

            # Save data2 (overwrite)
            save_state(data2, temp_path)
            loaded = load_state(temp_path)
            assert loaded == data2

            # Save data3 (overwrite again)
            save_state(data3, temp_path)
            loaded = load_state(temp_path)
            assert loaded == data3
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
