"""
Tests for _build_validation_error_message() internationalization.

These tests verify that validation error messages are generated in the correct
language based on the Interface instance's language setting.
"""

import pytest


class TestValidationErrorsI18n:
    """Test suite for i18n support in _build_validation_error_message()."""

    def test_validation_error_message_english(self, english_language_config):
        """Test validation error message is generated in English."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput
        from pydantic import ValidationError

        interface = Interface(Models=[])

        # Create real ValidationError by violating Pydantic model
        try:
            ChapterOutput(chapter_number=1)  # Missing 'text' field
        except ValidationError as ve:
            # Act
            message = interface._build_validation_error_message(ve, 'ChapterOutput')

            # Assert - verify English text
            assert 'Your response had validation errors' in message
            assert 'This field is required but was not provided' in message or 'required' in message.lower()
            assert 'Return ONLY the corrected JSON data' in message
            assert 'Respons Anda memiliki kesalahan validasi' not in message

    def test_validation_error_message_indonesian(self, indonesian_language_config):
        """Test validation error message is generated in Indonesian."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput
        from pydantic import ValidationError

        interface = Interface(Models=[])

        # Create real ValidationError by violating Pydantic model
        try:
            ChapterOutput(chapter_number=1)  # Missing 'text' field
        except ValidationError as ve:
            # Act
            message = interface._build_validation_error_message(ve, 'ChapterOutput')

            # Assert - verify Indonesian text
            assert 'Respons Anda memiliki kesalahan validasi' in message
            assert 'Field ini wajib tetapi tidak disediakan' in message or 'wajib' in message.lower()
            assert 'Kembalikan HANYA data JSON yang sudah diperbaiki' in message
            assert 'Your response had validation errors' not in message

    def test_missing_field_error_english(self, english_language_config):
        """Test missing field error is in English."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput
        from pydantic import ValidationError

        interface = Interface(Models=[])

        try:
            ChapterOutput(chapter_number=1)  # Missing 'text' field
        except ValidationError as ve:
            # Act
            message = interface._build_validation_error_message(ve, 'ChapterOutput')

            # Assert - verify missing field error in English
            assert 'text' in message  # Field name should appear
            assert 'required' in message.lower() or 'not provided' in message.lower()

    def test_missing_field_error_indonesian(self, indonesian_language_config):
        """Test missing field error is in Indonesian."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput
        from pydantic import ValidationError

        interface = Interface(Models=[])

        try:
            ChapterOutput(chapter_number=1)  # Missing 'text' field
        except ValidationError as ve:
            # Act
            message = interface._build_validation_error_message(ve, 'ChapterOutput')

            # Assert - verify missing field error in Indonesian
            assert 'text' in message  # Field name should appear
            assert 'wajib' in message.lower() or 'tidak disediakan' in message.lower()

    def test_string_too_short_error(self, english_language_config):
        """Test string length error with formatting."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput
        from pydantic import ValidationError

        interface = Interface(Models=[])

        try:
            # Create invalid ChapterOutput with empty text
            ChapterOutput(text="", chapter_number=1)
        except ValidationError as ve:
            # Act
            message = interface._build_validation_error_message(ve, 'ChapterOutput')

            # Assert - verify error includes actual length
            assert 'text' in message
            assert '0 characters' in message or 'you provided 0' in message

    def test_type_parsing_error(self, english_language_config):
        """Test type mismatch error."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from pydantic import BaseModel, ValidationError

        # Create simple test model
        class TestModel(BaseModel):
            count: int

        interface = Interface(Models=[])

        try:
            TestModel(count="not a number")  # Type error
        except ValidationError as ve:
            # Act
            message = interface._build_validation_error_message(ve, 'TestModel')

            # Assert - verify type error detected
            assert 'count' in message
            assert 'int' in message.lower() or 'integer' in message.lower()

    def test_value_error_preserves_message(self, english_language_config):
        """Test custom validator message is preserved."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from pydantic import BaseModel, field_validator, ValidationError

        # Create model with custom validator
        class TestModel(BaseModel):
            value: str

            @field_validator('value')
            @classmethod
            def validate_value(cls, v):
                if not v.startswith('test'):
                    raise ValueError("Value must start with 'test'")
                return v

        interface = Interface(Models=[])

        try:
            TestModel(value="invalid")
        except ValidationError as ve:
            # Act
            message = interface._build_validation_error_message(ve, 'TestModel')

            # Assert - verify custom message preserved
            assert "must start with 'test'" in message.lower() or 'value must start' in message.lower()

    def test_multiple_errors_concatenation(self, indonesian_language_config):
        """Test multiple errors in one message."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput
        from pydantic import ValidationError

        interface = Interface(Models=[])

        try:
            # Multiple errors: missing text, empty text
            ChapterOutput(chapter_number=1)
        except ValidationError as ve:
            # Act
            message = interface._build_validation_error_message(ve, 'ChapterOutput')

            # Assert - verify message contains multiple error entries
            lines = message.split('\n')
            error_lines = [l for l in lines if l.strip().startswith('-')]
            # At least one error listed
            assert len(error_lines) >= 1

    def test_error_footer_included(self, english_language_config):
        """Test footer instruction is present."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput
        from pydantic import ValidationError

        interface = Interface(Models=[])

        try:
            ChapterOutput(chapter_number=1)
        except ValidationError as ve:
            # Act
            message = interface._build_validation_error_message(ve, 'ChapterOutput')

            # Assert - verify footer present
            assert 'Return ONLY the corrected JSON data' in message

    def test_field_path_preserved(self, english_language_config):
        """Test nested field paths are preserved."""
        # Arrange
        from Writer.Interface.Wrapper import Interface
        from Writer.Models import ChapterOutput
        from pydantic import ValidationError

        interface = Interface(Models=[])

        try:
            ChapterOutput(chapter_number=1)  # Missing text
        except ValidationError as ve:
            # Act
            message = interface._build_validation_error_message(ve, 'ChapterOutput')

            # Assert - verify field name appears in error
            assert 'text' in message
