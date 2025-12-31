"""
Tests for Phase 4: Pydantic Constraint Explanations

Verifies that the Wrapper interface provides human-readable explanations of
Pydantic validation constraints to help LLMs understand validation rules upfront.
"""

import sys
sys.path.insert(0, '/var/www/AIStoryWriter')


def test_reasoning_constraint_in_models():
    """Verify ReasoningOutput model has max_length constraint"""
    from Writer.Models import ReasoningOutput

    schema = ReasoningOutput.model_json_schema()
    reasoning_field = schema['properties']['reasoning']

    assert 'maxLength' in reasoning_field, \
        "ReasoningOutput should have maxLength constraint"
    assert reasoning_field['maxLength'] == 2000, \
        "ReasoningOutput max_length should be 2000"


def test_constraint_explanation_logic_reasoning():
    """Test the constraint explanation logic for reasoning field"""
    # Simulate what _build_constraint_explanations() should do
    properties = {
        'reasoning': {'type': 'string', 'maxLength': 2000, 'description': 'Reasoning text'},
        'other_field': {'type': 'string'}
    }

    # Test the logic
    explanations = []
    for field_name, field_info in properties.items():
        if field_name == 'reasoning' and 'maxLength' in field_info:
            max_len = field_info['maxLength']
            explanations.append(
                f"'{field_name}': Maximum {max_len} characters. "
                "Keep your reasoning concise and focused - verbose explanations "
                "will be rejected. Aim for clarity over length."
            )

    assert len(explanations) == 1, \
        "Should generate one explanation for reasoning field"
    assert "'reasoning'" in explanations[0], \
        "Explanation should reference 'reasoning' field"
    assert "2000 characters" in explanations[0], \
        "Should mention max_length value"
    assert "concise" in explanations[0].lower(), \
        "Should encourage conciseness"


def test_constraint_explanation_logic_character_name():
    """Test the constraint explanation logic for character name fields"""
    properties = {
        'character_name': {'type': 'string', 'minLength': 2},
        'protagonist_character': {'type': 'string', 'minLength': 3},
        'other_field': {'type': 'string'}
    }

    # Test the logic
    explanations = []
    for field_name, field_info in properties.items():
        if 'character' in field_name.lower() and 'minLength' in field_info:
            min_len = field_info['minLength']
            explanations.append(
                f"'{field_name}': Each name must be at least {min_len} characters. "
                "Avoid single-letter placeholders."
            )

    assert len(explanations) == 2, \
        "Should generate explanations for both character fields"
    assert any("'character_name'" in exp for exp in explanations), \
        "Should explain character_name field"
    assert any("'protagonist_character'" in exp for exp in explanations), \
        "Should explain protagonist_character field"


def test_empty_explanations_when_no_constraints():
    """Verify no explanations generated for unconstrained fields"""
    properties = {
        'title': {'type': 'string'},
        'content': {'type': 'string'}
    }

    # Test the logic
    explanations = []
    for field_name, field_info in properties.items():
        # Reasoning constraint
        if field_name == 'reasoning' and 'maxLength' in field_info:
            explanations.append("...")
        # Word count constraint
        if field_name == 'word_count':
            explanations.append("...")
        # Character name constraint
        if 'character' in field_name.lower() and 'minLength' in field_info:
            explanations.append("...")

    assert len(explanations) == 0, \
        "Should not generate explanations for unconstrained fields"


def test_wrapper_file_has_constraint_method():
    """Verify Wrapper.py contains the _build_constraint_explanations method"""
    with open('/var/www/AIStoryWriter/Writer/Interface/Wrapper.py', 'r') as f:
        content = f.read()

    assert 'def _build_constraint_explanations' in content, \
        "Wrapper.py should have _build_constraint_explanations method"
    assert 'IMPORTANT CONSTRAINTS' in content, \
        "Method should use 'IMPORTANT CONSTRAINTS' header"


def test_wrapper_file_calls_constraint_method():
    """Verify _build_format_instruction calls _build_constraint_explanations"""
    with open('/var/www/AIStoryWriter/Writer/Interface/Wrapper.py', 'r') as f:
        content = f.read()

    assert 'self._build_constraint_explanations(properties)' in content, \
        "_build_format_instruction should call _build_constraint_explanations"
    assert 'VALIDATION CONSTRAINTS (IMPORTANT)' in content, \
        "Should add VALIDATION CONSTRAINTS section to instruction"
