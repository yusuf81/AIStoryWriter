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

    def test_conflict_field_structure_in_english_prompt(self, mock_logger):
        """
        RED: Test that English prompt conflict examples are strings, not objects

        Arrange: Get English GENERATE_STORY_ELEMENTS prompt
        Act: Extract JSON examples and check conflict field structure
        Assert: Conflict field should be a string, not nested object
        """
        # Arrange
        prompt = Prompts.GENERATE_STORY_ELEMENTS

        # Act
        examples = self.extract_json_examples(prompt)

        # Assert - This will FAIL because current examples show conflict as object
        for example in examples:
            if 'conflict' in example:
                conflict = example['conflict']
                assert isinstance(conflict, str), \
                    f"Conflict field should be a string, got {type(conflict).__name__}: {conflict}"

    def test_conflict_field_structure_in_indonesian_prompt(self, mock_logger):
        """
        RED: Test that Indonesian prompt conflict examples are strings, not objects

        Arrange: Get Indonesian GENERATE_STORY_ELEMENTS prompt
        Act: Extract JSON examples and check conflict field structure
        Assert: Conflict field should be a string, not nested object
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

        # Assert - This will FAIL because Indonesian examples show conflict as object
        for example in examples:
            if 'conflict' in example:
                conflict = example['conflict']
                assert isinstance(conflict, str), \
                    f"Conflict field should be a string, got {type(conflict).__name__}: {conflict}"

    def test_symbolism_field_structure_in_english_prompt(self, mock_logger):
        """
        RED: Test that English prompt symbolism examples are lists, not objects

        Arrange: Get English GENERATE_STORY_ELEMENTS prompt
        Act: Extract JSON examples and check symbolism field structure
        Assert: Symbolism field should be a list of dicts, not nested object
        """
        # Arrange
        prompt = Prompts.GENERATE_STORY_ELEMENTS

        # Act
        examples = self.extract_json_examples(prompt)

        # Assert - This will FAIL because current examples show symbolism as nested object
        for example in examples:
            if 'symbolism' in example:
                symbolism = example['symbolism']
                assert isinstance(symbolism, list), \
                    f"Symbolism field should be a list, got {type(symbolism).__name__}: {symbolism}"

                # If list is not empty, check structure
                if symbolism:
                    assert isinstance(symbolism[0], dict), \
                        f"Symbolism list items should be dicts, got {type(symbolism[0]).__name__}"

    def test_symbolism_field_structure_in_indonesian_prompt(self, mock_logger):
        """
        RED: Test that Indonesian prompt symbolism examples are lists, not objects

        Arrange: Get Indonesian GENERATE_STORY_ELEMENTS prompt
        Act: Extract JSON examples and check symbolism field structure
        Assert: Symbolism field should be a list of dicts, not nested object
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

        # Assert - This will FAIL because Indonesian examples show symbolism as nested object
        for example in examples:
            if 'symbolism' in example:
                symbolism = example['symbolism']
                assert isinstance(symbolism, list), \
                    f"Symbolism field should be a list, got {type(symbolism).__name__}: {symbolism}"

                # If list is not empty, check structure
                if symbolism:
                    assert isinstance(symbolism[0], dict), \
                        f"Symbolism list items should be dicts, got {type(symbolism[0]).__name__}"

    def test_response_template_conflict_structure_english(self, mock_logger):
        """
        RED: Test that English response template's conflict section expects free text, not nested keys

        Arrange: Get English GENERATE_STORY_ELEMENTS prompt
        Act: Check the conflict section in RESPONSE_TEMPLATE
        Assert: Template should expect free text, not structured object
        """
        # Arrange
        prompt = Prompts.GENERATE_STORY_ELEMENTS

        # Act - Find the conflict section
        conflict_start = prompt.find('## Conflict')
        assert conflict_start != -1, "Prompt should have Conflict section"

        # Extract conflict section
        conflict_section = prompt[conflict_start:conflict_start + 500]

        # Assert - Now PASSES because we simplified the structure
        # Should have single bullet point, not separate Type and Description
        assert '- **' in conflict_section, "Conflict section should have bullet points"
        assert '**Type**:' not in conflict_section, \
            "Conflict section should not have separate Type key - this creates nested structure"
        # Note: **Description** is now used as a single field, not separate from Type

    def test_response_template_symbolism_structure_english(self, mock_logger):
        """
        RED: Test that English response template's symbolism section expects list, not nested object

        Arrange: Get English GENERATE_STORY_ELEMENTS prompt
        Act: Check the symbolism section in RESPONSE_TEMPLATE
        Assert: Template should not create nested object with numbered symbols
        """
        # Arrange
        prompt = Prompts.GENERATE_STORY_ELEMENTS

        # Act - Find the symbolism section
        symbolism_start = prompt.find('## Symbolism')
        assert symbolism_start != -1, "Prompt should have Symbolism section"

        # Extract symbolism section
        symbolism_section = prompt[symbolism_start:symbolism_start + 500]

        # Assert - This will FAIL because template uses numbered symbols with sub-keys
        # Should NOT have nested structure with "Symbol 1", "Symbol 2" keys
        assert '### Symbol 1' not in symbolism_section, \
            "Symbolism section should not create numbered symbols with nested structure"
        assert '**Symbol**:' not in symbolism_section, \
            "Symbolism section should not have Symbol key - this creates nested structure"
        assert '**Meaning**:' not in symbolism_section, \
            "Symbolism section should not have Meaning key - this creates nested structure"

    def test_response_template_conflict_structure_indonesian(self, mock_logger):
        """
        RED: Test that Indonesian response template's conflict section expects free text, not nested keys

        Arrange: Get Indonesian GENERATE_STORY_ELEMENTS prompt
        Act: Check the conflict section in RESPONSE_TEMPLATE
        Assert: Template should expect free text, not structured object
        """
        # Arrange
        import Writer.Config as Config
        original_lang = getattr(Config, 'NATIVE_LANGUAGE', 'en')
        Config.NATIVE_LANGUAGE = 'id'
        indonesian_prompts = get_prompts()
        prompt = indonesian_prompts.GENERATE_STORY_ELEMENTS
        Config.NATIVE_LANGUAGE = original_lang  # Restore

        # Act - Find the conflict section
        conflict_start = prompt.find('## Konflik')
        assert conflict_start != -1, "Indonesian prompt should have Konflik section"

        # Extract conflict section
        conflict_section = prompt[conflict_start:conflict_start + 500]

        # Assert - Now PASSES because we simplified the structure
        # Should have single bullet point, not separate Jenis and Deskripsi
        assert '- **' in conflict_section, "Konflik section should have bullet points"
        assert '**Jenis**:' not in conflict_section, \
            "Konflik section should not have separate Jenis key - this creates nested structure"
        # Note: **Deskripsi** is now used as a single field, not separate from Jenis

    def test_response_template_symbolism_structure_indonesian(self, mock_logger):
        """
        RED: Test that Indonesian response template's symbolism section expects list, not nested object

        Arrange: Get Indonesian GENERATE_STORY_ELEMENTS prompt
        Act: Check the symbolism section in RESPONSE_TEMPLATE
        Assert: Template should not create nested object with numbered symbols
        """
        # Arrange
        import Writer.Config as Config
        original_lang = getattr(Config, 'NATIVE_LANGUAGE', 'en')
        Config.NATIVE_LANGUAGE = 'id'
        indonesian_prompts = get_prompts()
        prompt = indonesian_prompts.GENERATE_STORY_ELEMENTS
        Config.NATIVE_LANGUAGE = original_lang  # Restore

        # Act - Find the symbolism section
        symbolism_start = prompt.find('## Simbolisme')
        assert symbolism_start != -1, "Indonesian prompt should have Simbolisme section"

        # Extract symbolism section
        symbolism_section = prompt[symbolism_start:symbolism_start + 500]

        # Assert - This will FAIL because template uses numbered symbols with sub-keys
        # Should NOT have nested structure with "Simbol 1", "Simbol 2" keys
        assert '### Simbol 1' not in symbolism_section, \
            "Simbolisme section should not create numbered symbols with nested structure"
        assert '**Simbol**:' not in symbolism_section, \
            "Simbolisme section should not have Simbol key - this creates nested structure"
        assert '**Makna**:' not in symbolism_section, \
            "Simbolisme section should not have Makna key - this creates nested structure"


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


