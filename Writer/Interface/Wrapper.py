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
        # --- AWAL PERHITUNGAN INPUT ---
        TotalInputChars = 0
        EstimatedInputTokens = 0  # Tambahkan ini
        try:
            for msg in _Messages:
                if isinstance(msg.get("content"), str):
                    TotalInputChars += len(msg["content"])
            # Hitung estimasi token (gunakan pembagi 5 seperti log estimasi lainnya)
            EstimatedInputTokens = round(TotalInputChars / 5)
            # --- HAPUS LOG INI ---
            # _Logger.Log(f"Input Content Length (chars): {TotalInputChars} being sent to {_Model}", 6)
            # --- AKHIR HAPUS LOG INI ---
        except Exception as e:
            _Logger.Log(
                f"Warning: Could not calculate input character/token count. Error: {e}",
                7,
            )
        # --- AKHIR PERHITUNGAN INPUT ---

        # --- AWAL DEBUG LOGGING UNTUK KONTEN PROMPT ---
        if Writer.Config.DEBUG:
            _Logger.Log("--------- PROMPT CONTENT SENT TO LLM START ---------", 6)
            for i, msg in enumerate(_Messages):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if isinstance(content, list): # Handle kasus Google Gemini dengan 'parts'
                    try:
                        # Coba gabungkan 'parts' jika itu adalah list of strings atau dicts dengan 'text'
                        if all(isinstance(part, str) for part in content):
                            content_snippet = "".join(content)
                        elif all(isinstance(part, dict) and "text" in part for part in content):
                            content_snippet = "".join(part.get("text","") for part in content)
                        else: # Fallback jika struktur 'parts' tidak terduga
                            content_snippet = str(content)
                    except Exception:
                        content_snippet = str(content) # Fallback jika ada error saat memproses 'parts'
                elif isinstance(content, str):
                    content_snippet = content
                else: # Fallback jika content bukan string atau list yang dikenal
                    content_snippet = str(content)

                snippet_limit = 150  # Batas karakter untuk snippet
                if len(content_snippet) > snippet_limit:
                    snippet_display = content_snippet[:snippet_limit] + "..."
                else:
                    snippet_display = content_snippet
                # Ganti newline dengan spasi untuk tampilan log yang lebih ringkas
                snippet_display = snippet_display.replace("\n", " ") 
                _Logger.Log(f"Message {i} - Role: {role}, Snippet: \"{snippet_display}\"", 6)
            _Logger.Log("--------- PROMPT CONTENT SENT TO LLM END -----------", 6)
        # --- AKHIR DEBUG LOGGING UNTUK KONTEN PROMPT ---

        # --- Sisa kode fungsi dimulai di sini ---
        Provider, ProviderModel, ModelHost, ModelOptions = self.GetModelAndProvider(
            _Model
        )

        # Calculate Seed Information
        Seed = Writer.Config.SEED if _SeedOverride == -1 else _SeedOverride

        # Log message history if DEBUG is enabled
        if Writer.Config.DEBUG:
            print("--------- Message History START ---------")
            print("[")
            for Message in _Messages:
                print(f"{Message},\n----\n")
            print("]")
            print("--------- Message History END --------")

        StartGeneration = time.time()

        # Calculate estimated tokens
        TotalChars = len(str(_Messages))
        AvgCharsPerToken = 5  # estimated average chars per token
        EstimatedTokens = TotalChars / AvgCharsPerToken
        _Logger.Log(
            f"Using Model '{ProviderModel}' from '{Provider}@{ModelHost}' | (Est. ~{EstimatedTokens}tok Context Length)",
            4,
        )

        # Log if there's a large estimated tokens of context history
        if EstimatedTokens > 24000:
            _Logger.Log(
                f"Warning, Detected High Token Context Length of est. ~{EstimatedTokens}tok",
                6,
            )

        if Provider == "ollama":

            # remove host
            if "@" in ProviderModel:
                ProviderModel = ProviderModel.split("@")[0]

            # https://github.com/ollama/ollama/blob/main/docs/modelfile.md#valid-parameters-and-values
            ValidParameters = [
                "mirostat",
                "mirostat_eta",
                "mirostat_tau",
                "num_ctx",
                "repeat_last_n",
                "repeat_penalty",
                "temperature",
                "seed",
                "tfs_z",
                "num_predict",
                "top_k",
                "top_p",
            ]
            ModelOptions = ModelOptions if ModelOptions is not None else {}

            # Check if the parameters are valid
            for key in ModelOptions:
                if key not in ValidParameters:
                    raise ValueError(f"Invalid parameter: {key}")

            # Set the default num_ctx if not set by args
            if "num_ctx" not in ModelOptions:
                ModelOptions["num_ctx"] = Writer.Config.OLLAMA_CTX

            _Logger.Log(f"Using Ollama Model Options: {ModelOptions}", 4)

            # Menggunakan structured output jika skema disediakan
            if _FormatSchema is not None:
                ModelOptions["format"] = _FormatSchema
                # Set temperature to 0 for more deterministic structured output
                if "temperature" not in ModelOptions:
                    ModelOptions["temperature"] = 0
                _Logger.Log(f"Using Ollama Structured Output with schema", 4)
            # Hapus logika _Format == "json"

            # Tambahkan loop retry untuk Ollama
            import ollama  # Pastikan ollama diimpor

            # Gunakan konstanta dari Config jika ada, jika tidak gunakan default 3
            MaxRetries = getattr(Writer.Config, "MAX_OLLAMA_RETRIES", 3)
            LastTokenUsage = None  # Initialize token usage variable
            while MaxRetries > 0:
                try:
                    Stream = self.Clients[_Model].chat(
                        model=ProviderModel,
                        messages=_Messages,
                        stream=True,
                        options=ModelOptions,
                    )

                    # Capture both return values from StreamResponse
                    AssistantMessage, LastChunk = self.StreamResponse(
                        Stream, Provider
                    )  # Capture LastChunk
                    _Messages.append(AssistantMessage)

                    # --- RE-ADD OLLAMA TOKEN EXTRACTION LOGIC ---
                    if LastChunk and LastChunk.get("done"):
                        prompt_tokens = LastChunk.get("prompt_eval_count", 0)
                        completion_tokens = LastChunk.get("eval_count", 0)
                        LastTokenUsage = {
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                        }
                        _Logger.Log(
                            f"Ollama Token Usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}",
                            6,
                        )
                    else:
                        _Logger.Log(
                            "Could not extract Ollama token usage from last chunk.", 6
                        )
                        LastTokenUsage = None  # Set to None if extraction fails
                    # --- END OLLAMA TOKEN EXTRACTION LOGIC ---

                    break  # Exit loop on success

                except ollama.ResponseError as e:  # Tangkap error spesifik Ollama
                    MaxRetries -= 1
                    _Logger.Log(
                        f"Exception During Ollama Generation/Stream: '{e}', {MaxRetries} Retries Remaining",
                        7,
                    )
                    if MaxRetries <= 0:
                        _Logger.Log(
                            f"Max Retries Exceeded During Ollama Generation, Aborting!",
                            7,
                        )
                        # Naikkan exception jika retry habis
                        raise Exception(
                            f"Ollama StreamResponse failed after retries: {e}"
                        )
                    else:
                        # import time # Pastikan 'import time' ada di awal file
                        time.sleep(2)  # Jeda singkat sebelum mencoba lagi
                        continue  # Lanjutkan ke iterasi retry berikutnya
                except Exception as e:
                    # Tangani exception lain yang mungkin terjadi selama streaming (misal: koneksi)
                    # dan tidak terkait langsung dengan respons Ollama
                    _Logger.Log(
                        f"Unexpected Exception During Ollama Stream Handling: '{e}'", 7
                    )
                    # Langsung naikkan exception non-ResponseError
                    raise Exception(f"Ollama Stream Handling failed: {e}")

        elif Provider == "google":

            from google.generativeai.types import (
                HarmCategory,
                HarmBlockThreshold,
            )

            # replace "content" with "parts" for google
            _Messages = [{"role": m["role"], "parts": m["content"]} for m in _Messages]
            for m in _Messages:
                if "content" in m:
                    m["parts"] = m["content"]
                    del m["content"]
                if "role" in m and m["role"] == "assistant":
                    m["role"] = "model"
                    # Google doesn't support "system" role while generating content (only while instantiating the model)
                if "role" in m and m["role"] == "system":
                    m["role"] = "user"

            MaxRetries = 3  # Anda mungkin ingin memindahkan ini ke Writer.Config.MAX_GOOGLE_RETRIES
            LastTokenUsage = None
            GeneratedContentResponse = None

            # --- START MODIFICATION FOR STRUCTURED OUTPUT AND CONFIG ---
            # ModelOptions sudah tersedia dari self.GetModelAndProvider(_Model)

            safety_settings_val = {
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            }

            # Inisialisasi generation_config_dict dengan ModelOptions jika ada
            generation_config_dict = (
                ModelOptions.copy() if ModelOptions is not None else {}
            )

            # Tambahkan/Timpa safety_settings
            generation_config_dict["safety_settings"] = safety_settings_val

            if _FormatSchema is not None:
                generation_config_dict["response_mime_type"] = "application/json"
                generation_config_dict["response_schema"] = _FormatSchema
                _Logger.Log(f"Using Google Structured Output with schema", 4)
                # Atur temperature ke 0 untuk output terstruktur yang deterministik jika belum diatur
                if (
                    "temperature" not in generation_config_dict
                ):  # Periksa apakah sudah ada dari ModelOptions
                    generation_config_dict["temperature"] = 0.0

            _Logger.Log(
                f"Using Google Generation Config: {generation_config_dict}", 4
            )  # Log config yang digunakan

            # --- END MODIFICATION FOR STRUCTURED OUTPUT AND CONFIG ---

            while True:
                try:
                    GeneratedContentResponse = self.Clients[_Model].generate_content(
                        contents=_Messages,
                        stream=True,
                        # Hapus safety_settings dari sini
                        generation_config=generation_config_dict,  # Tambahkan generation_config
                    )
                    AssistantMessage, _ = self.StreamResponse(
                        GeneratedContentResponse, Provider
                    )
                    _Messages.append(AssistantMessage)

                    # --- Keep existing Google token extraction logic ---
                    try:
                        # Access usage_metadata after the stream is consumed
                        if hasattr(GeneratedContentResponse, "usage_metadata"):
                            metadata = GeneratedContentResponse.usage_metadata
                            prompt_tokens = metadata.prompt_token_count
                            completion_tokens = (
                                metadata.candidates_token_count
                            )  # Use candidates_token_count for completion
                            LastTokenUsage = {
                                "prompt_tokens": prompt_tokens,
                                "completion_tokens": completion_tokens,
                            }
                            _Logger.Log(
                                f"Google Token Usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}",
                                6,
                            )
                        else:
                            _Logger.Log(
                                "Google usage_metadata not found on response object.", 6
                            )
                            LastTokenUsage = None  # Set to None if metadata not found
                    except Exception as meta_e:
                        _Logger.Log(
                            f"Error accessing Google usage_metadata: {meta_e}", 7
                        )
                        LastTokenUsage = None  # Set to None on error
                    # --- AKHIR LOGIKA EKSTRAKSI TOKEN ---

                    break  # Exit loop on success
                except Exception as e:
                    # Make sure the exception is raised if retries are exceeded
                    # ... (keep existing retry logic) ...
                    if MaxRetries > 0:
                        _Logger.Log(
                            f"Exception During Generation '{e}', {MaxRetries} Retries Remaining",
                            7,
                        )
                        MaxRetries -= 1
                    else:
                        _Logger.Log(
                            f"Max Retries Exceeded During Generation, Aborting!", 7
                        )
                        raise Exception(
                            "Generation Failed, Max Retries Exceeded, Aborting"
                        )  # Ensure exception is raised

            # Replace "parts" back to "content" and "model" back to "assistant" for ALL messages
            # before logging or returning, to maintain consistent internal format.
            for m in _Messages:
                if "parts" in m:
                    m["content"] = m["parts"]
                    del m["parts"]
                if "role" in m and m["role"] == "model":
                    m["role"] = "assistant"
                # Juga konversi kembali 'user' yang mungkin berasal dari 'system' jika perlu
                # (Namun, ini mungkin tidak diperlukan jika 'system' tidak digunakan lagi setelah konversi awal)
                # Jika Anda ingin mempertahankan peran 'system' secara internal:
                # Anda perlu menyimpan peran asli sebelum konversi ke Google
                # atau menandainya dengan cara lain. Untuk saat ini, kita biarkan 'system' menjadi 'user'.

        elif Provider == "openai":
            raise NotImplementedError("OpenAI API not supported")

        elif Provider == "openrouter":

            # https://openrouter.ai/docs/parameters
            # Be aware that parameters depend on models and providers.
            ValidParameters = [
                "max_token",
                "presence_penalty",
                "frequency_penalty",
                "repetition_penalty",
                "response_format",
                "temperature",
                "seed",
                "top_k",
                "top_p",
                "top_a",
                "min_p",
            ]
            ModelOptions = ModelOptions if ModelOptions is not None else {}

            Client = self.Clients[_Model]
            # Client.set_params(**ModelOptions) # ModelOptions might conflict with structured output, handle carefully
            Client.model = ProviderModel
            print(ProviderModel)

            # --- START MODIFICATION ---
            openrouter_response_format = None
            if _FormatSchema is not None:
                # Construct the response_format payload for OpenRouter
                # The schema itself is expected to be in _FormatSchema
                # We need to wrap it as per OpenRouter's documentation
                openrouter_response_format = {
                    "type": "json_schema",
                    "json_schema": {
                        # "name": "your_schema_name", # Name is optional, can be omitted or derived
                        "strict": True,  # Recommended by OpenRouter docs
                        "schema": _FormatSchema,  # This is the Pydantic schema
                    },
                }
                _Logger.Log(f"Using OpenRouter Structured Output with schema", 4)
                # Ensure temperature is low for deterministic structured output, if not already set by ModelOptions
                if "temperature" not in ModelOptions:  # Check ModelOptions first
                    ModelOptions["temperature"] = 0.0  # Set to float

            # Apply ModelOptions and the constructed response_format
            # We need to be careful not to overwrite response_format if it's part of ModelOptions
            # and _FormatSchema was not provided.
            # A safer way is to merge them, giving priority to the structured output if _FormatSchema is present.

            final_params_for_openrouter = (
                ModelOptions.copy() if ModelOptions is not None else {}
            )

            if openrouter_response_format:
                final_params_for_openrouter["response_format"] = (
                    openrouter_response_format
                )
            elif (
                "response_format" not in final_params_for_openrouter
            ):  # If not set by ModelOptions and no _FormatSchema
                final_params_for_openrouter["response_format"] = None

            Client.set_params(**final_params_for_openrouter)
            # --- END MODIFICATION ---

            # --- START MODIFICATION FOR STREAMING ---
            try:
                # Panggil chat dengan stream=True
                Stream = Client.chat(messages=_Messages, seed=Seed, stream=True)

                # Proses stream menggunakan self.StreamResponse
                AssistantMessage, LastChunk = self.StreamResponse(
                    Stream, Provider
                )  # Provider adalah "openrouter"

                _Messages.append(AssistantMessage)

                # Ekstrak token usage dari LastChunk jika tersedia
                LastTokenUsage = None # Default ke None
                if LastChunk and isinstance(LastChunk, dict) and "usage" in LastChunk:
                    usage_data = LastChunk["usage"]
                    prompt_tokens = usage_data.get("prompt_tokens", 0)
                    completion_tokens = usage_data.get("completion_tokens", 0)
                    LastTokenUsage = {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                    }
                    _Logger.Log(
                        f"OpenRouter Token Usage (from stream) - Prompt: {prompt_tokens}, Completion: {completion_tokens}",
                        6,
                    )
                    # Anda juga bisa log 'cost' jika mau: cost = usage_data.get("cost")
                else:
                    _Logger.Log(
                        "OpenRouter Token Usage: Not found in the last stream chunk.", 6
                    )

            except Exception as e:
                _Logger.Log(f"Error during OpenRouter streaming: {e}", 7)
                # Tambahkan pesan error dummy atau naikkan exception jika diperlukan
                _Messages.append(
                    {
                        "role": "assistant",
                        "content": f"Error: OpenRouter stream failed. {e}",
                    }
                )
                LastTokenUsage = None
                # Pertimbangkan untuk menaikkan kembali exception jika ini adalah error fatal
                # raise
            # --- END MODIFICATION FOR STREAMING ---

        elif Provider == "Anthropic":
            raise NotImplementedError("Anthropic API not supported")

        else:
            raise Exception(f"Model Provider {Provider} for {_Model} not found")

        # Log the time taken to generate the response
        EndGeneration = time.time()
        _Logger.Log(
            f"Generated Response in {round(EndGeneration - StartGeneration, 2)}s (~{round(EstimatedTokens / (EndGeneration - StartGeneration), 2)}tok/s)",
            4,
        )

        CallStack: str = ""
        for Frame in inspect.stack()[1:]:
            CallStack += f"{Frame.function}."
        CallStack = CallStack[:-1].replace("<module>", "Main")
        _Logger.SaveLangchain(CallStack, _Messages)
        # --- MODIFIKASI RETURN STATEMENT ---
        # Kembalikan juga TotalInputChars dan EstimatedInputTokens
        # return _Messages, LastTokenUsage # Baris lama
        return (
            _Messages,
            LastTokenUsage,
            TotalInputChars,
            EstimatedInputTokens,
        )  # Baris baru

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
