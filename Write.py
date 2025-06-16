"""Main script for generating stories using AI models."""

#!/bin/python3

#!/bin/python3

import argparse
import time
import datetime
import os
import json
import sys
import shutil  # Untuk penulisan atomik
import importlib # Tambahkan importlib

import Writer.Config

import Writer.Interface.Wrapper
import Writer.PrintUtils
import Writer.Chapter.ChapterDetector
import Writer.Scrubber
import Writer.Statistics
import Writer.OutlineGenerator
import Writer.Chapter.ChapterGenerator
import Writer.StoryInfo
import Writer.NovelEditor
import Writer.Translator
# import Writer.Prompts # Dihapus karena kita akan menggunakan ActivePrompts yang dimuat secara dinamis
import Writer.Statistics  # Pastikan ini ada
import types # Untuk type hinting modul
from Writer.Pipeline import StoryPipeline # Import StoryPipeline


# Fungsi untuk memuat modul prompt secara dinamis
def load_active_prompts(native_language_code: str, logger_func_print, logger_func_warn, logger_func_error) -> types.ModuleType | None:
    """
    Loads the appropriate prompt module based on the native_language_code.
    Falls back to English if the specified language module is not found.
    Returns the loaded module or None if a critical error occurs.
    """
    active_prompts_module = None
    effective_language_code = native_language_code.lower() if native_language_code else 'en'

    if effective_language_code == 'en':
        try:
            import Writer.Prompts as Prompts_en
            active_prompts_module = Prompts_en
            logger_func_print(f"Using English prompts (Writer.Prompts) as NATIVE_LANGUAGE is '{effective_language_code}'.")
        except ImportError as e:
            logger_func_error(f"CRITICAL: Failed to import Writer.Prompts (English default): {e}.")
            return None
    else:
        try:
            module_name = f"Writer.Prompts_{effective_language_code}"
            active_prompts_module = importlib.import_module(module_name)
            logger_func_print(f"Successfully loaded prompt module '{module_name}' for NATIVE_LANGUAGE '{effective_language_code}'.")
        except ImportError:
            logger_func_warn(f"Prompt module for NATIVE_LANGUAGE '{effective_language_code}' ('{module_name}') not found. Falling back to English prompts (Writer.Prompts).")
            try:
                import Writer.Prompts as Prompts_en  # Fallback ke English
                active_prompts_module = Prompts_en
            except ImportError as e:
                logger_func_error(f"CRITICAL: Failed to import fallback Writer.Prompts (English default) after failing to load '{module_name}': {e}.")
                return None
        except Exception as e:
            logger_func_error(f"CRITICAL: Unexpected error loading prompt module for NATIVE_LANGUAGE '{effective_language_code}': {e}. Attempting fallback to English.")
            try:
                import Writer.Prompts as Prompts_en  # Fallback ke English
                active_prompts_module = Prompts_en
            except ImportError as ie:
                logger_func_error(f"CRITICAL: Failed to import fallback Writer.Prompts (English default) after unexpected error: {ie}.")
                return None

    if active_prompts_module is None:
        logger_func_error(f"CRITICAL: ActivePrompts module is None after attempting to load for NATIVE_LANGUAGE '{effective_language_code}'. This should not happen if fallbacks are working.")
    return active_prompts_module


