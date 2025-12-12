# conftest.py for shared pytest fixtures

import pytest
import os
import glob


@pytest.fixture(autouse=True)
def cleanup_test_artifacts():
    """Automatically cleanup test output files after each test."""
    # Setup: nothing to do before test
    yield

    # Teardown: cleanup after test
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_artifacts = [
        "test_output.md*",  # Will match test_output.md.md, test_output.md_info.json, etc.
        "dummy_state.json",
    ]

    for pattern in test_artifacts:
        for filepath in glob.glob(os.path.join(root_dir, pattern)):
            try:
                os.remove(filepath)
                print(f"Cleaned up test artifact: {filepath}")
            except Exception as e:
                print(f"Warning: Could not remove {filepath}: {e}")
