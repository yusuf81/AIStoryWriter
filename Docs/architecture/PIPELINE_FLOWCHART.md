# AI Story Writer - Pipeline Flowchart Documentation

## Overview
This document describes the comprehensive story generation pipeline implemented in the AI Story Writer system. The pipeline consists of multiple stages that transform a user prompt into a complete story with optional post-processing features.

## Flowchart Files
- **Source**: `docs/pipeline_flowchart.mmd` (Mermaid syntax)
- **PNG**: `docs/pipeline_flowchart.png` (Raster image)
- **SVG**: `docs/pipeline_flowchart.svg` (Vector image, recommended)

## Pipeline Stages

### 1. Initialization Stage
**Purpose**: Set up the story generation environment and create the foundational narrative structure.

**Key Steps**:
- Load configuration and language settings
- Handle resume functionality from previous state
- Extract important context from user prompt
- Generate story elements (genre, theme, characters, settings, etc.)
- Create initial story outline
- Iterative outline refinement with quality checks

**Configuration Dependencies**:
- `NATIVE_LANGUAGE`: Determines prompt language (English/Indonesian)
- `OUTLINE_QUALITY`: Quality threshold for outline acceptance
- `OUTLINE_MAX_REVISIONS`: Maximum revision attempts

### 2. Chapter Detection Stage
**Purpose**: Analyze the outline to determine the story structure.

**Key Steps**:
- Use LLM to count chapters in the generated outline
- Store chapter count for subsequent stages
- Validate outline structure consistency

**LLM Model Used**: `CHECKER_MODEL`

### 3. Chapter Outline Expansion Stage (Optional)
**Purpose**: Create detailed per-chapter outlines for more structured generation.

**Key Steps**:
- **Global Outline Refinement**: Improve overall story structure
- **Per-Chapter Outline Generation**: Create detailed outlines for each chapter
- Can be skipped if `EXPAND_OUTLINE = False`

**Configuration Dependencies**:
- `EXPAND_OUTLINE`: Enable/disable this stage
- `ENABLE_GLOBAL_OUTLINE_REFINEMENT`: Enable global refinement sub-step

### 4. Chapter Writing Stage
**Purpose**: Generate the actual story content chapter by chapter.

#### Chapter Generation Process (Per Chapter):

**Stage 0: Context Preparation**
- Extract chapter-specific outline from main outline
- Generate summary of previous chapter (if exists)
- Prepare message history and context

**Stage 1: Plot Generation**
- **Scene Pipeline Option**: Generate chapter scene-by-scene
- **Direct Generation Option**: Generate plot content directly
- **Quality Control**: Use `LLMSummaryCheck` for revision loops
- **Caching Optimization**: Cache outline summaries to avoid redundant LLM calls

**Stage 2: Character Development**
- Enhance plot with character depth, motivations, and development
- Iterative revision with quality checks
- Build upon Stage 1 content without removing existing material

**Stage 3: Dialogue Enhancement**
- Add dialogue and conversational elements
- Refine pacing and character voice
- Final content enhancement stage

**Stage 5: Chapter-Level Revision (Optional)**
- Full chapter quality assessment and revision
- Can be disabled with `CHAPTER_NO_REVISIONS = True`
- Uses separate revision models for more sophisticated feedback

**Chapter Title Generation**
- Automatic title generation if `AUTO_CHAPTER_TITLES = True`
- Uses chapter content and story context for relevant titles

**Configuration Dependencies**:
- `SCENE_GENERATION_PIPELINE`: Choose generation method
- `CHAPTER_NO_REVISIONS`: Skip chapter-level revisions
- `AUTO_CHAPTER_TITLES`: Enable automatic title generation
- `CHAPTER_MAX_REVISIONS`: Maximum revision attempts per stage
- Various word count minimums and model selections

### 5. Post-Processing Stage
**Purpose**: Refine and finalize the complete story.

**Sub-Stages**:

**Final Editing** (Optional)
- Edit the complete novel for coherence and flow
- Ensure consistency across chapters
- Controlled by `ENABLE_FINAL_EDIT_PASS`

