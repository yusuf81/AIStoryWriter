#!/bin/python3
"""Simulates the GetStoryInfo step using data from a run state file."""

import argparse
import json
import os
import sys
import traceback  # Moved import to top

# Third-party imports
import dotenv

# --- Keep this block if needed to find the Writer package ---
# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (which should contain the Writer directory)
parent_dir = os.path.dirname(script_dir)
# Add the parent directory to sys.path if it's not already there
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
# --- End sys.path block ---

# First-party imports (Writer package)
import Writer.Config
import Writer.Interface.Wrapper
import Writer.PrintUtils
import Writer.StoryInfo
# import Writer.Prompts # Dihapus karena tidak digunakan secara langsung di file ini


# Load environment variables (e.g., GOOGLE_API_KEY)
dotenv.load_dotenv()


# Replace the existing load_state function with this more specific exception handling
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
    except IOError as e:  # More specific than generic Exception
        raise IOError(f"Failed to read state file {filepath}: {e}") from e


# Add helper function for logger initialization
def _initialize_logger(state_data):
    """Initializes the logger based on state data."""
    log_directory = state_data.get("log_directory")
    if not log_directory:
        print("Warning: Log directory not found in state, creating temporary logs.")
        sim_log_base_dir = "SimulateLogs"
        os.makedirs(sim_log_base_dir, exist_ok=True)
        # Rename SysLogger to sys_logger
        sys_logger = Writer.PrintUtils.Logger(_LogfilePrefix=sim_log_base_dir)
    else:
        sim_log_base_dir = "SimulateLogs"
        sim_log_dir = os.path.join(
            sim_log_base_dir, f"Simulate_{os.path.basename(log_directory)}"
        )
        print(f"Creating simulation logs in: {sim_log_dir}")
        os.makedirs(sim_log_dir, exist_ok=True)
        # Rename SysLogger to sys_logger
        sys_logger = Writer.PrintUtils.Logger(_LogfilePrefix=sim_log_dir)
    return sys_logger  # Return the logger instance


# Add helper function for determining the info model
def _determine_info_model(state_data, info_model_override):
    """Determines the INFO_MODEL to use."""
    info_model = info_model_override
    if not info_model:
        state_config = state_data.get("config", {})
        info_model = state_config.get("INFO_MODEL", state_config.get("InfoModel"))
    if not info_model:
        info_model = Writer.Config.INFO_MODEL
    return info_model


# Add helper function for determining the query content
def _determine_query_content(state_data, sys_logger):
    """Determines the content to use for the GetStoryInfo query."""
    # Rename InfoQueryContent to info_query_content
    info_query_content = ""
    source = "N/A"
    expand_outline_enabled = state_data.get("config", {}).get(
        "EXPAND_OUTLINE", Writer.Config.EXPAND_OUTLINE
    )

    if expand_outline_enabled and state_data.get("expanded_chapter_outlines"):
        expanded_outlines = state_data["expanded_chapter_outlines"]
        if isinstance(expanded_outlines, list) and expanded_outlines:
            # Extract text from dict format
            outline_texts = [item["text"] for item in expanded_outlines]
            info_query_content = "\n\n---\n\n".join(outline_texts)
            source = "expanded_chapter_outlines"
            sys_logger.Log(
                "Using joined expanded chapter outlines for GetStoryInfo.",
                6,  # Removed f-string
            )

    if not info_query_content:
        full_outline_content = state_data.get("full_outline")
        if full_outline_content:
            info_query_content = full_outline_content
            source = "full_outline"
            sys_logger.Log(
                "Using full_outline for GetStoryInfo.", 6
            )  # Removed f-string
        else:
            info_query_content = "No outline information available."
            source = "fallback_string"
            sys_logger.Log(
                "Warning: No outline found for GetStoryInfo, using fallback string.",
                6,  # Removed f-string
            )

    sys_logger.Log(f"Using story content source: '{source}' for GetStoryInfo", 6)
    sys_logger.Log(f"Content length (chars): {len(info_query_content)}", 6)
    return info_query_content


