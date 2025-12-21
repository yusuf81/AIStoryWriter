#ollamasemua="ollama://huihui_ai/qwen3-abliterated:16b@10.23.82.116"
#ollamasemua="huihui_ai/qwen2.5-abliterate:32b"
#ollamasemua="aisingapore/Qwen-SEA-LION-v4-32B-IT:latest"
ollamasemua="aisingapore/Llama-SEA-LION-v3.5-8B-R:latest"
#ollamasemua="aisingapore/Gemma-SEA-LION-v4-27B-IT:latest"
INITIAL_OUTLINE_WRITER_MODEL = (
    #"ollama://gemma3:27b@10.23.82.116"  # Note this value is overridden by the argparser
    ollamasemua
)
CHAPTER_OUTLINE_WRITER_MODEL = (
#    "ollama://gemma3:27b@10.23.82.116"  # Note this value is overridden by the argparser
    ollamasemua
)
CHAPTER_STAGE1_WRITER_MODEL = (
#    "ollama://gemma3:27b@10.23.82.116"  # Note this value is overridden by the argparser
    ollamasemua
)
CHAPTER_STAGE2_WRITER_MODEL = (
#    "ollama://gemma3:27b@10.23.82.116"  # Note this value is overridden by the argparser
    ollamasemua
)
CHAPTER_STAGE3_WRITER_MODEL = (
#    "ollama://gemma3:27b@10.23.82.116"  # Note this value is overridden by the argparser
    ollamasemua
)
#FINAL_NOVEL_EDITOR_MODEL = "ollama://gemma3:27b@10.23.82.116"
FINAL_NOVEL_EDITOR_MODEL = ollamasemua

# Model for the final novel-wide edit pass (used by NovelEditor.py) # Note this value is overridden by the argparser
#CHAPTER_REVISION_WRITER_MODEL = "ollama://qwen2.5:32b@10.23.147.239"  # Note this value is overridden by the argparser
CHAPTER_REVISION_WRITER_MODEL = ollamasemua  # Note this value is overridden by the argparser
REVISION_MODEL = ollamasemua  # Note this value is overridden by the argparser
EVAL_MODEL = ollamasemua  # Note this value is overridden by the argparser
INFO_MODEL = ollamasemua  # Note this value is overridden by the argparser
SCRUB_MODEL = ollamasemua  # Note this value is overridden by the argparser
CHECKER_MODEL = ollamasemua # Model used to check results
TRANSLATOR_MODEL = ollamasemua
FAST_MODEL = (
#    "ollama://gemma3:27b@10.23.82.116"  # Default fast model for tasks like titling
    ollamasemua  # Default fast model for tasks like titling
)

# OLLAMA_CTX = 8192
OLLAMA_CTX = 16384

OLLAMA_HOST = "10.23.82.116:11434"
# OLLAMA_HOST = "10.23.147.239:11434"


SEED = 12  # Note this value is overridden by the argparser

# TRANSLATE_LANGUAGE = "Indonesian"  # If the user wants to translate, this'll be changed from empty to a language e.g 'French' or 'Russian'
# TRANSLATE_PROMPT_LANGUAGE = "Indonesian"  # If the user wants to translate their prompt, this'll be changed from empty to a language e.g 'French' or 'Russian'

TRANSLATE_LANGUAGE = ""  # If the user wants to translate, this'll be changed from empty to a language e.g 'French' or 'Russian'
TRANSLATE_PROMPT_LANGUAGE = ""  # If the user wants to translate their prompt, this'll be changed from empty to a language e.g 'French' or 'Russian'

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

SCRUB_NO_SCRUB = False  # Note this value is overridden by the argparser
EXPAND_OUTLINE = True  # Note this value is overridden by the argparser
ENABLE_FINAL_EDIT_PASS = True  # Note this value is overridden by the argparser

SCENE_GENERATION_PIPELINE = True

OPTIONAL_OUTPUT_NAME = ""

DEBUG = False

