import Writer.Config
import dotenv
import inspect
import json
import os
import time
import random
import importlib
import importlib.metadata  # Add this import
import subprocess
import sys
from urllib.parse import parse_qs, urlparse
from pydantic import BaseModel  # Ditambahkan
import Writer.Config  # Pastikan ini diimpor
import json_repair  # Add near other imports at the top

dotenv.load_dotenv()


class Interface:

    def __init__(
        self,
        Models: list = [],
    ):
        self.Clients: dict = {}
        self.History = []
        self.LoadModels(Models)

    def ensure_package_is_installed(self, package_name):
        """Checks if a package is installed and installs it if not."""
        try:
            # Check if package metadata exists
            importlib.metadata.distribution(package_name)
            # If the above line doesn't raise PackageNotFoundError, the package is installed.
            # No need to print anything if it's found.
        except importlib.metadata.PackageNotFoundError:
            # Package is not found, print message and install
            print(f"Package {package_name} not found. Installing...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", package_name]
                )
                print(f"Package {package_name} installed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to install package {package_name}: {e}", file=sys.stderr)
                # Optionally re-raise or exit if installation is critical
                # raise e
            except Exception as e:
                print(
                    f"An unexpected error occurred during installation: {e}",
                    file=sys.stderr,
                )

    def LoadModels(self, Models: list):
        for Model in Models:
            if Model in self.Clients:
                continue
            else:
                Provider, ProviderModel, ModelHost, ModelOptions = (
                    self.GetModelAndProvider(Model)
                )
                print(
                    f"DEBUG: Loading Model {ProviderModel} from {Provider}@{ModelHost}"
                )

                if Provider == "ollama":
                    # Get ollama models (only once)
                    self.ensure_package_is_installed("ollama")
                    import ollama

                    OllamaHost = ModelHost if ModelHost is not None else None

                    # Check if availabel via ollama.show(Model)
                    # check if the model is in the list of models
                    try:
                        ollama.Client(host=OllamaHost).show(ProviderModel)
                        pass
                    except Exception as e:
                        print(
                            f"Model {ProviderModel} not found in Ollama models. Downloading..."
                        )
                        OllamaDownloadStream = ollama.Client(host=OllamaHost).pull(
                            ProviderModel, stream=True
                        )
                        for chunk in OllamaDownloadStream:
                            if "completed" in chunk and "total" in chunk:
                                OllamaDownloadProgress = (
                                    chunk["completed"] / chunk["total"]
                                )
                                completedSize = chunk["completed"] / 1024**3
                                totalSize = chunk["total"] / 1024**3
                                print(
                                    f"Downloading {ProviderModel}: {OllamaDownloadProgress * 100:.2f}% ({completedSize:.3f}GB/{totalSize:.3f}GB)",
                                    end="\r",
                                )
                            else:
                                print(f"{chunk['status']} {ProviderModel}", end="\r")
                        print("\n\n\n")

                    self.Clients[Model] = ollama.Client(host=OllamaHost)
                    print(f"OLLAMA Host is '{OllamaHost}'")

                elif Provider == "google":
                    # Validate Google API Key
                    if (
                        not "GOOGLE_API_KEY" in os.environ
                        or os.environ["GOOGLE_API_KEY"] == ""
                    ):
                        raise Exception(
                            "GOOGLE_API_KEY not found in environment variables"
                        )
                    self.ensure_package_is_installed("google-generativeai")
                    import google.generativeai as genai

                    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
                    self.Clients[Model] = genai.GenerativeModel(
                        model_name=ProviderModel
                    )

                elif Provider == "openai":
                    raise NotImplementedError("OpenAI API not supported")

                elif Provider == "openrouter":
                    if (
                        not "OPENROUTER_API_KEY" in os.environ
                        or os.environ["OPENROUTER_API_KEY"] == ""
                    ):
                        raise Exception(
                            "OPENROUTER_API_KEY not found in environment variables"
                        )
                    from Writer.Interface.OpenRouter import OpenRouter

                    self.Clients[Model] = OpenRouter(
                        api_key=os.environ["OPENROUTER_API_KEY"], model=ProviderModel
                    )

                elif Provider == "Anthropic":
                    raise NotImplementedError("Anthropic API not supported")

                else:
                    print(f"Warning, ")
                    raise Exception(f"Model Provider {Provider} for {Model} not found")

    def SafeGenerateText(
        self,
        _Logger,
        _Messages,
        _Model: str,
        _SeedOverride: int = -1,
        _FormatSchema: dict = None,  # Diubah dari _Format
        _MinWordCount: int = 1,
    ):
        """
        This function guarantees that the output will not be whitespace and meets minimum word count.
        """

        # Strip Empty Messages
        for i in range(len(_Messages) - 1, 0, -1):
            if _Messages[i]["content"].strip() == "":
                del _Messages[i]

        # Strip Empty Messages
        for i in range(len(_Messages) - 1, 0, -1):
            if _Messages[i]["content"].strip() == "":
                del _Messages[i]

        Retries = 0
        # Panggil ChatAndStreamResponse *sebelum* loop untuk percobaan pertama
        # Update unpack untuk menangkap 4 nilai
        NewMsgMessages, TokenUsage, InputChars, EstInputTokens = (
            self.ChatAndStreamResponse(  # Unpack 4 values
                _Logger, _Messages, _Model, _SeedOverride, _FormatSchema
            )
        )
        NewMsg = NewMsgMessages  # Keep variable name consistency if needed elsewhere

        # Loop untuk memeriksa dan mencoba lagi jika perlu
        # Inside the while loop, modify the retry call
        while (self.GetLastMessageText(NewMsg).strip() == "") or (
            len(self.GetLastMessageText(NewMsg).split(" ")) < _MinWordCount
        ):
            Retries += 1  # Tingkatkan penghitung retry

            # Log alasan retry
            if self.GetLastMessageText(NewMsg).strip() == "":
                _Logger.Log(
                    f"SafeGenerateText: Generation Failed Due To Empty (Whitespace) Response. Retry {Retries}/{Writer.Config.MAX_TEXT_RETRIES}",
                    7,
                )
            elif len(self.GetLastMessageText(NewMsg).split(" ")) < _MinWordCount:
                CurrentWordCount = len(self.GetLastMessageText(NewMsg).split(" "))
                _Logger.Log(
                    f"SafeGenerateText: Generation Failed Due To Short Response ({CurrentWordCount}, min is {_MinWordCount}). Retry {Retries}/{Writer.Config.MAX_TEXT_RETRIES}",
                    7,
                )

            # Periksa apakah batas retry tercapai
            if Retries >= Writer.Config.MAX_TEXT_RETRIES:
                _Logger.Log(
                    f"Max text retries ({Writer.Config.MAX_TEXT_RETRIES}) exceeded for whitespace/short response. Aborting text generation.",
                    7,
                )
                raise Exception(
                    f"Failed to generate valid text after {Writer.Config.MAX_TEXT_RETRIES} retries (whitespace/short response)."
                )  # Naikkan exception

            # Hapus respons asisten yang gagal (using NewMsg which is NewMsgMessages)
            if len(NewMsg) > 0 and NewMsg[-1]["role"] == "assistant":
                del NewMsg[-1]  # Delete from the list returned by ChatAndStreamResponse

            # --- AWAL LOGGING DIAGNOSTIK ---
            _Logger.Log(
                f"SafeGenerateText Retry {Retries}: Resending history. Last 2 messages:",
                6,
            )
            if len(_Messages) >= 2:
                _Logger.Log(
                    f"  - Role: {_Messages[-2]['role']}, Content: '{_Messages[-2]['content'][:100]}...'",
                    6,
                )  # Log 100 karakter pertama
                _Logger.Log(
                    f"  - Role: {_Messages[-1]['role']}, Content: '{_Messages[-1]['content'][:100]}...'",
                    6,
                )  # Log 100 karakter pertama
            elif len(_Messages) == 1:
                _Logger.Log(
                    f"  - Role: {_Messages[-1]['role']}, Content: '{_Messages[-1]['content'][:100]}...'",
                    6,
                )  # Log 100 karakter pertama
            else:
                _Logger.Log("  - History is empty?", 6)
            # --- AKHIR LOGGING DIAGNOSTIK ---

            # Coba lagi dengan seed acak baru
            # Update unpack untuk menangkap 4 nilai
            (
                NewMsgMessagesRetry,
                TokenUsageRetry,
                InputCharsRetry,
                EstInputTokensRetry,
            ) = self.ChatAndStreamResponse(  # Unpack 4 values
                _Logger, NewMsg, _Model, random.randint(0, 99999), _FormatSchema
            )
            NewMsg = NewMsgMessagesRetry
            # Update nilai untuk log akhir jika retry berhasil
            TokenUsage = TokenUsageRetry
            InputChars = InputCharsRetry
            EstInputTokens = EstInputTokensRetry

            # Hapus log token retry individual jika ada
            # if TokenUsageRetry:
            #     _Logger.Log(f"SafeGenerateText Retry Token Usage - Prompt: {TokenUsageRetry.get('prompt_tokens', 'N/A')}, Completion: {TokenUsageRetry.get('completion_tokens', 'N/A')}", 6)

        # --- HAPUS LOG LAMA INI ---
        # if TokenUsage:
        #     _Logger.Log(f"SafeGenerateText Final Token Usage - Prompt: {TokenUsage.get('prompt_tokens', 'N/A')}, Completion: {TokenUsage.get('completion_tokens', 'N/A')}", 6)
        # --- AKHIR HAPUS LOG LAMA ---

        # --- TAMBAHKAN LOG GABUNGAN BARU ---
        prompt_tokens_str = (
            TokenUsage.get("prompt_tokens", "N/A") if TokenUsage else "N/A"
        )
        completion_tokens_str = (
            TokenUsage.get("completion_tokens", "N/A") if TokenUsage else "N/A"
        )
        _Logger.Log(
            f"Text Call Stats: Input Chars={InputChars}, Est. Input Tokens={EstInputTokens} | Actual Tokens: Prompt={prompt_tokens_str}, Completion={completion_tokens_str}",
            6,
        )
        # --- AKHIR TAMBAHAN LOG GABUNGAN ---

        # Return the final, validated message list AND token usage
        return NewMsg, TokenUsage

    # --- START OF NEW PRIVATE HELPER METHODS ---
    def _ollama_chat(self, _Logger, _Model_key, ProviderModel_name, _Messages_list, ModelOptions_dict, Seed_int, _FormatSchema_dict):
        # Logic for Ollama will be moved here
        # Ensure 'import ollama' is available
        import ollama

        _Logger.Log(f"Executing _ollama_chat for {_Model_key}", 6)
        ProviderModel = ProviderModel_name # Already stripped of host by GetModelAndProvider

        ValidParameters = [
            "mirostat", "mirostat_eta", "mirostat_tau", "num_ctx", "repeat_last_n",
            "repeat_penalty", "temperature", "seed", "tfs_z", "num_predict", "top_k", "top_p",
        ]
        CurrentModelOptions = ModelOptions_dict.copy() if ModelOptions_dict is not None else {}

        for key in CurrentModelOptions:
            if key not in ValidParameters:
                # Log a warning instead of raising an error for flexibility, or make it strict
                _Logger.Log(f"Warning: Invalid Ollama parameter '{key}' found in ModelOptions for {_Model_key}.", 6)
                # raise ValueError(f"Invalid parameter: {key}")

        if "num_ctx" not in CurrentModelOptions:
            CurrentModelOptions["num_ctx"] = Writer.Config.OLLAMA_CTX

        CurrentModelOptions["seed"] = Seed_int # Ensure seed is passed to ollama options

        _Logger.Log(f"Using Ollama Model Options for {_Model_key}: {CurrentModelOptions}", 4)

        if _FormatSchema_dict is not None:
            CurrentModelOptions["format"] = "json" # Ollama uses "json" string for format when a schema is implied by usage
            if "temperature" not in CurrentModelOptions : # More deterministic for JSON
                CurrentModelOptions["temperature"] = 0.0
            _Logger.Log(f"Using Ollama Structured Output (format: json) for {_Model_key}", 4)

        MaxRetries = getattr(Writer.Config, "MAX_OLLAMA_RETRIES", 3)
        LastTokenUsage = None
        Messages_updated = _Messages_list[:] # Work on a copy

        while MaxRetries > 0:
            try:
                Stream = self.Clients[_Model_key].chat(
                    model=ProviderModel,
                    messages=Messages_updated,
                    stream=True,
                    options=CurrentModelOptions,
                )
                AssistantMessage, LastChunk = self.StreamResponse(Stream, "ollama")
                Messages_updated.append(AssistantMessage)

                if LastChunk and LastChunk.get("done"):
                    prompt_tokens = LastChunk.get("prompt_eval_count", 0)
                    completion_tokens = LastChunk.get("eval_count", 0)
                    LastTokenUsage = {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}
                    _Logger.Log(f"Ollama Token Usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}", 6)
                else:
                    _Logger.Log("Could not extract Ollama token usage from last chunk.", 6)
                    LastTokenUsage = None
                break
            except ollama.ResponseError as e:
                MaxRetries -= 1
                _Logger.Log(f"Exception During Ollama Generation/Stream for {_Model_key}: '{e}', {MaxRetries} Retries Remaining", 7)
                if MaxRetries <= 0:
                    _Logger.Log(f"Max Retries Exceeded During Ollama Generation for {_Model_key}, Aborting!", 7)
                    raise Exception(f"Ollama StreamResponse failed after retries for {_Model_key}: {e}")
                time.sleep(2)
            except Exception as e:
                _Logger.Log(f"Unexpected Exception During Ollama Stream Handling for {_Model_key}: '{e}'", 7)
                raise Exception(f"Ollama Stream Handling failed for {_Model_key}: {e}")

        return Messages_updated, LastTokenUsage

    def _google_chat(self, _Logger, _Model_key, ProviderModel_name, _Messages_list, ModelOptions_dict, Seed_int, _FormatSchema_dict):
        # Logic for Google will be moved here
        from google.generativeai.types import HarmCategory, HarmBlockThreshold # Specific import

        _Logger.Log(f"Executing _google_chat for {_Model_key}", 6)
        Messages_transformed = [{"role": m["role"], "parts": [m["content"]]} if isinstance(m["content"], str) else {"role": m["role"], "parts": m["content"]} for m in _Messages_list]

        for m in Messages_transformed:
            if "role" in m and m["role"] == "assistant":
                m["role"] = "model"
            if "role" in m and m["role"] == "system": # System messages become user messages for Google
                m["role"] = "user"

        MaxRetries = getattr(Writer.Config, "MAX_GOOGLE_RETRIES", 3)
        LastTokenUsage = None
        GeneratedContentResponse = None
        Messages_updated = Messages_transformed[:] # Work on the transformed copy

        safety_settings_val = {
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        }

        generation_config_dict = ModelOptions_dict.copy() if ModelOptions_dict is not None else {}
        generation_config_dict["safety_settings"] = safety_settings_val
        # Google's 'seed' parameter is part of the GenerationConfig.
        # However, google-genai python SDK currently doesn't directly support 'seed' in GenerationConfig object.
        # It might be supported for specific models or future SDK versions at API level.
        # For now, we acknowledge Seed_int but cannot directly pass it via documented SDK means.
        if Seed_int is not None:
             _Logger.Log(f"Google API does not directly support 'seed' via Python SDK's GenerationConfig for {_Model_key}. Seed {Seed_int} ignored.", 6)


        if _FormatSchema_dict is not None:
            generation_config_dict["response_mime_type"] = "application/json"
            generation_config_dict["response_schema"] = _FormatSchema_dict
            if "temperature" not in generation_config_dict:
                generation_config_dict["temperature"] = 0.0
            _Logger.Log(f"Using Google Structured Output with schema for {_Model_key}", 4)

        _Logger.Log(f"Using Google Generation Config for {_Model_key}: {generation_config_dict}", 4)

        retry_count = 0
        while True: # Original loop was `while True`, implies retries are handled by SDK or not explicitly here beyond first attempt.
                    # Let's stick to MaxRetries for consistency.
            try:
                GeneratedContentResponse = self.Clients[_Model_key].generate_content(
                    contents=Messages_updated, # Use the transformed list
                    stream=True,
                    generation_config=generation_config_dict,
                )
                AssistantMessage, _ = self.StreamResponse(GeneratedContentResponse, "google")
                Messages_updated.append(AssistantMessage)

                try:
                    if hasattr(GeneratedContentResponse, "usage_metadata"):
                        metadata = GeneratedContentResponse.usage_metadata
                        prompt_tokens = metadata.prompt_token_count
                        completion_tokens = metadata.candidates_token_count
                        LastTokenUsage = {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}
                        _Logger.Log(f"Google Token Usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}", 6)
                    else:
                        _Logger.Log("Google usage_metadata not found on response object.", 6)
                except Exception as meta_e:
                    _Logger.Log(f"Error accessing Google usage_metadata: {meta_e}", 7)

                break # Success
            except Exception as e:
                retry_count +=1
                if retry_count > MaxRetries:
                    _Logger.Log(f"Max Retries Exceeded During Google Generation for {_Model_key}, Aborting! Error: {e}", 7)
                    raise Exception(f"Google Generation Failed for {_Model_key} after retries: {e}")
                _Logger.Log(f"Exception During Google Generation for {_Model_key}: '{e}', {MaxRetries - retry_count} Retries Remaining", 7)
                time.sleep(2)

        # Transform messages back
        FinalMessages = []
        for m in Messages_updated:
            role = m["role"]
            if role == "model":
                role = "assistant"
            # Assuming 'parts' is always a list and we want its string content
            content = "".join(m["parts"]) if isinstance(m["parts"], list) else m["parts"]
            FinalMessages.append({"role": role, "content": content})

        return FinalMessages, LastTokenUsage

    def _openrouter_chat(self, _Logger, _Model_key, ProviderModel_name, _Messages_list, ModelOptions_dict, Seed_int, _FormatSchema_dict):
        # Logic for OpenRouter will be moved here
        _Logger.Log(f"Executing _openrouter_chat for {_Model_key}", 6)

        Client = self.Clients[_Model_key]
        Client.model = ProviderModel_name # ProviderModel_name is already just the model name

        CurrentModelOptions = ModelOptions_dict.copy() if ModelOptions_dict is not None else {}
        CurrentModelOptions["seed"] = Seed_int # Add seed to options

        openrouter_response_format = None
        if _FormatSchema_dict is not None:
            openrouter_response_format = {
                "type": "json_schema",
                "json_schema": {
                    "strict": True,
                    "schema": _FormatSchema_dict,
                },
            }
            _Logger.Log(f"Using OpenRouter Structured Output with schema for {_Model_key}", 4)
            if "temperature" not in CurrentModelOptions:
                CurrentModelOptions["temperature"] = 0.0

        if openrouter_response_format:
            CurrentModelOptions["response_format"] = openrouter_response_format

        # Parameter validation (example, can be expanded)
        # ValidParametersOpenRouter = ["max_tokens", "temperature", "top_p", "seed", "response_format", ...]
        # for key in CurrentModelOptions:
        #     if key not in ValidParametersOpenRouter:
        #         _Logger.Log(f"Warning: Potentially unsupported OpenRouter parameter '{key}' for {_Model_key}", 6)

        Client.set_params(**CurrentModelOptions)
        _Logger.Log(f"Using OpenRouter Model Options for {_Model_key}: {CurrentModelOptions}", 4)

        LastTokenUsage = None
        Messages_updated = _Messages_list[:] # Work on a copy

        try:
            Stream = Client.chat(messages=Messages_updated, stream=True) # Seed is set via set_params
            AssistantMessage, LastChunk = self.StreamResponse(Stream, "openrouter")
            Messages_updated.append(AssistantMessage)

            if LastChunk and isinstance(LastChunk, dict) and "usage" in LastChunk:
                usage_data = LastChunk["usage"]
                prompt_tokens = usage_data.get("prompt_tokens", 0)
                completion_tokens = usage_data.get("completion_tokens", 0)
                LastTokenUsage = {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}
                _Logger.Log(f"OpenRouter Token Usage (from stream) - Prompt: {prompt_tokens}, Completion: {completion_tokens}", 6)
            else:
                _Logger.Log("OpenRouter Token Usage: Not found in the last stream chunk.", 6)
        except Exception as e:
            _Logger.Log(f"Error during OpenRouter streaming for {_Model_key}: {e}", 7)
            Messages_updated.append({"role": "assistant", "content": f"Error: OpenRouter stream failed for {_Model_key}. {e}"})
            # raise # Optionally re-raise

        return Messages_updated, LastTokenUsage

    # --- END OF NEW PRIVATE HELPER METHODS ---

    def SafeGenerateJSON(
        self,
        _Logger,
        _Messages,
        _Model: str,
        _SeedOverride: int = -1,
        _FormatSchema: dict = None,  # Diubah dari _Format, _RequiredAttribs dihapus
    ):
        Retries = 0
        LastTokenUsage = None
        LastInputChars = 0  # Tambahkan ini
        LastEstInputTokens = 0  # Tambahkan ini
        while True:
            # Update unpack untuk menangkap 4 nilai
            ResponseMessages, TokenUsage, InputChars, EstInputTokens = (
                self.ChatAndStreamResponse(  # Unpack 4 values
                    _Logger,
                    _Messages,
                    _Model,
                    _SeedOverride,
                    _FormatSchema=_FormatSchema,
                )
            )
            # Simpan nilai dari iterasi ini
            LastTokenUsage = TokenUsage
            LastInputChars = InputChars
            LastEstInputTokens = EstInputTokens

            # Tambahkan blok ini untuk membersihkan markdown
            # --------------------------------------------------
            # Use ResponseMessages for subsequent processing
            RawResponseText = self.GetLastMessageText(ResponseMessages)
            CleanedResponseText = RawResponseText.strip()
            if CleanedResponseText.startswith("```json"):
                CleanedResponseText = CleanedResponseText[7:]  # Hapus ```json
            if CleanedResponseText.startswith("```"):
                CleanedResponseText = CleanedResponseText[3:]  # Hapus ```
            if CleanedResponseText.endswith("```"):
                CleanedResponseText = CleanedResponseText[:-3]  # Hapus ```
            CleanedResponseText = CleanedResponseText.strip()  # Hapus whitespace ekstra
            # --------------------------------------------------

            try:
                # --- AWAL BLOK EKSTRAKSI JSON ---
                # Coba cari blok JSON utama ({...} atau [...])
                # Ini membantu jika ada teks tambahan sebelum/sesudah JSON
                first_brace = CleanedResponseText.find("{")
                first_bracket = CleanedResponseText.find("[")
                last_brace = CleanedResponseText.rfind("}")
                last_bracket = CleanedResponseText.rfind("]")

                start_index = -1
                end_index = -1

                # Tentukan awal (brace atau bracket yang muncul pertama)
                if first_brace != -1 and first_bracket != -1:
                    start_index = min(first_brace, first_bracket)
                elif first_brace != -1:
                    start_index = first_brace
                elif first_bracket != -1:
                    start_index = first_bracket

                # Tentukan akhir (brace atau bracket yang cocok dengan awal)
                if start_index == first_brace and last_brace != -1:
                    end_index = last_brace
                elif start_index == first_bracket and last_bracket != -1:
                    end_index = last_bracket
                # Fallback jika hanya salah satu jenis penutup yang ditemukan
                elif last_brace != -1 and last_bracket != -1:
                    end_index = max(last_brace, last_bracket)
                elif last_brace != -1:
                    end_index = last_brace
                elif last_bracket != -1:
                    end_index = last_bracket

                if start_index != -1 and end_index != -1 and end_index > start_index:
                    CleanedResponseText = CleanedResponseText[
                        start_index : end_index + 1
                    ]
                    _Logger.Log(
                        f"Extracted potential JSON block: '{CleanedResponseText[:100]}...'",
                        6,
                    )  # Log potongan
                else:
                    _Logger.Log(
                        f"Could not reliably extract JSON block, using cleaned text as is.",
                        6,
                    )
                # --- AKHIR BLOK EKSTRAKSI JSON ---

                # Gunakan CleanedResponseText untuk parsing (yang mungkin sudah dipotong)
                # --- CHANGE THIS LINE ---
                # Replace standard json.loads with json_repair.loads
                # JSONResponse = json.loads(CleanedResponseText)
                JSONResponse = json_repair.loads(
                    CleanedResponseText
                )  # Use json_repair here
                # -----------------------

                # Validasi skema Pydantic jika perlu (opsional, karena Ollama seharusnya sudah melakukannya)
                # Jika Anda menggunakan Pydantic untuk validasi *setelah* menerima respons:
                # if _FormatSchema:
                #    # Anda perlu mengimpor BaseModel dari Pydantic di file ini
                #    # dan mungkin membuat instance model dari JSONResponse
                #    # Contoh: PydanticModel = YourSchemaModel(**JSONResponse)
                #    pass # Tambahkan validasi Pydantic di sini jika diinginkan

                # Validasi atribut tidak lagi diperlukan di sini jika skema digunakan
                # for _Attrib in _RequiredAttribs:
                #     JSONResponse[_Attrib]

                # --- TAMBAHKAN LOG GABUNGAN BARU ---
                prompt_tokens_str = (
                    LastTokenUsage.get("prompt_tokens", "N/A")
                    if LastTokenUsage
                    else "N/A"
                )
                completion_tokens_str = (
                    LastTokenUsage.get("completion_tokens", "N/A")
                    if LastTokenUsage
                    else "N/A"
                )
                _Logger.Log(
                    f"JSON Call Stats: Input Chars={LastInputChars}, Est. Input Tokens={LastEstInputTokens} | Actual Tokens: Prompt={prompt_tokens_str}, Completion={completion_tokens_str}",
                    6,
                )
                # --- AKHIR TAMBAHAN LOG GABUNGAN ---

                # Return yang berhasil
                return ResponseMessages, JSONResponse, LastTokenUsage

            except Exception as e:
                Retries += 1
                _Logger.Log(
                    f"JSON Error during parsing: {e}. Raw Response: '{RawResponseText}'. Retry {Retries}/{Writer.Config.MAX_JSON_RETRIES}",
                    7,
                )  # Log percobaan ulang

                # Periksa apakah batas retry tercapai
                if Retries >= Writer.Config.MAX_JSON_RETRIES:
                    _Logger.Log(
                        f"Max JSON retries ({Writer.Config.MAX_JSON_RETRIES}) exceeded. Aborting JSON generation.",
                        7,
                    )
                    raise Exception(
                        f"Failed to generate valid JSON after {Writer.Config.MAX_JSON_RETRIES} retries."
                    )  # Naikkan exception
                    # Return None, None, None # Or raise exception as above

                # Hapus pesan asisten yang gagal dari ResponseMessages
                if (
                    len(ResponseMessages) > 0
                    and ResponseMessages[-1]["role"] == "assistant"
                ):
                    del ResponseMessages[-1]
                # Update _Messages for the next retry iteration *if* ResponseMessages was based on it
                # It's safer to pass the modified list back into the next ChatAndStreamResponse call
                _Messages = ResponseMessages  # Ensure the list for the next loop iteration is the one without the failed assistant message

                # Mencoba lagi dengan seed baru dan skema yang sama pada iterasi berikutnya
                _SeedOverride = random.randint(
                    0, 99999
                )  # Gunakan seed baru untuk percobaan ulang
                # Tidak perlu memanggil ChatAndStreamResponse lagi di sini, loop akan melakukannya

    def ChatAndStreamResponse(
        self,
        _Logger,
        _Messages,
        _Model: str = "llama3",
        _SeedOverride: int = -1,
        _FormatSchema: dict = None,
    ):
        # --- COMMON INITIAL TASKS ---
        TotalInputChars = 0
        EstimatedInputTokens = 0
        try:
            for msg in _Messages:
                if isinstance(msg.get("content"), str): # Ensure content is a string
                    TotalInputChars += len(msg["content"])
                elif isinstance(msg.get("content"), list): # Handle Google's 'parts' list
                    for part in msg.get("content"):
                        if isinstance(part, str):
                            TotalInputChars += len(part)
                        elif isinstance(part, dict) and isinstance(part.get("text"), str):
                            TotalInputChars += len(part.get("text"))
            EstimatedInputTokens = round(TotalInputChars / 5)
        except Exception as e:
            _Logger.Log(f"Warning: Could not calculate input character/token count for {_Model}. Error: {e}", 6)

        if Writer.Config.DEBUG:
            _Logger.Log("--------- PROMPT CONTENT SENT TO LLM START ---------", 6)
            for i, msg in enumerate(_Messages):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                content_snippet_display = ""
                if isinstance(content, list):
                    parts_content = []
                    for item in content:
                        if isinstance(item, str):
                            parts_content.append(item)
                        elif isinstance(item, dict) and "text" in item: # Google structure
                            parts_content.append(item["text"])
                    content_snippet = "".join(parts_content)
                elif isinstance(content, str):
                    content_snippet = content
                else:
                    content_snippet = str(content) # Fallback for other types

                snippet_limit = 150
                if len(content_snippet) > snippet_limit:
                    content_snippet_display = content_snippet[:snippet_limit] + "..."
                else:
                    content_snippet_display = content_snippet
                content_snippet_display = content_snippet_display.replace("\n", " ")
                _Logger.Log(f"Message {i} - Role: {role}, Snippet: \"{content_snippet_display}\"", 6)
            _Logger.Log("--------- PROMPT CONTENT SENT TO LLM END -----------", 6)

        Provider, ProviderModelName, ModelHost, ModelOptionsDict = self.GetModelAndProvider(_Model)
        Seed = Writer.Config.SEED if _SeedOverride == -1 else _SeedOverride

        if Writer.Config.DEBUG and _Messages: # Simplified debug log for message history
             _Logger.Log(f"Message History (Count: {len(_Messages)}) being sent to {ProviderModelName} via {Provider}", 6)

        StartGeneration = time.time()
        # Log estimated tokens before the call
        _Logger.Log(f"Using Model '{ProviderModelName}' from '{Provider}@{ModelHost}' | Input Chars: {TotalInputChars} (Est. ~{EstimatedInputTokens}tok Context Length)", 4)
        if EstimatedInputTokens > 24000:
            _Logger.Log(f"Warning, Detected High Token Context Length of est. ~{EstimatedInputTokens}tok for {_Model}", 6)

        # --- DISPATCH TO PROVIDER-SPECIFIC HELPER ---
        LastTokenUsage = None
        # _Model is the original model key string e.g. "ollama://llama3"
        # ProviderModelName is just the model name e.g. "llama3"

        # Helpers expect _Messages to be in the standard format [{"role": ..., "content": ...}]
        # _google_chat will handle its own transformations.
        CurrentMessages = [m.copy() for m in _Messages] # Pass a shallow copy to helpers

        if Provider == "ollama":
            CurrentMessages, LastTokenUsage = self._ollama_chat(_Logger, _Model, ProviderModelName, CurrentMessages, ModelOptionsDict, Seed, _FormatSchema)
        elif Provider == "google":
            CurrentMessages, LastTokenUsage = self._google_chat(_Logger, _Model, ProviderModelName, CurrentMessages, ModelOptionsDict, Seed, _FormatSchema)
        elif Provider == "openrouter":
            CurrentMessages, LastTokenUsage = self._openrouter_chat(_Logger, _Model, ProviderModelName, CurrentMessages, ModelOptionsDict, Seed, _FormatSchema)
        elif Provider == "Anthropic":
            _Logger.Log(f"Anthropic API not supported in this version for model {_Model}.", 7)
            raise NotImplementedError(f"Anthropic API not supported for model {_Model}")
        else:
            _Logger.Log(f"Model Provider {Provider} for {_Model} not found.", 7)
            raise Exception(f"Model Provider {Provider} for {_Model} not found")

        _Messages = CurrentMessages # Update _Messages with the list returned by the helper

        # --- FINAL COMMON TASKS ---
        EndGeneration = time.time()
        GenerationTime = round(EndGeneration - StartGeneration, 2)

        # Calculate actual tokens per second if possible
        completion_tokens_for_tps = LastTokenUsage.get("completion_tokens", 0) if LastTokenUsage else 0
        tokens_per_second_str = "N/A"
        if completion_tokens_for_tps > 0 and GenerationTime > 0:
            tokens_per_second = round(completion_tokens_for_tps / GenerationTime, 2)
            tokens_per_second_str = f"~{tokens_per_second}tok/s"

        _Logger.Log(f"Generated Response for {_Model} in {GenerationTime}s ({tokens_per_second_str})", 4)

        CallStack: str = ""
        try:
            for Frame in inspect.stack()[1:]:
                CallStack += f"{Frame.function}."
            CallStack = CallStack[:-1].replace("<module>", "Main")
            _Logger.SaveLangchain(CallStack, _Messages) # _Messages is now the updated list
        except Exception as e:
            _Logger.Log(f"Error saving langchain history for {_Model}: {e}", 6)

        return _Messages, LastTokenUsage, TotalInputChars, EstimatedInputTokens

    def StreamResponse(self, _Stream, _Provider: str):
        Response: str = ""
        LastChunk = None  # Add this line
        PromptTokens = 0  # Add this line
        CompletionTokens = 0  # Add this line

        for chunk in _Stream:
            LastChunk = chunk  # Store the current chunk
            if _Provider == "ollama":
                # Check if 'message' and 'content' exist before accessing
                if chunk.get("message") and chunk["message"].get("content"):
                    ChunkText = chunk["message"]["content"]
                    Response += ChunkText
                    print(ChunkText, end="", flush=True)
                # No else needed, just skip if content isn't there (like in the final chunk)
            elif _Provider == "google":
                ChunkText = chunk.text
                Response += ChunkText
                print(ChunkText, end="", flush=True)
            # --- START MODIFICATION FOR OPENROUTER STREAMING ---
            elif _Provider == "openrouter":
                # chunk diharapkan berupa dictionary dari event SSE yang sudah diparsing
                # Contoh: {"id": ..., "choices": [{"index": 0, "delta": {"content": "some text"}, "finish_reason": null}]}
                if isinstance(chunk, dict):
                    # Periksa apakah chunk ini berisi informasi 'usage'
                    # Ini akan menjadi chunk terakhir dari stream menurut dokumentasi OpenRouter
                    if "usage" in chunk:
                        # LastChunk akan secara otomatis menyimpan chunk ini karena loop
                        # Tidak perlu tindakan khusus di sini, penanganan token akan dilakukan
                        # di ChatAndStreamResponse menggunakan LastChunk.
                        # Kita bisa menambahkan log di sini jika mau:
                        # print(f"\nOpenRouter Usage Chunk: {chunk['usage']}", file=sys.stderr)
                        pass # Biarkan LastChunk menangkapnya

                    choices = chunk.get("choices")
                    if choices and isinstance(choices, list) and len(choices) > 0:
                        delta = choices[0].get("delta")
                        if delta and isinstance(delta, dict):
                            ChunkText = delta.get("content")
                            if (
                                ChunkText is not None
                            ):  # Konten bisa berupa string kosong
                                Response += ChunkText
                                print(ChunkText, end="", flush=True)
                        # finish_reason bisa diperiksa di sini jika perlu
                        # finish_reason = choices[0].get("finish_reason")
                        # if finish_reason:
                        #     # Stream untuk choice ini selesai
                        #     pass
                else:
                    # Ini seharusnya tidak terjadi jika OpenRouter.py menghasilkan dict
                    # Bisa ditambahkan log jika diperlukan:
                    # print(f"OpenRouter Stream: Received unexpected chunk type: {type(chunk)}", file=sys.stderr)
                    pass
            # --- END MODIFICATION FOR OPENROUTER STREAMING ---
            # else: # Hapus atau komentari error untuk provider yang tidak didukung jika ada
            #     raise ValueError(f"Unsupported provider: {_Provider}")

        print("\n\n\n" if Writer.Config.DEBUG else "")

        # Token extraction logic moved to ChatAndStreamResponse

        # Return the message dictionary AND the last chunk
        return {
            "role": "assistant",
            "content": Response,
        }, LastChunk  # Return message AND last chunk

    def BuildUserQuery(self, _Query: str):
        return {"role": "user", "content": _Query}

    def BuildSystemQuery(self, _Query: str):
        return {"role": "system", "content": _Query}

    def BuildAssistantQuery(self, _Query: str):
        return {"role": "assistant", "content": _Query}

    def GetLastMessageText(self, _Messages: list):
        return _Messages[-1]["content"]

    def GetModelAndProvider(self, _Model: str):
        # Format is `Provider://Model@Host?param1=value2&param2=value2`
        # default to ollama if no provider is specified
        if "://" in _Model:
            # this should be a valid URL
            parsed = urlparse(_Model)
            print(parsed)
            Provider = parsed.scheme

            if "@" in parsed.netloc:
                Model, Host = parsed.netloc.split("@")

            elif Provider == "openrouter":
                Model = f"{parsed.netloc}{parsed.path}"
                Host = None

            elif "ollama" in _Model:
                if "@" in parsed.path:
                    Model = parsed.netloc + parsed.path.split("@")[0]
                    Host = parsed.path.split("@")[1]
                else:
                    Model = parsed.netloc
                    Host = Writer.Config.OLLAMA_HOST  # Gunakan nilai dari Config

            else:
                Model = parsed.netloc
                Host = None
            QueryParams = parse_qs(parsed.query)

            # Flatten QueryParams
            for key in QueryParams:
                QueryParams[key] = float(QueryParams[key][0])

            return Provider, Model, Host, QueryParams
        else:
            # legacy support for `Model` format
            return (
                "ollama",
                _Model,
                Writer.Config.OLLAMA_HOST,
                None,
            )  # Gunakan nilai dari Config
