import Writer.Config
import dotenv
import inspect
import json
import os
import time
import random
import importlib
import subprocess
import sys
from urllib.parse import parse_qs, urlparse
from pydantic import BaseModel # Ditambahkan
import Writer.Config # Pastikan ini diimpor

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
        try:
            importlib.import_module(package_name)
        except ImportError:
            print(f"Package {package_name} not found. Installing...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package_name]
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
        _FormatSchema: dict = None, # Diubah dari _Format
        _MinWordCount: int = 1,
    ):
        """
        This function guarantees that the output will not be whitespace and meets minimum word count.
        """

        # Strip Empty Messages
        for i in range(len(_Messages) - 1, 0, -1):
            if _Messages[i]["content"].strip() == "":
                del _Messages[i]

        Retries = 0 # Tambahkan penghitung retry
        # Panggil ChatAndStreamResponse *sebelum* loop untuk percobaan pertama
        NewMsg = self.ChatAndStreamResponse(
            _Logger, _Messages, _Model, _SeedOverride, _FormatSchema
        )

        # Loop untuk memeriksa dan mencoba lagi jika perlu
        while (self.GetLastMessageText(NewMsg).strip() == "") or (
            len(self.GetLastMessageText(NewMsg).split(" ")) < _MinWordCount
        ):
            Retries += 1 # Tingkatkan penghitung retry

            # Log alasan retry
            if self.GetLastMessageText(NewMsg).strip() == "":
                _Logger.Log(
                    f"SafeGenerateText: Generation Failed Due To Empty (Whitespace) Response. Retry {Retries}/{Writer.Config.MAX_TEXT_RETRIES}",
                    7,
                )
            elif len(self.GetLastMessageText(NewMsg).split(" ")) < _MinWordCount:
                CurrentWordCount = len(self.GetLastMessageText(NewMsg).split(' '))
                _Logger.Log(
                    f"SafeGenerateText: Generation Failed Due To Short Response ({CurrentWordCount}, min is {_MinWordCount}). Retry {Retries}/{Writer.Config.MAX_TEXT_RETRIES}",
                    7,
                )

            # Periksa apakah batas retry tercapai
            if Retries >= Writer.Config.MAX_TEXT_RETRIES:
                _Logger.Log(f"Max text retries ({Writer.Config.MAX_TEXT_RETRIES}) exceeded for whitespace/short response. Aborting text generation.", 7)
                raise Exception(f"Failed to generate valid text after {Writer.Config.MAX_TEXT_RETRIES} retries (whitespace/short response).") # Naikkan exception

            # Hapus respons asisten yang gagal
            if len(_Messages) > 0 and _Messages[-1]["role"] == "assistant":
                del _Messages[-1]

            # --- AWAL LOGGING DIAGNOSTIK ---
            _Logger.Log(f"SafeGenerateText Retry {Retries}: Resending history. Last 2 messages:", 6)
            if len(_Messages) >= 2:
                _Logger.Log(f"  - Role: {_Messages[-2]['role']}, Content: '{_Messages[-2]['content'][:100]}...'", 6) # Log 100 karakter pertama
                _Logger.Log(f"  - Role: {_Messages[-1]['role']}, Content: '{_Messages[-1]['content'][:100]}...'", 6) # Log 100 karakter pertama
            elif len(_Messages) == 1:
                _Logger.Log(f"  - Role: {_Messages[-1]['role']}, Content: '{_Messages[-1]['content'][:100]}...'", 6) # Log 100 karakter pertama
            else:
                 _Logger.Log("  - History is empty?", 6)
            # --- AKHIR LOGGING DIAGNOSTIK ---

            # Coba lagi dengan seed acak baru
            NewMsg = self.ChatAndStreamResponse(
                _Logger, _Messages, _Model, random.randint(0, 99999), _FormatSchema
            )

        return NewMsg # Kembalikan NewMsg (yang merupakan _Messages yang berhasil)

    def SafeGenerateJSON(
        self,
        _Logger,
        _Messages,
        _Model: str,
        _SeedOverride: int = -1,
        _FormatSchema: dict = None, # Diubah dari _Format, _RequiredAttribs dihapus
    ):
        Retries = 0 # Tambahkan penghitung retry
        while True:
            # Menggunakan ChatAndStreamResponse langsung dengan skema
            Response = self.ChatAndStreamResponse(
                 _Logger, _Messages, _Model, _SeedOverride, _FormatSchema=_FormatSchema
            )

            # Tambahkan blok ini untuk membersihkan markdown
            # --------------------------------------------------
            RawResponseText = self.GetLastMessageText(Response)
            CleanedResponseText = RawResponseText.strip()
            if CleanedResponseText.startswith("```json"):
                CleanedResponseText = CleanedResponseText[7:] # Hapus ```json
            if CleanedResponseText.startswith("```"):
                 CleanedResponseText = CleanedResponseText[3:] # Hapus ```
            if CleanedResponseText.endswith("```"):
                CleanedResponseText = CleanedResponseText[:-3] # Hapus ```
            CleanedResponseText = CleanedResponseText.strip() # Hapus whitespace ekstra
            # --------------------------------------------------

            try:
                # Gunakan CleanedResponseText untuk parsing
                JSONResponse = json.loads(CleanedResponseText) # Modifikasi baris ini

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

                # Now return the json
                return Response, JSONResponse

            except Exception as e:
                Retries += 1 # Tingkatkan penghitung retry
                _Logger.Log(f"JSON Error during parsing: {e}. Raw Response: '{RawResponseText}'. Retry {Retries}/{Writer.Config.MAX_JSON_RETRIES}", 7) # Log percobaan ulang

                # Periksa apakah batas retry tercapai
                if Retries >= Writer.Config.MAX_JSON_RETRIES:
                    _Logger.Log(f"Max JSON retries ({Writer.Config.MAX_JSON_RETRIES}) exceeded. Aborting JSON generation.", 7)
                    raise Exception(f"Failed to generate valid JSON after {Writer.Config.MAX_JSON_RETRIES} retries.") # Naikkan exception

                # Hapus pesan terakhir (permintaan) dan respons gagal dari riwayat
                # Asumsi: ChatAndStreamResponse menambahkan respons ke _Messages. Jika tidak, baris ini mungkin perlu dihapus.
                if len(_Messages) > 0 and _Messages[-1]["role"] == "assistant":
                     del _Messages[-1] # Hapus respons gagal dari LLM

                # Mencoba lagi dengan seed baru dan skema yang sama pada iterasi berikutnya
                _SeedOverride = random.randint(0, 99999) # Gunakan seed baru untuk percobaan ulang
                # Tidak perlu memanggil ChatAndStreamResponse lagi di sini, loop akan melakukannya

    def ChatAndStreamResponse(
        self,
        _Logger,
        _Messages,
        _Model: str = "llama3",
        _SeedOverride: int = -1,
        _FormatSchema: dict = None, # Diubah dari _Format
    ):
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

            Stream = self.Clients[_Model].chat(
                model=ProviderModel,
                messages=_Messages,
                stream=True,
                options=ModelOptions,
            )
            MaxRetries = 3

            while True:
                try:
                    _Messages.append(self.StreamResponse(Stream, Provider))
                    break
                except Exception as e:
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
                            "Generation Failed, Max Retires Exceeded, Aborting"
                        )

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

            MaxRetries = 3
            while True:
                try:
                    Stream = self.Clients[_Model].generate_content(
                        contents=_Messages,
                        stream=True,
                        safety_settings={
                            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        },
                    )
                    _Messages.append(self.StreamResponse(Stream, Provider))
                    break
                except Exception as e:
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
                            "Generation Failed, Max Retires Exceeded, Aborting"
                        )

            # Replace "parts" back to "content" for generalization
            # and replace "model" with "assistant"
            for m in _Messages:
                if "parts" in m:
                    m["content"] = m["parts"]
                    del m["parts"]
                if "role" in m and m["role"] == "model":
                    m["role"] = "assistant"

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
            Client.set_params(**ModelOptions)
            Client.model = ProviderModel
            print(ProviderModel)

            Response = Client.chat(messages=_Messages, seed=Seed)
            _Messages.append({"role": "assistant", "content": Response})

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
        return _Messages

    def StreamResponse(self, _Stream, _Provider: str):
        Response: str = ""
        for chunk in _Stream:
            if _Provider == "ollama":
                ChunkText = chunk["message"]["content"]
            elif _Provider == "google":
                ChunkText = chunk.text
            else:
                raise ValueError(f"Unsupported provider: {_Provider}")

            Response += ChunkText
            print(ChunkText, end="", flush=True)

        print("\n\n\n" if Writer.Config.DEBUG else "")
        return {"role": "assistant", "content": Response}

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
                    Host = Writer.Config.OLLAMA_HOST # Gunakan nilai dari Config

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
            return "ollama", _Model, Writer.Config.OLLAMA_HOST, None # Gunakan nilai dari Config
