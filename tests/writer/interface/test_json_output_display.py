"""Test that JSON output doesn't display raw artifacts in console."""

import io
import sys
from unittest.mock import patch, MagicMock
from Writer.Interface.Wrapper import Interface
from Writer.PrintUtils import Logger

def test_json_output_not_displayed():
    """Test that SafeGenerateJSON doesn't print raw JSON to console."""
    # Capture stdout
    captured_output = io.StringIO()

    # Mock the _ollama_chat method to return a simple JSON response
    with patch.object(Interface, '_ollama_chat') as mock_chat:
        mock_chat.return_value = (
            [{'role': 'assistant', 'content': '{"IsComplete": true}'}],  # FullResponseMessages
            {'prompt_tokens': 5, 'completion_tokens': 1}  # TokenUsage
        )

        captured_output.seek(0)
        output = captured_output.read()

        # The JSON should NOT be in the console output
        assert '{"IsComplete": true}' not in output, f"Raw JSON found in output: {output}"

def test_outline_revision_tags_not_present():
    """Test that outline revision tags are cleaned from output."""
    from Writer.Interface.Wrapper import Interface
    interface = Interface([])

    # Test pure JSON is hidden
    result = interface._CleanStreamingOutput('{"IsComplete": true}', '{"IsComplete": true}')
    assert result == "", f"Pure JSON should be hidden, got: '{result}'"

    # Test outline revision tags are removed
    result = interface._CleanStreamingOutput('<OUTLINE REVISI>\nChapter content\n</OUTLINE REVISI>', '<OUTLINE REVISI>\nChapter content\n</OUTLINE REVISI>')
    assert '<OUTLINE REVISI>' not in result, f"Revision tags should be removed, got: '{result}'"
    assert '</OUTLINE REVISI>' not in result, f"Revision tags should be removed, got: '{result}'"
    assert 'Chapter content' in result, f"Content should remain, got: '{result}'"

    # Test normal content passes through
    result = interface._CleanStreamingOutput('This is normal text', 'This is normal text')
    assert result == 'This is normal text', f"Normal text should pass through, got: '{result}'"

    # Test JSON response with more content
    result = interface._CleanStreamingOutput('{"TotalChapters": 5}', '{"TotalChapters": 5}')
    assert result == "", f"JSON response should be hidden, got: '{result}'"