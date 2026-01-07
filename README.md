# AI Story Generator 📚✨

Generate full-length novels with AI! Harness the power of large language models to create engaging stories based on your prompts.

[![Discord](https://img.shields.io/discord/1255847829763784754?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://discord.gg/R2SySWDr2s)

## 🚀 Features

- **Generate medium to full-length novels**: Produce substantial stories with coherent narratives, suitable for novella or novel-length works
- **Multi-model provider support**: Support for Ollama (local), Google Gemini, OpenRouter, and xAI Grok
- **Multi-language support**: Generate stories in Indonesian and English with automatic prompt/output translation capabilities
- **Easy setup and use**: Get started quickly with minimal configuration required
- **Modular pipeline architecture**: Clean separation of concerns with dedicated modules for outline generation, chapter writing, and post-processing
- **Customizable prompts and models**: Choose from existing prompts or create your own, and select from various language models
- **Automatic model downloading**: The system can automatically download required models via Ollama if they aren't already available
- **Support for local models via Ollama**: Run language models locally for full control and privacy
- **Flexible configuration options**: Fine-tune the generation process through easily modifiable settings
- **Cross-platform compatibility**: Works across all operating systems
- **Advanced story generation pipeline**:
  - Multi-stage chapter generation (plot → character development → dialogue)
  - Optional scene-by-scene generation for detailed chapter crafting
  - Automatic quality evaluation and revision loops
  - Chapter outline expansion for structured writing
- **Resume interrupted generation**: Automatic state saving allows resuming from any point in the generation process
- **Vector-based lore management**: Automatic consistency checking with ChromaDB for characters, locations, and plot elements
- **Repetition detection and auto-retry**: Automatically detects repetitive outputs and retries with adjusted parameters
- **Post-processing capabilities**:
  - Optional final editing pass over the entire novel
  - Automatic scrubbing to remove AI artifacts and leftover instructions
  - Translation support for generated stories
  - PDF generation with optimized readability
- **Quality assurance**: Built-in evaluation system and story comparison tools (`Evaluate.py`)
- **Comprehensive testing**: Full test suite with pytest for reliable code quality

## 🏁 Quick Start

Getting started with AI Story Generator is easy:

### Prerequisites
1. **Python 3.11+** with pip
2. **Install [Ollama](https://ollama.com/)** for local model support (optional)
3. **Clone the repository**:
   ```bash
   git clone https://github.com/yusuf81/AIStoryWriter.git
   cd AIStoryWriter
   ```

### Installation
1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables** (optional, for cloud providers):
   ```bash
   cp .env.example .env
   # Edit .env to add your API keys for Google, OpenRouter, xAI, etc.
   ```

### Generate Your First Story
```bash
# Basic story generation (Indonesian prompts by default)
python Write.py -Prompt Prompts/horor3.txt

# Generate with custom models
python Write.py -Prompt Prompts/roman1.txt -InitialOutlineModel "google://gemini-2.5-flash"

# Resume interrupted generation
python Write.py -Resume Logs/Generation_YYYY-MM-DD_HH-MM-SS/run.state.json
```

That's it! The system will automatically download any required models and start generating your story.

### Development & Testing
```bash
# Run the test suite
pytest

# Run tests with verbose output
pytest -v

# Check specific functionality
python Write.py --help
```

## 💻 Hardware & Model Recommendations

### Model Providers

**Ollama (Local Models)**
- Full privacy and control
- No API costs
- Requires capable hardware for larger models
- Models: Llama 3, Qwen 2.5, Gemma, SEA-LION series

**Google Gemini**
- High-quality outputs with gemini-2.5-flash
- Fast inference with gemini-2.0-flash
- Requires `GOOGLE_API_KEY` in `.env`
- Recommended: `google://gemini-2.5-flash` or `google://gemini-flash-lite-latest`

**xAI Grok**
- Latest Grok-4 series with 2M context window
- Agentic reasoning capabilities
- Requires `XAI_API_KEY` in `.env`
- Recommended: `grok://grok-4-1-fast-reasoning` (default)

**OpenRouter**
- Access to 100+ models including Claude, GPT-4, etc.
- Requires `OPENROUTER_API_KEY` in `.env`

Not sure which models to use with your GPU? Check out our [Model Recommendations](Docs/Models.md) page for suggestions based on different GPU capabilities.

## 🛠️ Usage

The AI Story Generator provides flexible configuration options to customize your story generation experience.

### Command-Line Interface

The main interface uses `Write.py` with various command-line arguments:

#### Model Configuration
You can override the default models for different generation stages:

```bash
# Use different models for different stages
python Write.py -Prompt Prompts/horor3.txt \
  -InitialOutlineModel "google://gemini-2.5-flash" \
  -ChapterS1Model "grok://grok-4-1-fast-reasoning" \
  -ChapterS2Model "ollama://llama3:70b" \
  -ChapterS3Model "ollama://qwen2.5:32b"
```

#### Key Command-Line Arguments

**Core Generation:**
- `-Prompt {file}`: Path to your story prompt file
- `-Output {file}`: Optional output filename (auto-generated if not specified)
- `-Resume {state_file}`: Resume from a previous generation state

**Model Selection:**
- `-InitialOutlineModel`: Model for outline generation and revision
- `-ChapterOutlineModel`: Model for per-chapter outline expansion
- `-ChapterS1Model`: Model for chapter stage 1 (plot/scene writing)
- `-ChapterS2Model`: Model for chapter stage 2 (character development)
- `-ChapterS3Model`: Model for chapter stage 3 (dialogue)
- `-FinalNovelEditorModel`: Model for final novel-wide editing
- `-ChapterRevisionModel`: Model for chapter revisions
- `-RevisionModel`: Model for generating feedback/critique
- `-EvalModel`: Model for quality evaluation
- `-InfoModel`: Model for extracting story metadata
- `-ScrubModel`: Model for final cleanup pass
- `-TranslatorModel`: Model for translation tasks

**Generation Options:**
- `-ExpandOutline` / `-NoExpandOutline`: Enable/disable per-chapter outline expansion
- `-SceneGenerationPipeline` / `-NoSceneGenerationPipeline`: Enable/disable scene-by-scene generation
- `-EnableFinalEditPass` / `-NoEnableFinalEditPass`: Enable/disable final novel editing
- `-NoChapterRevision`: Disable chapter revision loops
- `-NoScrubChapters`: Disable final AI artifact cleanup

**Translation:**
- `-Translate {Language}`: Translate final story (e.g., 'French', 'English')
- `-TranslatePrompt {Language}`: Translate input prompt before generation

**Quality Control:**
- `-OutlineMinRevisions / -OutlineMaxRevisions`: Control outline revision loops
- `-ChapterMinRevisions / -ChapterMaxRevisions`: Control chapter revision loops
- `-Seed {number}`: Set random seed for reproducible generation

### Model Provider Format

The model format is: `{Provider}://{ModelName}@{Host}?parameter=value`

**Supported Providers:**
- `ollama`: Local models via Ollama
- `google`: Google Gemini models
- `openrouter`: OpenRouter API models
- `grok`: xAI Grok models

**Examples:**
```bash
# Local Ollama model (default host: 127.0.0.1:11434)
ollama://llama3:70b

# Ollama with custom host and parameters
ollama://qwen2.5:32b@192.168.1.100:11434?temperature=0.7

# Google Gemini model
google://gemini-2.5-flash

# xAI Grok model
grok://grok-4-1-fast-reasoning

# OpenRouter model
openrouter://anthropic/claude-3.5-sonnet
```

### Configuration File

You can also modify default settings in `Writer/Config.py`:

```python
# Default model for all tasks
ollamasemua = "grok://grok-4-1-fast-reasoning"
# ollamasemua = "google://gemini-2.5-flash"
# ollamasemua = "ollama://qwen2.5:32b"

# Stage-specific models (all default to ollamasemua unless overridden)
INITIAL_OUTLINE_WRITER_MODEL = ollamasemua
CHAPTER_STAGE1_WRITER_MODEL = ollamasemua
CHAPTER_STAGE2_WRITER_MODEL = ollamasemua
CHAPTER_STAGE3_WRITER_MODEL = ollamasemua

# Embedding model for lorebook
EMBEDDING_MODEL = "google://gemini-embedding-001"
# EMBEDDING_MODEL = "ollama://qwen3-embedding:latest"

# Generation parameters
OUTLINE_QUALITY = 92
CHAPTER_QUALITY = 90
EXPAND_OUTLINE = True
SCENE_GENERATION_PIPELINE = True

# Lorebook settings
USE_LOREBOOK = True  # Enable vector-based lore management
LOREBOOK_K_RETRIEVAL = 5  # Number of lore entries to retrieve

# Language settings
NATIVE_LANGUAGE = "id"  # "en" for English, "id" for Indonesian
```

### Automatic State Saving & Resuming

The application automatically saves its progress to allow resuming interrupted runs. This is particularly useful for long story generation sessions that might be interrupted.

#### State Saving Points

The system saves state after each major pipeline step:

1. **`init`**: Initial setup and configuration loaded
2. **`outline`**: Main story outline generation completed
3. **`detect_chapters`**: Chapter count detection finished
4. **`expand_chapters`**: Per-chapter outline expansion completed (if enabled)
5. **`chapter_generation`**: Saved after *each* individual chapter (allows mid-chapter resuming)
6. **`chapter_generation_complete`**: All chapters generated
7. **`post_processing`**: Before final editing/scrubbing/translation
8. **`complete`**: Full generation process finished

**Lorebook State Persistence**: Lorebook entries are automatically saved to state during checkpoints and restored when resuming, ensuring story consistency across interruptions.

#### State Files Location

State files are automatically saved in timestamped directories:

```
Logs/Generation_YYYY-MM-DD_HH-MM-SS/
├── run.state.json          # Resume from here
├── Main.log                # Generation logs
└── LangchainDebug/         # Detailed AI interaction logs
```

#### Resume Example

```bash
# Resume from a previous run
python Write.py -Resume Logs/Generation_2025-12-19_14-14-58/run.state.json

# The system will continue from where it left off, including lorebook state
```

## 🧰 Architecture Overview

![Block Diagram](Docs/BlockDiagram.drawio.svg)

The AI Story Generator uses a modular pipeline architecture:

### Core Components

- **`Write.py`**: Main entry point and argument parsing
- **`Writer/Pipeline.py`**: Orchestrates the entire generation process
- **`Writer/Config.py`**: Configuration settings and model assignments
- **`Writer/Prompts.py`** & **`Writer/Prompts_id.py`**: Multi-language prompt templates

### Generation Modules

- **`Writer/OutlineGenerator.py`**: Story outline creation and refinement
- **`Writer/Chapter/ChapterGenerator.py`**: Multi-stage chapter writing (plot → character → dialogue)
- **`Writer/Chapter/ChapterDetector.py`**: Automatic chapter count detection
- **`Writer/Scene/`**: Scene-by-scene generation pipeline
- **`Writer/NovelEditor.py`**: Final novel-wide editing pass
- **`Writer/Scrubber.py`**: AI artifact cleanup
- **`Writer/Translator.py`**: Multi-language translation support
- **`Writer/Lorebook.py`**: Vector-based lore management with ChromaDB

### Infrastructure

- **`Writer/Interface/Wrapper.py`**: Unified LLM provider interface (Ollama, Google, OpenRouter, Grok)
- **`Writer/PrintUtils.py`**: Logging and output formatting
- **`Writer/Statistics.py`**: Generation metrics and timing
- **`tests/`**: Comprehensive test suite with pytest

### Key Features Implementation

**Lorebook System** (`Writer/Lorebook.py`):
- ChromaDB vector storage for semantic retrieval
- Automatic character, location, and plot element tracking
- Configurable similarity threshold and retrieval count
- Persistent storage across generation sessions
- State checkpoint integration for resume capability

**Repetition Detection**:
- Character explosion detection (consecutive identical characters)
- N-gram loop detection (repeating word sequences)
- Phrase repetition detection
- Auto-retry with increased temperature on detection

**PDF Generation** (`Writer/PDFGenerator.py`):
- Optimized margins and line height for readability
- Configurable fonts and spacing
- Automatic chapter and section formatting

### Language Support

The system supports both Indonesian and English generation:
- Prompts automatically selected based on `NATIVE_LANGUAGE` config
- Translation capabilities for both input prompts and output stories
- Localized prompt templates maintained in parallel files

## 🛠️ Customization

### Model Experimentation
- **Mix and match models**: Use different models for different generation stages
- **Local vs Cloud**: Combine local Ollama models with cloud providers for optimal cost/performance
- **Quality tuning**: Adjust revision loops and quality thresholds
- **Repetition control**: Configure repetition penalties and auto-retry behavior

### Prompt Customization
- **Modify existing prompts**: Edit `Writer/Prompts.py` or `Writer/Prompts_id.py`
- **Create custom prompts**: Add new story prompts in the `Prompts/` directory
- **Multi-language support**: Ensure changes are reflected in both language files

### Pipeline Configuration
- **Enable/disable features**: Control outline expansion, scene generation, final editing, lorebook
- **Quality parameters**: Adjust minimum word counts, revision limits, quality scores
- **Performance tuning**: Optimize for speed vs quality based on your needs

## 💪 What's Working Well

- **Robust story generation**: Consistently produces substantial narratives suitable for novella or novel-length works
- **Character consistency**: AI models maintain coherent character traits and development throughout the generated stories
- **Compelling story outlines**: Initial outline generation creates strong story structures that serve as solid foundations
- **Multi-stage chapter development**: The plot → character → dialogue approach produces well-rounded chapters
- **Reliable resuming**: State saving system allows seamless continuation of interrupted generations
- **Multi-language support**: Indonesian and English generation with translation capabilities
- **Quality assurance**: Built-in revision loops and evaluation systems ensure story quality
- **Lorebook system**: Vector-based lore management maintains story consistency
- **Repetition handling**: Automatic detection and retry prevents repetitive outputs
- **Comprehensive testing**: Full test coverage ensures reliable functionality and catches regressions

## 🔧 Areas for Improvement

- **Language variety**: Enhancing vocabulary diversity to reduce repetitive phrases and create more natural-sounding prose
- **Chapter transitions**: Improving flow and connections between chapters for better narrative cohesion
- **Pacing optimization**: Fine-tuning story pacing to focus appropriately on crucial plot points
- **Generation speed**: Optimizing performance to reduce generation times while maintaining quality
- **Advanced scene control**: More granular control over scene-by-scene generation and editing
- **Interactive feedback**: Potential for user interaction during the generation process

## 🤝 Contributing

We're excited to hear from you! Your feedback and contributions are crucial to improving the AI Story Generator.

### How to Contribute

1. **🐛 Report Issues**: Found a bug or have a feature request? [Open an issue](https://github.com/yusuf81/AIStoryWriter/issues)

2. **🔧 Submit Pull Requests**: Ready to contribute code? We welcome PRs for:
   - Bug fixes and improvements
   - New features and enhancements
   - Test coverage improvements
   - Documentation updates

3. **💡 Join Discussions**: Have ideas or want to brainstorm? [Start a discussion](https://github.com/yusuf81/AIStoryWriter/discussions)

4. **🔬 Experiment and Share**: Try different model combinations and share your results

5. **💬 Join our Community**: [Discord Server](https://discord.gg/R2SySWDr2s) for real-time chat and support

### Development Setup

```bash
# Clone and setup
git clone https://github.com/yusuf81/AIStoryWriter.git
cd AIStoryWriter
pip install -r requirements.txt

# Run tests before making changes
pytest -v

# Make your changes, then run tests again
pytest -v

# Run specific tests for the area you're working on
pytest tests/writer/test_pipeline.py -v
```

### Code Standards

- Follow the existing code structure and naming conventions
- Add tests for new functionality
- Update both `Prompts.py` and `Prompts_id.py` for multi-language support
- Ensure all tests pass before submitting PRs
- Run `flake8` and `pyright` on modified files

Don't hesitate to reach out – your input is valuable, and we're here to help!

## 📄 License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). This means that if you modify the code and use it to provide a service over a network, you must make your modified source code available to the users of that service. For more details, see the [LICENSE](LICENSE) file in the repository or visit [https://www.gnu.org/licenses/agpl-3.0.en.html](https://www.gnu.org/licenses/agpl-3.0.en.html).

---

Join us in shaping the future of AI-assisted storytelling! 🖋️🤖