# Setup Argparser
Parser = argparse.ArgumentParser()
Parser.add_argument("-Prompt", help="Path to file containing the prompt")
Parser.add_argument(
    "-Output",
    default="",
    type=str,
    help="Optional file output path, if none is speciifed, we will autogenerate a file name based on the story title",
)
Parser.add_argument(
    "-InitialOutlineModel",
    default=Writer.Config.INITIAL_OUTLINE_WRITER_MODEL,
    type=str,
    help="Model to use for writing the base outline content",
)
Parser.add_argument(
    "-ChapterOutlineModel",
    default=Writer.Config.CHAPTER_OUTLINE_WRITER_MODEL,
    type=str,
    help="Model to use for writing the per-chapter outline content",
)
Parser.add_argument(
    "-ChapterS1Model",
    default=Writer.Config.CHAPTER_STAGE1_WRITER_MODEL,
    type=str,
    help="Model to use for writing the chapter (stage 1: plot)",
)
Parser.add_argument(
    "-ChapterS2Model",
    default=Writer.Config.CHAPTER_STAGE2_WRITER_MODEL,
    type=str,
    help="Model to use for writing the chapter (stage 2: character development)",
)
Parser.add_argument(
    "-ChapterS3Model",
    default=Writer.Config.CHAPTER_STAGE3_WRITER_MODEL,
    type=str,
    help="Model to use for writing the chapter (stage 3: dialogue)",
)
Parser.add_argument(
    "-FinalNovelEditorModel",  # Nama argumen baru
    default=Writer.Config.FINAL_NOVEL_EDITOR_MODEL,  # Default dari config baru
    type=str,
    help="Model to use for the final novel-wide edit pass (via NovelEditor.py)",  # Help text baru
)
Parser.add_argument(
    "-ChapterRevisionModel",
    default=Writer.Config.CHAPTER_REVISION_WRITER_MODEL,
    type=str,
    help="Model to use for revising the chapter until it meets criteria",
)
Parser.add_argument(
    "-RevisionModel",
    default=Writer.Config.REVISION_MODEL,
    type=str,
    help="Model to use for generating constructive criticism",
)
Parser.add_argument(
    "-EvalModel",
    default=Writer.Config.EVAL_MODEL,
    type=str,
    help="Model to use for evaluating the rating out of 100",
)
Parser.add_argument(
    "-InfoModel",
    default=Writer.Config.INFO_MODEL,
    type=str,
    help="Model to use when generating summary/info at the end",
)
Parser.add_argument(
    "-ScrubModel",
    default=Writer.Config.SCRUB_MODEL,
    type=str,
    help="Model to use when scrubbing the story at the end",
)
Parser.add_argument(
    "-CheckerModel",
    default=Writer.Config.CHECKER_MODEL,
    type=str,
    help="Model to use when checking if the LLM cheated or not",
)
Parser.add_argument(
    "-TranslatorModel",
    default=Writer.Config.TRANSLATOR_MODEL,
    type=str,
    help="Model to use if translation of the story is enabled",
)
Parser.add_argument(
    "-Translate",
    default=Writer.Config.TRANSLATE_LANGUAGE,
    type=str,
    help="Specify a language to translate the story to - will not translate by default. Ex: 'French'",
)
Parser.add_argument(
    "-TranslatePrompt",
    default=Writer.Config.TRANSLATE_PROMPT_LANGUAGE,
    type=str,
    help="Specify a language to translate your input prompt to. Ex: 'French'",
)
Parser.add_argument("-Seed", default=12, type=int, help="Used to seed models.")
Parser.add_argument(
    "-OutlineMinRevisions",
    default=Writer.Config.OUTLINE_MIN_REVISIONS,
    type=int,
    help="Number of minimum revisions that the outline must be given prior to proceeding",
)
Parser.add_argument(
    "-OutlineMaxRevisions",
    default=Writer.Config.OUTLINE_MAX_REVISIONS,
    type=int,
    help="Max number of revisions that the outline may have",
)
Parser.add_argument(
    "-ChapterMinRevisions",
    default=Writer.Config.CHAPTER_MIN_REVISIONS,
    type=int,
    help="Number of minimum revisions that the chapter must be given prior to proceeding",
)
Parser.add_argument(
    "-ChapterMaxRevisions",
    default=Writer.Config.CHAPTER_MAX_REVISIONS,
    type=int,
    help="Max number of revisions that the chapter may have",
)
Parser.add_argument(
    "-NoChapterRevision", action="store_true", help="Disables Chapter Revisions"
)
Parser.add_argument(
    "-NoScrubChapters",
    action="store_true",
    help="Disables a final pass over the story to remove prompt leftovers/outline tidbits",
)
Parser.add_argument(
    "-ExpandOutline",
    action="store_true",
    default=True,
    help="Disables the system from expanding the outline for the story chapter by chapter prior to writing the story's chapter content",
)
Parser.add_argument(
    "-EnableFinalEditPass",
    action="store_true",
    default=True,
    help="Enable a final edit pass of the whole story prior to scrubbing",
)
Parser.add_argument(
    "-Debug",
    action="store_true",
    help="Print system prompts to stdout during generation",
)
Parser.add_argument(
    "-SceneGenerationPipeline",
    action="store_true",
    default=True,
    help="Use the new scene-by-scene generation pipeline as an initial starting point for chapter writing",
)
Parser.add_argument(
    "-Resume",
    default=None,
    type=str,
    help="Path to a .state.json file to resume a previous run.",
)
# Args = Parser.parse_args() # Pindahkan parsing argumen ke dalam main()


