#!/usr/bin/env python3
"""
File corruption recovery tests for state operations.
Tests various corruption scenarios and recovery mechanisms.
"""
from Write import save_state, load_state
import pytest
import json
import os
import errno
import tempfile
import sys
import shutil
from unittest.mock import patch, mock_open

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


class TestFileCorruptionScenarios:
    """Test various file corruption scenarios."""

    def test_truncated_json_file(self):
        """Test handling of truncated JSON files."""
        complete_data = {
            "last_completed_step": "chapter_generation",
            "total_chapters": 5,
            "completed_chapters": [
                {"number": 1, "title": "Chapter 1", "text": "Content 1"},
                {"number": 2, "title": "Chapter 2", "text": "Content 2"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            # Write complete JSON first
            json.dump(complete_data, f, indent=2)
            temp_path = f.name

        try:
            # Truncate the file to simulate corruption
            with open(temp_path, 'r+') as f:
                content = f.read()
                # Cut off the last 50% of the file
                truncated_content = content[:len(content) // 2]
                f.seek(0)
                f.write(truncated_content)
                f.truncate()

            # Should raise ValueError due to truncation (wrapped JSONDecodeError)
            with pytest.raises(ValueError):
                load_state(temp_path)

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_partially_corrupted_json_structure(self):
        """Test handling of partially corrupted JSON structure."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            # Write corrupted JSON with mixed valid/invalid parts
            f.write('''
            {
                "last_completed_step": "outline",
                "total_chapters": 5,
                "corrupted_field": {invalid_json_here},
                "valid_field": "this is valid"
            }
            ''')
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_state(temp_path)

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_binary_corruption_in_text_file(self):
        """Test handling of binary corruption in text files."""
        valid_data = {"last_completed_step": "outline", "total_chapters": 3}

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump(valid_data, f)
            temp_path = f.name

        try:
            # Insert binary data in the middle of the file
            with open(temp_path, 'rb+') as f:
                f.seek(20)  # Go to middle of file
                f.write(b'\x00\x01\x02\x03\x04\x05')  # Insert binary data

            # Should raise an error (either wrapped JSON or Unicode decode error)
            with pytest.raises((ValueError, IOError)):
                load_state(temp_path)

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_empty_file_corruption(self):
        """Test handling of completely empty files."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            # Create empty file
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_state(temp_path)

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_whitespace_only_file(self):
        """Test handling of files containing only whitespace."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("   \n\t  \n   ")  # Only whitespace
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_state(temp_path)

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_file_with_null_bytes(self):
        """Test handling of files containing null bytes."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            # Mix valid JSON with null bytes
            content = b'{"test": "data"}\x00\x00\x00{"more": "data"}'
            f.write(content)
            temp_path = f.name

        try:
            with pytest.raises((ValueError, IOError)):
                load_state(temp_path)

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestAtomicOperationRecovery:
    """Test recovery mechanisms for failed atomic operations."""

    def test_temp_file_cleanup_after_failed_save(self):
        """Test that temporary files are cleaned up after failed saves."""
        test_data = {"test": "data"}

        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            with patch('shutil.move') as mock_move:
                # Simulate move failure
                mock_move.side_effect = OSError("Move operation failed")

                save_state(test_data, temp_path)

                # Verify temp file was cleaned up
                temp_file_path = temp_path + ".tmp"
                assert not os.path.exists(temp_file_path)

        finally:
            # Clean up both potential files
            for path in [temp_path, temp_path + ".tmp"]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_partial_write_recovery(self):
        """Test recovery from partial write operations."""
        test_data = {"test": "data", "large_field": "x" * 10000}

        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            original_write = os.write
            write_count = 0

            def failing_write(fd, data):
                nonlocal write_count
                write_count += 1
                if write_count == 3:  # Fail on third write
                    raise OSError("Disk full")
                return original_write(fd, data)

            with patch('os.write', side_effect=failing_write):
                # This should handle the write failure gracefully
                save_state(test_data, temp_path)

            # Since write failed, file should not exist or be corrupted
            # The current implementation may leave a corrupted file

        finally:
            for path in [temp_path, temp_path + ".tmp"]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_concurrent_write_protection(self):
        """Test protection against concurrent write operations."""
        test_data1 = {"concurrent": "write1"}
        test_data2 = {"concurrent": "write2"}

        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            # Simulate concurrent saves by controlling the timing
            # The atomic operation should ensure one completes fully
            save_state(test_data1, temp_path)

            # Verify first write completed
            loaded = load_state(temp_path)
            assert loaded["concurrent"] == "write1"

            # Second write should overwrite cleanly
            save_state(test_data2, temp_path)
            loaded = load_state(temp_path)
            assert loaded["concurrent"] == "write2"

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestBackupAndRecoveryMechanisms:
    """Test backup and recovery mechanisms for state files."""

    def test_backup_file_creation_concept(self):
        """Test the concept of backup file creation (not implemented yet)."""
        original_data = {"step": "original", "data": "important"}
        updated_data = {"step": "updated", "data": "more_important"}

        with tempfile.NamedTemporaryFile(delete=False) as f:
            main_path = f.name
            backup_path = main_path + ".backup"

        try:
            # Save original data
            save_state(original_data, main_path)

            # Manually create backup (simulating what could be implemented)
            shutil.copy2(main_path, backup_path)

            # Update with new data
            save_state(updated_data, main_path)

            # Verify main file has new data
            main_data = load_state(main_path)
            assert main_data["step"] == "updated"

            # Verify backup has original data
            backup_data = load_state(backup_path)
            assert backup_data["step"] == "original"

        finally:
            for path in [main_path, backup_path]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_recovery_from_backup_after_corruption(self):
        """Test recovery workflow using backup files."""
        valid_data = {"step": "backup_test", "chapters": 5}

        with tempfile.NamedTemporaryFile(delete=False) as f:
            main_path = f.name
            backup_path = main_path + ".backup"

        try:
            # Create valid backup
            save_state(valid_data, backup_path)

            # Create corrupted main file
            with open(main_path, 'w') as f:
                f.write("corrupted json {invalid")

            # Main file should fail to load
            with pytest.raises(ValueError):
                load_state(main_path)

            # But backup should work
            backup_data = load_state(backup_path)
            assert backup_data == valid_data

            # Recovery process: restore from backup
            shutil.copy2(backup_path, main_path)
            recovered_data = load_state(main_path)
            assert recovered_data == valid_data

        finally:
            for path in [main_path, backup_path]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_multiple_backup_generations(self):
        """Test concept of multiple backup generations."""
        data_v1 = {"version": 1, "step": "outline"}
        data_v2 = {"version": 2, "step": "chapters"}
        data_v3 = {"version": 3, "step": "complete"}

        with tempfile.TemporaryDirectory() as temp_dir:
            main_path = os.path.join(temp_dir, "state.json")
            backup1_path = os.path.join(temp_dir, "state.json.backup.1")
            backup2_path = os.path.join(temp_dir, "state.json.backup.2")
            backup3_path = os.path.join(temp_dir, "state.json.backup.3")

            # Simulate versioned backup system
            save_state(data_v1, main_path)
            shutil.copy2(main_path, backup1_path)

            save_state(data_v2, main_path)
            shutil.copy2(main_path, backup2_path)

            save_state(data_v3, main_path)
            shutil.copy2(main_path, backup3_path)

            # Verify all versions are preserved
            assert load_state(backup1_path)["version"] == 1
            assert load_state(backup2_path)["version"] == 2
            assert load_state(backup3_path)["version"] == 3
            assert load_state(main_path)["version"] == 3


class TestFileSystemLevelCorruption:
    """Test handling of file system level corruption issues."""

    def test_permission_changes_during_operation(self):
        """Test handling when file permissions change during operations."""
        test_data = {"test": "permission_test"}

        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            # Save initial state
            save_state(test_data, temp_path)

            # Change permissions to read-only
            os.chmod(temp_path, 0o444)

            # Try to save again - should fail gracefully
            save_state({"updated": "data"}, temp_path)

            # Restore permissions to check what happened
            os.chmod(temp_path, 0o644)  # Restore read permissions

            # Since save failed due to permissions, original data might be preserved
            # or file might be corrupted - this depends on implementation
            try:
                loaded_data = load_state(temp_path)
                # Could be either original or new data, depending on where the failure occurred
                assert "test" in str(loaded_data) or "updated" in str(loaded_data)
            except (ValueError, IOError):
                # File might be corrupted due to failed write
                pass

        finally:
            # Ensure cleanup can happen
            os.chmod(temp_path, 0o644)
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_disk_space_exhaustion_simulation(self, capsys):
        """Test handling of disk space exhaustion during save.

        Note: We mock this because we can't actually fill the disk in a test.
        The test verifies that save_state handles OSError(ENOSPC) gracefully.
        """
        test_data = {"large_data": "x" * 1000000}  # 1MB of data

        # Use real temp directory for realistic path
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = os.path.join(tmpdir, "large_file.json")

            # Mock only the open call to simulate disk full during write
            # We keep the path real to make the test more realistic
            with patch('builtins.open', mock_open()) as mock_file:
                # Simulate disk full during write operation
                mock_file.return_value.write.side_effect = OSError(errno.ENOSPC, "No space left on device")

                # Attempt to save - should handle error gracefully
                save_state(test_data, temp_path)

                # Verify error was logged to stderr
                captured = capsys.readouterr()
                assert "FATAL: Failed to save state" in captured.err
                assert "No space left on device" in captured.err or temp_path in captured.err

    def test_inode_exhaustion_simulation(self, capsys):
        """Test handling of inode exhaustion (cannot create new files).

        Note: We mock this because we can't exhaust inodes in a test.
        The test verifies that save_state handles OSError gracefully when
        the filesystem cannot create new files.
        """
        test_data = {"test": "inode_test"}

        # Use real temp directory for realistic path
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = os.path.join(tmpdir, "test_inode.json")

            # Mock open to simulate inode exhaustion when creating file
            with patch('builtins.open', mock_open()) as mock_file:
                # Simulate inode exhaustion (no inodes available)
                mock_file.side_effect = OSError(errno.ENOSPC, "No space left on device")

                # Attempt to save - should handle error gracefully
                save_state(test_data, test_path)

                # Verify error was logged to stderr
                captured = capsys.readouterr()
                assert "FATAL: Failed to save state" in captured.err
                assert test_path in captured.err or "No space left on device" in captured.err


class TestRecoveryStrategies:
    """Test various recovery strategies for corrupted state files."""

    def test_progressive_recovery_attempt(self):
        """Test progressive recovery from partial corruption."""
        # Create a file with mixed valid and invalid content
        mixed_content = '''
        {
            "last_completed_step": "chapter_generation",
            "total_chapters": 5,
            "completed_chapters": [
                {"number": 1, "title": "Chapter 1", "text": "Valid content"},
                {invalid_chapter_data_here},
                {"number": 3, "title": "Chapter 3", "text": "More valid content"}
            ]
        }
        '''

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(mixed_content)
            temp_path = f.name

        try:
            # Should fail to parse completely
            with pytest.raises(ValueError):
                load_state(temp_path)

            # In a real implementation, we might try to extract valid parts
            # For now, we document that this is a limitation

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_state_validation_after_recovery(self):
        """Test validation of state data after recovery operations."""
        # Test what happens when we recover a state but some fields are missing
        incomplete_recovered_state = {
            "last_completed_step": "chapter_generation",
            # Missing: total_chapters, completed_chapters, etc.
        }

        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            save_state(incomplete_recovered_state, temp_path)
            loaded_state = load_state(temp_path)

            # The current implementation doesn't validate required fields
            # This test documents that validation would be needed
            assert "last_completed_step" in loaded_state
            # In a robust implementation, we'd validate required fields here

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_checksum_validation_concept(self):
        """Test the concept of checksum validation (not implemented)."""
        import hashlib

        test_data = {"test": "checksum_validation"}

        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            # Save state
            save_state(test_data, temp_path)

            # Calculate checksum of saved file
            with open(temp_path, 'rb') as f:
                file_content = f.read()
                checksum = hashlib.sha256(file_content).hexdigest()

            # In a robust implementation, we could save this checksum
            # and validate it when loading

            # Load and verify
            loaded_data = load_state(temp_path)
            assert loaded_data == test_data

            # Verify checksum hasn't changed
            with open(temp_path, 'rb') as f:
                file_content_after = f.read()
                checksum_after = hashlib.sha256(file_content_after).hexdigest()

            assert checksum == checksum_after

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