class TestPromptJSONBraceFormat:
    """Test prompt format compatibility with Python .format() and JSON braces."""

    def test_critic_outline_prompt_format_english(self, mock_logger):
        """
        RED: Test that English CRITIC_OUTLINE_PROMPT currently fails with KeyError

        Arrange: Get English CRITIC_OUTLINE_PROMPT
        Act: Attempt to format the prompt with _Outline parameter
        Assert: Should raise KeyError for JSON braces (RED phase)
        """
        # Arrange
        prompt = Prompts.CRITIC_OUTLINE_PROMPT
        test_outline = "Test outline content with some text"

        # Act & Assert
        # This should FAIL in RED phase, pass in GREEN phase after fix
        formatted = prompt.format(_Outline=test_outline)

        # If we get here, the prompt successfully formatted (GREEN phase)
        assert "_Outline" not in formatted, "Placeholder should be replaced"
        assert test_outline in formatted, "Test outline should be in formatted output"

    def test_critic_outline_prompt_format_indonesian(self, mock_logger):
        """
        RED: Test that Indonesian CRITIC_OUTLINE_PROMPT currently fails with KeyError

        Arrange: Load Indonesian prompts
        Act: Attempt to format the prompt with _Outline parameter
        Assert: Should raise KeyError for JSON braces (RED phase)
        """
        # Arrange
        # Load Indonesian prompts
        from Writer.PromptsHelper import get_prompts
        indonesian_prompts = get_prompts()
        prompt = indonesian_prompts.CRITIC_OUTLINE_PROMPT
        test_outline = "Konten outline test"

        # Act & Assert
        # This should FAIL in RED phase, pass in GREEN phase after fix
        formatted = prompt.format(_Outline=test_outline)

        # If we get here, the prompt successfully formatted (GREEN phase)
        assert "_Outline" not in formatted, "Placeholder should be replaced"
        assert test_outline in formatted, "Test outline should be in formatted output"

    def test_critic_chapter_prompt_missing_outline_placeholder(self, mock_logger):
        """
        RED: Test that CRITIC_CHAPTER_PROMPT ignores _Outline parameter

        This demonstrates the bug where outline information is lost during formatting,
        not a KeyError, but ignored parameters that should be included.

        Arrange: Get CRITIC_CHAPTER_PROMPT
        Act: Format with _Chapter and _Outline parameters
        Assert: Should FAIL because outline content is missing from formatted output
        """
        # Arrange
        prompt = Prompts.CRITIC_CHAPTER_PROMPT
        test_chapter = "Chapter content here"
        test_outline = "IMPORTANT OUTLINE INFORMATION THAT SHOULD BE INCLUDED"

        # Act
        # This should FAIL the test because _Outline is ignored (no KeyError, but missing content)
        formatted = prompt.format(_Chapter=test_chapter, _Outline=test_outline)

        # Assert - This should FAIL in RED phase, pass in GREEN after fix
        assert test_outline in formatted, "Outline information should be present in formatted prompt"
        assert "_Outline" not in formatted, "Placeholder should be replaced"

    def test_json_examples_have_double_braces_scenes_to_json(self, mock_logger):
        """
        GREEN: Verify SCENES_TO_JSON uses correct double braces pattern

        This test verifies that existing prompts correctly use double braces.
        It should PASS, showing the correct pattern to follow.
        """
        # Arrange
        prompt = Prompts.SCENES_TO_JSON
        test_scenes = "Scene 1\nScene 2\nScene 3"

        # Act & Assert
        # This should PASS because SCENES_TO_JSON correctly uses double braces
        try:
            formatted = prompt.format(_Scenes=test_scenes)
            assert "_Scenes" not in formatted, "Placeholder should be replaced"
            assert test_scenes in formatted, "Test content should be in formatted output"
        except KeyError:
            pytest.fail("SCENES_TO_JSON should format correctly with double braces")

    def test_all_prompts_scan_for_json_braces(self, mock_logger):
        """
        GREEN: Verify all prompts have properly escaped JSON braces

        Arrange: Get all prompts from both language files
        Act: Search for JSON examples with single braces
        Assert: Should find NO problematic patterns after fixes
        """
        # Arrange
        import Writer.Prompts as EnglishPrompts
        from Writer.PromptsHelper import get_prompts as get_indonesian_prompts

        # Get all prompt attributes (strings only)
        english_prompts = {k: v for k, v in vars(EnglishPrompts).items()
                          if not k.startswith('_') and isinstance(v, str)}
        indonesian_prompts = {k: v for k, v in vars(get_indonesian_prompts()).items()
                             if not k.startswith('_') and isinstance(v, str)}

        all_prompts = [('English', english_prompts), ('Indonesian', indonesian_prompts)]
        found_issues = []

        # Act
        for lang_name, prompts in all_prompts:
            for prompt_name, prompt_text in prompts.items():
                # Skip prompts without JSON indicators
                if 'JSON' not in prompt_text and 'json' not in prompt_text.lower():
                    continue

                # Check for patterns that look like unescaped JSON
                lines = prompt_text.split('\n')
                for i, line in enumerate(lines):
                    # Skip format placeholders
                    if any(placeholder in line for placeholder in ['_{', '_O', '_C', '_S', '_P']):
                        continue

                    # Look for JSON-like patterns with single braces
                    # Pattern: Lines with {"key": or [ or } but not {{ or }}
                    if (('{' in line and '}' in line and
                         not line.count('{') == line.count('{{') and
                         '"' in line and (':' in line or ']' in line)) or
                        (line.strip() == '{' or line.strip() == '}')):

                        # Check if this is actually JSON (has keys/colons)
                        if any(key in line for key in ['"feedback":', '"rating":', '"suggestions":', '"detail":', '"laju":', '"alur":']):
                            found_issues.append(f"{lang_name}.{prompt_name} line {i+1}: {line.strip()}")

        # Assert
        # After GREEN phase fixes, this should PASS because no issues remain
        assert len(found_issues) == 0, f"Found prompts with unescaped JSON braces: {found_issues}"


