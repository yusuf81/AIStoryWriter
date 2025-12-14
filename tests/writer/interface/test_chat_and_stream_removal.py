"""
TDD Tests for ChatAndStreamResponse Removal - London School Approach
Tests for completely removing deprecated ChatAndStreamResponse method
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TestChatAndStreamRemoval:
    """TDD tests for ChatAndStreamResponse removal - London School Approach"""

    def test_chat_and_stream_response_completely_removed(self):
        """
        RED TEST: Verify ChatAndStreamResponse is completely removed

        This test will FAIL initially because the method still exists.
        After cleanup, this test will PASS because the method will be removed.
        """
        from Writer.Interface.Wrapper import Interface

        interface = Interface(Models=[])

        # RED: This should fail initially because method still exists
        # After cleanup: This should pass because method is removed
        with pytest.raises(AttributeError):
            interface.ChatAndStreamResponse

        # But ChatResponse should still exist
        assert hasattr(interface, 'ChatResponse'), "ChatResponse should still exist"

    def test_interface_functionality_intact_after_cleanup(self, mock_logger, capsys):
        """
        RED TEST: Verify ChatResponse works correctly after cleanup

        This test verifies that ChatResponse functionality is preserved
        after ChatAndStreamResponse removal.
        """
        from Writer.Interface.Wrapper import Interface
        import Writer.Config

        with patch.object(Writer.Config, 'DEBUG', True):
            interface = Interface(Models=[])

            # Mock the provider chat to return structured JSON response
            with patch.object(interface, '_ollama_chat') as mock_chat:
                mock_chat.return_value = (
                    [{"role": "assistant", "content": '{"result": "test", "value": 42}'}],
                    {"prompt_tokens": 10, "completion_tokens": 20}
                )

                # This should work with ChatResponse (identical functionality)
                messages, tokens, input_chars, est_tokens = interface.ChatResponse(
                    mock_logger(),
                    [{"role": "user", "content": "test"}],
                    "ollama://test",
                    123,
                    _FormatSchema={
                        "type": "object",
                        "properties": {
                            "result": {"type": "string"},
                            "value": {"type": "number"}
                        }
                    }
                )

                # Should complete without error
                assert messages is not None
                assert isinstance(messages, list)
                assert len(messages) > 0

    def test_no_production_code_uses_deprecated_method(self):
        """
        RED TEST: Verify no production code uses ChatAndStreamResponse

        This test ensures that ChatAndStreamResponse is only used in tests,
        making it safe to remove completely.
        """
        import Writer
        import Writer.Interface.Wrapper

        # Check main modules don't use the deprecated method
        main_files_to_check = [
            'Write.py',
            'Writer/Pipeline.py',
            'Writer/OutlineGenerator.py',
            'Writer/Chapter/ChapterGenerator.py',
            'Writer/LLMEditor.py'
        ]

        for file_path in main_files_to_check:
            full_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    assert 'ChatAndStreamResponse' not in content, f"Production file {file_path} should not use ChatAndStreamResponse"