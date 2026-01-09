###############################################################################
# QUICK START: Using Google Gemini
###############################################################################
#
# 1. Get API Key:
#    - Visit: https://makersuite.google.com/app/apikey
#    - Create or copy your API key
#
# 2. Setup .env file:
#    - Edit /var/www/AIStoryWriter/.env
#    - Add: GOOGLE_API_KEY=your-api-key-here
#
# 3. Configure model in this file (Config.py):
#    - Uncomment line 50: ollamasemua = "google://gemini-flash-latest"
#    - Comment out current ollamasemua line
#
# 4. Run story generation:
#    python Write.py -Prompt Prompts/YourPrompt.txt
#
###############################################################################
# MODEL CONFIGURATION EXAMPLES
###############################################################################
#
# GOOGLE GEMINI (via Google AI API):
#   Format: "google://model-name"
#   API Key: Set GOOGLE_API_KEY in .env file
#   Available models (2025):
#     - gemini-2.5-flash (Latest stable, best quality)
#     - gemini-2.5-pro (Best quality, slower)
#     - gemini-2.0-flash (Stable, very fast)
#     - gemini-2.0-flash-exp (Experimental features)
#     - gemini-flash-latest (Always newest)
#   Example:
#     ollamasemua = "google://gemini-2.5-flash"
#     ollamasemua = "google://gemini-2.0-flash-exp"
#     ollamasemua = "google://gemini-flash-latest"
#
# OLLAMA (local or remote):
#   Format: "ollama://model-name@host:port" or just "model-name"
#   Example:
#     ollamasemua = "ollama://qwen2.5:32b@10.23.82.116:11434"
#     ollamasemua = "aisingapore/Qwen-SEA-LION-v4-32B-IT:latest"
#
# OPENROUTER:
#   Format: "openrouter://model-name"
#   API Key: Set OPENROUTER_API_KEY in .env file
#   Example:
#     ollamasemua = "openrouter://anthropic/claude-3.5-sonnet"
#
# SYNTHETIC.DEV (OpenAI-compatible API):
#   Format: "synthetic://model-name"
#   API Key: Set SYNTHETIC_API_KEY in .env file
#   All models use Hugging Face format: "hf:{owner}/{model-name}"
#   Popular models (2025):
#     - DeepSeek V3.1 (Latest reasoning model, Jan 2025):
#       synthetic://hf:deepseek-ai/DeepSeek-V3.1
#     - Qwen 3 235B (Large Chinese model, Jan 2025):
#       synthetic://hf:Qwen/Qwen3-235B-A22B-Instruct-2507
#     - GLM 4.6 (Zhihu AI, Chinese model):
#       synthetic://hf:zai-org/GLM-4.6
#     - Kimi K2 Instruct (Moonshot AI, Chinese model):
#       synthetic://hf:moonshotai/Kimi-K2-Instruct
#     - OpenAI GPT-OSS 120B (Open-source GPT alternative):
#       synthetic://hf:openai/gpt-oss-120b
#   Example:
#     ollamasemua = "synthetic://hf:deepseek-ai/DeepSeek-V3.1"
#
# XAI GROK (via xAI API):
#   Format: "grok://model-name"
#   API Key: Set XAI_API_KEY in .env file
#   Available models (2025-2026):
#     Grok 4 Series (Latest, Released Nov 2025):
#       - grok-4-1-fast-reasoning (Best: 2M context, agentic, reasoning)
#       - grok-4-1-fast-non-reasoning (Fast: 2M context, instant responses)
#       - grok-4-fast (Fast: 40% fewer tokens, 2M context)
#       - grok-4-heavy (Powerful: Highest quality)
#       - grok-4 (Standard: Balanced performance)
#     Grok 3 Series (Released Feb 2025):
#       - grok-3 (Flagship: Excellent quality)
#       - grok-3-mini (Small: Fast responses)
#     Vision & Multimodal:
#       - grok-2-vision-1212 (Vision: Image understanding)
#       - grok-vision-beta (Beta: Vision tasks)
#       - grok-2-1212 (Multimodal: 131K context)
#     Specialized:
#       - grok-code-fast-1 (Coding: Agentic coding tasks)
#       - grok-2-image-1212 (Image: Text-to-image generation)
#     Legacy (Still available):
#       - grok-2, grok-2-mini, grok-1.5, grok-1
#   Example:
#     ollamasemua = "grok://grok-4-1-fast-reasoning"  # Best for complex tasks
#     ollamasemua = "grok://grok-3"                   # Good balance
#     ollamasemua = "grok://grok-3-mini"              # Fast & lightweight
#     ollamasemua = "grok://grok-2-vision-1212"       # For vision tasks
#
###############################################################################

