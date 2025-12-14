"""
TDD Tests for Non-Streaming Pydantic Display - London School Approach
Tests for removing streaming logic and implementing user-friendly content display
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TestPydanticNonStreaming:
    """Test non-streaming behavior with SafeGeneratePydantic"""

    def test_safe_generate_pydantic_displays_extracted_content(self, mock_logger, capsys):
        """
        GREEN TEST: SafeGeneratePydantic displays user-friendly content, not raw JSON

        This PASSes because:
        - Now uses non-streaming ChatResponse
        - _DisplayPydanticResponse extracts and shows user-friendly content
        - JSON is properly parsed and displayed meaningfully
        """
        from Writer.Interface.Wrapper import Interface
        import Writer.Config

        # Enable DEBUG to see what's happening
        with patch.object(Writer.Config, 'DEBUG', True):
            # Create real Interface instance
            real_interface = Interface(Models=[])

            # Mock the provider chat to return JSON response
            with patch.object(real_interface, '_ollama_chat') as mock_chat:
                mock_chat.return_value = (
                    [{"role": "user", "content": "test"},  # Original messages + new assistant message
                     {"role": "assistant", "content": '{"context": "- Cerita tentang petualang menemukan harta karun"}'}],
                    {"prompt_tokens": 10, "completion_tokens": 20}
                )

                # Call ChatResponse with _FormatSchema (triggers Pydantic mode)
                messages, tokens, input_chars, est_tokens = real_interface.ChatResponse(
                    mock_logger(),
                    [{"role": "user", "content": "test"}],
                    "ollama://test",
                    123,
                    _FormatSchema={"type": "object", "properties": {"context": {"type": "string"}}}
                )

                # Check that user-friendly content was displayed
                captured = capsys.readouterr()
                assert "✓ Konteks:" in captured.out, f"Expected '✓ Konteks:' in output, got: {captured.out}"
                assert "- Cerita tentang petualang menemukan harta karun" in captured.out

    def test_debug_mode_shows_full_pydantic_response(self, mock_logger, capsys):
        """
        GREEN TEST: DEBUG=True shows full Pydantic response

        This PASSes because:
        - DEBUG mode full response is implemented
        - Content extraction and display works correctly
        """
        from Writer.Interface.Wrapper import Interface
        import Writer.Config

        with patch.object(Writer.Config, 'DEBUG', True):
            real_interface = Interface(Models=[])

            with patch.object(real_interface, '_ollama_chat') as mock_chat:
                mock_chat.return_value = (
                    [{"role": "user", "content": "test"},
                     {"role": "assistant", "content": '{"context": "test debug context"}'}],
                    {"prompt_tokens": 10, "completion_tokens": 20}
                )

                real_interface.ChatResponse(
                    mock_logger(),
                    [{"role": "user", "content": "test"}],
                    "ollama://test",
                    123,
                    _FormatSchema={"type": "object"}
                )

                captured = capsys.readouterr()
                assert "--- Full Pydantic Response ---" in captured.out
                assert '"context": "test debug context"' in captured.out

    def test_streaming_methods_removed(self):
        """
        GREEN TEST: Verify old streaming methods are removed/replaced

        This PASSes because:
        - StreamResponse has been removed
        - _CleanStreamingOutput has been removed
        - ChatAndStreamResponse has been completely removed
        """
        from Writer.Interface.Wrapper import Interface

        # After cleanup, streaming methods should be removed
        assert not hasattr(Interface, 'StreamResponse'), "StreamResponse should have been removed"
        assert not hasattr(Interface, '_CleanStreamingOutput'), "_CleanStreamingOutput should have been removed"
        assert not hasattr(Interface, 'ChatAndStreamResponse'), "ChatAndStreamResponse should be completely removed"
        assert hasattr(Interface, 'ChatResponse'), "ChatResponse should exist as the new method"

    def test_base_context_display_format(self, mock_logger, capsys):
        """
        GREEN TEST: BaseContext is displayed in user-friendly format
        """
        from Writer.Interface.Wrapper import Interface

        real_interface = Interface(Models=[])

        with patch.object(real_interface, '_ollama_chat') as mock_chat:
            mock_chat.return_value = (
                [{"role": "user", "content": "test"},
                 {"role": "assistant", "content": '{"context": "- Dua bab cerita\\n- Tentang petualang\\n- Ada harta karun"}'}],
                {"prompt_tokens": 10, "completion_tokens": 20}
            )

            real_interface.ChatResponse(
                mock_logger(),
                [{"role": "user", "content": "test"}],
                "ollama://test",
                123,
                _FormatSchema={"type": "object", "properties": {"context": {"type": "string"}}}
            )

            captured = capsys.readouterr()
            assert "✓ Konteks:" in captured.out
            assert "- Dua bab cerita" in captured.out

    def test_outline_output_display_format(self, mock_logger, capsys):
        """
        GREEN TEST: OutlineOutput shows title and chapter count
        """
        from Writer.Interface.Wrapper import Interface

        real_interface = Interface(Models=[])

        with patch.object(real_interface, '_ollama_chat') as mock_chat:
            mock_chat.return_value = (
                [{"role": "user", "content": "test"},
                 {"role": "assistant", "content": '{"title": "Petualangan Naga", "chapters": [{"chapter": 1}, {"chapter": 2}]}'}],
                {"prompt_tokens": 10, "completion_tokens": 20}
            )

            real_interface.ChatResponse(
                mock_logger(),
                [{"role": "user", "content": "test"}],
                "ollama://test",
                123,
                _FormatSchema={"type": "object", "properties": {"title": {"type": "string"}}}
            )

            captured = capsys.readouterr()
            assert "✓ Judul: Petualangan Naga" in captured.out
            assert "✓ Bab: 2 bab dibuat" in captured.out

    def test_chapter_output_display_format(self, mock_logger, capsys):
        """
        GREEN TEST: ChapterOutput shows word count
        """
        from Writer.Interface.Wrapper import Interface

        real_interface = Interface(Models=[])

        with patch.object(real_interface, '_ollama_chat') as mock_chat:
            chapter_text = "Ini adalah bab pertama dari cerita petualangan yang sangat menarik. " * 20
            mock_chat.return_value = (
                [{"role": "user", "content": "test"},
                 {"role": "assistant", "content": f'{{"text": "{chapter_text}"}}'}],
                {"prompt_tokens": 10, "completion_tokens": 20}
            )

            real_interface.ChatResponse(
                mock_logger(),
                [{"role": "user", "content": "test"}],
                "ollama://test",
                123,
                _FormatSchema={"type": "object", "properties": {"text": {"type": "string"}}}
            )

            captured = capsys.readouterr()
            assert "✓ Bab di-generate:" in captured.out
            word_count = len(chapter_text.split())
            assert f"{word_count} kata" in captured.out