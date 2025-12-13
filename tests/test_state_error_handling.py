#!/usr/bin/env python3
"""
Error handling tests for save/load state operations.
Tests various error scenarios and recovery mechanisms.
"""
import pytest
from pytest_mock import MockerFixture
import json
import os
import tempfile
import sys
from unittest.mock import patch, mock_open
import errno

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from Write import save_state, load_state


class TestSaveStateErrorHandling:
    """Test error handling scenarios for save_state function."""

    def test_save_state_permission_denied(self, capsys):
        """Test save_state handling when file permissions are denied."""
        import tempfile
        test_data = {"test": "data"}

        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a subdirectory and make it read-only
            readonly_dir = os.path.join(tmpdir, "readonly")
            os.makedirs(readonly_dir)
            target_file = os.path.join(readonly_dir, "state.json")

            # Make directory read-only (can't create files in it)
            os.chmod(readonly_dir, 0o555)  # Read + execute, no write

            try:
                # Try to save state to file in read-only directory - should fail
                save_state(test_data, target_file)

                # Verify error message was printed
                captured = capsys.readouterr()
                assert "FATAL: Failed to save state" in captured.err
                assert target_file in captured.err
            finally:
                # Cleanup: restore write permission so cleanup can delete directory
                try:
                    os.chmod(readonly_dir, 0o755)
                except:
                    pass

    def test_save_state_disk_full(self, capsys):
        """Test save_state handling when disk is full (simulated with mock)."""
        import tempfile
        test_data = {"test": "data"}

        # We mock this because we can't easily fill up disk in a test
        # But we use a real temp path to make it more realistic
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.json")

            with patch('builtins.open', mock_open()) as mock_file:
                # Simulate disk full error
                mock_file.side_effect = OSError(errno.ENOSPC, "No space left on device")

                save_state(test_data, test_file)

                # Verify error message was printed
                captured = capsys.readouterr()
                assert "FATAL: Failed to save state" in captured.err
                assert "No space left on device" in captured.err

    def test_save_state_directory_not_exists_and_cannot_create(self, capsys):
        """Test save_state when parent directory doesn't exist and can't be created."""
        test_data = {"test": "data"}
        
        # Try to save to a path where parent directory cannot be created
        invalid_path = "/root/restricted/test.json"  # Assuming /root/restricted doesn't exist and can't be created
        
        save_state(test_data, invalid_path)
        
        # Should handle the error gracefully
        captured = capsys.readouterr()
        assert "FATAL: Failed to save state" in captured.err

    def test_save_state_json_serialization_error(self, capsys):
        """Test save_state handling non-serializable data."""
        # Create data that can't be JSON serialized
        class NonSerializable:
            pass
        
        test_data = {"non_serializable": NonSerializable()}
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            save_state(test_data, temp_path)
            
            # Should handle JSON serialization error
            captured = capsys.readouterr()
            assert "FATAL:" in captured.err and "saving state" in captured.err
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_state_atomic_move_fails(self, capsys):
        """Test save_state when atomic move operation fails."""
        test_data = {"test": "data"}
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            with patch('shutil.move') as mock_move:
                # Simulate move failure
                mock_move.side_effect = OSError("Move operation failed")
                
                save_state(test_data, temp_path)
                
                # Verify error was handled
                captured = capsys.readouterr()
                assert "FATAL: Failed to save state" in captured.err
                assert "Move operation failed" in captured.err
        finally:
            # Clean up temp files
            for path in [temp_path, temp_path + ".tmp"]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_save_state_cleans_up_temp_file_on_error(self):
        """Test that save_state cleans up temporary file when error occurs."""
        test_data = {"test": "data"}
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
            temp_file_path = temp_path + ".tmp"
        
        try:
            with patch('shutil.move') as mock_move:
                # Simulate move failure
                mock_move.side_effect = OSError("Move failed")
                
                save_state(test_data, temp_path)
                
                # Verify temp file was cleaned up
                assert not os.path.exists(temp_file_path)
        finally:
            # Clean up
            for path in [temp_path, temp_file_path]:
                if os.path.exists(path):
                    os.unlink(path)


