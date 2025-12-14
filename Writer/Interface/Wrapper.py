import Writer.Config
import dotenv
import inspect
import json
import os
import time
import random
import importlib
import importlib.metadata
import subprocess
import sys
from urllib.parse import parse_qs, urlparse, unquote
import json_repair

try:
    from pydantic import BaseModel, ValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


def get_pydantic_format_instructions(model_class: type) -> str:
    """
    Generate format instructions for Pydantic models.

    Args:
        model_class: The Pydantic model class

    Returns:
        str: Format instructions string
    """
    if not PYDANTIC_AVAILABLE:
        return ""

    try:
        if hasattr(model_class, 'model_json_schema'):
            schema = model_class.model_json_schema()
        else:
            schema = model_class.schema()

        # Extract field descriptions from schema
        instructions = "\n\nPlease respond with a JSON object that follows this structure:\n"

        if 'properties' in schema:
            for field_name, field_info in schema['properties'].items():
                field_type = field_info.get('type', 'string')
                description = field_info.get('description', '')
                min_length = field_info.get('minLength')
                max_length = field_info.get('maxLength')

                instructions += f"\n- {field_name}: {field_type}"
                if description:
                    instructions += f" - {description}"
                if min_length is not None:
                    instructions += f" (minimum {min_length} characters)"
                if max_length is not None:
                    instructions += f" (maximum {max_length} characters)"

        instructions += "\n\nYour entire response must be valid JSON only. Do not include any other text or formatting."
        return instructions

    except Exception:
        # Fallback if schema generation fails
        return "\n\nPlease respond with valid JSON only. Do not include any other text or formatting."

dotenv.load_dotenv()

