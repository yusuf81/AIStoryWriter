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
###############################################################################

###############################################################################
# LLM MODEL CONFIGURATION
###############################################################################

# Default model for all tasks (use provider://model-name format)
# Provider formats:
#   - google://gemini-2.5-flash         (Google Genai, requires GOOGLE_API_KEY)
#   - google://gemini-flash-lite-latest (Google Genai, lightweight)
#   - openrouter://anthropic/claude-3.5-sonnet (OpenRouter, requires OPENROUTER_API_KEY)
#   - ollama://qwen2.5:32b              (Ollama, uses OLLAMA_HOST)
#   - qwen2.5:32b                       (Ollama, uses OLLAMA_HOST when no provider specified)
ollamasemua = "google://gemini-flash-lite-latest"
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
#EMBEDDING_MODEL = "ollama://qwen3-embedding:latest"
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

###############################################################################
# RETRY CONFIGURATION
###############################################################################

# Maximum retries for each provider
MAX_PYDANTIC_RETRIES = 5  # Pydantic validation retries
MAX_GOOGLE_RETRIES = 2  # Google Genai API retries
MAX_OPENROUTER_RETRIES = 2  # OpenRouter API retries
MAX_RETRIES_CHAPTER_TITLE = 3  # Chapter title generation retries

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
