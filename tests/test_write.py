import pytest
from pytest_mock import MockerFixture
import importlib
import types # For ModuleType

# Attempt to import the function to be tested.
# This assumes that Write.py is in a location where it can be imported,
# or PYTHONPATH is adjusted accordingly in the test execution environment.
try:
    from Write import load_active_prompts
except ImportError as e:
    # If Write.py is in the root and not installed, this might fail without PYTHONPATH adjustment.
    # For this subtask, we'll proceed assuming it can be resolved by the environment.
    print(f"Note: ImportError during 'from Write import load_active_prompts': {e}. Ensure PYTHONPATH is set if Write.py is in repo root.")
    # Define a dummy function to allow tests to be defined, though they will likely fail if the import truly fails.
    def load_active_prompts(native_language_code, logger_func_print, logger_func_warn, logger_func_error):
        raise e

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

def test_load_english_prompts_successfully(mocker: MockerFixture):
    mock_en_module = types.ModuleType("Writer.Prompts")
    # Configure the mock to return mock_en_module only for "Writer.Prompts"
    mock_import_module = mocker.patch("importlib.import_module", side_effect=lambda name: mock_en_module if name == "Writer.Prompts" else None)

    result = load_active_prompts("en", mock_logger_print, mock_logger_warn, mock_logger_error)

    assert result is mock_en_module
    assert any("Using English prompts (Writer.Prompts)" in entry for entry in mock_log_entries if entry.startswith("PRINT:"))
    mock_import_module.assert_called_once_with("Writer.Prompts")

def test_load_specific_language_successfully(mocker: MockerFixture):
    mock_id_module = types.ModuleType("Writer.Prompts_id")
    mock_import_module = mocker.patch("importlib.import_module")
    mock_import_module.side_effect = lambda name: mock_id_module if name == "Writer.Prompts_id" else None

    result = load_active_prompts("id", mock_logger_print, mock_logger_warn, mock_logger_error)

    assert result is mock_id_module
    assert any("Successfully loaded prompt module 'Writer.Prompts_id'" in entry for entry in mock_log_entries if entry.startswith("PRINT:"))
    mock_import_module.assert_called_once_with("Writer.Prompts_id")

def test_load_nonexistent_language_fallback_to_english(mocker: MockerFixture):
    mock_en_module = types.ModuleType("Writer.Prompts")

    def import_side_effect(name):
        if name == "Writer.Prompts_nonexistent":
            raise ImportError("No module named Writer.Prompts_nonexistent")
        elif name == "Writer.Prompts":
            return mock_en_module
        raise ImportError(f"Unexpected module import: {name}")

    mock_import_module = mocker.patch("importlib.import_module", side_effect=import_side_effect)

    result = load_active_prompts("nonexistent", mock_logger_print, mock_logger_warn, mock_logger_error)

    assert result is mock_en_module
    assert any("Prompt module for NATIVE_LANGUAGE 'nonexistent' ('Writer.Prompts_nonexistent') not found. Falling back" in entry for entry in mock_log_entries if entry.startswith("WARN:"))
    # Check if the fallback print message (which mentions the effective language code 'en') is present
    assert any("Using English prompts (Writer.Prompts) as NATIVE_LANGUAGE is 'en'" in entry for entry in mock_log_entries if entry.startswith("PRINT:"))
    assert mock_import_module.call_count == 2
    mock_import_module.assert_any_call("Writer.Prompts_nonexistent")
    mock_import_module.assert_any_call("Writer.Prompts")