# NATIVE_LANGUAGE = "en"  # Default ke Bahasa Inggris. Akan diubah menjadi "id" untuk pengujian.
# Nilai ini bisa juga di-override oleh argumen command-line jika diinginkan di masa depan.
NATIVE_LANGUAGE = "id"

# Maximum retries for Pydantic validation
MAX_PYDANTIC_RETRIES = 5  # Jumlah percobaan ulang maksimum untuk Pydantic validation

# Maximum retries for OpenRouter API
MAX_OPENROUTER_RETRIES = 2  # Maximum retries for OpenRouter API calls

# Maximum retries for Google API calls
MAX_GOOGLE_RETRIES = 2

# Configuration comment removed - SafeGenerateText is no longer used
# MAX_TEXT_RETRIES = 5  # This is deprecated as SafeGenerateText is replaced

# Added based on test_pipeline.py AttributeErrors
CHAPTER_HEADER_FORMAT = "## Chapter {chapter_num}: {chapter_title}"
CHAPTER_MEMORY_WORDS = 250  # Adaptive: Short stories (≤3 chapters) use min(100, this value), longer stories use full value
GENERATE_CHAPTER_TITLES = True
TITLE_MAX_TOKENS = 50
MAX_WORDS_FOR_CHAPTER_TITLE_PROMPT = 500  # Maximum words of chapter content to use for title generation
MIN_WORDS_FOR_CHAPTER_TITLE = 3  # Minimum words for chapter title
MAX_LENGTH_CHAPTER_TITLE = 100  # Maximum character length for chapter title
MAX_RETRIES_CHAPTER_TITLE = 3  # Maximum retries for chapter title generation
ENABLE_GLOBAL_OUTLINE_REFINEMENT = True  # Flag to enable global outline refinement
AUTO_CHAPTER_TITLES = True  # Flag to enable automatic chapter title generation
DEFAULT_CHAPTER_TITLE_PREFIX = "Chapter"  # Default prefix for chapter titles
ADD_CHAPTER_TITLES_TO_NOVEL_BODY_TEXT = True  # Add chapter titles to final novel text
STORIES_DIR = "Stories"  # Directory for generated stories
LOG_DIRECTORY = "Logs"  # Directory for log files

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

# LangChain Enhancement Configuration
USE_LOREBOOK = True  # Enable/disable lorebook system
LOREBOOK_K_RETRIEVAL = 5  # Number of lore entries to retrieve
LOREBOOK_PERSIST_DIR = "./lorebook_db"  # Directory for lorebook persistence
LOREBOOK_SIMILARITY_THRESHOLD = 0.7  # Minimum similarity for lore retrieval
LOREBOOK_AUTO_CLEAR = True  # Auto-clear lorebook for fresh runs (not resume)

USE_PYDANTIC_PARSING = True  # Enable/disable structured output
PYDANTIC_WORD_COUNT_TOLERANCE = 100  # Tolerance for word count validation (±N words)

USE_REASONING_CHAIN = True  # Enable/disable two-pass reasoning
REASONING_MODEL = CHAPTER_STAGE1_WRITER_MODEL  # Model to use for reasoning generation
REASONING_LOG_SEPARATE = True  # Log reasoning to separate file
REASONING_CACHE_RESULTS = False  # Cache reasoning results

# Embedding Model Configuration
EMBEDDING_MODEL = "ollama://nomic-embed-text:latest@10.23.82.116"  # Embedding model string (provider://format). Must be explicitly set.
EMBEDDING_DIMENSIONS = 768  # Default embedding dimensions (for nomic-embed-text)
EMBEDDING_CTX = 8192  # Context window for embeddings
EMBEDDING_FALLBACK_ENABLED = False  # Fail fast, no automatic fallback


# Example model URLs for reference (not actively used)
"ollama://mychen76/gemma3_cline_roocode_qat:12b@10.23.147.239"
"google://gemini-3-flash-preview"  # Updated to current model series
