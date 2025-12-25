import pytest
from pytest_mock import MockerFixture
import types  # For ModuleType

# Attempt to import the function to be tested.
# This assumes that Write.py is in a location where it can be imported,
# or PYTHONPATH is adjusted accordingly in the test execution environment.
try:
    from Write import load_active_prompts  # type: ignore[misc]
except ImportError as import_error:
    # If Write.py is in the root and not installed, this might fail without PYTHONPATH adjustment.
    # For this subtask, we'll proceed assuming it can be resolved by the environment.
    print(f"Note: ImportError during 'from Write import load_active_prompts': {import_error}. Ensure PYTHONPATH is set if Write.py is in repo root.")
    # Store the error for later use
    _import_error = import_error
    # Define a dummy function to allow tests to be defined, though they will likely fail if the import truly fails.

    def load_active_prompts(native_language_code, logger_func_print, logger_func_warn, logger_func_error):
        raise _import_error

# Mock Logger Utilities
mock_log_entries = []


def mock_logger_print(msg):
    mock_log_entries.append(f"PRINT: {msg}")


def mock_logger_warn(msg):
    mock_log_entries.append(f"WARN: {msg}")


def mock_logger_error(msg):
    mock_log_entries.append(f"ERROR: {msg}")

# Helper to clear logs before each test


def clear_mock_logs():
    mock_log_entries.clear()

# Fixture to automatically clear logs before each test


@pytest.fixture(autouse=True)
def reset_logs_fixture():
    clear_mock_logs()


def test_load_english_prompts_successfully():
    """Test loading English prompts when language code is 'en'"""
    result = load_active_prompts("en", mock_logger_print, mock_logger_warn, mock_logger_error)

    # The function should return a module (the actual Writer.Prompts since it exists)
    assert result is not None
    assert hasattr(result, '__name__')
    # Should log successful English loading
    assert any("Using English prompts (Writer.Prompts)" in entry for entry in mock_log_entries if entry.startswith("PRINT:"))


def test_load_specific_language_successfully(mocker: MockerFixture):
    """Test loading a specific language module successfully"""
    mock_id_module = types.ModuleType("Writer.Prompts_id")
    mock_import_module = mocker.patch("importlib.import_module")
    mock_import_module.return_value = mock_id_module

    result = load_active_prompts("id", mock_logger_print, mock_logger_warn, mock_logger_error)

    assert result is mock_id_module
    assert any("Successfully loaded prompt module 'Writer.Prompts_id'" in entry for entry in mock_log_entries if entry.startswith("PRINT:"))
    mock_import_module.assert_called_once_with("Writer.Prompts_id")


def test_load_nonexistent_language_fallback_to_english(mocker: MockerFixture):
    """Test fallback to English when specific language doesn't exist"""
    # This uses the real Writer.Prompts as fallback since it exists
    mock_import_module = mocker.patch("importlib.import_module", side_effect=ImportError("No module named Writer.Prompts_nonexistent"))

    result = load_active_prompts("nonexistent", mock_logger_print, mock_logger_warn, mock_logger_error)

    assert result is not None
    assert hasattr(result, '__name__')
    # Should warn about missing language and fall back
    assert any("Prompt module for NATIVE_LANGUAGE 'nonexistent'" in entry and "not found" in entry for entry in mock_log_entries if entry.startswith("WARN:"))
    mock_import_module.assert_called_once_with("Writer.Prompts_nonexistent")


def test_load_none_or_empty_language_defaults_to_english():
    """Test that None or empty language codes default to English"""
    for lang_code in [None, ""]:
        clear_mock_logs()  # Clear logs between iterations
        result = load_active_prompts(lang_code, mock_logger_print, mock_logger_warn, mock_logger_error)

        assert result is not None
        assert hasattr(result, '__name__')
        # Should log that it's using English as default
        assert any("Using English prompts (Writer.Prompts) as NATIVE_LANGUAGE is 'en'" in entry for entry in mock_log_entries if entry.startswith("PRINT:"))


def test_load_unexpected_error_during_specific_language_import_fallback(mocker: MockerFixture):
    """Test fallback to English when unexpected error occurs during language import"""
    # Mock importlib for the initial language attempt that should fail with generic exception
    mock_import_module = mocker.patch("importlib.import_module", side_effect=Exception("Simulated unexpected error"))

    result = load_active_prompts("errorlang", mock_logger_print, mock_logger_warn, mock_logger_error)

    # Should still fallback to English (the real Writer.Prompts module)
    assert result is not None
    assert hasattr(result, '__name__')
    assert any("CRITICAL: Unexpected error loading prompt module for NATIVE_LANGUAGE 'errorlang'" in entry for entry in mock_log_entries if entry.startswith("ERROR:"))
    mock_import_module.assert_called_once_with("Writer.Prompts_errorlang")