def test_load_nonexistent_language_and_english_fallback_fails(mocker: MockerFixture):
    def import_side_effect(name):
        if name == "Writer.Prompts_nonexistent" or name == "Writer.Prompts":
            raise ImportError(f"Simulated import error for {name}")
        raise ImportError(f"Unexpected module import: {name}")

    mock_import_module = mocker.patch("importlib.import_module", side_effect=import_side_effect)

    result = load_active_prompts("nonexistent", mock_logger_print, mock_logger_warn, mock_logger_error)

    assert result is None
    assert any("Prompt module for NATIVE_LANGUAGE 'nonexistent' ('Writer.Prompts_nonexistent') not found." in entry for entry in mock_log_entries if entry.startswith("WARN:"))
    assert any("CRITICAL: Failed to import fallback Writer.Prompts (English default)" in entry for entry in mock_log_entries if entry.startswith("ERROR:"))
    assert mock_import_module.call_count == 2

@pytest.mark.parametrize("lang_code", [None, ""])
def test_load_none_or_empty_language_defaults_to_english_parametrized(mocker: MockerFixture, lang_code):
    mock_en_module = types.ModuleType("Writer.Prompts")
    # Configure side_effect to ensure only Writer.Prompts is called and no other module.
    mock_import_module = mocker.patch("importlib.import_module", side_effect=lambda name: mock_en_module if name == "Writer.Prompts" else pytest.fail(f"Tried to import unexpected module: {name}"))

    result = load_active_prompts(lang_code, mock_logger_print, mock_logger_warn, mock_logger_error)

    assert result is mock_en_module
    assert any("Using English prompts (Writer.Prompts) as NATIVE_LANGUAGE is 'en'" in entry for entry in mock_log_entries if entry.startswith("PRINT:"))
    mock_import_module.assert_called_once_with("Writer.Prompts")

def test_unexpected_error_during_specific_language_import_fallback(mocker: MockerFixture):
    mock_en_module = types.ModuleType("Writer.Prompts")

    def import_side_effect(name):
        if name == "Writer.Prompts_errorlang":
            raise Exception("Simulated unexpected error") # Generic Exception
        elif name == "Writer.Prompts":
            return mock_en_module
        raise ImportError(f"Unexpected module import: {name}")

    mock_import_module = mocker.patch("importlib.import_module", side_effect=import_side_effect)

    result = load_active_prompts("errorlang", mock_logger_print, mock_logger_warn, mock_logger_error)

    assert result is mock_en_module # Should still fallback to English
    assert any("CRITICAL: Unexpected error loading prompt module for NATIVE_LANGUAGE 'errorlang'" in entry for entry in mock_log_entries if entry.startswith("ERROR:"))
    assert any("Using English prompts (Writer.Prompts) as NATIVE_LANGUAGE is 'en'" in entry for entry in mock_log_entries if entry.startswith("PRINT:"))
    assert mock_import_module.call_count == 2
    mock_import_module.assert_any_call("Writer.Prompts_errorlang")
    mock_import_module.assert_any_call("Writer.Prompts")

def test_critical_failure_if_activeprompts_is_none_at_end(mocker: MockerFixture):
    # This test ensures the final check for active_prompts_module being None logs an error.
    # This scenario is hard to hit if fallbacks work as intended with ImportError,
    # but this tests the specific safeguard if active_prompts_module somehow ends up as None.

    # Mock import_module to always return None, simulating a catastrophic failure
    # where even fallbacks don't yield a module (though the code structure makes this unlikely
    # unless the fallback itself fails to assign to active_prompts_module).
    # More directly, we test the condition where active_prompts_module is None before the final check.
    # The function's structure with try-except for imports and fallbacks means
    # it would return None from an inner block if an import fails critically.
    # This test will simulate the scenario where all import attempts (initial and fallback) result in None.

    mocker.patch("importlib.import_module", side_effect=ImportError("Simulating all imports fail, leading to None"))

    # Call with a language that would normally try to load a specific module then fallback
    result = load_active_prompts("specific_lang_all_fail", mock_logger_print, mock_logger_warn, mock_logger_error)

    assert result is None # Explicitly check that None is returned
    # Check for the final critical error message from the function itself
    assert any("CRITICAL: ActivePrompts module is None after attempting to load" in entry for entry in mock_log_entries if entry.startswith("ERROR:"))
