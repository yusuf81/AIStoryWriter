INITIAL_OUTLINE_WRITER_MODEL = (
    "ollama://gemma3:27b@10.23.82.116"  # Note this value is overridden by the argparser
)
CHAPTER_OUTLINE_WRITER_MODEL = (
    "ollama://gemma3:27b@10.23.82.116"  # Note this value is overridden by the argparser
)
CHAPTER_STAGE1_WRITER_MODEL = (
    "ollama://gemma3:27b@10.23.82.116"  # Note this value is overridden by the argparser
)
CHAPTER_STAGE2_WRITER_MODEL = (
    "ollama://gemma3:27b@10.23.82.116"  # Note this value is overridden by the argparser
)
CHAPTER_STAGE3_WRITER_MODEL = (
    "ollama://gemma3:27b@10.23.82.116"  # Note this value is overridden by the argparser
)
FINAL_NOVEL_EDITOR_MODEL = "ollama://gemma3:27b@10.23.82.116"

# Model for the final novel-wide edit pass (used by NovelEditor.py) # Note this value is overridden by the argparser
CHAPTER_REVISION_WRITER_MODEL = "ollama://qwen2.5:32b@10.23.82.116"  # Note this value is overridden by the argparser
REVISION_MODEL = "ollama://qwen2.5:32b@10.23.82.116"  # Note this value is overridden by the argparser
EVAL_MODEL = "ollama://qwen2.5:32b@10.23.82.116"  # Note this value is overridden by the argparser
INFO_MODEL = "ollama://qwen2.5:32b@10.23.82.116"  # Note this value is overridden by the argparser
SCRUB_MODEL = "ollama://qwen2.5:32b@10.23.82.116"  # Note this value is overridden by the argparser
CHECKER_MODEL = "ollama://qwen2.5:32b@10.23.82.116"  # Model used to check results
TRANSLATOR_MODEL = "ollama://qwen2.5:32b@10.23.82.116"
FAST_MODEL_NAME = (
    "ollama://qwen2:7b@10.23.82.116"  # Default fast model for tasks like titling
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

OUTLINE_QUALITY = 87  # Note this value is overridden by the argparser
OUTLINE_MIN_REVISIONS = 0  # Note this value is overridden by the argparser
OUTLINE_MAX_REVISIONS = 3  # Note this value is overridden by the argparser
CHAPTER_NO_REVISIONS = False  # Note this value is overridden by the argparser # disables all revision checks for the chapter, overriding any other chapter quality/revision settings
CHAPTER_QUALITY = 85  # Note this value is overridden by the argparser
CHAPTER_MIN_REVISIONS = 0  # Note this value is overridden by the argparser
CHAPTER_MAX_REVISIONS = 3  # Note this value is overridden by the argparser

# Minimum Word Counts for SafeGenerateText calls
MIN_WORDS_TRANSLATE_PROMPT = 10  # Minimum words for prompt translation
MIN_WORDS_INITIAL_OUTLINE = 250  # Minimum words for initial outline generation
MIN_WORDS_REVISE_OUTLINE = 250  # Minimum words for outline revision
MIN_WORDS_PER_CHAPTER_OUTLINE = 50  # Minimum words for per-chapter outline generation
MIN_WORDS_STORY_ELEMENTS = 150  # Minimum words for story elements generation
MIN_WORDS_CHAPTER_SEGMENT_EXTRACT = (
    120  # Minimum words for extracting chapter outline segment
)
MIN_WORDS_CHAPTER_SUMMARY = 100  # Minimum words for summarizing previous chapter
MIN_WORDS_CHAPTER_DRAFT = 100  # Minimum words for chapter draft stages (1, 2, 3)
MIN_WORDS_REVISE_CHAPTER = 100  # Minimum words for chapter revision
MIN_WORDS_OUTLINE_FEEDBACK = 70  # Minimum words for outline feedback/critique
MIN_WORDS_SCENE_OUTLINE = 100  # Minimum words for scene-by-scene outline generation
MIN_WORDS_SCENE_WRITE = 100  # Minimum words for writing a scene from its outline
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

# Maximum retries for SafeGenerateJSON
MAX_JSON_RETRIES = 5  # Jumlah percobaan ulang maksimum untuk SafeGenerateJSON

# Maximum retries for SafeGenerateText (whitespace/short response)
MAX_TEXT_RETRIES = 5  # Jumlah percobaan ulang maksimum untuk SafeGenerateText

# Added based on test_pipeline.py AttributeErrors
CHAPTER_HEADER_FORMAT = "### Chapter {chapter_num}: {chapter_title}"
CHAPTER_MEMORY_WORDS = 250
GENERATE_CHAPTER_TITLES = True
TITLE_MAX_TOKENS = 50


"ollama://mychen76/gemma3_cline_roocode_qat:12b@10.23.147.239"
"google://gemini-1.5-pro"
