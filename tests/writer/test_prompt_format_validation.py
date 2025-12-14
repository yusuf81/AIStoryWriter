#!/usr/bin/env python3
"""
TDD tests for prompt format validation against Pydantic models.
Ensures prompts generate responses that match Pydantic model structure.
"""

import json
import re
from typing import Dict, Any

import pytest

from Writer.Models import StoryElements, CharacterDetail
from Writer import Prompts
from Writer.PromptsHelper import get_prompts


class TestPromptFormatValidation:
    """Test prompt format matching Pydantic model requirements using AAA pattern."""

    def extract_json_examples(self, prompt_text: str) -> list[Dict[str, Any]]:
        """
        Helper to extract JSON examples from prompt text.
        Returns list of parsed JSON dictionaries.
        """
        json_blocks = []

        # Find "Example format:" section
        example_start = prompt_text.find('Example format:')
        if example_start != -1:
            # Extract everything after "Example format:"
            after_example = prompt_text[example_start + len('Example format:'):].strip()

            # Find the JSON block (handle double braces)
            if after_example.startswith('{{'):
                # Convert {{ to { and }} to } to get valid JSON
                json_text = after_example.replace('{{', '{').replace('}}', '}')

                # Count braces to find the complete JSON object
                brace_count = 0
                json_end = 0
                for i, char in enumerate(json_text):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break

                if json_end > 50:  # Make sure we got a reasonable size
                    json_text = json_text[:json_end]
                    try:
                        parsed = json.loads(json_text)
                        if isinstance(parsed, dict):
                            json_blocks.append(parsed)
                    except json.JSONDecodeError:
                        pass

        return json_blocks

    def test_story_elements_prompt_english_format(self, mock_logger):
        """
        RED: Test that English GENERATE_STORY_ELEMENTS prompt produces examples matching StoryElements

        Arrange: Get English prompt and extract JSON examples
        Act: Extract and validate JSON examples from the prompt
        Assert: All examples should validate against StoryElements model
        """
        # Arrange
        prompt = Prompts.GENERATE_STORY_ELEMENTS

        # Act
        examples = self.extract_json_examples(prompt)

        # Assert - This will FAIL (RED phase) because the current example is too generic
        assert len(examples) > 0, "Prompt should contain at least one JSON example"

        # Try to validate each example against StoryElements
        for i, example in enumerate(examples):
            try:
                StoryElements(**example)
            except Exception as e:
                pytest.fail(f"Example {i} from English prompt fails StoryElements validation: {e}")

    def test_story_elements_prompt_indonesian_format(self, mock_logger):
        """
        RED: Test that Indonesian GENERATE_STORY_ELEMENTS prompt produces examples matching StoryElements

        Arrange: Load Indonesian prompts and extract JSON examples
        Act: Extract and validate JSON examples from the Indonesian prompt
        Assert: All examples should validate against StoryElements model
        """
        # Arrange
        import Writer.Config as Config
        original_lang = getattr(Config, 'NATIVE_LANGUAGE', 'en')
        Config.NATIVE_LANGUAGE = 'id'
        indonesian_prompts = get_prompts()
        prompt = indonesian_prompts.GENERATE_STORY_ELEMENTS
        Config.NATIVE_LANGUAGE = original_lang  # Restore

        # Act
        examples = self.extract_json_examples(prompt)

        # Assert - This will FAIL (RED phase) because Indonesian examples have wrong structure
        assert len(examples) > 0, "Indonesian prompt should contain at least one JSON example"

        # Try to validate each example against StoryElements
        for i, example in enumerate(examples):
            try:
                StoryElements(**example)
            except Exception as e:
                pytest.fail(f"Example {i} from Indonesian prompt fails StoryElements validation: {e}")

    def test_character_structure_format(self, mock_logger):
        """
        RED: Test that character examples follow Dict[str, List[CharacterDetail]] structure

        Arrange: Get prompts with character examples
        Act: Extract character-related JSON examples
        Assert: All character examples should have list structure, not single objects
        """
        # Arrange
        import Writer.Config as Config
        original_lang = getattr(Config, 'NATIVE_LANGUAGE', 'en')
        Config.NATIVE_LANGUAGE = 'id'
        prompt_indo = get_prompts().GENERATE_STORY_ELEMENTS
        Config.NATIVE_LANGUAGE = original_lang  # Restore

        # Act - Extract examples that contain character fields
        examples = self.extract_json_examples(prompt_indo)

        # Assert - This will FAIL because Indonesian examples use single dict structure
        for example in examples:
            if 'characters' in example:
                characters = example['characters']
                for char_type, char_data in characters.items():
                    assert isinstance(char_data, list), \
                        f"Character '{char_type}' should be a list, got {type(char_data).__name__}"

                    # If list is not empty, validate CharacterDetail structure
                    if char_data:
                        for char_item in char_data:
                            try:
                                CharacterDetail(**char_item)
                            except Exception as e:
                                pytest.fail(f"Character item fails CharacterDetail validation: {e}")

    def test_style_field_format(self, mock_logger):
        """
        RED: Test that style field examples are simple strings, not objects

        Arrange: Get prompts with style examples
        Act: Extract style-related JSON examples
        Assert: All style examples should be strings, not objects
        """
        # Arrange
        import Writer.Config as Config
        original_lang = getattr(Config, 'NATIVE_LANGUAGE', 'en')
        Config.NATIVE_LANGUAGE = 'id'
        indonesian_prompts = get_prompts()
        prompt = indonesian_prompts.GENERATE_STORY_ELEMENTS
        Config.NATIVE_LANGUAGE = original_lang  # Restore

        # Act
        examples = self.extract_json_examples(prompt)

        # Assert - This will FAIL because Indonesian examples show style as object
        for example in examples:
            if 'style' in example:
                style = example['style']
                assert isinstance(style, str), \
                    f"Style field should be a string, got {type(style).__name__}: {style}"

    def test_wrapper_examples_format(self, mock_logger):
        """
        RED: Test that hardcoded examples in Wrapper.py match Pydantic models

        Arrange: Check hardcoded examples in Wrapper.py build_format_instruction
        Act: Extract and validate the examples
        Assert: All examples should validate against appropriate models
        """
        # Arrange
        from Writer.Interface.Wrapper import Interface

        # Act - Create interface and get format instruction for StoryElements
        interface = Interface()
        schema = StoryElements.model_json_schema()
        format_instruction = interface._build_format_instruction(schema)

        # Extract examples from the format instruction
        examples = self.extract_json_examples(format_instruction)

        # Assert - This will FAIL because Wrapper examples use non-existent fields
        for i, example in enumerate(examples):
            try:
                StoryElements(**example)
            except Exception as e:
                pytest.fail(f"Wrapper example {i} fails StoryElements validation: {e}")


