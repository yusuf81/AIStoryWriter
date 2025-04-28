"""Main script for generating stories using AI models."""

#!/bin/python3

#!/bin/python3

import argparse
import time
import datetime
import os
import json
import sys  # Tambahkan ini
import shutil  # Untuk penulisan atomik

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
import Writer.Prompts
import Writer.Statistics  # Pastikan ini ada


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
# Parser.add_argument(
#     "-ChapterS4Model",
#     default=Writer.Config.CHAPTER_STAGE4_WRITER_MODEL, # Default diambil dari config baru
#     type=str,
#     help="Model to use for writing the chapter (stage 4: final correction pass)",
# )
Parser.add_argument(
    "-FinalNovelEditorModel", # Nama argumen baru
    default=Writer.Config.FINAL_NOVEL_EDITOR_MODEL, # Default dari config baru
    type=str,
    help="Model to use for the final novel-wide edit pass (via NovelEditor.py)", # Help text baru
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
def _build_mega_outline(current_state):
    """Builds the MegaOutline string from the current state."""
    Elements = current_state.get("story_elements", "")
    ChapterOutlines = current_state.get("expanded_chapter_outlines", [])
    DetailedOutline = ""
    if Writer.Config.EXPAND_OUTLINE and ChapterOutlines:
        for Chapter in ChapterOutlines:
            DetailedOutline += Chapter + "\n\n"
    MegaOutline = f"""
# Base Outline
{Elements if Elements else "N/A"}

# Detailed Outline
{DetailedOutline if DetailedOutline else "N/A"}
"""
    return MegaOutline


# Fungsi Helper Baru untuk Mendapatkan Outline Bab dengan Fallback
def _get_outline_for_chapter(SysLogger, current_state, chapter_index):
    """Determines the best outline to use for a specific chapter, with fallback."""
    Outline = current_state.get("full_outline", "")
    ChapterOutlines = current_state.get("expanded_chapter_outlines", [])
    MegaOutline = _build_mega_outline(current_state)  # Bangun untuk potensi penggunaan

    # Default ke MegaOutline jika ekspansi aktif & berhasil, jika tidak, ke base outline
    UsedOutline = (
        MegaOutline if Writer.Config.EXPAND_OUTLINE and ChapterOutlines else Outline
    )

    # Jika ekspansi aktif dan outline bab spesifik ada, coba validasi dan gunakan
    if (
        Writer.Config.EXPAND_OUTLINE
        and ChapterOutlines
        and len(ChapterOutlines) >= chapter_index
    ):
        potential_expanded_outline = ChapterOutlines[chapter_index - 1]
        # --- AWAL BLOK VALIDASI ---
        min_len_threshold = (
            Writer.Config.MIN_WORDS_PER_CHAPTER_OUTLINE
        )  # Ambil batas minimal dari config
        word_count = Writer.Statistics.GetWordCount(potential_expanded_outline)

        if word_count >= min_len_threshold:
            # Outline yang diperluas valid, gunakan ini
            SysLogger.Log(
                f"Using valid expanded outline for Chapter {chapter_index} from state.",
                6,
            )
            return potential_expanded_outline
        else:
            # Outline yang diperluas tidak valid/terlalu pendek, log peringatan dan biarkan fallback terjadi
            SysLogger.Log(
                f"Warning: Expanded outline for Chapter {chapter_index} from state is too short ({word_count} words, min {min_len_threshold}). Falling back to general outline.",
                6,
            )
        # --- AKHIR BLOK VALIDASI ---
        # Jika validasi gagal, kita tidak return di sini, biarkan fungsi melanjutkan ke fallback di bawah

    # Fallback jika ekspansi tidak aktif, atau outline bab spesifik tidak ada/tidak valid
    if not UsedOutline:  # Fallback terakhir jika UsedOutline juga kosong
        SysLogger.Log(
            f"Warning: No valid outline found for Chapter {chapter_index}, using base outline as last resort.",
            6,
        )
        return (
            Outline if Outline else ""
        )  # Kembalikan Outline dasar atau string kosong jika tidak ada
    else:
        SysLogger.Log(
            f"Using general outline (MegaOutline or Base) for Chapter {chapter_index}.",
            6,
        )
        return UsedOutline  # Return Mega atau Base outline


def main():
    """Parses arguments, manages state (new run or resume), and orchestrates the story generation pipeline."""
    Args = Parser.parse_args()  # Pindahkan parsing ke sini

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
                    setattr(Writer.Config, key, value)
                    # print(f"  Restored Config.{key} = {value}") # Debugging
                # else:
                # print(f"  Skipping restore for {key}") # Debugging

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
        # Setup Config dari Args
        Writer.Config.SEED = Args.Seed
        Writer.Config.INITIAL_OUTLINE_WRITER_MODEL = Args.InitialOutlineModel
        Writer.Config.CHAPTER_OUTLINE_WRITER_MODEL = Args.ChapterOutlineModel
        Writer.Config.CHAPTER_STAGE1_WRITER_MODEL = Args.ChapterS1Model
        Writer.Config.CHAPTER_STAGE2_WRITER_MODEL = Args.ChapterS2Model
        Writer.Config.CHAPTER_STAGE3_WRITER_MODEL = Args.ChapterS3Model
        # Writer.Config.CHAPTER_STAGE4_WRITER_MODEL = Args.ChapterS4Model # Baris lama dikomentari/dihapus
        Writer.Config.FINAL_NOVEL_EDITOR_MODEL = Args.FinalNovelEditorModel # Gunakan nama argumen dan variabel config baru
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
        Writer.Config.DEBUG = Args.Debug

        # Setup Logger untuk run baru
        SysLogger = Writer.PrintUtils.Logger()
        log_directory = (
            SysLogger.LogDirPrefix
        )  # Dapatkan direktori log yang baru dibuat

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
        current_state["input_prompt_content"] = Prompt
        # BasePrompt = Prompt # Removed unused variable

        # Translate prompt jika perlu (sebelum save state awal)
        if Writer.Config.TRANSLATE_PROMPT_LANGUAGE != "":
            SysLogger.Log(
                f"Translating prompt to {Writer.Config.TRANSLATE_PROMPT_LANGUAGE}...", 4
            )
            Prompt = Writer.Translator.TranslatePrompt(
                Interface, SysLogger, Prompt, Writer.Config.TRANSLATE_PROMPT_LANGUAGE
            )
            current_state["translated_prompt_content"] = (
                Prompt  # Simpan hasil terjemahan jika ada
            )
            SysLogger.Log("Prompt translation complete.", 4)

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

    # --- Mulai logika utama, gunakan variabel yang sudah di-restore/diinisialisasi ---

    # Generate the Outline (Hanya jika belum selesai)
    if last_completed_step == "init":
        SysLogger.Log("Starting Outline Generation...", 3)
        Outline, Elements, RoughChapterOutline, BaseContext = (
            Writer.OutlineGenerator.GenerateOutline(
                Interface,
                SysLogger,
                Prompt,
                Writer.Config.OUTLINE_QUALITY,  # Gunakan Prompt (mungkin sudah diterjemahkan)
            )
        )
        # Save state setelah outline
        current_state["full_outline"] = Outline
        current_state["story_elements"] = Elements
        current_state["rough_chapter_outline"] = RoughChapterOutline
        current_state["base_context"] = BaseContext
        current_state["last_completed_step"] = "outline"
        save_state(current_state, state_filepath)
        SysLogger.Log("Outline Generation Complete. State Saved.", 4)
        last_completed_step = "outline"  # Update status lokal
    elif Outline is None:  # Jika resume tapi outline belum ada
        SysLogger.Log(
            "FATAL: Resuming after 'init' but outline data is missing in state.", 7
        )
        sys.exit(1)
    else:
        SysLogger.Log("Skipping Outline Generation (already completed).", 4)

    # Detect the number of chapters (Hanya jika belum selesai)
    if last_completed_step == "outline":
        SysLogger.Log("Detecting Chapters...", 5)
        # Gunakan Outline yang sudah ada/dimuat
        if not Outline:
            SysLogger.Log("FATAL: Cannot detect chapters, Outline is missing.", 7)
            sys.exit(1)
        Messages = [Interface.BuildUserQuery(Outline)]
        NumChapters = Writer.Chapter.ChapterDetector.LLMCountChapters(
            Interface, SysLogger, Interface.GetLastMessageText(Messages)
        )
        # Save state setelah deteksi chapter
        current_state["total_chapters"] = NumChapters
        current_state["last_completed_step"] = "detect_chapters"
        save_state(current_state, state_filepath)
        SysLogger.Log(f"Found {NumChapters} Chapter(s). State Saved.", 5)
        last_completed_step = "detect_chapters"
    elif NumChapters is None:  # Handle jika resume tapi NumChapters belum ada di state
        SysLogger.Log(
            "FATAL: Resuming after 'outline' but total_chapters data is missing in state.",
            7,
        )
        sys.exit(1)
    else:
        SysLogger.Log(
            f"Skipping Chapter Detection ({NumChapters} chapters already known).", 4
        )

    # Write Per-Chapter Outline (Hanya jika diaktifkan dan belum selesai)
    if Writer.Config.EXPAND_OUTLINE:
        if last_completed_step == "detect_chapters":
            SysLogger.Log("Starting Per-Chapter Outline Expansion...", 3)
            # Gunakan Outline dan NumChapters yang sudah ada/dimuat
            if not Outline or not NumChapters:
                SysLogger.Log(
                    "FATAL: Cannot expand chapters, Outline or NumChapters is missing.",
                    7,
                )
                sys.exit(1)
            Messages = [
                Interface.BuildUserQuery(
                    Writer.Prompts.EXPAND_OUTLINE_CHAPTER_BY_CHAPTER.format(
                        _Outline=Outline
                    )
                )
            ]  # Reset messages untuk langkah ini
            ChapterOutlines = []  # Mulai list kosong
            for ChapterIdx in range(1, NumChapters + 1):
                ChapterOutline, Messages = (
                    Writer.OutlineGenerator.GeneratePerChapterOutline(
                        Interface,
                        SysLogger,
                        ChapterIdx,
                        NumChapters,
                        Outline,
                        Messages,
                    )
                )
                ChapterOutlines.append(ChapterOutline)
            # Save state setelah ekspansi outline
            current_state["expanded_chapter_outlines"] = ChapterOutlines
            current_state["last_completed_step"] = "expand_chapters"
            save_state(current_state, state_filepath)
            SysLogger.Log("Per-Chapter Outline Expansion Complete. State Saved.", 4)
            last_completed_step = "expand_chapters"
        elif last_completed_step not in [
            "expand_chapters",
            "chapter_generation",
            "chapter_generation_complete",
            "post_processing",
            "complete",
        ]:
            SysLogger.Log(
                f"FATAL: Resuming after '{last_completed_step}' but per-chapter outlines are missing.",
                7,
            )
            sys.exit(1)
        else:
            SysLogger.Log(
                "Skipping Per-Chapter Outline Expansion (already completed or disabled).",
                4,
            )
    else:
        SysLogger.Log("Skipping Per-Chapter Outline Expansion (disabled in config).", 4)

    # Create MegaOutline (selalu hitung ulang dari state/variabel saat ini)
    DetailedOutline = ""
    if Writer.Config.EXPAND_OUTLINE and ChapterOutlines:  # Pastikan ChapterOutlines ada
        for Chapter in ChapterOutlines:
            DetailedOutline += Chapter + "\n\n"  # Tambah newline antar outline bab
    MegaOutline = f"""
# Base Outline
{Elements if Elements else "N/A"}

# Detailed Outline
{DetailedOutline if DetailedOutline else "N/A"}
"""
    # Setup Base Outline For Per-Chapter Generation
    UsedOutline = Outline if Outline else ""  # Pastikan Outline ada
    if (
        Writer.Config.EXPAND_OUTLINE and DetailedOutline
    ):  # Gunakan MegaOutline jika ekspansi aktif DAN berhasil
        UsedOutline = MegaOutline

    # Write the chapters (Mulai dari start_chapter)
    if last_completed_step in [
        "detect_chapters",
        "expand_chapters",
        "chapter_generation",
    ]:
        SysLogger.Log(f"Starting Chapter Writing from chapter {start_chapter}...", 5)
        # Pastikan Chapters adalah list (penting untuk resume)
        if not isinstance(Chapters, list):
            Chapters = []
        if NumChapters is None:
            SysLogger.Log(
                "FATAL: Cannot start chapter generation, NumChapters is unknown.", 7
            )
            sys.exit(1)

        for i in range(start_chapter, NumChapters + 1):
            SysLogger.Log(f"--- Generating Chapter {i}/{NumChapters} ---", 3)
            # Panggil helper untuk mendapatkan outline bab dengan fallback
            CurrentChapterOutlineTarget = _get_outline_for_chapter(
                SysLogger, current_state, i
            )

            if (
                not CurrentChapterOutlineTarget
            ):  # Periksa apakah helper mengembalikan sesuatu yang valid
                SysLogger.Log(
                    f"FATAL: No outline could be determined for generating Chapter {i}.",
                    7,
                )
                sys.exit(1)

            ChapterContent = Writer.Chapter.ChapterGenerator.GenerateChapter(
                Interface,
                SysLogger,
                i,
                NumChapters,
                CurrentChapterOutlineTarget,  # Berikan outline yang relevan
                Chapters,  # Berikan bab yang *sudah* selesai
                Writer.Config.OUTLINE_QUALITY,  # Kualitas outline tidak digunakan lagi di generator? Periksa.
                BaseContext if BaseContext else "",  # Pastikan BaseContext string
            )

            FormattedChapter = f"### Chapter {i}\n\n{ChapterContent}"
            # Jika melanjutkan dan bab ini sudah ada, ganti. Jika baru, tambahkan.
            if len(Chapters) >= i:
                Chapters[i - 1] = FormattedChapter  # Ganti bab yang ada (index i-1)
                SysLogger.Log(
                    f"Overwriting existing Chapter {i} data during resume.", 6
                )
            else:
                Chapters.append(FormattedChapter)  # Tambahkan bab baru

            # --- SAVE POINT KRUSIAL ---
            current_state["completed_chapters"] = Chapters
            current_state["next_chapter_index"] = i + 1  # Bab berikutnya
            current_state["last_completed_step"] = "chapter_generation"
            save_state(current_state, state_filepath)
            SysLogger.Log(f"--- Chapter {i} Generation Complete. State Saved. ---", 4)
            # --- AKHIR SAVE POINT ---

            ChapterWordCount = Writer.Statistics.GetWordCount(ChapterContent)
            SysLogger.Log(f"Chapter {i} Word Count: {ChapterWordCount}", 2)

        # Setelah loop selesai, tandai langkah ini selesai
        last_completed_step = "chapter_generation_complete"
        current_state["last_completed_step"] = last_completed_step
        save_state(current_state, state_filepath)  # Simpan status akhir loop bab
        SysLogger.Log("All Chapters Generated. State Saved.", 5)

    elif last_completed_step not in [
        "chapter_generation_complete",
        "post_processing",
        "complete",
    ]:
        SysLogger.Log(
            f"FATAL: Resuming after '{last_completed_step}' but chapter generation was not completed.",
            7,
        )
        sys.exit(1)
    else:
        SysLogger.Log("Skipping Chapter Generation (already completed).", 4)

    # --- Langkah Pasca-Pemrosesan (Edit, Scrub, Translate) ---
    # Tandai awal pasca-pemrosesan
    if last_completed_step == "chapter_generation_complete":
        current_state["last_completed_step"] = "post_processing"
        save_state(current_state, state_filepath)
        last_completed_step = "post_processing"
        SysLogger.Log("Starting Post-Processing Steps. State Saved.", 4)

    if last_completed_step == "post_processing":

        # Siapkan StoryInfoJSON (selalu buat ulang dari state/variabel saat ini)
        StoryInfoJSON = {"Outline": Outline if Outline else ""}
        StoryInfoJSON.update({"StoryElements": Elements if Elements else ""})
        StoryInfoJSON.update(
            {"RoughChapterOutline": RoughChapterOutline if RoughChapterOutline else ""}
        )
        StoryInfoJSON.update({"BaseContext": BaseContext if BaseContext else ""})
        StoryInfoJSON.update(
            {"UnscrubbedChapters": Chapters}
        )  # Simpan bab sebelum edit/scrub

        # Edit Novel (jika diaktifkan)
        NewChapters = Chapters  # Mulai dengan bab yang ada
        if Writer.Config.ENABLE_FINAL_EDIT_PASS:
            SysLogger.Log("Starting Final Edit Pass...", 3)
            if not Chapters:
                SysLogger.Log("Warning: No chapters available for final edit pass.", 6)
            else:
                NewChapters = Writer.NovelEditor.EditNovel(
                    Interface, SysLogger, Chapters, Outline, NumChapters
                )
                StoryInfoJSON.update(
                    {"EditedChapters": NewChapters}
                )  # Simpan hasil edit
                SysLogger.Log("Final Edit Pass Complete.", 4)
        else:
            SysLogger.Log("Skipping Final Edit Pass (disabled).", 4)

        # Scrub Novel (jika diaktifkan)
        if not Writer.Config.SCRUB_NO_SCRUB:
            SysLogger.Log("Starting Scrubbing Pass...", 3)
            if not NewChapters:
                SysLogger.Log("Warning: No chapters available for scrubbing pass.", 6)
            else:
                NewChapters = Writer.Scrubber.ScrubNovel(
                    Interface, SysLogger, NewChapters, NumChapters
                )
                StoryInfoJSON.update(
                    {"ScrubbedChapter": NewChapters}
                )  # Simpan hasil scrub
                SysLogger.Log("Scrubbing Pass Complete.", 4)
        else:
            SysLogger.Log(f"Skipping Scrubbing Due To Config", 4)

        # Translate Novel (jika diaktifkan)
        if Writer.Config.TRANSLATE_LANGUAGE != "":
            SysLogger.Log(
                f"Starting Translation to {Writer.Config.TRANSLATE_LANGUAGE}...", 3
            )
            if not NewChapters:
                SysLogger.Log("Warning: No chapters available for translation.", 6)
            else:
                NewChapters = Writer.Translator.TranslateNovel(
                    Interface,
                    SysLogger,
                    NewChapters,
                    NumChapters,
                    Writer.Config.TRANSLATE_LANGUAGE,
                )
                StoryInfoJSON.update(
                    {"TranslatedChapters": NewChapters}
                )  # Simpan hasil terjemahan
                SysLogger.Log("Translation Complete.", 4)
        else:
            SysLogger.Log(
                f"No Novel Translation Requested, Skipping Translation Step", 4
            )

        # Compile The Final Story Text (setelah semua proses)
        StoryBodyText = ""
        for Chapter in NewChapters:
            StoryBodyText += Chapter + "\n\n\n"

        # Generate Info (gunakan StoryBodyText final)
        SysLogger.Log("Generating Story Info...", 5)
        # Membuat pesan baru khusus untuk GetStoryInfo dengan konten cerita akhir
        # Gunakan outline jika body text kosong (misalnya jika semua bab gagal dibuat)
        InfoQueryContent = (
            StoryBodyText
            if StoryBodyText
            else (Outline if Outline else "No content available.")
        )
        StoryInfoMessages = [Interface.BuildUserQuery(InfoQueryContent)]
        try:
            Info = Writer.StoryInfo.GetStoryInfo(
                Interface, SysLogger, StoryInfoMessages
            )
            Title = Info.get("Title", "Untitled Story")  # Gunakan .get() untuk fallback
            StoryInfoJSON.update({"Title": Title})
            Summary = Info.get("Summary", "No summary generated.")
            StoryInfoJSON.update({"Summary": Summary})
            Tags = Info.get("Tags", "")
            StoryInfoJSON.update({"Tags": Tags})
            SysLogger.Log("Story Info Generation Complete.", 5)
        except Exception as e:
            SysLogger.Log(f"Error generating story info: {e}. Using defaults.", 7)
            Title = "Untitled Story"
            Summary = "Error generating summary."
            Tags = ""
            StoryInfoJSON.update({"Title": Title, "Summary": Summary, "Tags": Tags})

        # Cetak Info
        print("---------------------------------------------")
        print(f"Story Title: {Title}")
        print(f"Summary: {Summary}")
        print(f"Tags: {Tags}")
        print("---------------------------------------------")

        # Hitung Waktu Total
        ElapsedTime = time.time() - StartTime

        # Hitung Total Kata
        TotalWords = Writer.Statistics.GetWordCount(StoryBodyText)
        SysLogger.Log(f"Story Total Word Count: {TotalWords}", 4)

        # Buat String Statistik (gunakan nilai dari Writer.Config yang mungkin dimuat dari state)
        StatsString = "Work Statistics:  \n"
        StatsString += " - Total Words: " + str(TotalWords) + "  \n"
        StatsString += f" - Title: {Title}  \n"
        StatsString += f" - Summary: {Summary}  \n"
        StatsString += f" - Tags: {Tags}  \n"
        # Gunakan waktu dari state jika ada, atau hitung ulang
        gen_start_time_str = current_state.get(
            "generation_start_time",
            datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        )
        StatsString += f" - Generation Start Date: {gen_start_time_str}\n"  # Removed trailing space
        StatsString += f" - Generation Total Time: {ElapsedTime:.2f}s  \n"
        StatsString += (
            f" - Generation Average WPM: {60 * (TotalWords/ElapsedTime):.2f}  \n"
            if ElapsedTime > 0
            else "N/A"
        )

        StatsString += "\n\nUser Settings:  \n"
        StatsString += f" - Base Prompt File: {current_state.get('input_prompt_file', 'N/A')}  \n"  # Ambil dari state
        # Tampilkan prompt asli jika ada terjemahan
        if "translated_prompt_content" in current_state:
            StatsString += f" - Original Prompt Content: {current_state.get('input_prompt_content', 'N/A')} \n"
            StatsString += f" - Translated Prompt Content ({Writer.Config.TRANSLATE_PROMPT_LANGUAGE}): {current_state.get('translated_prompt_content', 'N/A')} \n"
        else:
            StatsString += f" - Prompt Content: {current_state.get('input_prompt_content', 'N/A')} \n"

        StatsString += "\n\nGeneration Settings:  \n"
        StatsString += " - Generator: AIStoryGenerator_2024-06-27  \n"  # Versi bisa ditambahkan ke state
        # Ambil nama model dari Writer.Config
        StatsString += f" - Base Outline Writer Model: {Writer.Config.INITIAL_OUTLINE_WRITER_MODEL}  \n"
        StatsString += f" - Chapter Outline Writer Model: {Writer.Config.CHAPTER_OUTLINE_WRITER_MODEL}  \n"
        StatsString += f" - Chapter Writer (Stage 1: Plot) Model: {Writer.Config.CHAPTER_STAGE1_WRITER_MODEL}  \n"
        StatsString += f" - Chapter Writer (Stage 2: Char Development) Model: {Writer.Config.CHAPTER_STAGE2_WRITER_MODEL}  \n"
        StatsString += f" - Chapter Writer (Stage 3: Dialogue) Model: {Writer.Config.CHAPTER_STAGE3_WRITER_MODEL}  \n"
        StatsString += f" - Final Novel Editor Model: {Writer.Config.FINAL_NOVEL_EDITOR_MODEL}  \n" # Gunakan nama variabel config baru dan label yang sesuai
        StatsString += f" - Chapter Writer (Revision) Model: {Writer.Config.CHAPTER_REVISION_WRITER_MODEL}  \n"
        StatsString += f" - Revision Model: {Writer.Config.REVISION_MODEL}  \n"
        StatsString += f" - Eval Model: {Writer.Config.EVAL_MODEL}  \n"
        StatsString += f" - Info Model: {Writer.Config.INFO_MODEL}  \n"
        StatsString += f" - Scrub Model: {Writer.Config.SCRUB_MODEL}  \n"
        StatsString += f" - Checker Model: {Writer.Config.CHECKER_MODEL}  \n"
        StatsString += f" - Translator Model: {Writer.Config.TRANSLATOR_MODEL}  \n"
        StatsString += f" - Seed: {Writer.Config.SEED}  \n"
        StatsString += (
            f" - Outline Min Revisions: {Writer.Config.OUTLINE_MIN_REVISIONS}  \n"
        )
        StatsString += (
            f" - Outline Max Revisions: {Writer.Config.OUTLINE_MAX_REVISIONS}  \n"
        )
        StatsString += (
            f" - Chapter Min Revisions: {Writer.Config.CHAPTER_MIN_REVISIONS}  \n"
        )
        StatsString += (
            f" - Chapter Max Revisions: {Writer.Config.CHAPTER_MAX_REVISIONS}  \n"
        )
        StatsString += (
            f" - Chapter Disable Revisions: {Writer.Config.CHAPTER_NO_REVISIONS}  \n"
        )
        StatsString += f" - Disable Scrubbing: {Writer.Config.SCRUB_NO_SCRUB}  \n"
        StatsString += f" - Expand Outline: {Writer.Config.EXPAND_OUTLINE}  \n"
        StatsString += (
            f" - Enable Final Edit Pass: {Writer.Config.ENABLE_FINAL_EDIT_PASS}  \n"
        )
        StatsString += f" - Scene Generation Pipeline: {Writer.Config.SCENE_GENERATION_PIPELINE}  \n"
        StatsString += f" - Debug Mode: {Writer.Config.DEBUG}  \n"
        StatsString += f" - Translate Novel To: {Writer.Config.TRANSLATE_LANGUAGE if Writer.Config.TRANSLATE_LANGUAGE else 'None'}  \n"

        # Save The Story To Disk
        SysLogger.Log("Saving Final Story To Disk", 3)
        os.makedirs("Stories", exist_ok=True)  # Pastikan direktori ada
        # Gunakan judul dari Info, bersihkan untuk nama file
        safe_title = "".join(
            c for c in Title if c.isalnum() or c in (" ", "_")
        ).rstrip()
        # Gunakan timestamp dari awal run jika ada di state, jika tidak gunakan waktu sekarang
        run_timestamp = (
            datetime.datetime.strptime(
                gen_start_time_str, "%Y/%m/%d %H:%M:%S"
            ).strftime("%Y%m%d%H%M%S")
            if gen_start_time_str
            else datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        )
        FNameBase = f"Stories/Story_{safe_title.replace(' ', '_') if safe_title else 'Untitled'}_{run_timestamp}"
        # Gunakan output name dari config jika ada
        if Writer.Config.OPTIONAL_OUTPUT_NAME:
            # Coba buat direktori jika output name mengandung path
            output_dir = os.path.dirname(Writer.Config.OPTIONAL_OUTPUT_NAME)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            FNameBase = Writer.Config.OPTIONAL_OUTPUT_NAME

        FinalMDPath = f"{FNameBase}.md"
        FinalJSONPath = f"{FNameBase}.json"

        try:
            with open(FinalMDPath, "w", encoding="utf-8") as F:
                Out = f"""
{StatsString}

---

Note: An outline of the story is available at the bottom of this document.
Please scroll to the bottom if you wish to read that.

---
# {Title}

{StoryBodyText}


---
# Outline
```
{Outline if Outline else "No outline generated."}
```
"""
                # SysLogger.SaveStory(Out) # SaveStory sekarang hanya mencatat path, bukan menulis
                F.write(Out)
            SysLogger.Log(f"Final story saved to {FinalMDPath}", 5)  # Log path aktual
        except Exception as e:
            SysLogger.Log(f"Error writing final story file {FinalMDPath}: {e}", 7)

        # Save JSON Info
        try:
            with open(FinalJSONPath, "w", encoding="utf-8") as F:
                # Tambahkan statistik ke JSON jika diinginkan
                StoryInfoJSON["Stats"] = {
                    "TotalWords": TotalWords,
                    "GenerationTimeSeconds": ElapsedTime,
                    "AverageWPM": (
                        60 * (TotalWords / ElapsedTime) if ElapsedTime > 0 else 0
                    ),
                    "GenerationStartDate": gen_start_time_str,
                }
                # Tambahkan path file output ke JSON
                StoryInfoJSON["OutputFiles"] = {
                    "Markdown": FinalMDPath,
                    "JSONInfo": FinalJSONPath,
                    "StateFile": state_filepath,
                    "LogDirectory": log_directory,
                }
                F.write(json.dumps(StoryInfoJSON, indent=4))
            SysLogger.Log(f"Story info JSON saved to {FinalJSONPath}", 5)
        except Exception as e:
            SysLogger.Log(f"Error writing story info JSON file {FinalJSONPath}: {e}", 7)

        # Tandai run sebagai selesai di state file
        current_state["status"] = "completed"
        current_state["final_story_path"] = FinalMDPath
        current_state["final_json_path"] = FinalJSONPath
        current_state["last_completed_step"] = "complete"
        save_state(current_state, state_filepath)
        SysLogger.Log("Run completed successfully and state marked as completed.", 5)

    elif last_completed_step == "complete":
        SysLogger.Log("Run already marked as complete. Nothing to do.", 5)
    else:
        SysLogger.Log(
            f"Warning: Reached end of script with unexpected state '{last_completed_step}'.",
            6,
        )


if __name__ == "__main__":
    main()


# Pindahkan semua setup config ke dalam logika run baru di main()
# Hapus blok ini dari sini
# Setup Config
# Writer.Config.SEED = Args.Seed
#
# Writer.Config.INITIAL_OUTLINE_WRITER_MODEL = Args.InitialOutlineModel
# Writer.Config.CHAPTER_OUTLINE_WRITER_MODEL = Args.ChapterOutlineModel
# Writer.Config.CHAPTER_STAGE1_WRITER_MODEL = Args.ChapterS1Model
# Writer.Config.CHAPTER_STAGE2_WRITER_MODEL = Args.ChapterS2Model
# Writer.Config.CHAPTER_STAGE3_WRITER_MODEL = Args.ChapterS3Model
# Writer.Config.CHAPTER_STAGE4_WRITER_MODEL = Args.ChapterS4Model
# Writer.Config.CHAPTER_REVISION_WRITER_MODEL = Args.ChapterRevisionModel
# Writer.Config.EVAL_MODEL = Args.EvalModel
# Writer.Config.REVISION_MODEL = Args.RevisionModel
# Writer.Config.INFO_MODEL = Args.InfoModel
# Writer.Config.SCRUB_MODEL = Args.ScrubModel
# Writer.Config.CHECKER_MODEL = Args.CheckerModel
# Writer.Config.TRANSLATOR_MODEL = Args.TranslatorModel
#
# Writer.Config.TRANSLATE_LANGUAGE = Args.Translate
# Writer.Config.TRANSLATE_PROMPT_LANGUAGE = Args.TranslatePrompt
#
# Writer.Config.OUTLINE_MIN_REVISIONS = Args.OutlineMinRevisions
# Writer.Config.OUTLINE_MAX_REVISIONS = Args.OutlineMaxRevisions
#
# Writer.Config.CHAPTER_MIN_REVISIONS = Args.ChapterMinRevisions
# Writer.Config.CHAPTER_MAX_REVISIONS = Args.ChapterMaxRevisions
# Writer.Config.CHAPTER_NO_REVISIONS = Args.NoChapterRevision
#
# Writer.Config.SCRUB_NO_SCRUB = Args.NoScrubChapters
# Writer.Config.EXPAND_OUTLINE = Args.ExpandOutline
# Writer.Config.ENABLE_FINAL_EDIT_PASS = Args.EnableFinalEditPass
#
# Writer.Config.OPTIONAL_OUTPUT_NAME = Args.Output
# Writer.Config.SCENE_GENERATION_PIPELINE = Args.SceneGenerationPipeline
# Pindahkan semua setup config ke dalam logika run baru di main()
# Hapus blok ini dari sini
# Writer.Config.DEBUG = Args.Debug
#
# # Get a list of all used providers
# Models = [
#     Writer.Config.INITIAL_OUTLINE_WRITER_MODEL,
#     Writer.Config.CHAPTER_OUTLINE_WRITER_MODEL,
#     Writer.Config.CHAPTER_STAGE1_WRITER_MODEL,
#     Writer.Config.CHAPTER_STAGE2_WRITER_MODEL,
#     Writer.Config.CHAPTER_STAGE3_WRITER_MODEL,
#     Writer.Config.CHAPTER_STAGE4_WRITER_MODEL,
#     Writer.Config.CHAPTER_REVISION_WRITER_MODEL,
#     Writer.Config.EVAL_MODEL,
#     Writer.Config.REVISION_MODEL,
#     Writer.Config.INFO_MODEL,
#     Writer.Config.SCRUB_MODEL,
#     Writer.Config.CHECKER_MODEL,
# ] # Tambahkan penutup list yang hilang dan komentari
# Pindahkan semua logika utama ke dalam fungsi main()
# Hapus blok ini dari sini
# Models = list(set(Models))
#
# # Setup Logger
# SysLogger = Writer.PrintUtils.Logger()
#
# # Initialize Interface
# SysLogger.Log("Created OLLAMA Interface", 5)
# Interface = Writer.Interface.Wrapper.Interface(Models)
#
# # Load User Prompt
# Prompt: str = ""
# if Args.Prompt is None:
#     raise Exception("No Prompt Provided")
# with open(Args.Prompt, "r") as f:
#     Prompt = f.read()
#
#
# # If user wants their prompt translated, do so
# if Writer.Config.TRANSLATE_PROMPT_LANGUAGE != "":
#     Prompt = Writer.Translator.TranslatePrompt(
#         Interface, SysLogger, Prompt, Writer.Config.TRANSLATE_PROMPT_LANGUAGE
#     )
#
#
# # Generate the Outline
# Outline, Elements, RoughChapterOutline, BaseContext = (
#     Writer.OutlineGenerator.GenerateOutline(
#         Interface, SysLogger, Prompt, Writer.Config.OUTLINE_QUALITY
#     )
# )
# BasePrompt = Prompt
#
#
# # Detect the number of chapters
# SysLogger.Log("Detecting Chapters", 5)
# Messages = [Interface.BuildUserQuery(Outline)]
# NumChapters: int = Writer.Chapter.ChapterDetector.LLMCountChapters(
#     Interface, SysLogger, Interface.GetLastMessageText(Messages)
# )
# SysLogger.Log(f"Found {NumChapters} Chapter(s)", 5)
#
#
# ## Write Per-Chapter Outline
# Prompt = Writer.Prompts.EXPAND_OUTLINE_CHAPTER_BY_CHAPTER.format(_Outline=Outline) # Menggunakan prompt terpusat
# Messages = [Interface.BuildUserQuery(Prompt)]
# ChapterOutlines: list = []
# if Writer.Config.EXPAND_OUTLINE:
#     for Chapter in range(1, NumChapters + 1):
#         # Modifikasi panggilan fungsi ini untuk menyertakan NumChapters
#         ChapterOutline, Messages = Writer.OutlineGenerator.GeneratePerChapterOutline(
#             Interface,
#             SysLogger,
#             Chapter,
#             NumChapters,
#             Outline,
#             Messages,  # Tambahkan NumChapters di sini
#         )
#         ChapterOutlines.append(ChapterOutline)
#
#
# # Create MegaOutline
# DetailedOutline: str = ""
# for Chapter in ChapterOutlines:
#     DetailedOutline += Chapter
# MegaOutline: str = f"""
#
# # Base Outline
# {Elements}
#
# # Detailed Outline
# {DetailedOutline}
#
# """
#
# # Setup Base Prompt For Per-Chapter Generation
# UsedOutline: str = Outline
# if Writer.Config.EXPAND_OUTLINE:
#     UsedOutline = MegaOutline
#
#
# # Write the chapters
# SysLogger.Log("Starting Chapter Writing", 5)
# Chapters = []
# for i in range(1, NumChapters + 1):
#
#     Chapter = Writer.Chapter.ChapterGenerator.GenerateChapter(
#         Interface,
#         SysLogger,
#         i,
#         NumChapters,
#         Outline,
#         Chapters,
#         Writer.Config.OUTLINE_QUALITY,
#         BaseContext,
#     )
#
#     Chapter = f"### Chapter {i}\n\n{Chapter}"
#     Chapters.append(Chapter)
#     ChapterWordCount = Writer.Statistics.GetWordCount(Chapter)
#     SysLogger.Log(f"Chapter Word Count: {ChapterWordCount}", 2)
#
#
# # Now edit the whole thing together
# StoryBodyText: str = ""
# StoryInfoJSON: dict = {"Outline": Outline}
# StoryInfoJSON.update({"StoryElements": Elements})
# StoryInfoJSON.update({"RoughChapterOutline": RoughChapterOutline})
# StoryInfoJSON.update({"BaseContext": BaseContext})
#
# if Writer.Config.ENABLE_FINAL_EDIT_PASS:
#     NewChapters = Writer.NovelEditor.EditNovel(
#         Interface, SysLogger, Chapters, Outline, NumChapters
#     )
# NewChapters = Chapters
# StoryInfoJSON.update({"UnscrubbedChapters": NewChapters})
#
# # Now scrub it (if enabled)
# if not Writer.Config.SCRUB_NO_SCRUB:
#     NewChapters = Writer.Scrubber.ScrubNovel(
#         Interface, SysLogger, NewChapters, NumChapters
#     )
# else:
#     SysLogger.Log(f"Skipping Scrubbing Due To Config", 4)
# StoryInfoJSON.update({"ScrubbedChapter": NewChapters})
#
#
# # If enabled, translate the novel
# if Writer.Config.TRANSLATE_LANGUAGE != "":
#     NewChapters = Writer.Translator.TranslateNovel(
#         Interface, SysLogger, NewChapters, NumChapters, Writer.Config.TRANSLATE_LANGUAGE
#     )
# else:
#     SysLogger.Log(f"No Novel Translation Requested, Skipping Translation Step", 4)
# StoryInfoJSON.update({"TranslatedChapters": NewChapters})
#
#
# # Compile The Story
# for Chapter in NewChapters:
#     StoryBodyText += Chapter + "\n\n\n"
#
#
# # Now Generate Info
# Messages = []
# Messages.append(Interface.BuildUserQuery(Outline))
# Info = Writer.StoryInfo.GetStoryInfo(Interface, SysLogger, Messages)
# Title = Info["Title"]
# StoryInfoJSON.update({"Title": Info["Title"]})
# Summary = Info["Summary"]
# StoryInfoJSON.update({"Summary": Info["Summary"]})
# Tags = Info["Tags"]
# StoryInfoJSON.update({"Tags": Info["Tags"]})
#
# print("---------------------------------------------")
# print(f"Story Title: {Title}")
# print(f"Summary: {Summary}")
# print(f"Tags: {Tags}")
# print("---------------------------------------------")
#
# ElapsedTime = time.time() - StartTime
#
#
# # Calculate Total Words
# TotalWords: int = Writer.Statistics.GetWordCount(StoryBodyText)
# SysLogger.Log(f"Story Total Word Count: {TotalWords}", 4)
#
# StatsString: str = "Work Statistics:  \n"
# StatsString += " - Total Words: " + str(TotalWords) + "  \n"
# StatsString += f" - Title: {Title}  \n"
# StatsString += f" - Summary: {Summary}  \n"
# StatsString += f" - Tags: {Tags}  \n"
# StatsString += f" - Generation Start Date: {datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}  \n"
# StatsString += f" - Generation Total Time: {ElapsedTime}s  \n"
# StatsString += f" - Generation Average WPM: {60 * (TotalWords/ElapsedTime)}  \n"
#
# StatsString += "\n\nUser Settings:  \n"
# StatsString += f" - Base Prompt: {BasePrompt}  \n"
#
# StatsString += "\n\nGeneration Settings:  \n"
# StatsString += f" - Generator: AIStoryGenerator_2024-06-27  \n"
# StatsString += (
#     f" - Base Outline Writer Model: {Writer.Config.INITIAL_OUTLINE_WRITER_MODEL}  \n"
# )
# StatsString += (
#     f" - Chapter Outline Writer Model: {Writer.Config.CHAPTER_OUTLINE_WRITER_MODEL}  \n"
# )
# StatsString += f" - Chapter Writer (Stage 1: Plot) Model: {Writer.Config.CHAPTER_STAGE1_WRITER_MODEL}  \n"
# StatsString += f" - Chapter Writer (Stage 2: Char Development) Model: {Writer.Config.CHAPTER_STAGE2_WRITER_MODEL}  \n"
# StatsString += f" - Chapter Writer (Stage 3: Dialogue) Model: {Writer.Config.CHAPTER_STAGE3_WRITER_MODEL}  \n"
# StatsString += f" - Chapter Writer (Stage 4: Final Pass) Model: {Writer.Config.CHAPTER_STAGE4_WRITER_MODEL}  \n"
# StatsString += f" - Chapter Writer (Revision) Model: {Writer.Config.CHAPTER_REVISION_WRITER_MODEL}  \n"
# StatsString += f" - Revision Model: {Writer.Config.REVISION_MODEL}  \n"
# StatsString += f" - Eval Model: {Writer.Config.EVAL_MODEL}  \n"
# StatsString += f" - Info Model: {Writer.Config.INFO_MODEL}  \n"
# StatsString += f" - Scrub Model: {Writer.Config.SCRUB_MODEL}  \n"
# StatsString += f" - Seed: {Writer.Config.SEED}  \n"
# # StatsString += f" - Outline Quality: {Writer.Config.OUTLINE_QUALITY}  \n"
# StatsString += f" - Outline Min Revisions: {Writer.Config.OUTLINE_MIN_REVISIONS}  \n"
# StatsString += f" - Outline Max Revisions: {Writer.Config.OUTLINE_MAX_REVISIONS}  \n"
# # StatsString += f" - Chapter Quality: {Writer.Config.CHAPTER_QUALITY}  \n"
# StatsString += f" - Chapter Min Revisions: {Writer.Config.CHAPTER_MIN_REVISIONS}  \n"
# StatsString += f" - Chapter Max Revisions: {Writer.Config.CHAPTER_MAX_REVISIONS}  \n"
# StatsString += f" - Chapter Disable Revisions: {Writer.Config.CHAPTER_NO_REVISIONS}  \n"
# StatsString += f" - Disable Scrubbing: {Writer.Config.SCRUB_NO_SCRUB}  \n"
#
#
# # Save The Story To Disk
# SysLogger.Log("Saving Story To Disk", 3)
# os.makedirs("Stories", exist_ok=True)
# FName = f"Stories/Story_{Title.replace(' ', '_')}"
# if Writer.Config.OPTIONAL_OUTPUT_NAME != "":
#     FName = Writer.Config.OPTIONAL_OUTPUT_NAME
# with open(f"{FName}.md", "w", encoding="utf-8") as F:
#     Out = f"""
# {StatsString}
#
# ---
#
# Note: An outline of the story is available at the bottom of this document.
# Please scroll to the bottom if you wish to read that.
#
# ---
# # {Title}
#
# {StoryBodyText}
#
#
# ---
# # Outline
# ```
# {Outline}
# ```
# """
#     SysLogger.SaveStory(Out)
#     F.write(Out)
#
# # Save JSON
# with open(f"{FName}.json", "w", encoding="utf-8") as F:
#     F.write(json.dumps(StoryInfoJSON, indent=4))