###############################################################################
# LLM MODEL CONFIGURATION
###############################################################################

# Default model for all tasks (use provider://model-name format)
# Provider formats:
#   - google://gemini-2.5-flash         (Google Genai, requires GOOGLE_API_KEY)
#   - google://gemini-flash-lite-latest (Google Genai, lightweight)
#   - openrouter://anthropic/claude-3.5-sonnet (OpenRouter, requires OPENROUTER_API_KEY)
#   - synthetic://hf:deepseek-ai/DeepSeek-V3.1 (Synthetic.dev, requires SYNTHETIC_API_KEY)
#   - grok://grok-4-1-fast-reasoning     (xAI, requires XAI_API_KEY)
#   - ollama://qwen2.5:32b              (Ollama, uses OLLAMA_HOST)
#   - qwen2.5:32b                       (Ollama, uses OLLAMA_HOST when no provider specified)
# ollamasemua = "grok://grok-4-1-fast-reasoning"
ollamasemua = "synthetic://hf:meta-llama/Llama-3.3-70B-Instruct"  # Requires SYNTHETIC_API_KEY in .env
# ollamasemua = "google://gemini-flash-lite-latest"
# ollamasemua = "huihui_ai/qwen2.5-abliterate:32b"
# ollamasemua = "aisingapore/Qwen-SEA-LION-v4-32B-IT:latest"
# ollamasemua = "aisingapore/Llama-SEA-LION-v3.5-8B-R:f16"
# ollamasemua = "aisingapore/Gemma-SEA-LION-v4-27B-IT:latest"
# ollamasemua = "google://gemini-2.5-flash"  # Requires GOOGLE_API_KEY in .env

# Stage-specific LLM models (all default to ollamasemua unless overridden)
INITIAL_OUTLINE_WRITER_MODEL = ollamasemua
CHAPTER_OUTLINE_WRITER_MODEL = ollamasemua
CHAPTER_STAGE1_WRITER_MODEL = ollamasemua  # Plot and scene writing
CHAPTER_STAGE2_WRITER_MODEL = ollamasemua  # Character development
CHAPTER_STAGE3_WRITER_MODEL = ollamasemua  # Dialogue refinement
FINAL_NOVEL_EDITOR_MODEL = ollamasemua
CHAPTER_REVISION_WRITER_MODEL = ollamasemua
REVISION_MODEL = ollamasemua
EVAL_MODEL = ollamasemua
INFO_MODEL = ollamasemua
SCRUB_MODEL = ollamasemua
CHECKER_MODEL = ollamasemua
TRANSLATOR_MODEL = ollamasemua
FAST_MODEL = ollamasemua  # For quick tasks like titling

# Reasoning model (two-pass reasoning system)
REASONING_MODEL = CHAPTER_STAGE1_WRITER_MODEL

# SEED for reproducibility (can be overridden by argparser)
SEED = 12

###############################################################################
# EMBEDDING MODEL CONFIGURATION
###############################################################################

# Format: "provider://model-name" or just "model-name"
#
# OLLAMA (local or remote):
#   - ollama://nomic-embed-text:latest
#   - ollama://qwen3-embedding:latest (recommended)
#
# GOOGLE GEMINI (via Google AI API):
#   - google://gemini-embedding-001 (Stable, recommended for production)
#   API Key: Set GOOGLE_API_KEY in .env file
#   Dimensions: Default 3072, flexible 128-3072 (recommended: 768, 1536, or 3072)
#   Input limit: 2,048 tokens
#   Example: EMBEDDING_MODEL = "google://gemini-embedding-001"
#
# OPENROUTER:
#   - openrouter://openai/text-embedding-3-small
#   API Key: Set OPENROUTER_API_KEY in .env file
#
# SYNTHETIC.DEV (OpenAI-compatible API):
#   Popular embedding models:
#   - synthetic://hf:nomic-ai/nomic-embed-text-v1.5 (Nomic AI, 768 dim, recommended)
#   - synthetic://hf:Qwen/Qwen2.5-72B-Instruct (Qwen, supports embeddings)
#   API Key: Set SYNTHETIC_API_KEY in .env file
#
# EMBEDDING_MODEL = "ollama://qwen3-embedding:latest"
EMBEDDING_MODEL = "google://gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768  # Default embedding dimensions (for qwen3-embedding)
EMBEDDING_CTX = 8192  # Context window for embeddings
EMBEDDING_FALLBACK_ENABLED = False  # Fail fast, no automatic fallback