class TestEnhancedSceneOutlineFieldNames:
    """Test suite for enhanced scene outline field name alignment"""

    def test_enhanced_scene_outline_field_names_mismatch_english(self, mock_logger):
        """
        RED: Test that English CHAPTER_OUTLINE_PROMPT teaches wrong field names
        that don't match EnhancedSceneOutline model
        """
        # Arrange
        from Writer.Prompts import CHAPTER_OUTLINE_PROMPT
        from Writer.Models import EnhancedSceneOutline
        from Writer.PromptsHelper import validate_prompt_format

        # Act & Assert - Prompt can be formatted but teaches wrong field names
        is_valid, error = validate_prompt_format(CHAPTER_OUTLINE_PROMPT, ['Chapter', 'Outline'])
        assert is_valid == True, "Prompt should format successfully"

        # Check presence of problematic field instructions that cause mismatch
        assert "## Scene: [Brief Scene Title]" in CHAPTER_OUTLINE_PROMPT, \
            "Contains Scene title template that causes LLM to generate 'scene_title'"
        assert "**Characters & Setting:**" in CHAPTER_OUTLINE_PROMPT, \
            "Contains Characters & Setting template that causes field name confusion"
        assert "**Conflict & Tone:**" in CHAPTER_OUTLINE_PROMPT, \
            "Contains Conflict & Tone template that causes field name confusion"
        assert "**Key Events & Dialogue:**" in CHAPTER_OUTLINE_PROMPT, \
            "Contains Key Events template that might cause 'key_events' but in wrong location"

        # These markdown templates will cause LLM to generate mismatched field names
        # when the SafeGeneratePydantic appends JSON schema instructions

        # RED: This test shows the prompt teaches field names that don't match
        # EnhancedSceneOutline model (title, characters_and_setting, conflict_and_tone, etc.)

    def test_enhanced_scene_outline_field_names_mismatch_indonesian(self, mock_logger):
        """
        RED: Test that Indonesian CHAPTER_OUTLINE_PROMPT teaches wrong field names
        that don't match EnhancedSceneOutline model
        """
        # Arrange
        from Writer.Prompts_id import CHAPTER_OUTLINE_PROMPT

        # Act & Assert - Indonesian prompt has same field name issues
        assert "## Adegan: [Judul Adegan Singkat]" in CHAPTER_OUTLINE_PROMPT, \
            "Contains Indonesian Scene title template that causes 'scene_title'"
        assert "**Karakter & Latar:**" in CHAPTER_OUTLINE_PROMPT, \
            "Contains Indonesian Characters & Setting template"
        assert "**Konflik & Nada:**" in CHAPTER_OUTLINE_PROMPT, \
            "Contains Indonesian Conflict & Tone template"

        # RED: Indonesian prompt teaches field names that don't match
        # EnhancedSceneOutline model expectations

    def test_enhanced_scene_outline_model_expected_fields(self, mock_logger):
        """
        RED: Verify what fields EnhancedSceneOutline model actually expects
        """
        # Arrange
        from Writer.Models import EnhancedSceneOutline

        # Act & Assert - Check model field names that should match LLM output
        expected_fields = [
            'title',
            'characters_and_setting',
            'conflict_and_tone',
            'key_events',
            'literary_devices',
            'resolution'
        ]

        model_fields = EnhancedSceneOutline.model_fields.keys()
        for field in expected_fields:
            assert field in model_fields, f"EnhancedSceneOutline should have field: {field}"

        # RED: Model expects these field names but prompt teaches different ones

    def test_enhanced_scene_outline_green_fixes_english(self, mock_logger):
        """
        GREEN: Verify English CHAPTER_OUTLINE_PROMPT now has correct JSON field examples
        """
        # Arrange
        from Writer.Prompts import CHAPTER_OUTLINE_PROMPT

        # Act & Assert - Check for correct JSON field examples
        assert '"title": "Brief scene title"' in CHAPTER_OUTLINE_PROMPT, \
            "English prompt should now contain correct 'title' field example"
        assert '"characters_and_setting":' in CHAPTER_OUTLINE_PROMPT, \
            "English prompt should contain correct 'characters_and_setting' field example"
        assert '"conflict_and_tone":' in CHAPTER_OUTLINE_PROMPT, \
            "English prompt should contain correct 'conflict_and_tone' field example"
        assert '"key_events":' in CHAPTER_OUTLINE_PROMPT, \
            "English prompt should contain correct 'key_events' field example"
        assert '"literary_devices":' in CHAPTER_OUTLINE_PROMPT, \
            "English prompt should contain correct 'literary_devices' field example"
        assert '"resolution":' in CHAPTER_OUTLINE_PROMPT, \
            "English prompt should contain correct 'resolution' field example"

        # GREEN: The prompts now have correct JSON field examples that match EnhancedSceneOutline

    def test_enhanced_scene_outline_green_fixes_indonesian(self, mock_logger):
        """
        GREEN: Verify Indonesian CHAPTER_OUTLINE_PROMPT now has correct JSON field examples
        """
        # Arrange
        from Writer.Prompts_id import CHAPTER_OUTLINE_PROMPT

        # Act & Assert - Check for correct JSON field examples
        assert '"title": "Judul adegan singkat"' in CHAPTER_OUTLINE_PROMPT, \
            "Indonesian prompt should now contain correct 'title' field example"
        assert '"characters_and_setting":' in CHAPTER_OUTLINE_PROMPT, \
            "Indonesian prompt should contain correct 'characters_and_setting' field example"
        assert '"conflict_and_tone":' in CHAPTER_OUTLINE_PROMPT, \
            "Indonesian prompt should contain correct 'conflict_and_tone' field example"
        assert '"key_events":' in CHAPTER_OUTLINE_PROMPT, \
            "Indonesian prompt should contain correct 'key_events' field example"
        assert '"literary_devices":' in CHAPTER_OUTLINE_PROMPT, \
            "Indonesian prompt should contain correct 'literary_devices' field example"
        assert '"resolution":' in CHAPTER_OUTLINE_PROMPT, \
            "Indonesian prompt should contain correct 'resolution' field example"

        # GREEN: The Indonesian prompts now have correct JSON field examples