# Modify the main simulate_get_info function
def simulate_get_info(state_filepath, info_model_override=None):
    """
    Simulates the GetStoryInfo step using data from a state file.
    """
    # 1. Muat State
    try:
        print(f"Loading state from: {state_filepath}")
        current_state = load_state(state_filepath)
        if not current_state:
            print("Error: Failed to load state.")
            return
    # Use more specific exceptions if load_state raises them
    except (FileNotFoundError, ValueError, IOError) as e:
        print(f"Error loading state file: {e}")
        return
    # Keep a general catch for unexpected issues during loading, but log traceback
    except Exception as e:
        print(f"Unexpected error loading state file: {e}")
        traceback.print_exc()  # Log traceback for unexpected errors
        return

    # 2. Initialize Logger (using helper function)
    # Rename SysLogger to sys_logger
    sys_logger = _initialize_logger(current_state)
    sys_logger.Log("Starting Story Info Simulation...", 5)

    # 3. Determine Info Model (using helper function)
    info_model = _determine_info_model(current_state, info_model_override)
    sys_logger.Log(f"Using INFO_MODEL: {info_model}", 4)

    # 4. Initialize Interface
    try:
        # Rename Interface to interface
        interface = Writer.Interface.Wrapper.Interface([info_model])
    except (
        Exception
    ) as e:  # Keep general exception here as Interface init could fail variously
        sys_logger.Log(f"Error initializing interface: {e}", 7)
        traceback.print_exc()
        return

    # 5. Determine Query Content (using helper function)
    # Rename InfoQueryContent to info_query_content
    info_query_content = _determine_query_content(current_state, sys_logger)

    # 6. Build Initial Messages
    # Rename Interface to interface
    initial_messages_for_info = [interface.BuildUserQuery(info_query_content)]

    # 7. Call GetStoryInfo
    try:
        sys_logger.Log("Calling Writer.StoryInfo.GetStoryInfo...", 5)
        # Rename Interface to interface, SysLogger to sys_logger
        # Rename GeneratedInfo to generated_info, TokenUsage to token_usage
        generated_info, token_usage = Writer.StoryInfo.GetStoryInfo(
            interface, sys_logger, initial_messages_for_info, _Model=info_model
        )

        sys_logger.Log("Writer.StoryInfo.GetStoryInfo call finished.", 5)

        # Check if generated_info is not None before printing
        if generated_info:
            print("\n--- Generated Story Info ---")
            print(json.dumps(generated_info, indent=4))
            print("---------------------------")
            # Print token usage if available
            if token_usage:
                # Rename TokenUsage to token_usage
                print(f"Prompt Tokens: {token_usage.get('prompt_tokens', 'N/A')}")
                print(
                    f"Completion Tokens: {token_usage.get('completion_tokens', 'N/A')}"
                )
            else:
                print(
                    "Token usage information not available."
                )  # Handle case where token_usage might be None
            print("---------------------------\n")
        else:
            # Handle the case where GetStoryInfo returned None for info
            sys_logger.Log("GetStoryInfo returned None for generated info.", 6)
            print("\n--- Generated Story Info ---")
            print("Failed to generate story info.")
            print("---------------------------\n")

    except Exception as e:  # Keep general exception for the main execution block
        sys_logger.Log(f"Error during GetStoryInfo execution: {e}", 7)
        traceback.print_exc()

    sys_logger.Log("Simulation finished.", 5)


# --- Keep the __main__ block as is, but ensure args are passed correctly ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate the GetStoryInfo step.")
    parser.add_argument(
        "--state-file",  # Renamed from -StateFile
        dest="state_file",  # Use dest to store in snake_case variable
        required=True,
        help="Path to the run.state.json file of a completed or near-completed run.",
    )
    parser.add_argument(
        "--info-model",  # Renamed from -InfoModel
        dest="info_model",  # Use dest to store in snake_case variable
        default=None,
        help="Override the INFO_MODEL defined in the state file or Config.py.",
    )
    args = parser.parse_args()

    # Pass snake_case variables to the function
    simulate_get_info(args.state_file, args.info_model)