###############################################################################
# OLLAMA-SPECIFIC CONFIGURATION
###############################################################################

OLLAMA_CTX = 16384  # Default: 8192. Increased for longer contexts.

# Ollama host (used when provider is ollama or no provider specified)
# OLLAMA_HOST = "https://xxxx-11434.proxy.runpod.net"
# OLLAMA_HOST = "http://10.23.82.116:11434"
# OLLAMA_HOST = "10.23.147.239:11434"
# OLLAMA_HOST = "http://127.0.0.1:22434"
OLLAMA_HOST = "http://127.0.0.1:11434"

# Synthetic.dev API endpoint (OpenAI-compatible API)
# Get your API key from: https://dev.synthetic.new/
# Set SYNTHETIC_API_KEY in .env or environment
SYNTHETIC_API_URL = "https://api.synthetic.new/openai/v1"

###############################################################################
# RETRY CONFIGURATION
###############################################################################

# Maximum retries for each provider
MAX_PYDANTIC_RETRIES = 5  # Pydantic validation retries
MAX_GOOGLE_RETRIES = 2  # Google Genai API retries
MAX_OPENROUTER_RETRIES = 2  # OpenRouter API retries
MAX_GROK_RETRIES = 2  # xAI Grok API retries
MAX_SYNTHETIC_RETRIES = 2  # Synthetic.dev API retries
MAX_RETRIES_CHAPTER_TITLE = 3  # Chapter title generation retries

###############################################################################
# MAX TOKENS CONFIGURATION (OUTPUT LIMITS)
# These control OUTPUT tokens only, not context window capacity
# Formula: Prompt Tokens + MAX_*_TOKENS ≤ Context Window
#
# ⚠️ IMPORTANT: Currently ONLY Synthetic.dev actively uses max_tokens configuration
# in Wrapper.py::_synthetic_chat(). Other providers rely on their defaults or
# handle token limits automatically via their APIs.
#
# The values below are RESERVED for future implementation if needed:
# - OpenAI/OpenRouter: Rely on model defaults (typically 4096-8192)
# - Gemini: API handles max_output_tokens automatically based on model
# - Grok: Supports max_tokens via query parameter (ModelOptions_dict)
# - Ollama: Uses num_predict, controlled via query parameter
#
# To enable max_tokens for other providers:
# 1. Uncomment/configure the provider's chat method in Wrapper.py
# 2. Add logic similar to _synthetic_chat() to set ReqOptions["max_tokens"]
###############################################################################

# OpenAI / OpenRouter / Compatible providers
# ⚠️ NOT YET IMPLEMENTED - Uses model defaults
MAX_OPENAI_TOKENS_STRUCTURED = 4096  # For structured output (JSON Schema)
MAX_OPENAI_TOKENS_FREEFORM = 2048   # For free-form text generation

# Synthetic.dev (default is 2048, need higher for structured output)
# ✅ ACTIVE - Implemented in Wrapper.py::_synthetic_chat()
MAX_SYNTHETIC_TOKENS_STRUCTURED = 4096
MAX_SYNTHETIC_TOKENS_FREEFORM = 2048

# Google Gemini (uses max_output_tokens, API handles automatically)
# ⚠️ NOT YET IMPLEMENTED - Gemini API handles this automatically
MAX_GEMINI_TOKENS_STRUCTURED = 8192
MAX_GEMINI_TOKENS_FREEFORM = 4096

# xAI Grok
# ⚠️ NOT YET IMPLEMENTED - Supports max_tokens via query parameter
MAX_GROK_TOKENS_STRUCTURED = 4096
MAX_GROK_TOKENS_FREEFORM = 2048

# Ollama (local, uses num_predict parameter)
# ⚠️ NOT YET IMPLEMENTED - Uses num_predict via query parameter
MAX_OLLAMA_TOKENS_STRUCTURED = 4096
MAX_OLLAMA_TOKENS_FREEFORM = 2048

###############################################################################
# LLM SAMPLING & REPETITION CONTROL
###############################################################################