# Fungsi Helper untuk Save/Load State
def save_state(state_data, filepath):
    """Saves the current state to a JSON file atomically."""
    temp_filepath = filepath + ".tmp"
    try:
        with open(temp_filepath, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=4)
        # Operasi atomik: ganti file lama dengan yang baru
        shutil.move(temp_filepath, filepath)
    except (IOError, OSError) as e:  # Catch specific file errors
        print(f"FATAL: Failed to save state to {filepath}: {e}", file=sys.stderr)
        # Hapus file temp jika ada
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except OSError:
                pass  # Abaikan jika tidak bisa dihapus
    except Exception as e:  # Keep a fallback for truly unexpected errors
        print(
            f"FATAL: Unexpected error saving state to {filepath}: {type(e).__name__} - {e}",
            file=sys.stderr,
        )
        # Hapus file temp jika ada
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except OSError:
                pass  # Abaikan jika tidak bisa dihapus


def load_state(filepath):
    """Loads the state from a JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"State file not found: {filepath}")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            state_data = json.load(f)
        return state_data
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode state file {filepath}: {e}") from e
    except Exception as e:
        raise IOError(f"Failed to read state file {filepath}: {e}") from e


# Fungsi Helper Baru untuk Membangun MegaOutline
# _build_mega_outline and _get_outline_for_chapter are no longer used in main()
# as this logic is now part of StoryPipeline.
# def _build_mega_outline(current_state):
#    ... (removed) ...
# def _get_outline_for_chapter(SysLogger, current_state, chapter_index):
#    ... (removed) ...

# The definitions of _build_mega_outline and _get_outline_for_chapter that were previously here
# (even if commented out or misplaced inside a dummy main) are now fully removed.

def main():
    """Parses arguments, manages state (new run or resume), and orchestrates the story generation pipeline."""
    Args = Parser.parse_args()

    # --- AWAL BLOK SETUP CONFIG (UNTUK RUN BARU) ---
    if not Args.Resume: # Hanya set dari Args jika bukan resume
        Writer.Config.SEED = Args.Seed
        Writer.Config.INITIAL_OUTLINE_WRITER_MODEL = Args.InitialOutlineModel
        Writer.Config.CHAPTER_OUTLINE_WRITER_MODEL = Args.ChapterOutlineModel
        Writer.Config.CHAPTER_STAGE1_WRITER_MODEL = Args.ChapterS1Model
        Writer.Config.CHAPTER_STAGE2_WRITER_MODEL = Args.ChapterS2Model
        Writer.Config.CHAPTER_STAGE3_WRITER_MODEL = Args.ChapterS3Model
        Writer.Config.FINAL_NOVEL_EDITOR_MODEL = Args.FinalNovelEditorModel
        Writer.Config.CHAPTER_REVISION_WRITER_MODEL = Args.ChapterRevisionModel
        Writer.Config.EVAL_MODEL = Args.EvalModel
        Writer.Config.REVISION_MODEL = Args.RevisionModel
        Writer.Config.INFO_MODEL = Args.InfoModel
        Writer.Config.SCRUB_MODEL = Args.ScrubModel
        Writer.Config.CHECKER_MODEL = Args.CheckerModel
        Writer.Config.TRANSLATOR_MODEL = Args.TranslatorModel
        Writer.Config.TRANSLATE_LANGUAGE = Args.Translate
        Writer.Config.TRANSLATE_PROMPT_LANGUAGE = Args.TranslatePrompt
        Writer.Config.OUTLINE_MIN_REVISIONS = Args.OutlineMinRevisions
        Writer.Config.OUTLINE_MAX_REVISIONS = Args.OutlineMaxRevisions
        Writer.Config.CHAPTER_MIN_REVISIONS = Args.ChapterMinRevisions
        Writer.Config.CHAPTER_MAX_REVISIONS = Args.ChapterMaxRevisions
        Writer.Config.CHAPTER_NO_REVISIONS = Args.NoChapterRevision
        Writer.Config.SCRUB_NO_SCRUB = Args.NoScrubChapters
        Writer.Config.EXPAND_OUTLINE = Args.ExpandOutline
        Writer.Config.ENABLE_FINAL_EDIT_PASS = Args.EnableFinalEditPass
        Writer.Config.OPTIONAL_OUTPUT_NAME = Args.Output
        Writer.Config.SCENE_GENERATION_PIPELINE = Args.SceneGenerationPipeline
        
        # Atur Writer.Config.DEBUG berdasarkan nilai dari Config.py dan flag Args.Debug
        # Jika Args.Debug adalah True (flag -Debug diberikan), maka Writer.Config.DEBUG akan True.
        # Jika Args.Debug adalah False (flag -Debug tidak diberikan),
        # maka Writer.Config.DEBUG akan mempertahankan nilainya dari Config.py.
        current_debug_setting_from_config_file = Writer.Config.DEBUG
        Writer.Config.DEBUG = current_debug_setting_from_config_file or Args.Debug
        
        # Jika Anda menambahkan argumen -NativeLanguage, proses di sini:
        # Writer.Config.NATIVE_LANGUAGE = getattr(Args, 'NativeLanguage', Writer.Config.NATIVE_LANGUAGE)
    # --- AKHIR BLOK SETUP CONFIG ---

    # --- AWAL PEMUATAN PROMPT DINAMIS ---
    ActivePrompts = None
    # Dapatkan NATIVE_LANGUAGE dari Config, yang mungkin sudah di-override oleh Args atau state (jika resume)
    # Untuk run baru, ini akan mengambil dari Writer.Config (yang mungkin baru saja diatur oleh Args)
    # Untuk resume, Writer.Config akan di-override oleh state_config *setelah* blok ini jika Args.Resume True.
    # Jadi, kita perlu memastikan NATIVE_LANGUAGE dari state digunakan jika resume.
    # Ini akan ditangani nanti di blok resume. Untuk sekarang, kita gunakan apa yang ada di Writer.Config.
    
    _early_print = lambda msg: print(f"INFO: {msg}")
    _early_warn = lambda msg: print(f"WARNING: {msg}")
    _early_error = lambda msg: print(f"ERROR: {msg}")

    # Logika ini akan dijalankan sebelum SysLogger mungkin diinisialisasi jika ini adalah run baru.
    # Jika ini adalah resume, Writer.Config.NATIVE_LANGUAGE akan diatur dari state *sebelum* blok ini.
    # Namun, pemuatan prompt dinamis harus terjadi setelah konfigurasi (termasuk NATIVE_LANGUAGE) final.
    # Jadi, kita akan memindahkan bagian inti dari pemuatan prompt dinamis ke *setelah* konfigurasi dari state (jika resume).

    # Placeholder untuk ActivePrompts, akan diisi setelah konfigurasi NATIVE_LANGUAGE final.
    ActivePrompts = None # Default initialization
    # --- AKHIR PEMUATAN PROMPT DINAMIS (BAGIAN AWAL) ---

    # --- AWAL LOGIKA RESUME ---
    current_state = {}
    state_filepath = None
    log_directory = None  # Inisialisasi log_directory

    if Args.Resume:
        state_filepath = Args.Resume
        try:
            print(f"Attempting to resume from state file: {state_filepath}")
            current_state = load_state(state_filepath)
            if current_state.get("status") != "in_progress":
                print(
                    f"Run already completed or in unknown state ({current_state.get('status')}). Exiting."
                )
                sys.exit(1)

            # Pulihkan Konfigurasi dari state
            print("Restoring configuration from state file...")
            state_config = current_state.get("config", {})
            # Timpa nilai Writer.Config
            for key, value in state_config.items():
                # Periksa apakah atribut ada dan bukan metode bawaan
                if (
                    hasattr(Writer.Config, key)
                    and not callable(getattr(Writer.Config, key))
                    and not key.startswith("_")
                ):
                    setattr(Writer.Config, key, value) # Ini akan me-restore NATIVE_LANGUAGE
                    # print(f"  Restored Config.{key} = {value}") # Debugging
                # else:
                # print(f"  Skipping restore for {key}") # Debugging
            
            # --- PEMUATAN PROMPT DINAMIS (BAGIAN INTI SETELAH CONFIG DARI STATE) ---
            native_lang_config_resume = getattr(Writer.Config, 'NATIVE_LANGUAGE', 'en') # No lower() here, load_active_prompts handles it
            _early_print(f"NATIVE_LANGUAGE for resumed run, before dynamic prompt load: '{native_lang_config_resume}'")

            ActivePrompts = load_active_prompts(native_lang_config_resume, _early_print, _early_warn, _early_error)
            if ActivePrompts is None:
                _early_error(f"CRITICAL: Failed to load ActivePrompts for NATIVE_LANGUAGE '{native_lang_config_resume}'. Cannot continue.")
                sys.exit(1)

            sys.modules['Writer.Prompts'] = ActivePrompts
            _early_print(f"Dynamically set sys.modules['Writer.Prompts'] to '{ActivePrompts.__name__}'.")
            # --- AKHIR PEMUATAN PROMPT DINAMIS (BAGIAN INTI) ---

            # Setup Logger untuk resume
            log_directory = current_state.get("log_directory")
            if not log_directory or not os.path.isdir(log_directory):
                print(
                    f"FATAL: Log directory '{log_directory}' not found or invalid in state file. Cannot resume."
                )
                sys.exit(1)
            SysLogger = Writer.PrintUtils.Logger(_ExistingLogDir=log_directory)
            SysLogger.Log(
                f"Successfully resumed run from state file: {state_filepath}", 5
            )
            SysLogger.Log(f"NATIVE_LANGUAGE (resumed) set to '{native_lang_config_resume}'. Active prompt module: '{ActivePrompts.__name__}'.", 5) # Tambahan log

            # Pulihkan variabel penting dari state
            Prompt = current_state.get(
                "translated_prompt_content"
            ) or current_state.get(
                "input_prompt_content"
            )  # Prioritaskan terjemahan
            if not Prompt:
                SysLogger.Log("FATAL: Could not find prompt content in state file.", 7)
                sys.exit(1)
            # BasePrompt = current_state.get("input_prompt_content") # Removed unused variable
            Outline = current_state.get("full_outline")
            Elements = current_state.get("story_elements")
            RoughChapterOutline = current_state.get("rough_chapter_outline")
            BaseContext = current_state.get("base_context")
            NumChapters = current_state.get("total_chapters")
            ChapterOutlines = current_state.get("expanded_chapter_outlines", [])
            Chapters = current_state.get(
                "completed_chapters", []
            )  # List bab yang sudah jadi
            start_chapter = current_state.get("next_chapter_index", 1)
            last_completed_step = current_state.get("last_completed_step", "init")

            # Inisialisasi Interface (model sudah diatur di Writer.Config)
            Models = list(
                set(
                    [
                        getattr(Writer.Config, model_var)
                        for model_var in dir(Writer.Config)
                        if model_var.endswith("_MODEL")
                        and hasattr(Writer.Config, model_var)
                    ]
                )
            )
            Interface = Writer.Interface.Wrapper.Interface(Models)

        except (FileNotFoundError, ValueError, IOError) as e:
            print(f"FATAL: Error loading state file: {e}", file=sys.stderr)
            sys.exit(1)
        except (
            KeyError,
            AttributeError,
            TypeError,
        ) as e:  # Catch potential state structure/type errors
            print(
                f"FATAL: Error processing state data during resume setup: {type(e).__name__} - {e}",
                file=sys.stderr,
            )
            sys.exit(1)
        except Exception as e:  # Fallback for other unexpected errors
            print(
                f"FATAL: Unexpected error during resume setup: {type(e).__name__} - {e}",
                file=sys.stderr,
            )
            sys.exit(1)

    else:
        # --- AWAL LOGIKA RUN BARU ---
        # Config sudah di-set dari Args di awal fungsi main() jika bukan resume.
    
        # --- PEMUATAN PROMPT DINAMIS (BAGIAN INTI UNTUK RUN BARU) ---
        # NATIVE_LANGUAGE sudah final di Writer.Config pada titik ini (dari Args atau default Config)
        native_lang_config_new = getattr(Writer.Config, 'NATIVE_LANGUAGE', 'en') # No lower() here
        _early_print(f"NATIVE_LANGUAGE for new run, before dynamic prompt load: '{native_lang_config_new}'")

        ActivePrompts = load_active_prompts(native_lang_config_new, _early_print, _early_warn, _early_error)
        if ActivePrompts is None:
            _early_error(f"CRITICAL: Failed to load ActivePrompts for NATIVE_LANGUAGE '{native_lang_config_new}'. Cannot continue.")
            sys.exit(1)
            
        sys.modules['Writer.Prompts'] = ActivePrompts
        _early_print(f"Dynamically set sys.modules['Writer.Prompts'] to '{ActivePrompts.__name__}'.")
        # --- AKHIR PEMUATAN PROMPT DINAMIS (BAGIAN INTI) ---

        SysLogger = Writer.PrintUtils.Logger()
        log_directory = SysLogger.LogDirPrefix
        SysLogger.Log(f"NATIVE_LANGUAGE set to '{native_lang_config_new}'. Active prompt module: '{ActivePrompts.__name__}'.", 5)


        # Buat state awal
        current_state = {
            "status": "in_progress",
            "log_directory": log_directory,
            "config": {},
        }
        # Salin SEMUA konfigurasi dari Args ke state
        for key, value in vars(Args).items():
            if key != "Resume":  # Jangan simpan state Resume itu sendiri
                current_state["config"][key] = value
        # Salin juga SEMUA konstanta dari Writer.Config ke state
        for key in dir(Writer.Config):
            if not key.startswith("_") and key.isupper():  # Simpan konstanta config
                current_state["config"][key] = getattr(Writer.Config, key)

        # Tentukan state_filepath
        state_filepath = os.path.join(log_directory, "run.state.json")
        current_state["state_filepath"] = (
            state_filepath  # Simpan path state itu sendiri
        )

        # Inisialisasi Interface (setelah config diatur)
        Models = list(
            set(
                [
                    getattr(Writer.Config, model_var)
                    for model_var in dir(Writer.Config)
                    if model_var.endswith("_MODEL")
                    and hasattr(Writer.Config, model_var)
                ]
            )
        )
        Interface = Writer.Interface.Wrapper.Interface(Models)

        # Load User Prompt
        Prompt = ""
        if Args.Prompt is None:
            # Cek apakah prompt ada di config state (seharusnya tidak untuk run baru, tapi untuk keamanan)
            if (
                "input_prompt_file" in current_state["config"]
                and current_state["config"]["input_prompt_file"]
            ):
                Args.Prompt = current_state["config"]["input_prompt_file"]
                SysLogger.Log(
                    f"Warning: Using prompt file from config: {Args.Prompt}", 6
                )
            else:
                SysLogger.Log(
                    "FATAL: No Prompt Provided (-Prompt) and none in config.", 7
                )
                raise ValueError("No Prompt Provided (-Prompt)")

        try:
            with open(Args.Prompt, "r", encoding="utf-8") as f:  # Tambahkan encoding
                Prompt = f.read()
        except FileNotFoundError:
            SysLogger.Log(f"FATAL: Prompt file not found: {Args.Prompt}", 7)
            sys.exit(1)
        except IOError as e:  # Catch file reading errors
            SysLogger.Log(f"FATAL: Error reading prompt file {Args.Prompt}: {e}", 7)
            sys.exit(1)
        except Exception as e:  # Fallback
            SysLogger.Log(
                f"FATAL: Unexpected error reading prompt file {Args.Prompt}: {type(e).__name__} - {e}",
                7,
            )
            sys.exit(1)

        current_state["input_prompt_file"] = Args.Prompt
        # Prompt asli disimpan sebelum potensi terjemahan ke native
        original_prompt_content_for_state = Prompt 
        current_state["input_prompt_content"] = original_prompt_content_for_state
        translated_to_native_prompt_content_for_state = None

        # --- AWAL BLOK TERJEMAHAN PROMPT INPUT (HANYA UNTUK RUN BARU) ---
        # 'Prompt' adalah variabel yang berisi konten prompt dari file.
        # Writer.Config.TRANSLATE_PROMPT_LANGUAGE adalah bahasa ASLI dari file input prompt pengguna.
        # Writer.Config.NATIVE_LANGUAGE adalah bahasa target untuk generasi internal.
        if Writer.Config.TRANSLATE_PROMPT_LANGUAGE and \
           Writer.Config.TRANSLATE_PROMPT_LANGUAGE.lower() != Writer.Config.NATIVE_LANGUAGE.lower():
            SysLogger.Log(
                f"Translating user prompt from '{Writer.Config.TRANSLATE_PROMPT_LANGUAGE}' to native language '{Writer.Config.NATIVE_LANGUAGE}'...",
                4,
            )
            Prompt = Writer.Translator.TranslatePrompt( # Prompt di sini adalah konten yang akan diterjemahkan
                Interface, SysLogger, Prompt,
                _SourceLanguage=Writer.Config.TRANSLATE_PROMPT_LANGUAGE,
                TargetLang=Writer.Config.NATIVE_LANGUAGE
            )
            translated_to_native_prompt_content_for_state = Prompt # Simpan hasil terjemahan
            SysLogger.Log("User prompt translation to native language complete.", 4)
        
        if translated_to_native_prompt_content_for_state:
            current_state["translated_to_native_prompt_content"] = translated_to_native_prompt_content_for_state
        # 'Prompt' sekarang berisi versi yang akan digunakan untuk generasi (asli atau terjemahan ke native)
        # --- AKHIR BLOK TERJEMAHAN PROMPT INPUT ---

        # Inisialisasi variabel lain untuk run baru
        Outline, Elements, RoughChapterOutline, BaseContext = (
            None,
            None,
            None,
            None,
        )  # Gunakan None untuk menandakan belum dibuat
        NumChapters = None
        ChapterOutlines = []
        Chapters = []
        start_chapter = 1
        last_completed_step = "init"
        current_state["last_completed_step"] = last_completed_step
        current_state["completed_chapters"] = []
        current_state["next_chapter_index"] = 1

        # Save state awal
        SysLogger.Log(f"Saving initial state to {state_filepath}", 6)
        save_state(current_state, state_filepath)
        # --- AKHIR LOGIKA RUN BARU ---

    # --- AKHIR LOGIKA RESUME ---

    # Ukur waktu mulai (setelah setup)
    StartTime = time.time()  # Pindahkan ini setelah setup resume/baru
    current_state["start_time"] = StartTime # Store StartTime in state for potential use by pipeline post-processing

    # --- Mulai logika utama ---
    # Instantiate and run the pipeline
    try:
        pipeline = StoryPipeline(Interface, SysLogger, Writer.Config, ActivePrompts)

        # Determine initial_prompt_for_outline based on new/resume and translation
        # This prompt is what gets passed to the outline generation stage
        initial_prompt_for_outline_gen = ""
        if Args.Resume:
            # For resume, the prompt for outline generation would have been the one used initially.
            # It's either translated_to_native_prompt_content or input_prompt_content
            initial_prompt_for_outline_gen = current_state.get("translated_to_native_prompt_content") or \
                                           current_state.get("input_prompt_content")
            if not initial_prompt_for_outline_gen:
                SysLogger.Log("FATAL: Could not find prompt content in state file for pipeline (resumed run).", 7)
                sys.exit(1)
        else:
            # For new run, 'Prompt' variable (which might be translated to native) holds the content for outline.
            initial_prompt_for_outline_gen = Prompt
            if not initial_prompt_for_outline_gen :
                 SysLogger.Log("FATAL: Prompt content for pipeline is empty (new run).", 7)
                 sys.exit(1)
        
        # Pass necessary original prompt details for post-processing if needed by the pipeline later
        original_prompt_content_for_pp = current_state.get("input_prompt_content")
        translated_prompt_content_for_pp = current_state.get("translated_to_native_prompt_content")
        input_prompt_file_for_pp = current_state.get("input_prompt_file")


        current_state = pipeline.run_pipeline(
            current_state,
            state_filepath,
            initial_prompt_for_outline_gen,
            Args=Args, # Pass Args for potential use in pipeline stages
            original_prompt_content_for_post_processing=original_prompt_content_for_pp,
            translated_prompt_content_for_post_processing=translated_prompt_content_for_pp,
            start_time_for_post_processing=StartTime, # Pass StartTime
            log_directory_for_post_processing=log_directory,
            input_prompt_file_for_post_processing=input_prompt_file_for_pp
        )

        # After pipeline.run_pipeline finishes, current_state is the final state.
        final_step = current_state.get("last_completed_step")
        if final_step == "complete" or final_step == "complete_through_outline": # Adjust as pipeline grows
            SysLogger.Log(f"Main: Story generation pipeline ended successfully at step: {final_step}.", 5)
        else:
            SysLogger.Log(f"Main: Story generation pipeline ended at step: {final_step}. Check logs.", 6)

    except Exception as e:
        SysLogger.Log(f"FATAL error during pipeline execution: {e}", 7)
        import traceback
        traceback.print_exc()
        # Ensure state is saved even on catastrophic pipeline failure, if possible
        try:
            current_state["status"] = "error"
            current_state["error_message"] = str(e)
            save_state(current_state, state_filepath if state_filepath else "error_state.json")
            SysLogger.Log(f"Saved error state to {state_filepath if state_filepath else 'error_state.json'}",6)
        except Exception as se:
            SysLogger.Log(f"CRITICAL: Could not save error state: {se}",7)
        sys.exit(1)

    # --- Old logic below this point will be progressively removed or moved into the pipeline ---

    # Retrieve potentially updated values from current_state if they were handled by the pipeline
    # For now, Outline and NumChapters are examples.
    Outline = current_state.get("full_outline")
    NumChapters = current_state.get("total_chapters")
    # last_completed_step needs to be read back if main loop continues to depend on it here
    last_completed_step = current_state.get("last_completed_step")


    # Detect the number of chapters is now handled by the pipeline.
    # The old logic below is removed.
    # if last_completed_step == "outline":
    #    ...
    # elif NumChapters is None:
    #    ...
    # else:
    #    ...

    # Update local variables that might have been changed by the pipeline and are needed by subsequent old code
    # NumChapters is crucial for the next block (Per-Chapter Outline) if it's still here.
    NumChapters = current_state.get("total_chapters")
    Outline = current_state.get("full_outline") # Potentially refined by pipeline steps later
    # Elements, RoughChapterOutline, BaseContext might also be updated by pipeline.
    Elements = current_state.get("story_elements")
    RoughChapterOutline = current_state.get("rough_chapter_outline")
    BaseContext = current_state.get("base_context")
    ChapterOutlines = current_state.get("expanded_chapter_outlines", []) # This will be populated by a pipeline stage
    Chapters = current_state.get("completed_chapters", [])
    start_chapter = current_state.get("next_chapter_index", 1)
    # last_completed_step is already up-to-date from pipeline return

    # Ensure NumChapters is available if the next block (Per-Chapter Outline) is still to be executed from main
    # This check becomes less critical as more logic moves to the pipeline.
    if last_completed_step == "detect_chapters" and NumChapters is None:
        SysLogger.Log(
            "FATAL: Pipeline completed 'detect_chapters' but NumChapters is still None in main.", 7
        )
        sys.exit(1)


    # Write Per-Chapter Outline is now handled by the pipeline.
    # The old logic below is removed.
    # if Writer.Config.EXPAND_OUTLINE:
    #    if last_completed_step == "detect_chapters" or last_completed_step == "refine_chapters": # refine_chapters is new state from pipeline
    #        ...
    #    elif last_completed_step not in [...]: (this complex condition is handled by pipeline)
    #        ...
    #    else:
    #        ...
    # else:
    #    ...

    # Update local variables that might have been changed by the pipeline.
    Outline = current_state.get("full_outline")
    ChapterOutlines = current_state.get("expanded_chapter_outlines", [])
    # last_completed_step is already up-to-date.

    # The step_before_chapters logic, MegaOutline creation, and the chapter writing loop
    # are now handled by the StoryPipeline._write_chapters_stage or its helpers.
    # Old logic is removed from here.

    # Update local variables that might have been changed by the pipeline.
    Chapters = current_state.get("completed_chapters", [])
    # last_completed_step is already up-to-date from the pipeline's return.
    # The entire post-processing block, including saving files and final state updates,
    # is now handled by the StoryPipeline._perform_post_processing_stage.

    # Final check on the status from the pipeline.
    if current_state.get("last_completed_step") == "complete":
        SysLogger.Log("Main: Pipeline confirmed run completion.", 5)
        # Potentially print final file paths from current_state if desired
        final_md = current_state.get("final_story_path", "N/A")
        final_json = current_state.get("final_json_path", "N/A")
        SysLogger.Log(f"Main: Final MD output: {final_md}", 5)
        SysLogger.Log(f"Main: Final JSON output: {final_json}", 5)
    elif current_state.get("status") == "error":
        SysLogger.Log(f"Main: Pipeline reported an error: {current_state.get('error_message', 'Unknown error')}", 7)
    else:
        SysLogger.Log(f"Main: Pipeline ended with step: {current_state.get('last_completed_step')}. This might indicate an incomplete run if not 'complete'.", 6)


if __name__ == "__main__":
    main()