class TestFormatInstructionBuilder:
    """
    Test format instruction building functionality.
    Tests that format instructions help LLM generate correct structure.
    """

    def test_format_instruction_contains_character_examples(self, mock_logger):
        """
        RED: Test that format instructions provide correct character structure example

        Arrange: Create interface
        Act: Build format instruction for StoryElements
        Assert: Instruction should contain character list structure example
        """
        # Arrange
        from Writer.Interface.Wrapper import Interface
        interface = Interface()

        # Act
        schema = StoryElements.model_json_schema()
        instruction = interface._build_format_instruction(schema)

        # Assert - This might FAIL if instruction doesn't show correct structure
        # Look for pattern indicating list structure in character examples
        has_character_example = False
        has_list_structure = False

        # Check for character field examples
        if 'characters' in instruction.lower():
            has_character_example = True

        # Check for list pattern in examples
        list_patterns = [': [{', '": [{"', '[']
        for pattern in list_patterns:
            if pattern in instruction:
                has_list_structure = True
                break

        assert has_character_example, "Format instruction should contain character field examples"
        assert has_list_structure, "Format instruction should show character fields as lists"

    def test_format_instruction_contains_style_example(self, mock_logger):
        """
        RED: Test that format instructions show style as string, not object

        Arrange: Create interface
        Act: Build format instruction for StoryElements
        Assert: Style example should be shown as string value
        """
        # Arrange
        from Writer.Interface.Wrapper import Interface
        interface = Interface()

        # Act
        schema = StoryElements.model_json_schema()
        instruction = interface._build_format_instruction(schema)

        # Assert - Check that style example is shown as string
        has_style_example = False
        has_string_style = False

        if 'style' in instruction.lower():
            has_style_example = True

        # Look for style patterns that indicate string, not object
        string_patterns = ['style": "', 'style": "Descriptive', '"style": "']
        for pattern in string_patterns:
            if pattern in instruction:
                has_string_style = True
                break

        assert has_style_example, "Format instruction should contain style field examples"
        assert has_string_style, "Style example should be shown as string, not object"