# Temperature settings
# - Controls randomness: 0.0 = deterministic, 1.0 = balanced, 2.0 = very creative
# - Used for non-structured output (free-form text generation)
# - Structured output (Pydantic/JSON) always uses 0.0 for determinism
DEFAULT_TEMPERATURE_FREEFORM = 0.7  # Default for story/chapter generation
DEFAULT_TEMPERATURE_STRUCTURED = 0.0  # For JSON/Pydantic output (DO NOT CHANGE)

# Repetition penalty settings (prevent model from repeating itself)
# Different providers use different parameter names - see provider-specific sections below

# --- OLLAMA REPETITION CONTROL ---
# repeat_penalty: Penalizes token repetition
#   1.0 = no penalty, >1.0 = penalize repetition
#   Range: >0, typical values: 1.0-1.3
#   Too high (>1.5) causes incoherence
OLLAMA_REPEAT_PENALTY = 1.1  # Slight penalty for story generation

# repeat_last_n: Number of tokens to look back for repetition detection
#   Default: 64, higher = catches longer-distance repetition
OLLAMA_REPEAT_LAST_N = 64

# --- OPENROUTER REPETITION CONTROL ---
# frequency_penalty: Penalizes tokens based on occurrence frequency
#   Range: [-2, 2], 0 = no penalty
#   Positive values decrease repetition, negative encourages it
OPENROUTER_FREQUENCY_PENALTY = 0.5  # Moderate penalty

# presence_penalty: Penalizes tokens that already appeared (flat penalty)
#   Range: [-2, 2], 0 = no penalty
#   Unlike frequency_penalty, doesn't scale with count
OPENROUTER_PRESENCE_PENALTY = 0.3  # Light penalty for diversity

# repetition_penalty: OpenRouter-specific repetition control
#   Range: (0, 2], 1.0 = no penalty
#   Scales based on original token probability
OPENROUTER_REPETITION_PENALTY = 1.0  # Neutral (let frequency/presence handle it)

# --- GOOGLE GEMINI REPETITION CONTROL ---
# frequency_penalty & presence_penalty: Same as OpenRouter
#   ⚠️ WARNING: Only supported by gemini-2.0-* models
#   gemini-2.5-* models do NOT support these (returns INVALID_ARGUMENT error)
GOOGLE_FREQUENCY_PENALTY = 0.5  # Only for 2.0 models
GOOGLE_PRESENCE_PENALTY = 0.3   # Only for 2.0 models

# --- GROK REPETITION CONTROL ---
# frequency_penalty: Limited support
#   ⚠️ WARNING: Grok-4 models auto-filter these parameters
GROK_FREQUENCY_PENALTY = 0.5  # May be filtered by API

# --- SYNTHETIC.DEV REPETITION CONTROL ---
# LLaMA-specific settings to prevent degenerative repetition
# See: https://discuss.huggingface.co/t/repetition-issues-in-llama-models-3-8b-3-70b-3-1-3-2/144196

# Temperature for structured output (higher temp breaks repetition loops)
SYNTHETIC_TEMPERATURE_STRUCTURED = 0.8  # Higher temp for LLaMA structured output

# frequency_penalty: Penalizes tokens based on occurrence frequency
#   Range: [-2, 2], 0 = no penalty
SYNTHETIC_FREQUENCY_PENALTY = 1.0  # Stronger penalty for LLaMA

# presence_penalty: Penalizes tokens that already appeared (flat penalty)
#   Range: [-2, 2], 0 = no penalty
SYNTHETIC_PRESENCE_PENALTY = 0.6  # Encourages topic diversity

# --- REPETITION DETECTION THRESHOLDS ---
# Used by RepetitionDetector to identify problematic outputs

# Character explosion detection
# Example: "aaaaaaaaaa..." triggers when same char repeats >= threshold
MAX_CONSECUTIVE_CHARS = 10  # Max consecutive identical characters (non-structured output)
MAX_CONSECUTIVE_CHARS_STRUCTURED = 20  # Higher threshold for structured output (JSON values can have legitimate repetition)

# N-gram loop detection
# Example: "The cat sat. The cat sat. The cat sat." triggers when n-gram repeats >= threshold
NGRAM_SIZE = 5  # Number of words in n-gram sequence
MAX_NGRAM_REPETITIONS = 3  # Max times n-gram can repeat

# Minimum phrase length for phrase repetition detection (in characters)
MIN_PHRASE_LENGTH = 20  # Ignore very short phrases
MAX_PHRASE_REPETITIONS = 2  # Max times phrase can repeat

# --- AUTO-RETRY CONFIGURATION ---
# When repetition detected, automatically retry with adjusted parameters

