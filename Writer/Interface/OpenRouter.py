import json, requests, time, sys  # Add sys for stderr
from typing import Any, List, Mapping, Optional, Literal, Union, TypedDict


class OpenRouter:
    """OpenRouter.
    https://openrouter.ai/docs#models
    https://openrouter.ai/docs#llm-parameters
    """

    Message_Type = TypedDict(
        "Message",
        {"role": Literal["user", "assistant", "system", "tool"], "content": str},
    )
    ProviderPreferences_Type = TypedDict(
        "ProviderPreferences",
        {
            "allow_fallbacks": Optional[bool],
            "require_parameters": Optional[bool],
            "data_collection": Union[Literal["deny"], Literal["allow"], None],
            "order": Optional[
                List[
                    Literal[
                        "OpenAI",
                        "Anthropic",
                        "HuggingFace",
                        "Google",
                        "Together",
                        "DeepInfra",
                        "Azure",
                        "Modal",
                        "AnyScale",
                        "Replicate",
                        "Perplexity",
                        "Recursal",
                        "Fireworks",
                        "Mistral",
                        "Groq",
                        "Cohere",
                        "Lepton",
                        "OctoAI",
                        "Novita",
                        "DeepSeek",
                        "Infermatic",
                        "AI21",
                        "Featherless",
                        "Mancer",
                        "Mancer 2",
                        "Lynn 2",
                        "Lynn",
                    ]
                ]
            ],
        },
        total=False,
    )

    def __init__(
        self,
        api_key: str,
        provider: Optional[ProviderPreferences_Type] | None = None,
        model: str = "microsoft/wizardlm-2-7b",
        max_tokens: int = 0,
        temperature: Optional[float] | None = 1.0,
        top_k: Optional[int] | None = 0.0,
        top_p: Optional[float] = 1.0,
        presence_penalty: Optional[float] = 0.0,
        frequency_penalty: Optional[float] = 0.0,
        repetition_penalty: Optional[float] = 1.0,
        min_p: Optional[float] = 0.0,
        top_a: Optional[float] = 0.0,
        seed: Optional[int] | None = None,
        logit_bias: Optional[Mapping[int, int]] | None = None,
        response_format: Optional[Mapping[str, str]] | None = None,
        stop: Optional[Mapping[str, str]] | None = None,
        set_p50: bool = False,
        set_p90: bool = False,
        api_url: str = "https://openrouter.ai/api/v1/chat/completions",
        timeout: int = 3600,
    ):

        self.api_url = api_url
        self.api_key = api_key
        self.provider = provider
        self.model = model
        self.max_tokens = max_tokens
        self.seed = seed
        self.logit_bias = logit_bias
        self.response_format = (
            response_format  # Ensure this line is present and correctly assigned
        )
        self.stop = stop
        self.timeout = timeout

        # Get the top LLM sampling parameter configurations used by users on OpenRouter.
        # https://openrouter.ai/docs/parameters-api
        if set_p90 or set_p50:
            parameters_url = f"https://openrouter.ai/api/v1/parameters/{self.model}"
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            params = requests.get(parameters_url, headers=headers).json()["data"]
            # I am so sorry
            self.temperature = (
                params["temperature_p50"] if set_p50 else params["temperature_p90"]
            )
            self.top_k = params["top_k_p50"] if set_p50 else params["top_k_p90"]
            self.top_p = params["top_p_p50"] if set_p50 else params["top_p_p90"]
            self.presence_penalty = (
                params["presence_penalty_p50"]
                if set_p50
                else params["presence_penalty_p90"]
            )
            self.frequency_penalty = (
                params["frequency_penalty_p50"]
                if set_p50
                else params["frequency_penalty_p90"]
            )
            self.repetition_penalty = (
                params["repetition_penalty_p50"]
                if set_p50
                else params["repetition_penalty_p90"]
            )
            self.min_p = params["min_p_p50"] if set_p50 else params["min_p_p90"]
            self.top_a = params["top_a_p50"] if set_p50 else params["top_a_p90"]
        else:
            self.temperature = temperature
            self.top_k = top_k
            self.top_p = top_p
            self.presence_penalty = presence_penalty
            self.frequency_penalty = frequency_penalty
            self.repetition_penalty = repetition_penalty
            self.min_p = min_p
            self.top_a = top_a

    def set_params(
        self,
        max_tokens: Optional[int] | None = None,
        presence_penalty: Optional[float] | None = None,
        frequency_penalty: Optional[float] | None = None,
        repetition_penalty: Optional[float] | None = None,
        response_format: Optional[Mapping[str, str]] | None = None,
        temperature: Optional[float] | None = None,
        seed: Optional[int] | None = None,
        top_k: Optional[int] | None = None,
        top_p: Optional[float] | None = None,
        min_p: Optional[float] | None = None,
        top_a: Optional[float] | None = None,
    ):

        if max_tokens is not None:
            self.max_tokens = max_tokens
        if presence_penalty is not None:
            self.presence_penalty = presence_penalty
        if frequency_penalty is not None:
            self.frequency_penalty = frequency_penalty
        if repetition_penalty is not None:
            self.repetition_penalty = repetition_penalty
        if response_format is not None:
            self.response_format = response_format
        if temperature is not None:
            self.temperature = temperature
        if seed is not None:
            self.seed = seed
        if top_k is not None:
            self.top_k = top_k
        if top_p is not None:
            self.top_p = top_p
        if min_p is not None:
            self.min_p = min_p
        if top_a is not None:
            self.top_a = top_a

    def ensure_array(
        self, input_msg: List[Message_Type] | Message_Type
    ) -> List[Message_Type]:
        if isinstance(input_msg, (list, tuple)):
            return input_msg
        else:
            return [input_msg]

    # Modifikasi signature metode chat
    def chat(
        self,
        messages: Message_Type,
        max_retries: int = 10,
        seed: int = None,
        stream: bool = False,
    ):  # Tambahkan stream
        messages = self.ensure_array(messages)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/datacrystals/AIStoryWriter",  # Opsional, bisa dipertimbangkan untuk dihapus jika tidak diperlukan
            "X-Title": "StoryForgeAI",  # Opsional
        }
        body = {
            "model": self.model,
            "messages": messages,
            "max_token": (
                self.max_tokens if self.max_tokens > 0 else None
            ),  # Kirim None jika 0
            "temperature": self.temperature,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "repetition_penalty": self.repetition_penalty,
            "min_p": self.min_p,
            "top_a": self.top_a,
            "seed": self.seed if seed is None else seed,
            "logit_bias": self.logit_bias,
            "response_format": self.response_format,
            "stop": self.stop,
            "provider": self.provider,
            "stream": stream,  # Atur stream secara dinamis
            "usage": {"include": True} # <-- TAMBAHKAN BARIS INI
        }

        # Hapus kunci dengan nilai None dari body untuk menghindari error dari beberapa model/provider
        body = {k: v for k, v in body.items() if v is not None}

        if stream:
            try:
                response = requests.post(
                    url=self.api_url,
                    headers=headers,
                    data=json.dumps(body),
                    timeout=self.timeout,  # Timeout untuk keseluruhan stream
                    stream=True,  # Penting untuk library requests
                )
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        if decoded_line.startswith("data: "):
                            json_data_string = decoded_line[len("data: ") :].strip()
                            if json_data_string == "[DONE]":
                                break
                            try:
                                data = json.loads(json_data_string)
                                yield data  # Yield dictionary yang diparsing
                            except json.JSONDecodeError:
                                print(
                                    f"OpenRouter Stream: JSONDecodeError for '{json_data_string}'",
                                    file=sys.stderr,
                                )
                                continue
                return  # Akhir dari generator
            except requests.exceptions.RequestException as e:
                print(f"OpenRouter Stream: RequestException: {e}", file=sys.stderr)
                raise  # Naikkan kembali exception agar bisa ditangani di level atas
            except Exception as e:
                print(f"OpenRouter Stream: Unexpected error: {e}", file=sys.stderr)
                raise
        else:
            # Logika non-streaming yang sudah ada
            retries = 0
            while retries < max_retries:
                try:
                    response = requests.post(
                        url=self.api_url,
                        headers=headers,
                        data=json.dumps(body),  # body sudah memiliki stream: False
                        timeout=self.timeout,
                        stream=False,  # Eksplisit False untuk non-streaming
                    )
                    response.raise_for_status()
                    response_json = response.json()
                    if "choices" in response_json:
                        content = response_json["choices"][0]["message"]["content"]
                        usage_info = response_json.get("usage")
                        return content, usage_info
                    elif "error" in response_json:
                        print(
                            f"Openrouter returns error '{response_json['error']['code']}' with message '{response_json['error']['message']}', retry attempt {retries + 1}."
                        )
                        if response_json["error"]["code"] == 400:
                            print("Bad Request (invalid or missing params, CORS)")
                        if response_json["error"]["code"] == 401:
                            raise Exception(
                                "Invalid credentials (OAuth session expired, disabled/invalid API key)"
                            )
                        if response_json["error"]["code"] == 402:
                            raise Exception(
                                "Your account or API key has insufficient credits. Add more credits and retry the request."
                            )
                        if response_json["error"]["code"] == 403:
                            print(
                                "Your chosen model requires moderation and your input was flagged"
                            )
                        if response_json["error"]["code"] == 408:
                            print("Your request timed out")
                        if (
                            response_json["error"]["code"] == 429
                        ):  # Pastikan ini response_json
                            print("You are being rate limited")
                            print("Waiting 10 seconds")
                            time.sleep(10)
                        if response_json["error"]["code"] == 502:
                            print(
                                "Your chosen model is down or we received an invalid response from it"
                            )
                        if response_json["error"]["code"] == 503:
                            print(
                                "There is no available model provider that meets your routing requirements"
                            )
                    else:
                        from pprint import pprint  # Pastikan import ada jika digunakan

                        print(
                            f"Response without error but missing choices, retry attempt {retries + 1}."
                        )
                        pprint(response.json())
                except requests.exceptions.HTTPError as http_err:
                    print(
                        f"HTTP error occurred: '{http_err}' - Status Code: '{http_err.response.status_code}', retry attempt {retries + 1}."
                    )
                    if http_err.response.status_code == 524:
                        time.sleep(10)
                except (
                    requests.exceptions.Timeout,
                    requests.exceptions.TooManyRedirects,
                ) as err:
                    print(f"Retry attempt {retries + 1} after error: '{err}'")
                except requests.exceptions.RequestException as req_err:
                    print(
                        f"An error occurred while making the request: '{req_err}', retry attempt {retries + 1}."
                    )
                except Exception as e:
                    print(
                        f"An unexpected error occurred: '{e}', retry attempt {retries + 1}."
                    )
                retries += 1
            return None, None  # Jika semua retry gagal untuk non-streaming
