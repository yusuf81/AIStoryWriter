import Writer.Config
import dotenv
import inspect
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
    from pydantic import ValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


def _is_validation_or_missing_error(error) -> bool:
    """
    Robust error classification using FieldConstants.

    Args:
        error: Exception to classify

    Returns:
        bool: True if error is validation or missing field error
    """
    try:
        from Writer.FieldConstants import classify_error

        error_types = classify_error(str(error))
        return "missing_field" in error_types or "validation_error" in error_types
    except (ImportError, Exception):
        # Fallback to simple check if FieldConstants not available
        if error is None:
            return False
        error_str = str(error).lower()
        return "missing" in error_str or "validation" in error_str


dotenv.load_dotenv()


class Interface:
    # Language strings for i18n support
    # Centralized dictionary of all translatable strings used in format instructions,
    # validation error messages, and constraint explanations.
    _LANGUAGE_STRINGS = {
        'en': {
            'json_schema_header': "=== JSON SCHEMA (REFERENCE ONLY) ===",
            'json_schema_note': "This defines the structure. DO NOT repeat the schema in your response!",
            'your_response_header': "=== YOUR RESPONSE (JSON ONLY) ===",
            'provide_json_only': "Provide ONLY the JSON data below. DO NOT include explanations or the schema.",
            'required_fields': "Required fields:",
            'optional_fields': "Optional fields:",
            'more_optional_fields': "... and {count} more optional fields",
            'example_format': 'Example format: {{"field1": "value", "field2": 123}}',
            'important_return_only': "IMPORTANT: Return ONLY the JSON data, not the schema!",
            'validation_constraints_header': "=== VALIDATION CONSTRAINTS (IMPORTANT) ===",
            'constraint_reasoning_max': "'{field}': Maximum {max_len} characters. Keep your reasoning concise and focused - verbose explanations will be rejected. Aim for clarity over length.",
            'constraint_word_count': "'{field}': Must match actual text word count within ±{tolerance} words. Be accurate but don't obsess over exact counts.",
            'constraint_min_length': "'{field}': Each name must be at least {min_len} characters. Avoid single-letter placeholders.",
            'important_constraints': "IMPORTANT CONSTRAINTS:",
            'validation_error_header': "Your response had validation errors. Please correct these fields:",
            'validation_error_footer': "Important: Return ONLY the corrected JSON data. Do NOT include explanations or other text.",
            'error_missing': "This field is required but was not provided",
            'error_too_short': "{msg} (you provided {actual_len} characters)",
            'error_expected_type': "Expected {expected_type} (you provided: {input_val})",
            'hint_single_json': "Hint: Ensure response is single JSON object, not multiple objects. DO NOT include schema in response.",
            'hint_required_fields': "Hint: Ensure all required fields are present and correct.",
            'example_string_array': '["String 1", "String 2"]',
            'example_label': "Example",
            'required_label': "Required",
            'optional_label': "Optional",
            'array_of_strings_required': "array of strings, Required",
            'array_of_objects_required': "array of objects, Required",
            'array_of_strings_optional': "array of strings, Optional",
            'array_of_objects_optional': "array of objects, Optional",
            'story_elements_example_label': 'For example:',
            'story_elements_example': '''{
    "title": "The Dragon's Treasure Cave",
    "genre": "Fantasy Adventure",
    "themes": ["courage", "friendship", "self-discovery"],
    "characters": {
        "Main Character(s)": [
            {
                "name": "Rian",
                "physical_description": "Young explorer with determined eyes and weathered gear.",
                "personality": "Brave, curious, and kind-hearted.",
                "background": "Village boy seeking adventure and treasure.",
                "motivation": "To prove himself and find the legendary dragon's treasure."
            }
        ],
        "Supporting Characters": [
            {
                "name": "The Dragon",
                "physical_description": "Small green dragon with gleaming emerald scales.",
                "personality": "Wise and protective, with a playful spirit.",
                "background": "Ancient guardian of the cave's treasure for centuries.",
                "role in the story": "Tests the hero's worthiness and becomes an unexpected friend."
            }
        ]
    },
    "pacing": "Moderate with moments of excitement and wonder.",
    "style": "Descriptive narrative with vivid imagery and emotional depth",
    "plot_structure": {
        "exposition": "Rian hears legends of the dragon's treasure cave in his village.",
        "rising_action": "Rian journeys through the forest and discovers the hidden cave entrance.",
        "climax": "Rian faces the dragon in a test of character rather than strength.",
        "falling_action": "The dragon reveals the true nature of the treasure.",
        "resolution": "Rian gains wisdom and friendship instead of gold."
    },
    "settings": {
        "Village": {
            "time": "Medieval fantasy era",
            "location": "Small mountain village",
            "culture": "Close-knit community with oral traditions",
            "mood": "Warm and hopeful"
        },
        "Dragon's Cave": {
            "time": "Timeless",
            "location": "Deep within ancient mountains",
            "culture": "Ancient magical realm",
            "mood": "Mysterious and awe-inspiring"
        }
    },
    "conflict": "External conflict between hero and antagonist over the treasure",
    "symbolism": [{"symbol": "Treasure", "meaning": "Symbol of achievement and self-worth"}],
    "resolution": "The hero learns that true treasure is wisdom and friendship, not material wealth."
}''',
            'field_descriptions': {
                # StoryElements
                'title': 'Story title',
                'genre': 'Story genre category',
                'themes': 'Central themes of the story',
                'characters': 'Character lists by type with detailed information...',
                'pacing': 'Story pacing speed (e.g., slow, moderate, fast)...',
                'style': 'Language style description...',
                'plot_structure': 'Plot elements (exposition, rising action, climax, ...',
                'settings': 'Setting details with time, location, culture, mood...',
                'conflict': 'Central conflict of the story',
                'symbolism': 'Symbols and their meanings',
                'resolution': 'Story resolution or ending direction',
                # OutlineOutput
                'theme': 'Central theme of the story',
                'chapters': 'List of chapter outlines',
                'character_list': 'List of main characters',
                'character_details': 'Character descriptions',
                'setting': 'Story setting details',
                'target_chapter_count': 'Target number of chapters',
                # ChapterOutput
                'text': 'Full chapter text content',
                'word_count': 'Total word count',
                'scenes': 'Scene descriptions',
                'characters_present': 'Characters in this chapter',
                'chapter_number': 'Chapter number',
                'chapter_title': 'Chapter title',
            },
        },
        'id': {
            'json_schema_header': "=== SKEMA JSON (HANYA REFERENSI) ===",
            'json_schema_note': "Ini mendefinisikan struktur. JANGAN ulangi skema dalam respons Anda!",
            'your_response_header': "=== RESPONS ANDA (HANYA JSON) ===",
            'provide_json_only': "Berikan HANYA data JSON di bawah. JANGAN sertakan penjelasan atau skema.",
            'required_fields': "Field wajib:",
            'optional_fields': "Field opsional:",
            'more_optional_fields': "... dan {count} field opsional lainnya",
            'example_format': 'Format contoh: {{"field1": "nilai", "field2": 123}}',
            'important_return_only': "PENTING: Kembalikan HANYA data JSON, bukan skemanya!",
            'validation_constraints_header': "=== BATASAN VALIDASI (PENTING) ===",
            'constraint_reasoning_max': "'{field}': Maksimum {max_len} karakter. Buat reasoning Anda ringkas dan fokus - penjelasan yang bertele-tele akan ditolak. Utamakan kejelasan daripada panjang.",
            'constraint_word_count': "'{field}': Harus sesuai dengan jumlah kata teks sebenarnya dalam rentang ±{tolerance} kata. Akurat tapi jangan terlalu fokus pada hitungan yang tepat.",
            'constraint_min_length': "'{field}': Setiap nama harus minimal {min_len} karakter. Hindari placeholder satu huruf.",
            'important_constraints': "BATASAN PENTING:",
            'validation_error_header': "Respons Anda memiliki kesalahan validasi. Harap perbaiki field-field berikut:",
            'validation_error_footer': "Penting: Kembalikan HANYA data JSON yang sudah diperbaiki. JANGAN sertakan penjelasan atau teks lain.",
            'error_missing': "Field ini wajib tetapi tidak disediakan",
            'error_too_short': "{msg} (Anda memberikan {actual_len} karakter)",
            'error_expected_type': "Diharapkan {expected_type} (Anda memberikan: {input_val})",
            'hint_single_json': "Petunjuk: Pastikan respons adalah objek JSON tunggal, bukan beberapa objek. JANGAN sertakan skema dalam respons.",
            'hint_required_fields': "Petunjuk: Pastikan semua field wajib ada dan benar.",
            'example_string_array': '["String 1", "String 2"]',
            'example_label': "Contoh",
            'required_label': "Wajib",
            'optional_label': "Opsional",
            'array_of_strings_required': "array of strings, Wajib",
            'array_of_objects_required': "array of objects, Wajib",
            'array_of_strings_optional': "array of strings, Opsional",
            'array_of_objects_optional': "array of objects, Opsional",
            'story_elements_example_label': 'Contoh:',
            'story_elements_example': '''{
    "title": "Gua Harta Karun Naga",
    "genre": "Petualangan Fantasi",
    "themes": ["keberanian", "persahabatan", "penemuan-diri"],
    "characters": {
        "Karakter Utama": [
            {
                "name": "Rian",
                "physical_description": "Penjelajah muda dengan mata penuh tekad dan peralatan yang sudah usang.",
                "personality": "Berani, penasaran, dan baik hati.",
                "background": "Anak desa yang mencari petualangan dan harta karun.",
                "motivation": "Ingin membuktikan dirinya dan menemukan harta karun legendaris."
            }
        ],
        "Karakter Pendukung": [
            {
                "name": "Naga",
                "physical_description": "Naga hijau kecil dengan sisik zamrud yang berkilauan.",
                "personality": "Bijaksana dan protektif, dengan semangat yang ceria.",
                "background": "Penjaga kuno harta gua selama berabad-abad.",
                "role in the story": "Menguji kelayakan pahlawan dan menjadi teman yang tak terduga."
            }
        ]
    },
    "pacing": "Sedang dengan momen kegembiraan dan keajaiban.",
    "style": "Narasi deskriptif dengan citraan yang hidup dan kedalaman emosional",
    "plot_structure": {
        "exposition": "Rian mendengar legenda gua harta karun naga di desanya.",
        "rising_action": "Rian melakukan perjalanan melalui hutan dan menemukan pintu masuk gua tersembunyi.",
        "climax": "Rian menghadapi naga dalam ujian karakter, bukan kekuatan.",
        "falling_action": "Naga mengungkapkan sifat sejati harta karun.",
        "resolution": "Rian memperoleh kebijaksanaan dan persahabatan daripada emas."
    },
    "settings": {
        "Desa": {
            "time": "Era fantasi abad pertengahan",
            "location": "Desa kecil di pegunungan",
            "culture": "Komunitas erat dengan tradisi lisan",
            "mood": "Hangat dan penuh harapan"
        },
        "Gua Naga": {
            "time": "Abadi",
            "location": "Jauh di dalam pegunungan kuno",
            "culture": "Alam magis kuno",
            "mood": "Misterius dan menakjubkan"
        }
    },
    "conflict": "Konflik eksternal antara pahlawan dan antagonis tentang harta karun",
    "symbolism": [{"symbol": "Harta Karun", "meaning": "Simbol pencapaian dan harga diri"}],
    "resolution": "Pahlawan belajar bahwa harta sejati adalah kebijaksanaan dan persahabatan, bukan kekayaan materi."
}''',
            'field_descriptions': {
                # StoryElements
                'title': 'Judul cerita',
                'genre': 'Kategori genre cerita',
                'themes': 'Tema sentral cerita',
                'characters': 'Daftar karakter berdasarkan tipe dengan informasi detail...',
                'pacing': 'Kecepatan alur cerita (misalnya, lambat, sedang, cepat)...',
                'style': 'Deskripsi gaya bahasa...',
                'plot_structure': 'Elemen plot (eksposisi, aksi meningkat, klimaks, ...',
                'settings': 'Detail latar dengan waktu, lokasi, budaya, suasana...',
                'conflict': 'Konflik sentral cerita',
                'symbolism': 'Simbol dan maknanya',
                'resolution': 'Resolusi cerita atau arah akhir',
                # OutlineOutput
                'theme': 'Tema sentral cerita',
                'chapters': 'Daftar outline bab',
                'character_list': 'Daftar karakter utama',
                'character_details': 'Deskripsi karakter',
                'setting': 'Detail latar cerita',
                'target_chapter_count': 'Target jumlah bab',
                # ChapterOutput
                'text': 'Konten teks bab lengkap',
                'word_count': 'Jumlah kata total',
                'scenes': 'Deskripsi adegan',
                'characters_present': 'Karakter di bab ini',
                'chapter_number': 'Nomor bab',
                'chapter_title': 'Judul bab',
            },
        }
    }

    def __init__(self, Models: list = []):
        self.Clients: dict = {}
        self.LoadModels(Models)

    def _get_retry_limit(self, override: int = None) -> int:  # type: ignore[assignment]
        """DRY helper: Get retry limit with safe fallback to MAX_PYDANTIC_RETRIES.

        Args:
            override: Optional explicit retry limit override

        Returns:
            int: Retry limit to use (override if provided, else config value, else 5)
        """
        if override is not None:
            return override
        return getattr(Writer.Config, 'MAX_PYDANTIC_RETRIES', 5)

    def _get_text(self, key: str, **kwargs) -> str:
        """Get language-specific text string with optional formatting.

        This helper method retrieves translated text based on the current language setting.
        Supports string formatting with keyword arguments.

        Args:
            key: The text key to retrieve from _LANGUAGE_STRINGS
            **kwargs: Optional keyword arguments for string formatting

        Returns:
            str: Translated text (formatted if kwargs provided), empty string if key missing
        """
        # Get current language, fallback to 'en' if not set or invalid
        lang = self.language if hasattr(self, 'language') else 'en'

        # Get language dict, fallback to English if language invalid
        lang_dict = self._LANGUAGE_STRINGS.get(lang, self._LANGUAGE_STRINGS['en'])

        # Get text from key, return empty string if missing
        text = lang_dict.get(key, '')

        # Apply formatting if kwargs provided
        if kwargs:
            return text.format(**kwargs)
        return text

    def _get_field_description(self, field_name: str, fallback_description: str) -> str:
        """Get translated field description with fallback to original.

        Retrieves language-specific field description from _LANGUAGE_STRINGS['field_descriptions'].
        Falls back to original description if translation not found.

        Args:
            field_name: The field name to look up
            fallback_description: The original description from Pydantic model

        Returns:
            str: Translated description if available, otherwise fallback description
        """
        # Get current language, fallback to 'en' if not set or invalid
        lang = self.language if hasattr(self, 'language') else 'en'

        # Get language dict, fallback to English if language invalid
        lang_dict = self._LANGUAGE_STRINGS.get(lang, self._LANGUAGE_STRINGS['en'])

        # Get field_descriptions dict
        descriptions = lang_dict.get('field_descriptions', {})

        # Return translated description or fallback
        return descriptions.get(field_name, fallback_description)

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

    def _build_response_format(self, FormatSchema_dict: dict = None) -> dict:  # type: ignore[assignment]
        """
        Build response_format dict for providers that support structured outputs.
        Supports both JSON Schema and basic JSON object formats.

        Args:
            FormatSchema_dict: JSON Schema dict or basic format specification

        Returns:
            dict: response_format configuration for API call
        """
        if FormatSchema_dict is None:
            return {}

        if (isinstance(FormatSchema_dict, dict) and
            'properties' in FormatSchema_dict and
                FormatSchema_dict['properties']):
            # Full JSON Schema support (only if has non-empty properties)
            return {
                "type": "json_schema",
                "json_schema": FormatSchema_dict,
                "strict": True
            }
        else:
            # Basic JSON object format (existing behavior) - for empty dict or non-schema
            return {"type": "json_object"}

    def LoadModels(self, Models: list):
        for Model in Models:
            if Model in self.Clients:
                continue
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
                        for _ in pull_stream:
                            pass
                        print(f"\nPull attempt for {ProviderModelName} finished.")
                    except Exception as pull_e:
                        print(f"Failed to pull {ProviderModelName}: {pull_e}", file=sys.stderr)
                        continue
                self.Clients[Model] = ollama.Client(host=OllamaHost)
            elif Provider == "google":
                if not os.environ.get("GOOGLE_API_KEY"):
                    raise Exception("GOOGLE_API_KEY missing")
                self.ensure_package_is_installed("google-genai")
                import google.genai as genai  # type: ignore[misc]
                genai.configure(api_key=os.environ["GOOGLE_API_KEY"])  # type: ignore[reportAttributeAccessIssue]
                self.Clients[Model] = genai.GenerativeModel(model_name=ProviderModelName)  # type: ignore[reportAttributeAccessIssue, misc]
            elif Provider == "openrouter":
                if not os.environ.get("OPENROUTER_API_KEY"):
                    raise Exception("OPENROUTER_API_KEY missing")
                from Writer.Interface.OpenRouter import OpenRouter
                self.Clients[Model] = OpenRouter(api_key=os.environ["OPENROUTER_API_KEY"], model=ProviderModelName)  # type: ignore
            else:
                raise NotImplementedError(f"Provider {Provider} not supported")

        # Language detection for i18n support
        import Writer.Config as Config
        self.language = getattr(Config, 'NATIVE_LANGUAGE', 'en') or 'en'

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
    def SafeGenerateText_DEPRECATED(self, _Logger, _Messages, _Model: str, _SeedOverride: int = -1, _FormatSchema: dict = None, _MinWordCount: int = 1, _max_retries_override: int = None):  # type: ignore[assignment]
        """DEPRECATED: This method is no longer used. Use SafeGeneratePydantic instead."""
        raise DeprecationWarning("SafeGenerateText is deprecated. Use SafeGeneratePydantic instead.")

    def SafeGenerateJSON(self, _Logger, _Messages, _Model: str, _SeedOverride: int = -1, _FormatSchema: dict = None, _max_retries_override: int = None):  # type: ignore[assignment]
        CurrentMessages = [m.copy() for m in _Messages]
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
            if CleanedResponseText.startswith("```json"):
                CleanedResponseText = CleanedResponseText[7:]
            if CleanedResponseText.startswith("```"):
                CleanedResponseText = CleanedResponseText[3:]
            if CleanedResponseText.endswith("```"):
                CleanedResponseText = CleanedResponseText[:-3]
            CleanedResponseText = CleanedResponseText.strip()

            try:
                if not CleanedResponseText:
                    raise ValueError("Cleaned response is empty.")

                # More robust JSON extraction
                first_brace = CleanedResponseText.find("{")
                first_bracket = CleanedResponseText.find("[")

                if first_brace == -1 and first_bracket == -1:  # No JSON start characters
                    raise ValueError("No JSON object or array start found in response.")

                start_index = -1
                if first_brace != -1 and first_bracket != -1:
                    start_index = min(first_brace, first_bracket)
                elif first_brace != -1:
                    start_index = first_brace
                else:
                    start_index = first_bracket  # Must be first_bracket != -1

                # If a start char is found, try to find its corresponding end char
                if start_index != -1:
                    is_object = CleanedResponseText[start_index] == '{'
                    expected_end_char = '}' if is_object else ']'
                    # Attempt to find the matching end character. This is simplified; robust parsing is hard.
                    # For now, json_repair will handle most structural issues.
                    # We just try to narrow down the string to the most likely JSON part.
                    last_end_char_idx = CleanedResponseText.rfind(expected_end_char)
                    if last_end_char_idx > start_index:
                        CleanedResponseText = CleanedResponseText[start_index: last_end_char_idx + 1]
                    # else, we might have a truncated JSON or other issues, let json_repair try

                JSONResponse = json_repair.loads(CleanedResponseText)
                token_info = TokenUsage if TokenUsage else "N/A (streaming incomplete)"
                _Logger.Log(f"JSON Call Stats: ... Tokens: {token_info}", 6)
                return ResponseMessagesList, JSONResponse, TokenUsage  # Success

            except Exception as e:
                _Logger.Log(f"SafeGenerateJSON: Parse Error: '{e}'. Raw: '{RawResponseText[:100]}...'. Cleaned: '{CleanedResponseText[:100]}...'. Retry {Retries + 1}/{max_r}", 7)
                Retries += 1
                CurrentMessages = ResponseMessagesList  # Use history from the failed attempt
                if CurrentMessages and CurrentMessages[-1]["role"] == "assistant":
                    del CurrentMessages[-1]
                if not CurrentMessages or not any(m['role'] == 'user' for m in CurrentMessages):
                    CurrentMessages = [m.copy() for m in _Messages]  # Reset

        _Logger.Log(f"SafeGenerateJSON: All {max_r} retries failed. RAISING EXCEPTION.", 7)
        raise Exception(f"Failed to generate valid JSON after {max_r} retries")

    def SafeGeneratePydantic(self, _Logger, _Messages, _Model: str, _PydanticModel: type, _SeedOverride: int = -1, _max_retries_override: int = None):  # type: ignore[assignment]
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

            except ValidationError as ve:
                # Handle Pydantic validation errors with targeted error feedback
                if attempt < max_attempts - 1:
                    _Logger.Log(f"Attempt {attempt + 1} failed: Pydantic validation error. Retrying with error feedback...", 5)

                    # Build targeted error message (no schema structure)
                    error_message = self._build_validation_error_message(ve, _PydanticModel.__name__)
                    _Logger.Log(f"Validation errors:\n{error_message}", 5)

                    # Add error feedback to conversation for retry
                    messages_for_parsing.append({
                        "role": "user",
                        "content": error_message
                    })

                    # Add delay before retry to allow model unload (prevents Ollama "Stopping..." stuck)
                    retry_delay = getattr(Writer.Config, 'PYDANTIC_RETRY_DELAY', 3)
                    _Logger.Log(f"Waiting {retry_delay}s before retry to allow model unload...", 6)
                    time.sleep(retry_delay)

                    continue
                else:
                    # Final attempt failed - format and raise
                    if hasattr(ve, 'errors'):
                        error_details = "\n".join([
                            f"- {'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                            for err in ve.errors()
                        ])
                        raise Exception(f"Pydantic validation failed after {max_attempts} attempts:\n{error_details}")
                    else:
                        raise Exception(f"Pydantic validation failed: {str(ve)}")

            except Exception as e:
                # Handle non-ValidationError exceptions (TypeError, etc.)
                if attempt < max_attempts - 1:
                    _Logger.Log(f"Attempt {attempt + 1} failed: {e}. Retrying...", 5)

                    # Keep existing generic hints for other error types
                    if isinstance(e, TypeError) and "list" in str(e):
                        _Logger.Log(self._get_text('hint_single_json'), 5)
                    elif _is_validation_or_missing_error(e):
                        _Logger.Log(self._get_text('hint_required_fields'), 5)

                    # Add delay before retry to allow model unload (prevents Ollama "Stopping..." stuck)
                    retry_delay = getattr(Writer.Config, 'PYDANTIC_RETRY_DELAY', 3)
                    _Logger.Log(f"Waiting {retry_delay}s before retry to allow model unload...", 6)
                    time.sleep(retry_delay)

                    continue
                else:
                    raise Exception(f"Failed to generate valid response after {max_attempts} attempts. Last error: {e}")

    def _build_constraint_explanations(self, properties):
        """
        Build human-readable explanations of Pydantic validation constraints.

        This helps LLMs understand validation rules upfront, reducing validation failures.
        """
        import Writer.Config as Config

        explanations = []

        for field_name, field_info in properties.items():
            # Reasoning field max_length constraint
            if field_name == 'reasoning' and 'maxLength' in field_info:
                max_len = field_info['maxLength']
                explanations.append(
                    self._get_text('constraint_reasoning_max', field=field_name, max_len=max_len)
                )

            # Word count tolerance
            if field_name == 'word_count':
                tolerance = getattr(Config, 'PYDANTIC_WORD_COUNT_TOLERANCE', 100)
                explanations.append(
                    self._get_text('constraint_word_count', field=field_name, tolerance=tolerance)
                )

            # Character name minimum length - use robust field detection
            from Writer.FieldConstants import is_character_field
            if is_character_field(field_name) and 'minLength' in field_info:
                min_len = field_info['minLength']
                explanations.append(
                    self._get_text('constraint_min_length', field=field_name, min_len=min_len)
                )

        if explanations:
            header = self._get_text('important_constraints')
            return header + "\n" + "\n".join(f"- {exp}" for exp in explanations) + "\n\n"
        return ""

    def _build_format_instruction(self, schema):
        """Build clear format instruction without showing full schema to prevent echoing"""
        properties = schema.get('properties', {})
        required_fields = schema.get('required', [])

        instruction = "\n\n" + self._get_text('json_schema_header') + "\n"
        instruction += self._get_text('json_schema_note') + "\n\n"

        # Add constraint explanations to help LLMs understand validation rules
        constraint_explanations = self._build_constraint_explanations(properties)
        if constraint_explanations:
            instruction += self._get_text('validation_constraints_header') + "\n"
            instruction += constraint_explanations

        instruction += self._get_text('your_response_header') + "\n"
        instruction += self._get_text('provide_json_only') + "\n\n"
        instruction += self._get_text('required_fields') + "\n"

        for field in required_fields:
            field_info = properties.get(field, {})
            field_type = field_info.get('type', 'unknown')
            original_desc = field_info.get('description', '')
            field_desc = self._get_field_description(field, original_desc)

            # Handle array types with specific examples
            if field_type == 'array':
                items_type = field_info.get('items', {}).get('type', 'unknown')
                if items_type == 'string':
                    instruction += f"  - {field} ({self._get_text('array_of_strings_required')}): {field_desc}\n"
                    instruction += f"    {self._get_text('example_label')}: {self._get_text('example_string_array')}\n"
                else:
                    instruction += f"  - {field} ({self._get_text('array_of_objects_required')}): {field_desc}\n"
            else:
                if field_desc:
                    instruction += f"  - {field} ({field_type}, {self._get_text('required_label')}): {field_desc}\n"
                else:
                    instruction += f"  - {field} ({field_type}, {self._get_text('required_label')})\n"

        # Add optional fields if any
        optional_fields = [k for k in properties.keys() if k not in required_fields]
        if optional_fields:
            instruction += "\n" + self._get_text('optional_fields') + "\n"
            for field in optional_fields[:5]:  # Limit to first 5 optional fields
                field_info = properties.get(field, {})
                field_type = field_info.get('type', 'unknown')
                original_desc = field_info.get('description', '')
                field_desc = self._get_field_description(field, original_desc)

                # Handle array types with specific examples
                if field_type == 'array':
                    items_type = field_info.get('items', {}).get('type', 'unknown')
                    if items_type == 'string':
                        instruction += f"  - {field} ({self._get_text('array_of_strings_optional')}): {field_desc[:50]}...\n"
                        instruction += f"    {self._get_text('example_label')}: {self._get_text('example_string_array')}\n"
                    else:
                        instruction += f"  - {field} ({self._get_text('array_of_objects_optional')}): {field_desc[:50]}...\n"
                else:
                    if field_desc:
                        instruction += f"  - {field} ({field_type}, {self._get_text('optional_label')}): {field_desc[:50]}...\n"
                    else:
                        instruction += f"  - {field} ({field_type}, {self._get_text('optional_label')})\n"
            if len(optional_fields) > 5:
                instruction += f"  - {self._get_text('more_optional_fields', count=len(optional_fields) - 5)}\n"

        instruction += "\n" + self._get_text('example_format') + "\n"
        instruction += self._get_text('important_return_only') + "\n"

        # Add specific examples for StoryElements model
        # Check for StoryElements specifically by looking for themes AND characters fields together
        if 'themes' in properties.keys() and 'characters' in properties.keys():
            instruction += "\n" + self._get_text('story_elements_example_label') + "\n"
            instruction += self._get_text('story_elements_example')

        return instruction

    def _build_validation_error_message(self, validation_error: "ValidationError", model_name: str) -> str:
        """
        Build targeted error message for Pydantic validation failures.

        Extracts specific field errors WITHOUT including schema structure.
        Prevents schema echoing while providing actionable feedback.

        Args:
            validation_error: Pydantic ValidationError instance
            model_name: Name of the Pydantic model for context

        Returns:
            str: Natural language error message with field-specific guidance
        """
        errors = validation_error.errors()
        error_lines = []

        for err in errors:
            field_path = '.'.join(str(x) for x in err['loc'])
            error_type = err['type']
            error_msg = err['msg']

            # Format based on error type
            if error_type == 'missing':
                line = f"- {field_path}: {self._get_text('error_missing')}"

            elif error_type == 'string_too_short':
                input_val = err.get('input', '')
                actual_len = len(str(input_val)) if input_val else 0
                line = f"- {field_path}: {self._get_text('error_too_short', msg=error_msg, actual_len=actual_len)}"

            elif error_type in ('int_parsing', 'float_parsing', 'bool_parsing'):
                input_val = err.get('input', 'unknown')
                expected_type = error_type.split('_')[0]
                line = f"- {field_path}: {self._get_text('error_expected_type', expected_type=expected_type, input_val=repr(input_val))}"

            elif error_type == 'value_error':
                # Custom validator error (e.g., word_count mismatch) - use message as-is
                line = f"- {field_path}: {error_msg}"

            else:
                # Generic format for other error types
                line = f"- {field_path}: {error_msg}"

            error_lines.append(line)

        # Build final message
        message = self._get_text('validation_error_header') + "\n\n"
        message += '\n'.join(error_lines)
        message += "\n\n" + self._get_text('validation_error_footer')

        return message

    def _ollama_chat(self, _Logger, _Model_key, ProviderModel_name, _Messages_list, ModelOptions_dict, Seed_int, _FormatSchema_dict):
        CurrentModelOptions = ModelOptions_dict.copy() if ModelOptions_dict is not None else {}
        ValidParameters = ["mirostat", "mirostat_eta", "mirostat_tau", "num_ctx", "repeat_last_n", "repeat_penalty", "temperature", "seed", "tfs_z", "num_predict", "top_k", "top_p"]
        for key in list(CurrentModelOptions.keys()):
            if key not in ValidParameters:
                del CurrentModelOptions[key]
        CurrentModelOptions.setdefault("num_ctx", getattr(Writer.Config, "OLLAMA_CTX", 4096))
        CurrentModelOptions["seed"] = Seed_int
        if _FormatSchema_dict:
            CurrentModelOptions.update({"temperature": CurrentModelOptions.get("temperature", 0.0)})

        # Prepare chat parameters - always non-streaming
        chat_params = {
            "model": ProviderModel_name,
            "messages": _Messages_list,
            "stream": False,
            "options": CurrentModelOptions
        }

        # Add format parameter at TOP level if structured output is needed
        if _FormatSchema_dict:
            chat_params["format"] = "json"

        # Control LLM reasoning mode via config
        # This controls native reasoning at model level, not app reasoning chain
        # Universal approach: send think=False for ALL models when reasoning is disabled
        # Non-reasoning models will simply ignore this parameter
        if not getattr(Writer.Config, 'ENABLE_LLM_REASONING_MODE', True):
            chat_params["think"] = False
            _Logger.Log(f"LLM reasoning mode DISABLED for {ProviderModel_name} (ENABLE_LLM_REASONING_MODE=False)", 6)

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
                if attempt + 1 >= MaxRetries:
                    raise
                time.sleep(random.uniform(0.5, 1.5) * (attempt + 1))
        raise Exception(f"Ollama chat failed for {_Model_key} after {MaxRetries} attempts.")

    def _execute_with_retry(self, _Logger, operation, _Model_key, operation_name="API call"):
        """DRY helper: Execute operation with retry logic"""
        MaxRetries = Writer.Config.MAX_GOOGLE_RETRIES
        for attempt in range(MaxRetries):
            try:
                return operation()
            except Exception as e:
                _Logger.Log(f"Google {operation_name} error ({_Model_key}, Attempt {attempt+1}/{MaxRetries}): {e}", 7)
                if attempt + 1 >= MaxRetries:
                    raise
                time.sleep(random.uniform(0.5, 1.5) * (attempt + 1))
        raise Exception(f"Google {operation_name} failed for {_Model_key} after {MaxRetries} attempts.")

    def _transform_messages_for_google(self, _Messages_list):
        """Transform messages for Google Gemini API compatibility"""
        return [
            {
                "role": "user" if m["role"] == "system" else ("model" if m["role"] == "assistant" else m["role"]),
                "parts": [m["content"]]
            }
            for m in _Messages_list
        ]

    def _google_chat(self, _Logger, _Model_key, ProviderModel_name, _Messages_list, ModelOptions_dict, Seed_int, _FormatSchema_dict):
        from google.genai.types import HarmCategory, HarmBlockThreshold, SafetySetting

        # Use helper methods
        Messages_transformed = self._transform_messages_for_google(_Messages_list)

        # Optimized safety settings
        safety_settings = [
            SafetySetting(category=cat, threshold=HarmBlockThreshold.BLOCK_NONE)
            for cat in HarmCategory if cat != HarmCategory.HARM_CATEGORY_UNSPECIFIED
        ]

        gen_config = ModelOptions_dict.copy() if ModelOptions_dict is not None else {}
        gen_config["safety_settings"] = safety_settings
        if _FormatSchema_dict:
            gen_config.update({
                "response_mime_type": "application/json",
                "response_schema": _FormatSchema_dict,
                "temperature": gen_config.get("temperature", 0.0)
            })

        client = self.Clients[_Model_key]

        # Use retry helper
        def operation():
            GenResponse = client.generate_content(
                contents=Messages_transformed,
                stream=False,
                generation_config=gen_config
            )

            AssistantMessage = {"role": "assistant", "content": GenResponse.text}
            FinalMessages = _Messages_list + [AssistantMessage]
            TokenUsage = None
            usage_meta = getattr(GenResponse, 'usage_metadata', None)
            if usage_meta:
                TokenUsage = {
                    "prompt_tokens": usage_meta.prompt_token_count,
                    "completion_tokens": usage_meta.candidates_token_count
                }
            return FinalMessages, TokenUsage

        return self._execute_with_retry(_Logger, operation, _Model_key, "chat")

    def _openrouter_chat(self, _Logger, _Model_key, ProviderModel_name, _Messages_list, ModelOptions_dict, Seed_int, _FormatSchema_dict):
        Client = self.Clients[_Model_key]
        if hasattr(Client, 'model_name'):
            Client.model_name = ProviderModel_name
        elif hasattr(Client, 'model'):
            Client.model = ProviderModel_name

        ReqOptions = ModelOptions_dict.copy() if ModelOptions_dict is not None else {}
        if Seed_int is not None:
            ReqOptions["seed"] = Seed_int

        # Enhanced FormatSchema handling for JSON Schema support (using DRY helper)
        if _FormatSchema_dict is not None:
            response_format = self._build_response_format(_FormatSchema_dict)
            if response_format:
                ReqOptions.update({"response_format": response_format})
                # Apply temperature adjustment for basic JSON object mode only
                if response_format.get("type") == "json_object":
                    ReqOptions.update({"temperature": ReqOptions.get("temperature", 0.0)})

        MaxRetries = Writer.Config.MAX_OPENROUTER_RETRIES
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
                    TokenUsage = {"prompt_tokens": usage.get("prompt_tokens", 0), "completion_tokens": usage.get("completion_tokens", 0)}
                return FullResponseMessages, TokenUsage
            except Exception as e:
                _Logger.Log(f"OpenRouter API Error ({_Model_key}, Attempt {attempt+1}/{MaxRetries}): {e}", 7)
                if attempt + 1 >= MaxRetries:
                    raise
                time.sleep(random.uniform(0.5, 1.5) * (attempt + 1))
        raise Exception(f"OpenRouter chat failed for {_Model_key} after {MaxRetries} attempts.")

    def ChatResponse(self, _Logger, _Messages, _Model: str, _SeedOverride: int, _FormatSchema: dict = None):  # type: ignore[assignment]
        """Non-streaming response for Pydantic generation with user-friendly display"""
        TotalInputChars, EstInputTokens = 0, 0
        try:
            for msg in _Messages:
                content = msg.get("content", "")
                TotalInputChars += len(str(content))
            EstInputTokens = round(TotalInputChars / getattr(Writer.Config, "CHARS_PER_TOKEN_ESTIMATE", 4.5))
        except Exception as e:
            _Logger.Log(f"Token calculation error: {e}", 6)

        if Writer.Config.DEBUG:
            _Logger.Log(f"--- Chat Req to {_Model} (Seed: {_SeedOverride}) ---", 6)
            for i, m in enumerate(_Messages):
                _Logger.Log(f"  Msg{i} {m.get('role')}: {str(m.get('content',''))[:100]}...", 6)
            _Logger.Log(f"--- End Req for {_Model} ---", 6)

        Provider, ProviderModelName, ModelHost, ModelOptions = self.GetModelAndProvider(_Model)
        SeedToUse = _SeedOverride if _SeedOverride != -1 else getattr(Writer.Config, "SEED", random.randint(0, 999999))

        _Logger.Log(f"Model: '{ProviderModelName}' ({Provider}@{ModelHost or 'Default'}) | InChars: {TotalInputChars} (Est~{EstInputTokens}tok)", 4)
        if EstInputTokens > getattr(Writer.Config, "TOKEN_WARNING_THRESHOLD", 20000):
            _Logger.Log(f"WARN: High Token Context: est~{EstInputTokens}tok for {_Model}", 6)

        start_time = time.time()
        ResponseHandler = getattr(self, f"_{Provider}_chat", None)
        if not ResponseHandler:
            raise Exception(f"Unsupported provider: {Provider}")

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
        comp_tokens = TokenUsage.get("completion_tokens", 0) if TokenUsage else 0
        tps = f"~{round(comp_tokens/gen_time,1)}tok/s" if comp_tokens and gen_time > 0.1 else "N/A"
        _Logger.Log(f"Response for {_Model} in {gen_time}s ({tps}). Tokens: {TokenUsage if TokenUsage else 'N/A'}", 4)

        caller_frame = inspect.stack()[1]
        caller_info = f"{os.path.basename(caller_frame.filename)}::{caller_frame.function}"
        try:
            _Logger.SaveLangchain(caller_info, FullResponseMessages)  # FullResponseMessages includes the latest assistant response
        except Exception as e:
            _Logger.Log(f"Langchain save error from {caller_info}: {e}", 6)

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
        if not _Messages or not isinstance(_Messages, list):
            return ""
        return str(_Messages[-1].get("content", "")) if isinstance(_Messages[-1], dict) else ""

    def _ollama_embedding(self, _Logger, _Model_key, ProviderModel_name, _Texts: list):
        """Generate embeddings using Ollama"""
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
        """Generate embeddings using Gemini with retry logic and client pattern"""
        from google.genai import types

        client = self.Clients[_Model_key]
        embeddings = []
        total_tokens = 0

        MaxRetries = Writer.Config.MAX_GOOGLE_RETRIES
        for attempt in range(MaxRetries):
            try:
                for text in _Texts:
                    # Use client pattern (latest SDK)
                    result = client.models.embed_content(
                        model=f'models/{ProviderModel_name}',
                        content=text,
                        config=types.EmbedContentConfig(task_type="retrieval_document")
                    )
                    # Use object attribute access (not dictionary)
                    embeddings.append(result.embedding)
                    total_tokens += len(text.split())

                return embeddings, {"prompt_tokens": total_tokens, "completion_tokens": 0}

            except Exception as e:
                _Logger.Log(f"Gemini embedding error ({_Model_key}, Attempt {attempt+1}/{MaxRetries}): {e}", 7)
                if attempt + 1 >= MaxRetries:
                    raise
                time.sleep(random.uniform(0.5, 1.5) * (attempt + 1))

        raise Exception(f"Google embedding failed for {_Model_key} after {MaxRetries} attempts.")

    def _openrouter_embedding(self, _Logger, _Model_key, ProviderModel_name, _Texts: list):
        """Generate embeddings using OpenRouter (OpenAI-compatible)"""
        import requests

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

        if "@" in Netloc:
            ModelName, Host = Netloc.split("@", 1)

        ModelName = ModelName.strip('/')  # Ensure no leading/trailing slashes from netloc part
        ModelName = unquote(ModelName)  # Decode URL encoded characters like %2F

        if Provider == "openrouter":
            ModelName = f"{ModelName}/{Path}" if Path and ModelName else (ModelName or Path)
        elif Provider == "ollama":
            if Path:
                if "@" in Path:
                    path_model_segment, host_from_path = Path.split('@', 1)
                    path_model_segment = path_model_segment.strip('/')
                    ModelName = f"{ModelName}/{path_model_segment}" if ModelName and path_model_segment else (ModelName or path_model_segment)
                    Host = host_from_path
                elif Host or (parsed.port or ('.' in ModelName and ModelName != '.') or ModelName == 'localhost'):  # ModelName from netloc was host
                    ModelName = Path
                else:  # ModelName from netloc was model, Path is sub-model
                    ModelName = f"{ModelName}/{Path}" if ModelName and Path else (ModelName or Path)
            if Host is None:
                Host = getattr(Writer.Config, 'OLLAMA_HOST', None)

        Options = {k: (float(v[0]) if v[0].replace('.', '', 1).isdigit() else v[0]) for k, v in parse_qs(Query).items()}
        return Provider, ModelName.strip('/'), Host, Options if Options else None