# Maximum retry attempts for repetition issues
MAX_REPETITION_RETRIES = 2  # Retry up to 2 times (total 3 attempts)

# Temperature increment per retry
# Each retry increases temperature to add randomness
TEMPERATURE_INCREMENT_PER_RETRY = 0.2  # +0.2 per retry (0.7 → 0.9 → 1.1)

# Delay between retries (seconds)
REPETITION_RETRY_DELAY = 3  # Wait 3s before retry (allow model unload)

###############################################################################
# QUALITY & REVISION CONFIGURATION
###############################################################################

OUTLINE_QUALITY = 92  # Note this value is overridden by the argparser
OUTLINE_MIN_REVISIONS = 1  # Note this value is overridden by the argparser
OUTLINE_MAX_REVISIONS = 3  # Note this value is overridden by the argparser
CHAPTER_NO_REVISIONS = False  # Note this value is overridden by the argparser # disables all revision checks for the chapter, overriding any other chapter quality/revision settings
CHAPTER_QUALITY = 90  # Note this value is overridden by the argparser
CHAPTER_MIN_REVISIONS = 1  # Note this value is overridden by the argparser
CHAPTER_MAX_REVISIONS = 3  # Note this value is overridden by the argparser

# Minimum Word Counts for chapter generation calls
MIN_WORDS_TRANSLATE_PROMPT = 10  # Minimum words for prompt translation
MIN_WORDS_INITIAL_OUTLINE = 250  # Minimum words for initial outline generation
MIN_WORDS_REVISE_OUTLINE = 250  # Minimum words for outline revision
MIN_WORDS_PER_CHAPTER_OUTLINE = 100  # Minimum words for per-chapter outline generation
MIN_WORDS_STORY_ELEMENTS = 150  # Minimum words for story elements generation
MIN_WORDS_CHAPTER_SEGMENT_EXTRACT = (
    120  # Minimum words for extracting chapter outline segment
)
MIN_WORDS_CHAPTER_SUMMARY = 100  # Minimum words for summarizing previous chapter
MIN_WORDS_CHAPTER_DRAFT = 300  # Minimum words for chapter draft stages (1, 2, 3)
MIN_WORDS_REVISE_CHAPTER = 100  # Minimum words for chapter revision
MIN_WORDS_OUTLINE_FEEDBACK = 70  # Minimum words for outline feedback/critique
MIN_WORDS_SCENE_OUTLINE = 100  # Minimum words for scene-by-scene outline generation
MIN_WORDS_SCENE_WRITE = 150  # Minimum words for writing a scene from its outline
MIN_WORDS_SCRUB_CHAPTER = 100  # Minimum words for scrubbing a chapter
MIN_WORDS_EDIT_NOVEL = 150  # Minimum words for final novel edit pass per chapter

###############################################################################
# FEATURE FLAGS
###############################################################################

SCRUB_NO_SCRUB = False  # Note this value is overridden by the argparser
EXPAND_OUTLINE = True  # Note this value is overridden by the argparser
ENABLE_FINAL_EDIT_PASS = True  # Note this value is overridden by the argparser
SCENE_GENERATION_PIPELINE = True

###############################################################################
# LANGUAGE CONFIGURATION
###############################################################################

NATIVE_LANGUAGE = "id"  # Default language for prompts (en or id)
# TRANSLATE_LANGUAGE = "Indonesian"  # If the user wants to translate, this'll be changed from empty to a language e.g 'French' or 'Russian'
# TRANSLATE_PROMPT_LANGUAGE = "Indonesian"  # If the user wants to translate their prompt, this'll be changed from empty to a language e.g 'French' or 'Russian'
TRANSLATE_LANGUAGE = ""  # If the user wants to translate, this'll be changed from empty to a language e.g 'French' or 'Russian'
TRANSLATE_PROMPT_LANGUAGE = ""  # If the user wants to translate their prompt, this'll be changed from empty to a language e.g 'French' or 'Russian'

###############################################################################
# LLM NATIVE REASONING MODE
###############################################################################

# CONTROLS native LLM-level reasoning (NOT app reasoning chain)
# Applies to models that support Ollama's 'think' parameter:
# - Llama-SEA-LION-v3.5-8B-R (models ending with -R suffix)
# - Qwen2.5-coder models (native reasoning variants)
#
# Setting to False prevents reasoning-related timeout/stuck issues
ENABLE_LLM_REASONING_MODE = True  # False = disable LLM native reasoning, True = allow reasoning

