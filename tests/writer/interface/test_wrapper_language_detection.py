"""
Tests for Wrapper.py language detection infrastructure.

These tests verify that the Interface class correctly detects and stores
the language setting from Config.NATIVE_LANGUAGE.
"""

import pytest
from unittest.mock import patch


class TestWrapperLanguageDetection:
    """Test suite for Interface language detection."""

    def test_language_defaults_to_english(self):
        """Test language defaults to 'en' when NATIVE_LANGUAGE is not set."""
        # Arrange & Act
        with patch('Writer.Config.NATIVE_LANGUAGE', None):
            from Writer.Interface.Wrapper import Interface
            interface = Interface(Models=[])

            # Assert
            assert hasattr(interface, 'language')
            assert interface.language == 'en'

    def test_language_reads_from_config_english(self, english_language_config):
        """Test Interface detects English from Config.NATIVE_LANGUAGE='en'."""
        # Arrange & Act
        from Writer.Interface.Wrapper import Interface
        interface = Interface(Models=[])

        # Assert
        assert hasattr(interface, 'language')
        assert interface.language == 'en'

    def test_language_reads_from_config_indonesian(self, indonesian_language_config):
        """Test Interface detects Indonesian from Config.NATIVE_LANGUAGE='id'."""
        # Arrange & Act
        from Writer.Interface.Wrapper import Interface
        interface = Interface(Models=[])

        # Assert
        assert hasattr(interface, 'language')
        assert interface.language == 'id'

    def test_language_persists_across_calls(self, indonesian_language_config):
        """Test language setting persists across multiple Interface instances."""
        # Arrange
        from Writer.Interface.Wrapper import Interface

        # Act - create multiple interfaces
        interface1 = Interface(Models=[])
        interface2 = Interface(Models=[])

        # Assert - both should have same language
        assert interface1.language == 'id'
        assert interface2.language == 'id'

    def test_language_set_on_init(self, english_language_config):
        """Test self.language is set during __init__()."""
        # Arrange & Act
        from Writer.Interface.Wrapper import Interface
        interface = Interface(Models=[])

        # Assert
        assert hasattr(interface, 'language')
        assert isinstance(interface.language, str)
        assert interface.language in ['en', 'id']  # Valid language codes
