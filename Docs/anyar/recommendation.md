## Improve Handling of Ollama Structured Output in `SafeGenerateJSON`

**Observation:**
The current code in `Writer/Interface/Wrapper.py` correctly activates Ollama's structured output feature by passing the Pydantic schema via the `format` parameter in `ChatAndStreamResponse` when `_FormatSchema` is provided. However, the subsequent processing in `SafeGenerateJSON` still includes steps to clean markdown artifacts (like ` ```json `) and manually extract the JSON block (`{...}` or `[...]`) from the response text before parsing with `json.loads()`.

This processing logic is inconsistent with the expectation that Ollama's `format` parameter should return *only* the valid JSON object conforming to the schema, without extra text or markdown. The Pydantic validation code after parsing is also commented out, likely assuming Ollama's output is already valid.

**Recommendations:**

To simplify the code and fully leverage Ollama's structured output feature:

1.  **Remove Markdown Cleanup:** Delete the code block in `SafeGenerateJSON` responsible for removing ` ```json ` and ` ``` ` prefixes/suffixes from the raw response text.
2.  **Remove JSON Block Extraction:** Delete the code block in `SafeGenerateJSON` that attempts to find the first `{` or `[` and the last `}` or `]` to extract the JSON block.
3.  **Direct Parsing:** Modify the code to directly use the raw response text obtained from `self.GetLastMessageText(Response)` as input for the `json.loads()` call.
4.  **Optional: Re-enable Pydantic Validation:** Consider uncommenting and re-enabling the Pydantic validation step (`YourSchemaModel.model_validate_json(raw_response_text)` or `YourSchemaModel(**parsed_json)`) *after* the `json.loads()` call. While potentially redundant if Ollama's feature is trusted, this adds an extra layer of validation and converts the dictionary into a Pydantic model instance directly.

**Benefit:**
These changes will make `SafeGenerateJSON` cleaner, more efficient, and more reliant on the intended behavior of Ollama's structured output feature, reducing potential points of failure related to manual text processing.
