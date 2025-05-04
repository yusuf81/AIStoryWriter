#!/bin/python3
import argparse
import json
import os
import sys

# Pastikan kita bisa mengimpor dari direktori Writer
# Dapatkan direktori tempat skrip ini berada
script_dir = os.path.dirname(os.path.abspath(__file__))
# Dapatkan direktori induk (yang seharusnya berisi direktori Writer)
parent_dir = os.path.dirname(script_dir)
# Tambahkan direktori induk ke sys.path jika belum ada
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


import Writer.Config
import Writer.Interface.Wrapper
import Writer.PrintUtils
import Writer.StoryInfo
import Writer.Prompts
import dotenv


# Muat variabel lingkungan (misalnya GOOGLE_API_KEY)
dotenv.load_dotenv()


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


def simulate_get_info(state_filepath, info_model_override=None):
    """
    Mensimulasikan langkah GetStoryInfo menggunakan data dari state file.
    """
    # 1. Muat State
    try:
        print(f"Loading state from: {state_filepath}")
        current_state = load_state(state_filepath)
        if not current_state:
            print("Error: Failed to load state.")
            return
    except Exception as e:
        print(f"Error loading state file: {e}")
        return

    # 2. Inisialisasi Logger
    log_directory = current_state.get("log_directory")
    if not log_directory:
        print("Warning: Log directory not found in state, creating temporary logs.")
        # Buat direktori log simulasi jika tidak ada
        sim_log_base_dir = "SimulateLogs"
        os.makedirs(sim_log_base_dir, exist_ok=True)
        SysLogger = Writer.PrintUtils.Logger(_LogfilePrefix=sim_log_base_dir)
    else:
        # Buat logger baru di direktori simulasi agar tidak menimpa log asli
        sim_log_base_dir = "SimulateLogs"
        sim_log_dir = os.path.join(
            sim_log_base_dir, f"Simulate_{os.path.basename(log_directory)}"
        )
        print(f"Creating simulation logs in: {sim_log_dir}")
        # Pastikan direktori ada
        os.makedirs(sim_log_dir, exist_ok=True)
        # Berikan path lengkap ke Logger
        SysLogger = Writer.PrintUtils.Logger(_LogfilePrefix=sim_log_dir)

    SysLogger.Log("Starting Story Info Simulation...", 5)

    # 3. Tentukan Model Info
    # Prioritaskan override dari command line, lalu dari state config, lalu default config
    info_model = info_model_override
    if not info_model:
        # Coba ambil dari config di dalam state
        state_config = current_state.get("config", {})
        # Cari kunci yang sesuai (mungkin INFO_MODEL atau InfoModel tergantung bagaimana disimpan)
        info_model = state_config.get("INFO_MODEL", state_config.get("InfoModel"))
    if not info_model:
        info_model = Writer.Config.INFO_MODEL  # Default dari Config.py
    SysLogger.Log(f"Using INFO_MODEL: {info_model}", 4)

    # 4. Inisialisasi Interface (HANYA dengan model info)
    try:
        Interface = Writer.Interface.Wrapper.Interface([info_model])
    except Exception as e:
        SysLogger.Log(f"Error initializing interface: {e}", 7)
        import traceback

        traceback.print_exc()
        return

    # 5. Dapatkan Konten Cerita dari State (dengan prioritas yang diperbarui)
    # Hapus logika lama yang mencari list bab untuk InfoQueryContent

    # --- Determine Content for GetStoryInfo (Solution 1: Use Outline) ---
    InfoQueryContent = ""
    source = "N/A"
    # Periksa apakah EXPAND_OUTLINE diaktifkan selama run asli (dari state config)
    expand_outline_enabled = current_state.get("config", {}).get(
        "EXPAND_OUTLINE", Writer.Config.EXPAND_OUTLINE
    )

    if expand_outline_enabled and current_state.get("expanded_chapter_outlines"):
        expanded_outlines = current_state["expanded_chapter_outlines"]
        if isinstance(expanded_outlines, list) and expanded_outlines:
            InfoQueryContent = "\n\n---\n\n".join(
                expanded_outlines
            )  # Gabungkan dengan pemisah
            source = "expanded_chapter_outlines"
            SysLogger.Log(
                f"Using joined expanded chapter outlines for GetStoryInfo.", 6
            )

    if not InfoQueryContent:  # Fallback ke full_outline
        full_outline_content = current_state.get("full_outline")
        if full_outline_content:
            InfoQueryContent = full_outline_content
            source = "full_outline"
            SysLogger.Log(f"Using full_outline for GetStoryInfo.", 6)
        else:  # Pilihan terakhir
            InfoQueryContent = "No outline information available."
            source = "fallback_string"
            SysLogger.Log(
                f"Warning: No outline found for GetStoryInfo, using fallback string.", 6
            )
    # --- End Determine Content ---

    SysLogger.Log(
        f"Using story content source: '{source}' for GetStoryInfo", 6
    )  # Perbarui pesan log
    SysLogger.Log(f"Content length (chars): {len(InfoQueryContent)}", 6)

    # 6. Bangun Pesan Awal
    # Baris ini tetap sama, menggunakan InfoQueryContent yang baru ditentukan
    initial_messages_for_info = [Interface.BuildUserQuery(InfoQueryContent)]

    # 7. Panggil GetStoryInfo (Sisa kode tetap sama)
    try:
        SysLogger.Log("Calling Writer.StoryInfo.GetStoryInfo...", 5)
        # Teruskan model yang benar (info_model) ke GetStoryInfo
        # Unpack both values returned by GetStoryInfo
        GeneratedInfo, TokenUsage = Writer.StoryInfo.GetStoryInfo(
            Interface, SysLogger, initial_messages_for_info, _Model=info_model
        )

        SysLogger.Log("Writer.StoryInfo.GetStoryInfo call finished.", 5)
        print("\n--- Generated Story Info ---")
        # GeneratedInfo sudah berupa dictionary JSON yang di-parse
        print(json.dumps(GeneratedInfo, indent=4))
        print("---------------------------")
        # Print token usage if available
        if TokenUsage:
            print(f"Prompt Tokens: {TokenUsage.get('prompt_tokens', 'N/A')}")
            print(f"Completion Tokens: {TokenUsage.get('completion_tokens', 'N/A')}")
        print("---------------------------\n")

    except Exception as e:
        SysLogger.Log(f"Error during GetStoryInfo execution: {e}", 7)
        import traceback

        traceback.print_exc()  # Cetak traceback lengkap untuk debug

    SysLogger.Log("Simulation finished.", 5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate the GetStoryInfo step.")
    parser.add_argument(
        "-StateFile",
        required=True,
        help="Path to the run.state.json file of a completed or near-completed run.",
    )
    parser.add_argument(
        "-InfoModel",
        default=None,
        help="Override the INFO_MODEL defined in the state file or Config.py.",
    )
    args = parser.parse_args()

    simulate_get_info(args.StateFile, args.InfoModel)