class Interface:
    def __init__(self, Models: list = []):
        self.Clients: dict = {}
        self.LoadModels(Models)

    def _get_retry_limit(self, override: int = None) -> int:
        """DRY helper: Get retry limit with safe fallback to MAX_PYDANTIC_RETRIES.

        Args:
            override: Optional explicit retry limit override

        Returns:
            int: Retry limit to use (override if provided, else config value, else 5)
        """
        if override is not None:
            return override
        return getattr(Writer.Config, 'MAX_PYDANTIC_RETRIES', 5)

    def ensure_package_is_installed(self, package_name):
        try:
            importlib.metadata.distribution(package_name)
        except importlib.metadata.PackageNotFoundError:
            print(f"Package {package_name} not found. Installing...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", package_name],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                print(f"Package {package_name} installed successfully.")
            except Exception as e:
                print(f"Failed to install {package_name}: {e}", file=sys.stderr)

    def LoadModels(self, Models: list):
        for Model in Models:
            if Model in self.Clients: continue
            Provider, ProviderModelName, ModelHost, _ = self.GetModelAndProvider(Model)
            if Provider == "ollama":
                self.ensure_package_is_installed("ollama")
                import ollama
                OllamaHost = ModelHost or getattr(Writer.Config, 'OLLAMA_HOST', None)
                try:
                    ollama.Client(host=OllamaHost).show(ProviderModelName)
                except Exception:
                    print(f"Ollama model {ProviderModelName} not found locally or host issue. Attempting pull...")
                    try:
                        pull_stream = ollama.Client(host=OllamaHost).pull(ProviderModelName, stream=True)
                        for _ in pull_stream: pass
                        print(f"\nPull attempt for {ProviderModelName} finished.")
                    except Exception as pull_e:
                        print(f"Failed to pull {ProviderModelName}: {pull_e}", file=sys.stderr)
                        continue
                self.Clients[Model] = ollama.Client(host=OllamaHost)
            elif Provider == "google":
                if not os.environ.get("GOOGLE_API_KEY"): raise Exception("GOOGLE_API_KEY missing")
                self.ensure_package_is_installed("google-genai")
                import google.genai as genai
                genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
                self.Clients[Model] = genai.GenerativeModel(model_name=ProviderModelName)
            elif Provider == "openrouter":
                if not os.environ.get("OPENROUTER_API_KEY"): raise Exception("OPENROUTER_API_KEY missing")
                from Writer.Interface.OpenRouter import OpenRouter
                self.Clients[Model] = OpenRouter(api_key=os.environ["OPENROUTER_API_KEY"], model_name=ProviderModelName)
            else: raise NotImplementedError(f"Provider {Provider} not supported")

    def GenerateEmbedding(self, _Logger, _Texts: list, _Model: str, _SeedOverride: int = -1):
        """
        Generate embeddings for a list of texts using the specified model.

        Args:
            _Logger: Logger instance
            _Texts: List of strings to embed
            _Model: Model string in provider://format
            _SeedOverride: Random seed override

        Returns:
            Tuple of (list of embeddings, token usage info)
        """
        if not _Texts:
            return [], {"prompt_tokens": 0, "completion_tokens": 0}

        # Parse provider and initialize if needed
        Provider, ProviderModelName, ModelHost, _ = self.GetModelAndProvider(_Model)

        # Ensure model is loaded
        if _Model not in self.Clients:
            self.LoadModels([_Model])

        # Call provider-specific method
        handler = getattr(self, f"_{Provider}_embedding", None)
        if not handler:
            raise Exception(f"Embeddings not supported for provider: {Provider}")

        return handler(_Logger, _Model, ProviderModelName, _Texts)

    # SafeGenerateText method removed - replaced with SafeGeneratePydantic
    def SafeGenerateText_DEPRECATED(self, _Logger, _Messages, _Model: str, _SeedOverride: int = -1, _FormatSchema: dict = None, _MinWordCount: int = 1, _max_retries_override: int = None):
        """DEPRECATED: This method is no longer used. Use SafeGeneratePydantic instead."""
        raise DeprecationWarning("SafeGenerateText is deprecated. Use SafeGeneratePydantic instead.")

    def SafeGenerateJSON(self, _Logger, _Messages, _Model: str, _SeedOverride: int = -1, _FormatSchema: dict = None, _max_retries_override: int = None):
        CurrentMessages = self.RemoveThinkTagFromAssistantMessages([m.copy() for m in _Messages])
        Retries = 0
        max_r = self._get_retry_limit(_max_retries_override)

        while Retries < max_r:
            CurrentSeed = _SeedOverride if Retries == 0 else random.randint(0, 99999)
            # ResponseMessagesList is the full history *after* the LLM call in this iteration
            ResponseMessagesList, TokenUsage, InputChars, EstInputTokens = self.ChatResponse(
                _Logger, CurrentMessages, _Model, CurrentSeed, _FormatSchema=_FormatSchema,
            )

            RawResponseText = self.GetLastMessageText(ResponseMessagesList)
            CleanedResponseText = RawResponseText.strip()
            # Standard cleaning for markdown-like code blocks
            if CleanedResponseText.startswith("```json"): CleanedResponseText = CleanedResponseText[7:]
            if CleanedResponseText.startswith("```"): CleanedResponseText = CleanedResponseText[3:]
            if CleanedResponseText.endswith("```"): CleanedResponseText = CleanedResponseText[:-3]
            CleanedResponseText = CleanedResponseText.strip()

            try:
                if not CleanedResponseText: raise ValueError("Cleaned response is empty.")

                # More robust JSON extraction
                first_brace = CleanedResponseText.find("{")
                first_bracket = CleanedResponseText.find("[")

                if first_brace == -1 and first_bracket == -1: # No JSON start characters
                    raise ValueError("No JSON object or array start found in response.")

                start_index = -1
                if first_brace != -1 and first_bracket != -1: start_index = min(first_brace, first_bracket)
                elif first_brace != -1: start_index = first_brace
                else: start_index = first_bracket # Must be first_bracket != -1

                # If a start char is found, try to find its corresponding end char
                if start_index != -1:
                    is_object = CleanedResponseText[start_index] == '{'
                    expected_end_char = '}' if is_object else ']'
                    # Attempt to find the matching end character. This is simplified; robust parsing is hard.
                    # For now, json_repair will handle most structural issues.
                    # We just try to narrow down the string to the most likely JSON part.
                    last_end_char_idx = CleanedResponseText.rfind(expected_end_char)
                    if last_end_char_idx > start_index:
                        CleanedResponseText = CleanedResponseText[start_index : last_end_char_idx + 1]
                    # else, we might have a truncated JSON or other issues, let json_repair try

                JSONResponse = json_repair.loads(CleanedResponseText)
                token_info = TokenUsage if TokenUsage else "N/A (streaming incomplete)"
                _Logger.Log(f"JSON Call Stats: ... Tokens: {token_info}", 6)
                return ResponseMessagesList, JSONResponse, TokenUsage # Success

            except Exception as e:
                _Logger.Log(f"SafeGenerateJSON: Parse Error: '{e}'. Raw: '{RawResponseText[:100]}...'. Cleaned: '{CleanedResponseText[:100]}...'. Retry {Retries + 1}/{max_r}", 7)
                Retries += 1
                CurrentMessages = ResponseMessagesList # Use history from the failed attempt
                if CurrentMessages and CurrentMessages[-1]["role"] == "assistant": del CurrentMessages[-1]
                if not CurrentMessages or not any(m['role'] == 'user' for m in CurrentMessages):
                    CurrentMessages = [m.copy() for m in _Messages] # Reset

        _Logger.Log(f"SafeGenerateJSON: All {max_r} retries failed. RAISING EXCEPTION.", 7)
        raise Exception(f"Failed to generate valid JSON after {max_r} retries")

    def SafeGeneratePydantic(self, _Logger, _Messages, _Model: str, _PydanticModel: type, _SeedOverride: int = -1, _max_retries_override: int = None):
        """
        Generate structured output using Pydantic model validation with smart retry.

        Args:
            _Logger: Logger instance
            _Messages: List of messages to send to LLM
            _Model: Model to use for generation
            _PydanticModel: Pydantic model class to validate against
            _SeedOverride: Override seed for generation
            _max_retries_override: Override max retries

        Returns:
            Tuple of (ResponseMessagesList, Validated Pydantic Model, TokenUsage)

        Raises:
            Exception: If validation fails after max retries (no fallback)
        """
        # Check if Pydantic is available - fail fast
        if not PYDANTIC_AVAILABLE:
            raise Exception("Pydantic is not available but required for SafeGeneratePydantic")

        # Check if Pydantic parsing is enabled - fail fast
        if Writer.Config.USE_PYDANTIC_PARSING is False:
            raise Exception("Pydantic parsing is disabled by config")

        from Writer.Models import get_model

        # If PydanticModel is string, get model from registry
        if isinstance(_PydanticModel, str):
            try:
                _PydanticModel = get_model(_PydanticModel)
            except KeyError as e:
                raise Exception(f"Pydantic model '{_PydanticModel}' not found in registry")

        # Get max retries from config
        max_attempts = self._get_retry_limit(_max_retries_override)

        # Get format instructions for the model
        if hasattr(_PydanticModel, 'model_json_schema'):
            schema = _PydanticModel.model_json_schema()
        else:
            # Fallback for older Pydantic versions
            schema = _PydanticModel.schema()

        # Prepare format instruction - use simplified format to prevent schema echoing
        format_instruction = self._build_format_instruction(schema)

        # Add format instruction to the last user message
        messages_for_parsing = [m.copy() for m in _Messages]
        if messages_for_parsing and messages_for_parsing[-1]["role"] == "user":
            messages_for_parsing[-1]["content"] += format_instruction
        elif messages_for_parsing:
            messages_for_parsing.append({"role": "user", "content": format_instruction})
        else:
            messages_for_parsing = [{"role": "user", "content": format_instruction}]

        _Logger.Log(f"SafeGeneratePydantic: Using schema for {_PydanticModel.__name__}", 5)

        # Smart retry loop with better error handling
        for attempt in range(max_attempts):
            try:
                # Generate structured response using JSON format
                ResponseMessagesList, JSONResponse, TokenUsage = self.SafeGenerateJSON(
                    _Logger, messages_for_parsing, _Model, _SeedOverride, schema, _max_retries_override
                )

                # PRE-CHECK: Validate JSONResponse format before Pydantic
                if isinstance(JSONResponse, list):
                    # This is malformed response (multiple JSON objects)
                    raise TypeError(f"Expected single JSON object, got list of {len(JSONResponse)} objects")

                # PRE-CHECK: Ensure it's a dict
                if not isinstance(JSONResponse, dict):
                    raise TypeError(f"Expected JSON object/dict, got {type(JSONResponse).__name__}")

                # Validate and convert to Pydantic model
                validated_model = _PydanticModel(**JSONResponse)
                _Logger.Log(f"SafeGeneratePydantic: Successfully validated {_PydanticModel.__name__} on attempt {attempt + 1}", 5)
                return ResponseMessagesList, validated_model, TokenUsage

            except Exception as e:  # Catch ALL response format errors
                # This triggers retry logic
                if attempt < max_attempts - 1:
                    _Logger.Log(f"Attempt {attempt + 1} failed: {e}. Retrying...", 5)

                    # For structured responses, provide more specific retry guidance
                    if isinstance(e, TypeError) and "list" in str(e):
                        _Logger.Log("Hint: Ensure response is single JSON object, not multiple objects. Do NOT include schema in response.", 5)
                    elif "missing" in str(e).lower() or "validation" in str(e).lower():
                        _Logger.Log("Hint: Ensure all required fields are present and correct.", 5)

                    continue
                else:
                    # Final attempt failed - raise exception
                    if isinstance(e, ValidationError):
                        # Format Pydantic errors nicely
                        pydantic_error = e  # type: ignore
                        if hasattr(pydantic_error, 'errors'):
                            error_details = "\n".join([
                                f"- {'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                                for err in pydantic_error.errors()
                            ])
                            raise Exception(f"Pydantic validation failed after {max_attempts} attempts:\n{error_details}")
                        else:
                            raise Exception(f"Pydantic validation failed after {max_attempts} attempts: {str(e)}")
                    else:
                        raise Exception(f"Failed to generate valid response after {max_attempts} attempts. Last error: {e}")

    def _build_format_instruction(self, schema):
        """Build clear format instruction without showing full schema to prevent echoing"""
        properties = schema.get('properties', {})
        required_fields = schema.get('required', [])

        instruction = "\n\n=== JSON SCHEMA (REFERENCE ONLY) ===\n"
        instruction += "This defines the structure. DO NOT repeat the schema in your response!\n\n"
        instruction += "=== YOUR RESPONSE (JSON ONLY) ===\n"
        instruction += "Provide ONLY the JSON data below. Do NOT include explanations or the schema.\n\n"
        instruction += "Required fields:\n"

        for field in required_fields:
            field_info = properties.get(field, {})
            field_type = field_info.get('type', 'unknown')
            field_desc = field_info.get('description', '')

            # Handle array types with specific examples
            if field_type == 'array':
                items_type = field_info.get('items', {}).get('type', 'unknown')
                if items_type == 'string':
                    instruction += f"  - {field} (array of strings, Required): {field_desc}\n"
                    instruction += f"    Example: [\"String 1\", \"String 2\"]\n"
                else:
                    instruction += f"  - {field} (array of objects, Required): {field_desc}\n"
            else:
                if field_desc:
                    instruction += f"  - {field} ({field_type}, Required): { field_desc}\n"
                else:
                    instruction += f"  - {field} ({field_type}, Required)\n"

        # Add optional fields if any
        optional_fields = [k for k in properties.keys() if k not in required_fields]
        if optional_fields:
            instruction += "\nOptional fields:\n"
            for field in optional_fields[:5]:  # Limit to first 5 optional fields
                field_info = properties.get(field, {})
                field_type = field_info.get('type', 'unknown')
                field_desc = field_info.get('description', '')

                # Handle array types with specific examples
                if field_type == 'array':
                    items_type = field_info.get('items', {}).get('type', 'unknown')
                    if items_type == 'string':
                        instruction += f"  - {field} (array of strings, Optional): {field_desc[:50]}...\n"
                        instruction += f"    Example: [\"String 1\", \"String 2\"]\n"
                    else:
                        instruction += f"  - {field} (array of objects, Optional): {field_desc[:50]}...\n"
                else:
                    if field_desc:
                        instruction += f"  - {field} ({field_type}, Optional): { field_desc[:50]}...\n"
                    else:
                        instruction += f"  - {field} ({field_type}, Optional)\n"
            if len(optional_fields) > 5:
                instruction += f"  - ... and {len(optional_fields) - 5} more optional fields\n"

        instruction += "\nExample format: {\"field1\": \"value\", \"field2\": 123}\n"
        instruction += "IMPORTANT: Return ONLY the JSON data, not the schema!\n"

        # Add specific examples for models with List[str] fields that are problematic
        if any(field in properties.keys() for field in ['chapters', 'character_list']):
            instruction += """
For example:
{
  "title": "Petualangan di Gua Tersembunyi",
  "chapters": [
    "Chapter 1: Rian menemukan gua mistis di tengah hutan",
    "Chapter 2: Pertarungan dengan naga kecil penjaga harta karun"
  ],
  "character_list": [
    "Rian - Petualang berani yang mencari harta karun",
    "Bang Jaga - Naga kecil bijaksana yang menjaga gua"
  ]
}"""

        return instruction

    def _ollama_chat(self, _Logger, _Model_key, ProviderModel_name, _Messages_list, ModelOptions_dict, Seed_int, _FormatSchema_dict):
        import ollama
        CurrentModelOptions = ModelOptions_dict.copy() if ModelOptions_dict is not None else {}
        ValidParameters = ["mirostat", "mirostat_eta", "mirostat_tau", "num_ctx", "repeat_last_n", "repeat_penalty", "temperature", "seed", "tfs_z", "num_predict", "top_k", "top_p"]
        for key in list(CurrentModelOptions.keys()):
            if key not in ValidParameters: del CurrentModelOptions[key]
        CurrentModelOptions.setdefault("num_ctx", getattr(Writer.Config, "OLLAMA_CTX", 4096))
        CurrentModelOptions["seed"] = Seed_int
        if _FormatSchema_dict: CurrentModelOptions.update({"format": "json", "temperature": CurrentModelOptions.get("temperature", 0.0)})

        # Prepare chat parameters - always non-streaming
        chat_params = {
            "model": ProviderModel_name,
            "messages": _Messages_list,
            "stream": False,
            "options": CurrentModelOptions
        }

        # Disable thinking for Qwen models to prevent infinite loops
        if "qwen" in ProviderModel_name.lower():
            chat_params["think"] = False

        MaxRetries = getattr(Writer.Config, "MAX_OLLAMA_RETRIES", 2)
        for attempt in range(MaxRetries):
            try:
                client = self.Clients[_Model_key]

                # Always use non-streaming mode (streaming removed)
                response = client.chat(**chat_params)
                AssistantMessage = {"role": "assistant", "content": response["message"]["content"]}
                LastChunk = {"done": True}
                if "prompt_eval_count" in response:
                    LastChunk.update({
                        "prompt_eval_count": response["prompt_eval_count"],
                        "eval_count": response["eval_count"]
                    })

                FullResponseMessages = _Messages_list + [AssistantMessage]
                TokenUsage = None
                if LastChunk:
                    if Writer.Config.DEBUG:
                        _Logger.Log(f"LastChunk keys: {list(LastChunk.keys()) if isinstance(LastChunk, dict) else 'Not a dict'}", 6)
                        _Logger.Log(f"LastChunk 'done' status: {LastChunk.get('done', 'missing')}", 6)

                    if LastChunk.get("done"):
                        prompt_tokens = LastChunk.get("prompt_eval_count", 0)
                        completion_tokens = LastChunk.get("eval_count", 0)
                        TokenUsage = {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}
                        
                        if Writer.Config.DEBUG:
                            _Logger.Log(f"Token usage extracted: prompt={prompt_tokens}, completion={completion_tokens}", 6)
                    else:
                        _Logger.Log(f"Warning: LastChunk exists but 'done' is not True. Keys: {list(LastChunk.keys()) if isinstance(LastChunk, dict) else 'Not a dict'}", 6)
                else:
                    _Logger.Log("Warning: LastChunk is None - streaming may have been interrupted", 6)
                return FullResponseMessages, TokenUsage
            except Exception as e:
                _Logger.Log(f"Ollama API Error ({_Model_key}, Attempt {attempt+1}/{MaxRetries}): {e}", 7)
                if attempt + 1 >= MaxRetries: raise
                time.sleep(random.uniform(0.5,1.5) * (attempt + 1))
        raise Exception(f"Ollama chat failed for {_Model_key} after {MaxRetries} attempts.")

    def _google_chat(self, _Logger, _Model_key, ProviderModel_name, _Messages_list, ModelOptions_dict, Seed_int, _FormatSchema_dict):
        from google.genai.types import HarmCategory, HarmBlockThreshold
        Messages_transformed = [{"role": "user" if m["role"] == "system" else ("model" if m["role"] == "assistant" else m["role"]),
                                 "parts": [m["content"]]} for m in _Messages_list]

        safety_settings = {cat: HarmBlockThreshold.BLOCK_NONE for cat in HarmCategory if cat != HarmCategory.HARM_CATEGORY_UNSPECIFIED}
        gen_config = ModelOptions_dict.copy() if ModelOptions_dict is not None else {}
        gen_config["safety_settings"] = safety_settings
        if _FormatSchema_dict: gen_config.update({"response_mime_type": "application/json", "response_schema": _FormatSchema_dict, "temperature": gen_config.get("temperature", 0.0)})

        MaxRetries = getattr(Writer.Config, "MAX_GOOGLE_RETRIES", 2)
        for attempt in range(MaxRetries):
            try:
                client = self.Clients[_Model_key]
                GenResponse = client.generate_content(contents=Messages_transformed, stream=False, generation_config=gen_config)

                # Always use non-streaming mode (streaming removed)
                AssistantMessage = {"role": "assistant", "content": GenResponse.text}

                # Append assistant message to the original _Messages_list structure for consistency
                FinalMessages = _Messages_list + [AssistantMessage]
                TokenUsage = None
                usage_meta = getattr(GenResponse, 'usage_metadata', None)
                if usage_meta: TokenUsage = {"prompt_tokens": usage_meta.prompt_token_count, "completion_tokens": usage_meta.candidates_token_count}
                return FinalMessages, TokenUsage
            except Exception as e:
                _Logger.Log(f"Google API Error ({_Model_key}, Attempt {attempt+1}/{MaxRetries}): {e}", 7)
                if attempt + 1 >= MaxRetries: raise
                time.sleep(random.uniform(0.5,1.5) * (attempt + 1))
        raise Exception(f"Google chat failed for {_Model_key} after {MaxRetries} attempts.")

    def _openrouter_chat(self, _Logger, _Model_key, ProviderModel_name, _Messages_list, ModelOptions_dict, Seed_int, _FormatSchema_dict):
        Client = self.Clients[_Model_key]
        if hasattr(Client, 'model_name'): Client.model_name = ProviderModel_name
        elif hasattr(Client, 'model'): Client.model = ProviderModel_name

        ReqOptions = ModelOptions_dict.copy() if ModelOptions_dict is not None else {}
        if Seed_int is not None: ReqOptions["seed"] = Seed_int
        if _FormatSchema_dict: ReqOptions.update({"response_format": {"type": "json_object"}, "temperature": ReqOptions.get("temperature", 0.0)})

        MaxRetries = getattr(Writer.Config, "MAX_OPENROUTER_RETRIES", 2)
        for attempt in range(MaxRetries):
            try:
                # Always use non-streaming mode (streaming removed)
                response = Client.chat(messages=_Messages_list, stream=False, **ReqOptions)
                AssistantMessage = response.choices[0].message.content
                AssistantMessage = {"role": "assistant", "content": AssistantMessage}
                LastChunk = {"usage": response.usage} if hasattr(response, 'usage') else {}

                FullResponseMessages = _Messages_list + [AssistantMessage]
                TokenUsage = None
                if LastChunk and isinstance(LastChunk, dict) and "usage" in LastChunk:
                    usage = LastChunk["usage"]
                    TokenUsage = {"prompt_tokens": usage.get("prompt_tokens",0), "completion_tokens": usage.get("completion_tokens",0)}
                return FullResponseMessages, TokenUsage
            except Exception as e:
                _Logger.Log(f"OpenRouter API Error ({_Model_key}, Attempt {attempt+1}/{MaxRetries}): {e}", 7)
                if attempt + 1 >= MaxRetries: raise
                time.sleep(random.uniform(0.5,1.5) * (attempt + 1))
        raise Exception(f"OpenRouter chat failed for {_Model_key} after {MaxRetries} attempts.")

    def ChatResponse(self, _Logger, _Messages, _Model: str, _SeedOverride: int, _FormatSchema: dict = None):
        """Non-streaming response for Pydantic generation with user-friendly display"""
        TotalInputChars, EstInputTokens = 0, 0
        try:
            for msg in _Messages: content = msg.get("content",""); TotalInputChars += len(str(content))
            EstInputTokens = round(TotalInputChars / getattr(Writer.Config, "CHARS_PER_TOKEN_ESTIMATE", 4.5))
        except Exception as e: _Logger.Log(f"Token calculation error: {e}", 6)

        if Writer.Config.DEBUG:
            _Logger.Log(f"--- Chat Req to {_Model} (Seed: {_SeedOverride}) ---",6)
            for i,m in enumerate(_Messages): _Logger.Log(f"  Msg{i} {m.get('role')}: {str(m.get('content',''))[:100]}...",6)
            _Logger.Log(f"--- End Req for {_Model} ---",6)

        Provider, ProviderModelName, ModelHost, ModelOptions = self.GetModelAndProvider(_Model)
        SeedToUse = _SeedOverride if _SeedOverride != -1 else getattr(Writer.Config, "SEED", random.randint(0,999999))

        _Logger.Log(f"Model: '{ProviderModelName}' ({Provider}@{ModelHost or 'Default'}) | InChars: {TotalInputChars} (Est~{EstInputTokens}tok)",4)
        if EstInputTokens > getattr(Writer.Config, "TOKEN_WARNING_THRESHOLD", 20000):
            _Logger.Log(f"WARN: High Token Context: est~{EstInputTokens}tok for {_Model}",6)

        start_time = time.time()
        ResponseHandler = getattr(self, f"_{Provider}_chat", None)
        if not ResponseHandler: raise Exception(f"Unsupported provider: {Provider}")

        # _Messages passed to ResponseHandler is the current state of history for this attempt
        FullResponseMessages, TokenUsage = ResponseHandler(
            _Logger, _Model, ProviderModelName, _Messages, ModelOptions, SeedToUse, _FormatSchema
        )

        # Display user-friendly content for Pydantic responses
        if _FormatSchema and FullResponseMessages:
            # Get the last assistant message content
            if isinstance(FullResponseMessages, list) and len(FullResponseMessages) > 0:
                # Find the last assistant message in the list
                assistant_message = None
                for msg in reversed(FullResponseMessages):
                    if isinstance(msg, dict) and msg.get("role") == "assistant":
                        assistant_message = msg
                        break

                if assistant_message:
                    content = assistant_message.get("content", "")
                else:
                    content = str(FullResponseMessages[-1])  # Fallback
            else:
                content = str(FullResponseMessages) if FullResponseMessages else ""

            if content:
                if getattr(Writer.Config, 'DEBUG', False):
                    print(f"[DEBUG] FullResponseMessages: {FullResponseMessages}")
                    print(f"[DEBUG] Content extracted: {content[:100]}...")
                self._DisplayPydanticResponse(content, _FormatSchema, _Logger)
            else:
                if getattr(Writer.Config, 'DEBUG', False):
                    print(f"[DEBUG] No content extracted. FullResponseMessages: {FullResponseMessages}")

        gen_time = round(time.time() - start_time, 2)
        comp_tokens = TokenUsage.get("completion_tokens",0) if TokenUsage else 0
        tps = f"~{round(comp_tokens/gen_time,1)}tok/s" if comp_tokens and gen_time > 0.1 else "N/A"
        _Logger.Log(f"Response for {_Model} in {gen_time}s ({tps}). Tokens: {TokenUsage if TokenUsage else 'N/A'}",4)

        caller_frame = inspect.stack()[1]; caller_info = f"{os.path.basename(caller_frame.filename)}::{caller_frame.function}"
        try: _Logger.SaveLangchain(caller_info, FullResponseMessages) # FullResponseMessages includes the latest assistant response
        except Exception as e: _Logger.Log(f"Langchain save error from {caller_info}: {e}",6)

        return FullResponseMessages, TokenUsage, TotalInputChars, EstInputTokens


    def _DisplayPydanticResponse(self, full_content: str, schema: dict, _Logger):
        """Display user-friendly extracted content from Pydantic response"""

        try:
            import json
            response_data = json.loads(full_content)

            # Get schema title for better identification
            schema_title = schema.get('title', '').lower() if schema else ''

            # Enhanced model detection and display
            # Priority: Check for specific combinations first, then single fields
            if "context" in response_data and len(response_data) == 1:
                # BaseContext
                print(f"✓ Konteks: {response_data['context']}")

            elif "characters" in response_data and "locations" in response_data:
                # StoryElements
                char_count = len(response_data.get('characters', {}))
                loc_count = len(response_data.get('locations', {}))
                theme_count = len(response_data.get('themes', []))
                print(f"✓ Elemen Cerita: {char_count} karakter, {loc_count} lokasi, {theme_count} tema")

            elif "title" in response_data and "chapters" in response_data:
                # OutlineOutput
                print(f"✓ Judul: {response_data['title']}")
                print(f"✓ Bab: {len(response_data['chapters'])} bab dibuat")

            elif "title" in response_data and "genre" in response_data and "summary" in response_data:
                # StoryInfoOutput
                print(f"✓ Info Cerita: {response_data['title']} ({response_data['genre']})")

            elif "text" in response_data:
                # ChapterOutput (also covers ChapterWithScenes)
                if isinstance(response_data['text'], str):
                    word_count = len(response_data['text'].split())
                    chapter_num = response_data.get('chapter_number', '')
                    print(f"✓ Bab {chapter_num} di-generate: {word_count} kata" if chapter_num else f"✓ Bab di-generate: {word_count} kata")
                else:
                    print(f"✓ Response generated ({len(full_content)} chars)")

            elif "reasoning" in response_data and len(response_data) == 1:
                # ReasoningOutput
                reasoning = response_data['reasoning']
                word_count = len(reasoning.split())
                print(f"✓ Reasoning dibuat: {word_count} kata")

            elif "title" in response_data and len(response_data) == 1:
                # TitleOutput
                print(f"✓ Judul dibuat: {response_data['title']}")

            elif "scene_number" in response_data and "setting" in response_data:
                # SceneOutline
                scene_num = response_data['scene_number']
                setting = response_data['setting'][:50] if 'setting' in response_data and response_data['setting'] else ''
                print(f"✓ Scene {scene_num}: {setting}..." if setting else f"✓ Scene {scene_num} dibuat")

            elif "is_valid" in response_data:
                # SceneValidationOutput
                status = "Valid" if response_data['is_valid'] else "Invalid"
                error_count = len(response_data.get('errors', []))
                print(f"✓ Validasi scene: {status}" + (f" ({error_count} error)" if error_count else ""))

            elif "score" in response_data and "strengths" in response_data:
                # Evaluation outputs (OutlineEvaluationOutput, ChapterEvaluationOutput)
                print(f"✓ Evaluasi: Score {response_data['score']}/10")

            elif "feedback" in response_data and "rating" in response_data:
                # ReviewOutput
                print(f"✓ Review: Rating {response_data['rating']}/10")

            elif "scenes" in response_data and len(response_data) == 1:
                # SceneListSchema
                scene_count = len(response_data['scenes'])
                print(f"✓ Daftar {scene_count} scene dibuat")

            elif "IsComplete" in response_data and len(response_data) == 1:
                # CompleteSchema models (OutlineCompleteSchema, ChapterCompleteSchema)
                status = "Selesai" if response_data['IsComplete'] else "Belum selesai"
                print(f"✓ Status: {status}")

            elif "suggestions" in response_data and isinstance(response_data['suggestions'], list):
                # Legacy fallback for suggestions
                print(f"✓ {len(response_data['suggestions'])} saran dibuat")

            else:
                # Generic fallback with better identification
                model_name = schema_title.replace('output', '').replace('schema', '').title() if schema_title else 'Response'
                print(f"✓ {model_name} generated ({len(str(full_content))} chars)")

            # DEBUG mode: show full response
            if getattr(Writer.Config, 'DEBUG', False):
                print("\n--- Full Pydantic Response ---")
                print(json.dumps(response_data, indent=2))

        except Exception as e:
            # Fallback: if parsing fails, just show basic info
            print(f"✓ Response generated ({len(full_content)} chars)")
            if getattr(Writer.Config, 'DEBUG', False):
                print(f"Content: {full_content}")


    def BuildUserQuery(self, _Query: str):
        return {"role": "user", "content": _Query}

    def BuildSystemQuery(self, _Query: str):
        return {"role": "system", "content": _Query}

    def BuildAssistantQuery(self, _Query: str):
        return {"role": "assistant", "content": _Query}

    def GetLastMessageText(self, _Messages: list):
        if not _Messages or not isinstance(_Messages, list): return ""
        return str(_Messages[-1].get("content", "")) if isinstance(_Messages[-1], dict) else ""

    def RemoveThinkTagFromAssistantMessages(self, _Messages: list):
        """
        Remove <thinking> tags and their content from assistant messages.
        Handles both paired and unpaired thinking tags.

        Args:
            _Messages: List of message dictionaries with 'role' and 'content' keys

        Returns:
            List of messages with thinking tags removed from assistant messages
        """
        if not _Messages or not isinstance(_Messages, list):
            return _Messages

        result = []
        for message in _Messages:
            if not isinstance(message, dict):
                result.append(message)
                continue

            # Create a copy to avoid modifying original
            cleaned_msg = message.copy()

            # Only process assistant messages
            if cleaned_msg.get("role") == "assistant" and "content" in cleaned_msg:
                content = str(cleaned_msg["content"])
                # Use regex to remove thinking tags and everything between them
                import re
                # Remove paired thinking tags first
                pattern = r'<thinking>.*?</thinking>'
                cleaned_content = re.sub(pattern, '', content, flags=re.DOTALL)
                # Also handle unclosed thinking tags (edge case)
                if "<thinking>" in cleaned_content:
                    # For unpaired tag, remove everything from <thinking> to the end
                    # since we can't reliably determine thinking section boundaries
                    cleaned_content = re.sub(r'<thinking>.*', '', cleaned_content, flags=re.DOTALL)
                # Clean up any extra whitespace at start and multiple newlines
                cleaned_content = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_content)
                cleaned_content = cleaned_content.lstrip('\n\r ')
                cleaned_msg["content"] = cleaned_content

            result.append(cleaned_msg)

        return result

    def _ollama_embedding(self, _Logger, _Model_key, ProviderModel_name, _Texts: list):
        """Generate embeddings using Ollama"""
        import ollama

        client = self.Clients[_Model_key]
        embeddings = []
        total_tokens = 0

        for text in _Texts:
            try:
                # Use Ollama's embeddings endpoint
                response = client.embeddings(
                    model=ProviderModel_name,
                    prompt=text
                )
                embeddings.append(response['embedding'])
                # Ollama doesn't provide token usage for embeddings
                total_tokens += len(text.split())  # Rough estimate
            except Exception as e:
                _Logger.Log(f"Ollama embedding error: {e}", 7)
                raise

        return embeddings, {"prompt_tokens": total_tokens, "completion_tokens": 0}

    def _google_embedding(self, _Logger, _Model_key, ProviderModel_name, _Texts: list):
        """Generate embeddings using Gemini"""
        import google.genai as genai

        client = self.Clients[_Model_key]
        embeddings = []
        total_tokens = 0

        for text in _Texts:
            try:
                # Use Gemini's embedding API
                result = genai.embed_content(
                    model=f'models/{ProviderModel_name}',
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
                # Gemini doesn't provide token count, rough estimate
                total_tokens += len(text.split())
            except Exception as e:
                _Logger.Log(f"Gemini embedding error: {e}", 7)
                raise

        return embeddings, {"prompt_tokens": total_tokens, "completion_tokens": 0}

    def _openrouter_embedding(self, _Logger, _Model_key, ProviderModel_name, _Texts: list):
        """Generate embeddings using OpenRouter (OpenAI-compatible)"""
        import requests
        import json

        client = self.Clients[_Model_key]

        # Prepare request for embeddings (OpenAI-compatible format)
        headers = {
            "Authorization": f"Bearer {client.api_key}",
            "Content-Type": "application/json"
        }

        all_embeddings = []
        total_tokens = 0

        for text in _Texts:
            data = {
                "model": ProviderModel_name,
                "input": text
            }

            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/embeddings",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                result = response.json()
                all_embeddings.append(result['data'][0]['embedding'])
                # OpenRouter typically returns token usage
                total_tokens += result.get('usage', {}).get('prompt_tokens', len(text.split()))
            except Exception as e:
                _Logger.Log(f"OpenRouter embedding error: {e}", 7)
                raise

        return all_embeddings, {"prompt_tokens": total_tokens, "completion_tokens": 0}

    def GetModelAndProvider(self, _Model: str):
        if "://" not in _Model:
            return "ollama", _Model, getattr(Writer.Config, 'OLLAMA_HOST', None), None

        parsed = urlparse(_Model)
        Provider, Netloc, Path, Query = parsed.scheme, parsed.netloc, parsed.path.strip('/'), parsed.query
        Host, ModelName = None, Netloc

        if "@" in Netloc: ModelName, Host = Netloc.split("@", 1)

        ModelName = ModelName.strip('/') # Ensure no leading/trailing slashes from netloc part
        ModelName = unquote(ModelName)  # Decode URL encoded characters like %2F

        if Provider == "openrouter":
            ModelName = f"{ModelName}/{Path}" if Path and ModelName else (ModelName or Path)
        elif Provider == "ollama":
            if Path:
                if "@" in Path:
                    path_model_segment, host_from_path = Path.split('@',1)
                    path_model_segment = path_model_segment.strip('/')
                    ModelName = f"{ModelName}/{path_model_segment}" if ModelName and path_model_segment else (ModelName or path_model_segment)
                    Host = host_from_path
                elif Host or (parsed.port or ('.' in ModelName and ModelName != '.') or ModelName == 'localhost'): # ModelName from netloc was host
                     ModelName = Path
                else: # ModelName from netloc was model, Path is sub-model
                     ModelName = f"{ModelName}/{Path}" if ModelName and Path else (ModelName or Path)
            if Host is None: Host = getattr(Writer.Config, 'OLLAMA_HOST', None)

        Options = {k: (float(v[0]) if v[0].replace('.','',1).isdigit() else v[0]) for k,v in parse_qs(Query).items()}
        return Provider, ModelName.strip('/'), Host, Options if Options else None
