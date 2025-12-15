# Word Count Validation Enhancement Proposal

## Problem Statement

Sporadic word count validation errors occur rarely (3-5% of runs) where LLM's claimed word count doesn't match actual text:
- Example: LLM claims 567 words, actual is 166 words (401 word difference)
- Current behavior: Direct retry with same prompt
- Missing: Diagnostic capability to understand root cause

## Proposed Solution: Interactive Word Count Validation

### Concept
When word count validation fails, send a special diagnostic prompt that asks the LLM to self-diagnose:
1. Did you underestimate required text length?
2. Or did you miscount the words?

### Implementation Options

## Option A: Modify SafeGeneratePydantic (Core Integration)

**Location**: `Writer/Interface/Wrapper.py` lines 310-337

**Flow Logic**:
```python
except Exception as e:
    # Detect word count error specifically
    if "Word count" in str(e) and "doesn't match actual word count" in str(e):
        # Extract mismatch info
        if match := re.search(r'Word count (\d+) doesn\'t match actual word count (\d+)', str(e)):
            claimed_count = int(match.group(1))
            actual_count = int(match.group(2))

            # Run validation prompt
            corrected_response = self._handle_word_count_validation_error(
                _Logger, MesssagesHistory, claimed_count, actual_count,
                JSONResponse, _PydanticModel
            )

            if corrected_response:
                # Try validation again with corrected response
                validated_model = _PydanticModel(**corrected_response)
                return ResponseMessagesList, validated_model, TokenUsage

    # Original retry for other errors
    if attempt < max_attempts - 1:
        # ... existing logic
```

**Pros**:
- Integrated with existing retry mechanism
- Centralized in one place
- Automatic detection

**Cons**:
- Modifies core SafeGeneratePydantic
- More complex error handling logic

## Option B: Wrapper Function Pattern (Recommended)

**Location**: New file `Writer/Interface/WordCountValidator.py`

**Implementation**:
```python
class WordCountValidator:
    @staticmethod
    def validate_with_interactive_retry(
        Interface, _Logger, ResponseMessagesList, JSONResponse,
        OriginalModel, ContextInfo={}
    ):
        """Wrap SafeGeneratePydantic with word count validation logic"""
        try:
            # Try normal validation first
            return Interface.SafeGeneratePydantic(
                _Logger, OriginalMessages, Model, OriginalModel
            )
        except Exception as e:
            if "Word count" in str(e) and "doesn't match actual word count" in str(e):
                # Extract and handle word count mismatch
                fixed_response = WordCountValidator._interactive_validation(
                    _Logger, claimed, actual, JSONResponse,
                    OriginalMessages, ContextInfo
                )

                if fixed_response:
                    # Retry with fixed response
                    return ResponseMessagesList, OriginalModel(**fixed_response), {}

            # Re-raise if not word count error
            raise
```

**Usage in ChapterGenerator.py**:
```python
# BEFORE:
CurrentMessages, pydantic_result, _ = Interface.SafeGeneratePydantic(...)

# AFTER:
CurrentMessages, pydantic_result, _ = WordCountValidator.validate_with_interactive_retry(
    Interface, _Logger, CurrentMessages,
    JSON_response, ChapterOutput,
    ContextInfo={
        "original_prompt": CHAPTER_STAGE2_PROMPT,
        "stage": "Stage 2 character development"
    }
)
```

**Pros**:
- Clean separation of concerns
- Doesn't disturb core SafeGeneratePydantic
- Reusable for multiple models (ChapterOutput, OutlineOutput, etc.)
- Easier to unit test independently
- Safer to disable if problematic
- Can log validation attempts for analytics

**Cons**:
- Need to modify all SafeGeneratePydantic call sites
- Slightly more complex deployment

## Validation Prompt Design

### Interactive Validation Prompt Template:
```python
validation_prompt = f"""
# WORD COUNT VALIDATION ERROR DETECTED

## Error Details:
- Your claimed word count: {claimed_count} words
- Actual word count: {actual_word_count} words
- Difference: {claimed_count - actual_word_count} words
- Tolerance: ±100 words

## Original Request:
{original_prompt}

## Your Response:
{original_response_text}

## Analysis Required:
Please analyze which statement is true:
1. You provided sufficient content but miscounted the words
2. You underestimated the required text length and provided less content

## Corrective Action Required:
Please provide a corrected response that:
- Has accurate word count within tolerance
- Maintains content quality and coherence
- Addresses the root cause (either better counting or more content)

## Format:
Return ONLY the corrected JSON response with accurate word_count field.
"""

# Add as new message to history and retry
ValidationMessages = OriginalMessages + [
    BuildUserQuery(validation_prompt)
]
```

## Data & Context

### Error Statistics:
- Total runs analyzed: ~64
- Word count errors: 2-3 occurrences (3-5% rate)
- Model: huihui_ai/qwen2.5-abliterate:32b
- Tolerance: ±100 words

### Example of Problem Case:
```
LLM Response:
{
  "word_count": 567,  # Claimed
  "text": "Rian duduk..."  # Actual: 166 words
}

Validation Error:
Word count 567 doesn't match actual word count 166 (tolerance: ±100)
```

## Recommendation: Option B

**Why Option B is preferred**:
1. **Clean Architecture** - Validation logic separated from core interface
2. **Future Extensible** - Can add validation for other fields later
3. **Easier Testing** - Can unit test validator independently
4. **Rollback Safe** - Easier to disable if problematic
5. **Analytics Ready** - Can log validation attempts for analysis

## Implementation Priority

**Low Priority** - Since this is a rare issue (3-5% occurrence), implement:
1. After fixing more critical pipeline errors
2. When improving overall system robustness
3. As part of quality control enhancement

## Status

- [ ] File created with proposal details
- [ ] Waiting for implementation decision
- [ ] Option B recommended but not yet implemented
- [ ] Will be revisited based on error frequency and user feedback

---

*Document created: 2025-12-15*
*Author: Claude Code Assistant*
*Context: Discussing interactive word count validation approach*