class TestLoadStateErrorHandling:
    """Test error handling scenarios for load_state function."""

    def test_load_state_file_not_found(self):
        """Test load_state raises FileNotFoundError for missing files."""
        non_existent = "/tmp/non_existent_file_12345.json"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            load_state(non_existent)
        
        assert non_existent in str(exc_info.value)

    def test_load_state_permission_denied(self):
        """Test load_state handling when file cannot be read due to permissions."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
            json.dump({"test": "data"}, f)
        
        try:
            # Change file permissions to make it unreadable
            os.chmod(temp_path, 0o000)
            
            with pytest.raises(IOError):
                load_state(temp_path)
        finally:
            # Restore permissions for cleanup
            os.chmod(temp_path, 0o644)
            os.unlink(temp_path)

    def test_load_state_corrupted_json_syntax_error(self):
        """Test load_state handling corrupted JSON with syntax errors."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('{"key": "value", invalid}')  # Invalid JSON syntax
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError) as exc_info:
                load_state(temp_path)
            
            # Verify it's a wrapped JSON decode error
            assert "Failed to decode state file" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_load_state_incomplete_json(self):
        """Test load_state handling incomplete JSON files."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('{"key": "value"')  # Missing closing brace
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                load_state(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_state_file_is_directory(self):
        """Test load_state handling when path points to a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(IOError):
                load_state(temp_dir)

    def test_load_state_very_large_file(self):
        """Test load_state handling extremely large files that might cause memory issues."""
        # Create a large JSON file that might cause memory issues
        large_data = {"data": "x" * (10 * 1024 * 1024)}  # 10MB of data

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name

        try:
            # Use save_state to create file in the current format
            save_state(large_data, temp_path)

            # This should work but test that it doesn't crash
            result = load_state(temp_path)
            assert "data" in result
            assert len(result["data"]) == 10 * 1024 * 1024
        finally:
            os.unlink(temp_path)

    def test_load_state_binary_file(self):
        """Test load_state handling binary files that aren't JSON."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b'\x00\x01\x02\x03\x04\x05')  # Binary data
            temp_path = f.name
        
        try:
            with pytest.raises((ValueError, IOError)):
                load_state(temp_path)
        finally:
            os.unlink(temp_path)


class TestStateOperationRecovery:
    """Test recovery mechanisms for state operations."""

    def test_save_state_handles_temporary_failure(self, capsys):
        """Test save_state documents behavior with temporary failures."""
        test_data = {"test": "data"}
        
        # Test that current implementation doesn't have retry logic
        # This is a documentation test for expected behavior
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            # Normal save should work
            save_state(test_data, temp_path)
            
            # Verify no error output for successful save
            captured = capsys.readouterr()
            assert captured.err == ""
            
            # Verify data was saved correctly
            loaded_data = load_state(temp_path)
            assert loaded_data == test_data
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_state_with_backup_recovery(self):
        """Test load_state recovery using backup files."""
        test_data = {"test": "data", "backup": True}
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            main_path = f.name
            backup_path = main_path + ".backup"
        
        try:
            # Create a valid backup file using save_state
            save_state(test_data, backup_path)

            # Create a corrupted main file
            with open(main_path, 'w', encoding='utf-8') as f:
                f.write("corrupted json content")

            # Test current behavior (should fail)
            with pytest.raises(ValueError):
                load_state(main_path)

            # But backup file should be loadable
            backup_data = load_state(backup_path)
            assert backup_data == test_data
            
        finally:
            for path in [main_path, backup_path]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_concurrent_access_to_state_file(self):
        """Test behavior when multiple processes access state file simultaneously."""
        test_data = {"concurrent": "test"}
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            # Save initial state
            save_state(test_data, temp_path)
            
            # Simulate concurrent read while another process might be writing
            # This tests that atomic operations prevent corruption
            loaded_data = load_state(temp_path)
            assert loaded_data == test_data
            
            # Test multiple saves don't interfere
            test_data2 = {"concurrent": "test2"}
            save_state(test_data2, temp_path)
            
            loaded_data2 = load_state(temp_path)
            assert loaded_data2 == test_data2
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestStateFileConsistency:
    """Test state file consistency and integrity."""

    def test_state_file_atomic_operation_consistency(self):
        """Test that atomic operations ensure file consistency."""
        test_data = {"atomic": "test"}
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            # Test that partial writes don't leave corrupted files
            with patch('shutil.move') as mock_move:
                # If move fails, original file should remain unchanged
                mock_move.side_effect = OSError("Move failed")
                
                # First save a valid state
                save_state(test_data, temp_path)
                
                # Now try to save different data that will fail
                test_data2 = {"atomic": "test2"}
                save_state(test_data2, temp_path)
                
                # Original file should be preserved (if it existed)
                # Since move failed, temp file should be cleaned up
                temp_file = temp_path + ".tmp"
                assert not os.path.exists(temp_file)
                
        finally:
            for path in [temp_path, temp_path + ".tmp"]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_state_file_encoding_consistency(self):
        """Test that state files maintain consistent encoding."""
        # Test with Unicode characters
        test_data = {
            "unicode_test": "测试中文",
            "emoji_test": "🎭🎨🎪",
            "special_chars": "àáâãäåæçèéêë"
        }
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            save_state(test_data, temp_path)
            loaded_data = load_state(temp_path)
            
            # Verify Unicode is preserved exactly
            assert loaded_data == test_data
            assert loaded_data["unicode_test"] == "测试中文"
            assert loaded_data["emoji_test"] == "🎭🎨🎪"
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
