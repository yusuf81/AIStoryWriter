"""
Tests for Phase 7: Reasoning Chain Logging

Verifies that ReasoningChain logs initialization status and reasoning generation progress.
"""

import sys
from typing import Any
sys.path.insert(0, '/var/www/AIStoryWriter')

from Writer.ReasoningChain import ReasoningChain  # noqa: E402
from Writer.Models import ReasoningOutput  # noqa: E402


class MockLogger:
    """Mock logger that captures log messages"""

    def __init__(self) -> None:
        self.logs: list[tuple[int, str]] = []

    def Log(self, message: str, level: int) -> None:
        self.logs.append((level, message))

    def get_messages(self) -> list[str]:
        return [msg for level, msg in self.logs]

    def has_message_containing(self, text: str) -> bool:
        return any(text in msg for msg in self.get_messages())


class MockConfig:
    """Mock configuration with dynamic attribute support"""

    def __init__(self) -> None:
        self.USE_REASONING_CHAIN = True
        self.REASONING_MODEL = "test-reasoning-model"
        self.REASONING_LOG_SEPARATE = False
        self.REASONING_CACHE_RESULTS = False

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)


class MockInterface:
    """Mock LLM interface"""

    def BuildSystemQuery(self, text: str) -> dict:
        return {"role": "system", "content": text}

    def BuildUserQuery(self, text: str) -> dict:
        return {"role": "user", "content": text}

    def SafeGeneratePydantic(self, logger: Any, messages: list, model: str,
                             output_class: type) -> tuple[Any, ReasoningOutput, None]:
        # Return mock reasoning output
        reasoning_obj = ReasoningOutput(reasoning="This is test reasoning about the plot.")
        return messages, reasoning_obj, None


def test_logs_reasoning_chain_enabled():
    """Verify __init__ logs when reasoning chain is enabled"""
    logger = MockLogger()
    config = MockConfig()
    config.USE_REASONING_CHAIN = True  # type: ignore[misc]

    _rc = ReasoningChain(MockInterface(), config, logger)  # type: ignore[misc]  # noqa: F841

    assert logger.has_message_containing("ENABLED"), \
        "Should log that reasoning chain is ENABLED"
    assert logger.has_message_containing("test-reasoning-model"), \
        "Should log the reasoning model name"


def test_logs_reasoning_chain_disabled():
    """Verify __init__ logs when reasoning chain is disabled"""
    logger = MockLogger()
    config = MockConfig()
    config.USE_REASONING_CHAIN = False  # type: ignore[misc]

    _rc = ReasoningChain(MockInterface(), config, logger)  # type: ignore[misc]  # noqa: F841

    assert logger.has_message_containing("DISABLED"), \
        "Should log that reasoning chain is DISABLED"


def test_logs_separate_file_mode():
    """Verify __init__ logs separate file logging status"""
    logger = MockLogger()
    config = MockConfig()
    config.USE_REASONING_CHAIN = True  # type: ignore[misc]
    config.REASONING_LOG_SEPARATE = True  # type: ignore[misc]

    _rc = ReasoningChain(MockInterface(), config, logger)  # type: ignore[misc]  # noqa: F841

    assert logger.has_message_containing("separate file"), \
        "Should log that separate file logging is enabled"


def test_logs_main_log_mode():
    """Verify __init__ logs main log mode"""
    logger = MockLogger()
    config = MockConfig()
    config.USE_REASONING_CHAIN = True  # type: ignore[misc]
    config.REASONING_LOG_SEPARATE = False  # type: ignore[misc]

    _rc = ReasoningChain(MockInterface(), config, logger)  # type: ignore[misc]  # noqa: F841

    assert logger.has_message_containing("main log"), \
        "Should log that main log mode is enabled"


def test_logs_reasoning_generation_start():
    """Verify reason() logs at start of generation"""
    logger = MockLogger()
    config = MockConfig()

    rc = ReasoningChain(MockInterface(), config, logger)  # type: ignore[misc]

    # Clear init logs
    logger.logs = []  # type: ignore[misc]

    rc.reason("Test context", "plot", None, 5)

    assert logger.has_message_containing("Generating plot reasoning"), \
        "Should log start of reasoning generation"
    assert logger.has_message_containing("Chapter 5"), \
        "Should include chapter number in log"


def test_logs_reasoning_generation_completion():
    """Verify reason() logs after generation completes"""
    logger = MockLogger()
    config = MockConfig()

    rc = ReasoningChain(MockInterface(), config, logger)  # type: ignore[misc]

    # Clear init logs
    logger.logs = []  # type: ignore[misc]

    _reasoning = rc.reason("Test context", "character", None, 3)  # noqa: F841

    assert logger.has_message_containing("Generated character reasoning"), \
        "Should log completion of reasoning generation"
    assert logger.has_message_containing("Chapter 3"), \
        "Should include chapter number in completion log"
    assert logger.has_message_containing("chars"), \
        "Should log character count of reasoning"


def test_logs_reasoning_without_chapter_number():
    """Verify reason() handles missing chapter number gracefully"""
    logger = MockLogger()
    config = MockConfig()

    rc = ReasoningChain(MockInterface(), config, logger)  # type: ignore[misc]

    # Clear init logs
    logger.logs = []  # type: ignore[misc]

    rc.reason("Test context", "outline", None, None)

    assert logger.has_message_containing("N/A"), \
        "Should use 'N/A' when chapter number is None"


def test_chapter_generator_logs_reasoning_request():
    """Verify ChapterGenerator logs reasoning requests"""
    from Writer.Chapter.ChapterGenerator import _generate_reasoning_for_stage

    logger = MockLogger()
    config = MockConfig()
    interface = MockInterface()

    _generate_reasoning_for_stage(  # type: ignore[misc]
        interface, logger, config, "plot",
        "Chapter outline", "", "", 7, ""
    )

    assert logger.has_message_containing("Requesting plot reasoning"), \
        "Should log reasoning request"
    assert logger.has_message_containing("test-reasoning-model"), \
        "Should log which model is being used"
    assert logger.has_message_containing("Chapter 7"), \
        "Should log chapter number"


def test_chapter_generator_logs_skipped_reasoning():
    """Verify ChapterGenerator logs when reasoning is skipped"""
    from Writer.Chapter.ChapterGenerator import _generate_reasoning_for_stage

    logger = MockLogger()
    config = MockConfig()
    config.USE_REASONING_CHAIN = False  # type: ignore[misc]
    interface = MockInterface()

    result = _generate_reasoning_for_stage(  # type: ignore[misc]
        interface, logger, config, "dialogue",
        "Chapter outline", "", "", 2, ""
    )

    assert result == "", "Should return empty string when reasoning disabled"
    assert logger.has_message_containing("Skipping reasoning"), \
        "Should log that reasoning is being skipped"
    assert logger.has_message_containing("USE_REASONING_CHAIN=False"), \
        "Should explain why reasoning is skipped"


def test_reasoning_caching_logs():
    """Verify cached reasoning is logged"""
    logger = MockLogger()
    config = MockConfig()
    config.REASONING_CACHE_RESULTS = True  # type: ignore[misc]

    rc = ReasoningChain(MockInterface(), config, logger)  # type: ignore[misc]

    # Clear init logs
    logger.logs = []  # type: ignore[misc]

    # First call - should generate
    rc.reason("Test context", "plot", None, 5)

    # Clear logs
    logger.logs = []  # type: ignore[misc]

    # Second call with same params - should use cache
    rc.reason("Test context", "plot", None, 5)

    assert logger.has_message_containing("cached reasoning"), \
        "Should log when using cached reasoning"
