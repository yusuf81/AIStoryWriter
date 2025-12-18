# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running the Story Generator
```bash
# Basic story generation
python Write.py -Prompt Prompts/YourChosenPrompt.txt

# Resume interrupted generation
python Write.py -Resume Logs/Generation_YYYY-MM-DD_HH-MM-SS/run.state.json

# Generate with custom models
python Write.py -Prompt Prompts/YourChosenPrompt.txt -InitialOutlineModel "google://gemini-1.5-pro" -ChapterOutlineModel "ollama://llama3:70b"

# Generate with translation
python Write.py -Prompt Prompts/YourChosenPrompt.txt -Translate French

# Generate without chapter revisions (faster)
python Write.py -Prompt Prompts/YourChosenPrompt.txt -NoChapterRevision
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_write.py

# Run tests with verbose output
pytest -v

# Run specific test method
pytest tests/writer/chapter/test_chapter_generator.py::test_specific_function
```

### Story Evaluation
```bash
# Compare two generated stories
python Evaluate.py -StoryA path/to/story1.md -StoryB path/to/story2.md -Model "ollama://llama3:70b"
```

## Project Architecture

### Core Pipeline Flow
The story generation follows a multi-stage pipeline orchestrated by `Writer/Pipeline.py`:

1. **Outline Generation** (`Writer/OutlineGenerator.py`)
   - Creates initial story outline from prompt
   - Generates story elements and character details
   - Supports revision loops based on quality evaluation

2. **Chapter Detection** (`Writer/Chapter/ChapterDetector.py`)
   - Analyzes outline to determine chapter count and structure

3. **Chapter Expansion** (optional, enabled by `-ExpandOutline`)
   - Expands main outline into detailed per-chapter outlines
   - Provides more structured guidance for chapter writing

4. **Chapter Generation** (`Writer/Chapter/ChapterGenerator.py`)
   - Three-stage process per chapter:
     - Stage 1: Plot and scene writing
     - Stage 2: Character development
     - Stage 3: Dialogue refinement
   - Optional scene-by-scene pipeline (`Writer/Scene/`)
   - Built-in revision system with quality evaluation

5. **Post-Processing**
   - Final novel editing (`Writer/NovelEditor.py`)
   - Scrubbing pass to remove AI artifacts (`Writer/Scrubber.py`)
   - Translation support (`Writer/Translator.py`)
   - Story metadata extraction (`Writer/StoryInfo.py`)

### Model Provider System
The project supports multiple AI model providers through a unified interface:

- **Ollama**: Local models (default: `127.0.0.1:11434`)
- **Google**: Gemini models via API
- **OpenRouter**: Various models via API

Model format: `{provider}://{model}@{host}?parameter=value`

### Configuration System

**Config.py is the master configuration** - `Writer/Config.py` defines all default values for generation parameters, quality thresholds, model assignments, and feature flags.

**CLI flags override Config.py ONLY when explicitly provided**:
- If you run `python Write.py -Prompt test.txt` without other flags, **all Config.py values are used**
- If you run `python Write.py -Prompt test.txt -ExpandOutline`, it **enables** expanded outlines regardless of Config.py value
- If you run `python Write.py -Prompt test.txt -NoExpandOutline`, it **disables** expanded outlines regardless of Config.py value

**Common CLI flags for feature control:**
- `-ExpandOutline` / `-NoExpandOutline`: Control detailed chapter outline expansion
- `-SceneGenerationPipeline` / `-NoSceneGenerationPipeline`: Control scene-by-scene generation
- `-EnableFinalEditPass` / `-NoEnableFinalEditPass`: Control final story editing pass
- `-ChapterRevision` / `-NoChapterRevision`: Control chapter quality revision loops

**Other configuration sources:**
- `.env`: API keys for cloud providers (Google, OpenRouter, etc.)
- State persistence in `run.state.json` for resumable generation

