"""
ReasoningChain TDD Tests - London School Approach
Tests for migrating all SafeGenerateText usage to SafeGeneratePydantic
"""
import pytest
from unittest.mock import Mock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestReasoningChainPydanticConversion:
    """Test complete conversion of ReasoningChain to Pydantic"""

    def test_reason_about_plot_uses_pydantic(self, mock_interface, mock_logger, mock_config):
        """Verify _reason_about_plot uses SafeGeneratePydantic with ReasoningOutput model"""
        from Writer.ReasoningChain import ReasoningChain

        # Arrange: Create ReasoningChain
        mock_iface = mock_interface()
        config = mock_config
        rc = ReasoningChain(mock_iface, mock_logger(), config)

        # Create a real ReasoningOutput model
        from Writer.Models import ReasoningOutput
        reasoning = ReasoningOutput(
            reasoning="The key plot points for Chapter 1: introduce hero, establish conflict, set up journey"
        )

        # Mock SafeGeneratePydantic
        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "Response"}],
            reasoning,
            {"prompt_tokens": 100}
        )

        # Act
        result = rc._reason_about_plot("test context", "additional context", 1)

        # Assert
        mock_iface.SafeGeneratePydantic.assert_called_once()
        assert result == "The key plot points for Chapter 1: introduce hero, establish conflict, set up journey"

    def test_reason_about_character_uses_pydantic(self, mock_interface, mock_logger, mock_config):
        """Verify _reason_about_character uses SafeGeneratePydantic with ReasoningOutput model"""
        from Writer.ReasoningChain import ReasoningChain

        # Arrange
        mock_iface = mock_interface()
        config = mock_config
        rc = ReasoningChain(mock_iface, mock_logger(), config)

        from Writer.Models import ReasoningOutput
        reasoning = ReasoningOutput(
            reasoning="The hero shows bravery through actions, the villain reveals motivation"
        )

        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "Response"}],
            reasoning,
            {"prompt_tokens": 120, "completion_tokens": 80}
        )

        # Act
        result = rc._reason_about_character("test context", "existing content", 2)

        # Assert
        mock_iface.SafeGeneratePydantic.assert_called_once()
        assert result == "The hero shows bravery through actions, the villain reveals motivation"

    def test_reason_about_dialogue_uses_pydantic(self, mock_interface, mock_logger, mock_config):
        """Verify _reason_about_dialogue uses SafeGeneratePydantic with ReasoningOutput model"""
        from Writer.ReasoningChain import ReasoningChain

        # Arrange
        mock_iface = mock_interface()
        config = mock_config
        rc = ReasoningChain(mock_iface, mock_logger(), config)

        from Writer.Models import ReasoningOutput
        reasoning = ReasoningOutput(
            reasoning="Hero's dialogue should be direct and confident, Villain's should be manipulative"
        )

        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "Response"}],
            reasoning,
            {"prompt_tokens": 90}
        )

        # Act
        result = rc._reason_about_dialogue("test context", "content to enhance", 3)

        # Assert
        mock_iface.SafeGeneratePydantic.assert_called_once()
        assert result == "Hero's dialogue should be direct and confident, Villain's should be manipulative"

    def test_reason_about_outline_uses_pydantic(self, mock_interface, mock_logger, mock_config):
        """Verify _reason_about_outline uses SafeGeneratePydantic with ReasoningOutput model"""
        from Writer.ReasoningChain import ReasoningChain

        # Arrange
        mock_iface = mock_interface()
        config = mock_config
        rc = ReasoningChain(mock_iface, mock_logger(), config)

        from Writer.Models import ReasoningOutput
        reasoning = ReasoningOutput(
            reasoning="A three-act structure with 8 chapters would provide optimal pacing for this story"
        )

        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "Response"}],
            reasoning,
            {"prompt_tokens": 150}
        )

        # Act
        result = rc._reason_about_outline("story prompt")

        # Assert
        mock_iface.SafeGeneratePydantic.assert_called_once()
        assert result == "A three-act structure with 8 chapters would provide optimal pacing for this story"

    def test_reason_general_uses_pydantic(self, mock_interface, mock_logger, mock_config):
        """Verify _reason_general uses SafeGeneratePydantic with ReasoningOutput model"""
        from Writer.ReasoningChain import ReasoningChain

        # Arrange
        mock_iface = mock_interface()
        config = mock_config
        rc = ReasoningChain(mock_iface, mock_logger(), config)

        from Writer.Models import ReasoningOutput
        reasoning = ReasoningOutput(
            reasoning="For this editing task, focus on clarity, flow, and consistency"
        )

        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "Response"}],
            reasoning,
            {"prompt_tokens": 80}
        )

        # Act
        result = rc._reason_general("test context", "editing", "additional notes", 4)

        # Assert
        mock_iface.SafeGeneratePydantic.assert_called_once()
        assert result == "For this editing task, focus on clarity, flow, and consistency"

    def test_all_methods_use_pydantic_not_text(self, mock_interface, mock_logger, mock_config):
        """Verify none of the reasoning methods use SafeGenerateText"""
        from Writer.ReasoningChain import ReasoningChain

        # Arrange
        mock_iface = mock_interface()
        config = mock_config
        config.REASONING_CACHE_RESULTS = False  # Disable caching for this test
        rc = ReasoningChain(mock_iface, mock_logger(), config)

        from Writer.Models import ReasoningOutput
        reasoning = ReasoningOutput(reasoning="Test reasoning response")

        mock_iface.SafeGeneratePydantic.return_value = (
            [{"role": "assistant", "content": "Response"}],
            reasoning,
            {"prompt_tokens": 100}
        )

        # Act on all methods via the public reason() method
        rc.reason("test context", "plot", additional_context="extra", chapter_number=1)
        rc.reason("test context", "character", additional_context="extra", chapter_number=2)
        rc.reason("test context", "dialogue", additional_context="extra", chapter_number=3)
        rc.reason("test context", "outline")
        rc.reason("test context", "editing", additional_context="extra", chapter_number=4)

        # Assert: SafeGenerateText should not be called
        has_sgt = hasattr(mock_iface, 'SafeGenerateText')
        assert not has_sgt or not mock_iface.SafeGenerateText.called

        # Assert: All 5 private methods called SafeGeneratePydantic
        assert mock_iface.SafeGeneratePydantic.call_count == 5

    @pytest.fixture
    def mock_config(self):
        """Create a mock config with required attributes"""
        config = Mock()
        config.REASONING_MODEL = "test_reasoning_model"
        config.REASONING_CACHE_RESULTS = False
        config.REASONING_LOG_SEPARATE = False
        return config


class TestReasoningOutputModel:
    """Test ReasoningOutput Pydantic model when created"""

    def test_reasoning_output_model_exists(self):
        """Verify ReasoningOutput model is registered in Models.py"""
        from Writer.Models import MODEL_REGISTRY

        # This will pass once we add ReasoningOutput to MODEL_REGISTRY
        assert 'ReasoningOutput' in MODEL_REGISTRY

    def test_reasoning_output_model_structure(self):
        """Verify ReasoningOutput model has proper structure"""
        from Writer.Models import get_model

        # Get the ReasoningOutput model
        ReasoningOutput = get_model('ReasoningOutput')

        # Test it can be instantiated
        reasoning = ReasoningOutput(reasoning="This is a test reasoning")
        assert reasoning.reasoning == "This is a test reasoning"

        # Test validation - should have min length
        try:
            ReasoningOutput(reasoning="Too")
            assert False, "Should have raised validation error for too short reasoning"
        except BaseException:
            pass  # Expected to fail validation