###############################################################################
# PYDANTIC VALIDATION CONFIGURATION
###############################################################################

MAX_PYDANTIC_RETRIES = 5  # Jumlah percobaan ulang maksimum untuk Pydantic validation
PYDANTIC_RETRY_DELAY = 3  # Delay in seconds before retry (helps Ollama model unload)
USE_PYDANTIC_PARSING = True  # Enable/disable structured output
PYDANTIC_WORD_COUNT_TOLERANCE = 100  # Tolerance for word count validation (±N words)

###############################################################################
# CHAPTER TITLE CONFIGURATION
###############################################################################

GENERATE_CHAPTER_TITLES = True
AUTO_CHAPTER_TITLES = True  # Flag to enable automatic chapter title generation
DEFAULT_CHAPTER_TITLE_PREFIX = "Chapter"  # Default prefix for chapter titles
ADD_CHAPTER_TITLES_TO_NOVEL_BODY_TEXT = True  # Add chapter titles to final novel text
CHAPTER_HEADER_FORMAT = "## Chapter {chapter_num}: {chapter_title}"
CHAPTER_MEMORY_WORDS = 250  # Adaptive: Short stories (≤3 chapters) use min(100, this value), longer stories use full value
TITLE_MAX_TOKENS = 50
MAX_WORDS_FOR_CHAPTER_TITLE_PROMPT = 500  # Maximum words of chapter content to use for title generation
MIN_WORDS_FOR_CHAPTER_TITLE = 3  # Minimum words for chapter title
MAX_LENGTH_CHAPTER_TITLE = 100  # Maximum character length for chapter title

###############################################################################
# DIRECTORY & OUTPUT CONFIGURATION
###############################################################################

STORIES_DIR = "Stories"  # Directory for generated stories
LOG_DIRECTORY = "Logs"  # Directory for log files
OPTIONAL_OUTPUT_NAME = ""
DEBUG = False

###############################################################################
# MARKDOWN & PDF OUTPUT CONFIGURATION
###############################################################################

# Markdown output configuration
INCLUDE_OUTLINE_IN_MD = True  # Include outline in final markdown output
INCLUDE_STATS_IN_MD = True  # Include statistics in final markdown output
INCLUDE_SUMMARY_IN_MD = True  # Include summary in final markdown output
INCLUDE_TAGS_IN_MD = True  # Include tags in final markdown output

# PDF generation configuration
ENABLE_PDF_GENERATION = True  # Enable PDF generation as post-processing step
PDF_FONT_FAMILY = "Georgia"  # Font family for PDF text
PDF_FONT_SIZE = 12  # Font size for regular text
PDF_TITLE_SIZE = 24  # Font size for title
PDF_CHAPTER_SIZE = 18  # Font size for chapter headings

# PDF readability improvements configuration
PDF_LINE_HEIGHT = 1.15  # Line height ratio for comfortable reading
PDF_PARAGRAPH_FIRST_LINE_INDENT = 12  # First line indent in points
PDF_PARAGRAPH_SPACING = 6  # Space between paragraphs in points
PDF_MARGIN_LEFT = 90  # Left margin in points (was 72, too cramped)
PDF_MARGIN_RIGHT = 90  # Right margin in points (was 72, too cramped)
PDF_MARGIN_TOP = 75  # Top margin in points (optimized for readability)
PDF_MARGIN_BOTTOM = 75  # Bottom margin in points (optimized for readability)

###############################################################################
# LANGCHAIN ENHANCEMENT CONFIGURATION
###############################################################################

USE_LOREBOOK = True  # Enable/disable lorebook system
LOREBOOK_K_RETRIEVAL = 5  # Number of lore entries to retrieve
LOREBOOK_PERSIST_DIR = "./lorebook_db"  # Directory for lorebook persistence
LOREBOOK_SIMILARITY_THRESHOLD = 0.7  # Minimum similarity for lore retrieval
LOREBOOK_AUTO_CLEAR = True  # Auto-clear lorebook for fresh runs (not resume)
ENABLE_GLOBAL_OUTLINE_REFINEMENT = True  # Flag to enable global outline refinement

###############################################################################
# REASONING CHAIN CONFIGURATION
###############################################################################

USE_REASONING_CHAIN = False  # Enable/disable two-pass reasoning
REASONING_LOG_SEPARATE = True  # Log reasoning to separate file
REASONING_CACHE_RESULTS = False  # Cache reasoning results
