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
from urllib.parse import parse_qs, urlparse
import json_repair

dotenv.load_dotenv()

class Interface:
    def __init__(self, Models: list = []):
        self.Clients: dict = {}
        self.LoadModels(Models)

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
                self.ensure_package_is_installed("google-generativeai")
                import google.generativeai as genai
                genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
                self.Clients[Model] = genai.GenerativeModel(model_name=ProviderModelName)
            elif Provider == "openrouter":
                if not os.environ.get("OPENROUTER_API_KEY"): raise Exception("OPENROUTER_API_KEY missing")
                from Writer.Interface.OpenRouter import OpenRouter
                self.Clients[Model] = OpenRouter(api_key=os.environ["OPENROUTER_API_KEY"], model_name=ProviderModelName)
            else: raise NotImplementedError(f"Provider {Provider} not supported")

    def SafeGenerateText(self, _Logger, _Messages, _Model: str, _SeedOverride: int = -1, _FormatSchema: dict = None, _MinWordCount: int = 1, _max_retries_override: int = None):
        CurrentMessages = [m.copy() for m in _Messages]
        # Strip initial empty messages from the end of the copied list
        while CurrentMessages and not CurrentMessages[-1]["content"].strip(): del CurrentMessages[-1]
        if not CurrentMessages: # If all messages were empty or became empty
             _Logger.Log("SafeGenerateText: Initial message list empty after stripping. Raising error as this indicates problematic input.", 7)
             raise ValueError("Initial message list results in empty history after stripping.")

        Retries = 0
        max_r = _max_retries_override if _max_retries_override is not None else Writer.Config.MAX_TEXT_RETRIES

        while Retries < max_r:
            CurrentSeed = _SeedOverride if Retries == 0 else random.randint(0, 99999)
            ResponseMessagesList, TokenUsage, InputChars, EstInputTokens = self.ChatAndStreamResponse(
                _Logger, CurrentMessages, _Model, CurrentSeed, _FormatSchema
            )

            last_response_text = self.GetLastMessageText(ResponseMessagesList)
            is_empty = not last_response_text.strip()
            word_count = len(last_response_text.split())
            is_too_short = word_count < _MinWordCount


            if not is_empty and not is_too_short: # Valid response
                _Logger.Log(f"Text Call Stats: Input Chars={InputChars}, Est. Input Tokens={EstInputTokens} | Actual Tokens: Prompt={TokenUsage.get('prompt_tokens', 'N/A') if TokenUsage else 'N/A'}, Completion={TokenUsage.get('completion_tokens', 'N/A') if TokenUsage else 'N/A'}",6)
                return ResponseMessagesList, TokenUsage

            log_retry_reason = "Empty Response" if is_empty else f"Short Response ({word_count} words, min {_MinWordCount})"
            # Log with Retries as 0-indexed for "attempt number", so Retries+1 for "retry number"
            _Logger.Log(f"SafeGenerateText: Generation Failed Due To {log_retry_reason}. Retry {Retries + 1}/{max_r}", 7)

            Retries += 1 # Crucially, increment after checking the current attempt but before next iteration

            # Prepare CurrentMessages for the next retry
            CurrentMessages = ResponseMessagesList
            if CurrentMessages and CurrentMessages[-1]["role"] == "assistant":
                del CurrentMessages[-1]
            if not CurrentMessages or not any(m['role'] == 'user' for m in CurrentMessages):
                _Logger.Log("SafeGenerateText: Message history for retry was invalidated. Restoring original messages for next attempt.", 6)
                CurrentMessages = [m.copy() for m in _Messages] # Reset to original state

        _Logger.Log(f"SafeGenerateText: All {max_r} retries failed. RAISING EXCEPTION.", 7)
        raise Exception(f"Failed to generate valid text after {max_r} retries")

    def SafeGenerateJSON(self, _Logger, _Messages, _Model: str, _SeedOverride: int = -1, _FormatSchema: dict = None, _max_retries_override: int = None):
        CurrentMessages = [m.copy() for m in _Messages]
        Retries = 0
        max_r = _max_retries_override if _max_retries_override is not None else Writer.Config.MAX_JSON_RETRIES

        while Retries < max_r:
            CurrentSeed = _SeedOverride if Retries == 0 else random.randint(0, 99999)
            # ResponseMessagesList is the full history *after* the LLM call in this iteration
            ResponseMessagesList, TokenUsage, InputChars, EstInputTokens = self.ChatAndStreamResponse(
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

    def _ollama_chat(self, _Logger, _Model_key, ProviderModel_name, _Messages_list, ModelOptions_dict, Seed_int, _FormatSchema_dict):
        import ollama
        CurrentModelOptions = ModelOptions_dict.copy() if ModelOptions_dict is not None else {}
        ValidParameters = ["mirostat", "mirostat_eta", "mirostat_tau", "num_ctx", "repeat_last_n", "repeat_penalty", "temperature", "seed", "tfs_z", "num_predict", "top_k", "top_p"]
        for key in list(CurrentModelOptions.keys()):
            if key not in ValidParameters: del CurrentModelOptions[key]
        CurrentModelOptions.setdefault("num_ctx", getattr(Writer.Config, "OLLAMA_CTX", 4096))
        CurrentModelOptions["seed"] = Seed_int
        if _FormatSchema_dict: CurrentModelOptions.update({"format": "json", "temperature": CurrentModelOptions.get("temperature", 0.0)})

        MaxRetries = getattr(Writer.Config, "MAX_OLLAMA_RETRIES", 2)
        for attempt in range(MaxRetries):
            try:
                client = self.Clients[_Model_key]
                Stream = client.chat(model=ProviderModel_name, messages=_Messages_list, stream=True, options=CurrentModelOptions)
                AssistantMessage, LastChunk = self.StreamResponse(Stream, "ollama")
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
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
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
                GenResponse = client.generate_content(contents=Messages_transformed, stream=True, generation_config=gen_config)
                AssistantMessage, _ = self.StreamResponse(GenResponse, "google")
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
                Stream = Client.chat(messages=_Messages_list, stream=True, **ReqOptions)
                AssistantMessage, LastChunk = self.StreamResponse(Stream, "openrouter")
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

    def ChatAndStreamResponse(self, _Logger, _Messages, _Model: str, _SeedOverride: int, _FormatSchema: dict):
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

        gen_time = round(time.time() - start_time, 2)
        comp_tokens = TokenUsage.get("completion_tokens",0) if TokenUsage else 0
        tps = f"~{round(comp_tokens/gen_time,1)}tok/s" if comp_tokens and gen_time > 0.1 else "N/A"
        _Logger.Log(f"Response for {_Model} in {gen_time}s ({tps}). Tokens: {TokenUsage if TokenUsage else 'N/A'}",4)

        caller_frame = inspect.stack()[1]; caller_info = f"{os.path.basename(caller_frame.filename)}::{caller_frame.function}"
        try: _Logger.SaveLangchain(caller_info, FullResponseMessages) # FullResponseMessages includes the latest assistant response
        except Exception as e: _Logger.Log(f"Langchain save error from {caller_info}: {e}",6)

        return FullResponseMessages, TokenUsage, TotalInputChars, EstInputTokens

    def StreamResponse(self, _Stream, _Provider: str):
        Content, LastChunk = "", None
        for chunk in _Stream:
            LastChunk, ChunkText = chunk, None
            if _Provider == "ollama": ChunkText = chunk.get("message",{}).get("content")
            elif _Provider == "google": ChunkText = getattr(chunk, 'text', None)
            elif _Provider == "openrouter": ChunkText = chunk.get("choices",[{}])[0].get("delta",{}).get("content")
            if ChunkText: Content += ChunkText; print(ChunkText, end="", flush=True)
        print("" if not Writer.Config.DEBUG else "\n\n\n", flush=True)
        return {"role": "assistant", "content": Content}, LastChunk

    def BuildUserQuery(self, _Query: str):
        return {"role": "user", "content": _Query}

    def BuildSystemQuery(self, _Query: str):
        return {"role": "system", "content": _Query}

    def BuildAssistantQuery(self, _Query: str):
        return {"role": "assistant", "content": _Query}

    def GetLastMessageText(self, _Messages: list):
        if not _Messages or not isinstance(_Messages, list): return ""
        return str(_Messages[-1].get("content", "")) if isinstance(_Messages[-1], dict) else ""

    def GetModelAndProvider(self, _Model: str):
        if "://" not in _Model:
            return "ollama", _Model, getattr(Writer.Config, 'OLLAMA_HOST', None), None

        parsed = urlparse(_Model)
        Provider, Netloc, Path, Query = parsed.scheme, parsed.netloc, parsed.path.strip('/'), parsed.query
        Host, ModelName = None, Netloc

        if "@" in Netloc: ModelName, Host = Netloc.split("@", 1)

        ModelName = ModelName.strip('/') # Ensure no leading/trailing slashes from netloc part

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