### Multi-Language Support
- `Writer/Prompts.py`: English prompts (default)
- `Writer/Prompts_id.py`: Indonesian prompts
- Dynamic prompt loading based on `NATIVE_LANGUAGE` config
- Translation capabilities for both input prompts and output stories

### Key Modules
- `Writer/Interface/Wrapper.py`: Core LLM interface abstraction
- `Writer/PrintUtils.py`: Logging and output formatting
- `Writer/Statistics.py`: Generation metrics and timing
- `Writer/LLMEditor.py`: Text editing and refinement utilities

### State Management
The system automatically saves progress at key checkpoints:
- `init`: Run initialization
- `outline`: Story outline completion
- `detect_chapters`: Chapter structure analysis
- `expand_chapters`: Chapter outline expansion
- `chapter_generation`: After each chapter (allows mid-process resume)
- `post_processing`: Before final editing/translation
- `complete`: Full generation finished

State files are saved in `Logs/Generation_YYYY-MM-DD_HH-MM-SS/run.state.json`

### Testing Structure
- Unit tests for core components in `tests/writer/`
- Integration tests for main workflow in `tests/test_write.py`
- Mock-based testing for LLM interfaces
- Test configuration in `tests/conftest.py`

## Development Notes

### Quality Control
The system includes multiple quality gates:
- Outline quality evaluation with configurable thresholds
- Chapter quality assessment with revision loops
- Word count minimums for generated content
- JSON structure validation with repair attempts

### Performance Considerations
- Parallel processing capabilities where possible
- Configurable retry limits for failed generations
- Memory management for long-running generations
- Context window optimization for different models

### Debugging
- Set `DEBUG = True` in `Writer/Config.py` for verbose logging
- Check `Logs/` directory for detailed generation logs
- Use `-NoChapterRevision` flag to speed up testing
- Monitor model-specific parameters in config


### Coding Rules

1. First think through the problem, read the codebase for relevant files, and write a plan to tasks/todo.md.
2. The plan should have a list of todo items that you can check off as you complete them
3. Before you begin working, check in with me and I will verify the plan.
4. Then, begin working on the todo items, marking them as complete as you go.
5. Please every step of the way just give me a high level explanation of what changes you made
6. Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity.
7. Finally, add a review section to the tasks/todo.md file with a summary of the changes you made and any other relevant information.
8. Please run pytest for every changes, to make sure no error.
9. Please use TDD (London School) for all aspect of source code modification
10. jalankan pyright dan flake8 --ignore=E501,W504,W503 untuk setiap files yang di edit, dan perbaiki error yang muncul
11. jalankan pytest untuk fungsi-fungsi yang terkait

### Dead Code Analysis

#### Running Dead Code Detection
```bash
# Quick scan (recommended for daily use)
make vulture

# Detailed scan with report
make vulture-report

# Generate whitelist suggestions
vulture --make-whitelist Writer/ Write.py Evaluate.py simulate_story_info.py
```

#### Interpreting Results
- **60-79% confidence**: Review manually - may be dynamic usage
- **80-99% confidence**: Likely dead code, safe to remove
- **100% confidence**: Definitely unused, safe to remove

#### Common False Positives in AIStoryWriter
- LLM provider interfaces (loaded dynamically via import_module)
- Feature flag controlled code (Config.USE_LOREBOOK, Config.USE_REASONING_CHAIN)
- Reflection-based module loading
- CLI entry points that appear unused statically

#### Dead Code Handling Workflow
1. **Scan**: Run `make vulture-report` to generate analysis
2. **Review**: Check reports in `/reports/` directory
3. **Verify**: Manually check high-confidence items before removal
4. **Clean**: Remove verified dead code, update whitelist for false positives
5. **Test**: Run pytest to ensure no regressions

#### Current Findings Summary
As of initial scan, **71 instances** of potential dead code found:
- 58 unused variables (60% confidence)
- 13 unused functions/methods (various confidence levels)
- Reports available in `/reports/dead_code_YYYYMMDD.txt`