**Scrubbing** (Optional)
- Remove AI artifacts and editorial comments
- Clean up the story for publication readiness
- Can be skipped with `SCRUB_NO_SCRUB = True`

**Translation** (Optional)
- Translate the complete story to target language
- Preserves story structure and formatting
- Triggered by command-line arguments

**Statistics Generation**
- Generate story metadata, tags, and statistics
- Create story summary and ratings
- Always performed regardless of other settings

**Final Compilation**
- Compile the final novel with optional elements
- Include outline, statistics, summary, or tags based on configuration
- Save to final output file

**Configuration Dependencies**:
- `ENABLE_FINAL_EDIT_PASS`: Enable final editing
- `SCRUB_NO_SCRUB`: Skip scrubbing process
- `INCLUDE_OUTLINE_IN_MD`, `INCLUDE_STATS_IN_MD`, etc.: Control final output elements

## Quality Control Mechanisms

### LLMSummaryCheck System
- **Purpose**: Ensure generated content matches the intended outline
- **Process**: Summarize work, summarize outline, compare for alignment
- **Optimization**: Caches outline summaries to avoid redundant processing
- **Feedback Loop**: Provides specific suggestions for improvement

### Revision Loops
- **Adaptive Quality**: Each stage has configurable revision limits
- **Graceful Degradation**: Force accept content after maximum attempts
- **Logging**: Comprehensive logging of revision attempts and reasons

### State Management
- **Resumable**: Complete state saved at each major checkpoint
- **Fault Tolerant**: Can resume from any completed stage
- **Incremental**: Save progress after each chapter completion

## Configuration Integration

The pipeline is highly configurable through `Writer/Config.py`:

### Model Selection
- Different LLM models for different tasks (writing, checking, revision)
- Supports multiple providers (Ollama, Google, OpenRouter)
- Model-specific parameters and timeouts

### Quality Thresholds
- Configurable quality standards for each stage
- Minimum word counts for generated content
- Maximum revision attempts before forced acceptance

### Feature Toggles
- Enable/disable entire stages or sub-processes
- Customize output format and included elements
- Control logging verbosity and debug information

## Multi-Language Support

The pipeline supports multiple languages through dynamic prompt loading:

- **Language Detection**: Based on `NATIVE_LANGUAGE` configuration
- **Dynamic Loading**: Automatically loads appropriate prompt templates
- **Consistent Processing**: Same pipeline logic regardless of language
- **Translation Support**: Built-in translation capabilities

## Error Handling and Recovery

### Robust Error Handling
- Try-catch blocks around major operations
- Detailed error logging with stack traces
- State preservation during errors

### Recovery Mechanisms
- Resume from last successful checkpoint
- Fallback to default values when generation fails
- Graceful degradation when quality checks fail repeatedly

### Logging and Debugging
- Comprehensive logging at multiple verbosity levels
- Debug file generation for LLM interactions
- State file inspection for troubleshooting

## Performance Considerations

### Caching Optimizations
- Outline summary caching in `LLMSummaryCheck`
- Reuse of generated content across stages
- State persistence to avoid re-computation

### Parallel Processing Potential
- Modular design allows for future parallelization
- Independent chapter generation stages
- Separate models for different tasks

### Resource Management
- Configurable retry limits prevent infinite loops
- Memory-conscious state management
- Efficient string manipulation and storage

---

## Usage Examples

### Basic Story Generation
```bash
python Write.py -Prompt Prompts/example.txt
```

### Resume from Previous State
```bash
python Write.py -Resume Logs/Generation_YYYY-MM-DD_HH-MM-SS/run.state.json
```

### Custom Model Configuration
```bash
python Write.py -Prompt Prompts/example.txt -InitialOutlineModel "google://gemini-1.5-pro"
```

### Multi-Language Generation
```bash
# Indonesian prompts (auto-detected from NATIVE_LANGUAGE config)
python Write.py -Prompt Prompts/hantu.txt

# With translation to English
python Write.py -Prompt Prompts/hantu.txt -Translate English
```

---

*This flowchart was generated based on the actual codebase implementation and validated using mermaid-cli (mmdc). For the most current implementation details, refer to the source code in the Writer/ directory.*