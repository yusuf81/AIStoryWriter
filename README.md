# AI Story Generator 📚✨

Generate full-length novels with AI! Harness the power of large language models to create engaging stories based on your prompts.

[![Discord](https://img.shields.io/discord/1255847829763784754?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://discord.gg/R2SySWDr2s)

## 🚀 Features

- Generate medium to full-length novels: Produce substantial stories with coherent narratives, suitable for novella or novel-length works.
- Easy setup and use: Get started quickly with minimal configuration required.
- Customizable prompts and models: Choose from existing prompts or create your own, and select from various language models.
- Automatic model downloading: The system can automatically download required models via Ollama if they aren't already available.
- Support for local models via Ollama: Run language models locally for full control and privacy.
- Cloud provider support (currently Google): Access high-performance computing resources for those without powerful GPUs.
- Flexible configuration options: Fine-tune the generation process through easily modifiable settings.
- Works across all operating systems
- Supoorts translation of the generated stories in all languages
- Resume interrupted generation runs from the last completed step
- Optional scene-by-scene generation pipeline for initial chapter drafts
- Optional final editing pass over the entire novel
- Optional scrubbing pass to remove potential AI artifacts (like leftover instructions)
- Includes a script (`Evaluate.py`) for comparing the quality of two generated stories

## 🏁 Quick Start

Getting started with AI Story Generator is easy:

1. Clone the repository
2. Install [Ollama](https://ollama.com/) for local model support
3. Run the generator:

```sh
./Write.py -Prompt Prompts/YourChosenPrompt.txt
```

That's it! The system will automatically download any required models and start generating your story.

**Optional steps:**

- Modify prompts in `Writer/Prompts.py` or create your own
- Configure the model selection in `Writer/Config.py`

## 💻 Hardware Recommendations

Not sure which models to use with your GPU? Check out our [Model Recommendations](Docs/Models.md) page for suggestions based on different GPU capabilities. We provide a quick reference table to help you choose the right models for your hardware, ensuring optimal performance and quality for your story generation projects.

## 🛠️ Usage

You can customize the models used for different parts of the story generation process in two ways:

### 1. Using Command-Line Arguments (Recommended)

You can override the default models by specifying them as command-line arguments:

```sh
./Write.py -Prompt Prompts/YourChosenPrompt.txt -InitialOutlineModel "ollama://llama3:70b" ...
```

Available command-line arguments are stated in the `Write.py` file.

Key arguments include:
*   `-Resume {path/to/run.state.json}`: Resume a previous run from its state file.
*   `-InitialOutlineModel {model_string}`: Model for initial outline generation and revision.
*   `-ChapterOutlineModel {model_string}`: Model for per-chapter outline expansion or scene outline generation.
*   `-ChapterS1Model {model_string}`: Model for chapter stage 1 (plot/scene writing).
*   `-ChapterS2Model {model_string}`: Model for chapter stage 2 (character development).
*   `-ChapterS3Model {model_string}`: Model for chapter stage 3 (dialogue).
*   `-FinalNovelEditorModel {model_string}`: Model for the final novel-wide edit pass.
*   `-ChapterRevisionModel {model_string}`: Model for revising chapters during the feedback loop.
*   `-RevisionModel {model_string}`: Model for generating feedback/critique.
*   `-EvalModel {model_string}`: Model for quality evaluation (true/false) and chapter counting.
*   `-InfoModel {model_string}`: Model for extracting final story info (title, summary, tags).
*   `-ScrubModel {model_string}`: Model for the final scrubbing pass.
*   `-CheckerModel {model_string}`: Model for internal checks (e.g., scene JSON conversion).
*   `-TranslatorModel {model_string}`: Model for translation tasks.
*   `-ExpandOutline`: Expand the main outline into detailed per-chapter outlines before writing. (Enabled by default)
*   `-SceneGenerationPipeline`: Use the scene-by-scene generation method for initial chapter drafts. (Enabled by default)
*   `-EnableFinalEditPass`: Perform an additional editing pass on the *entire novel* after initial generation. (Enabled by default)
*   `-NoScrubChapters`: Disable the final pass that cleans up potential AI artifacts. (Scrubbing enabled by default)
*   `-NoChapterRevision`: Disable the feedback/revision loop during chapter generation. (Revisions enabled by default)
*   `-Translate {Language}`: Translate the final story into the specified language (e.g., 'French').
*   `-TranslatePrompt {Language}`: Translate the input prompt into the specified language before generation.

The model format is: `{ModelProvider}://{ModelName}@{ModelHost}?parameter=value`

- Default host is `127.0.0.1:11434` (currently only affects ollama)
- Default ModelProvider is `ollama`
- Supported providers: `ollama`, `google`, `openrouter`
- For `ollama` we support the passing of parameters (e.g. `temperature`) on a per model basis

Example:
```sh
./Write.py -Prompt Prompts/YourChosenPrompt.txt -InitialOutlineModel "google://gemini-1.5-pro" -ChapterOutlineModel "ollama://llama3:70b@192.168.1.100:11434" ...
```

This flexibility allows you to experiment with different models for various parts of the story generation process, helping you find the optimal combination for your needs.


NOTE: If you're using a provider that needs an API key, please copy `.env.example` to `.env` and paste in your API keys there.


### 2. Using Writer/Config.py


Edit the `Writer/Config.py` file to change the default models:

```python
INITIAL_OUTLINE_WRITER_MODEL = "ollama://llama3:70b"
CHAPTER_OUTLINE_WRITER_MODEL = "ollama://gemma2:27b"
CHAPTER_WRITER_MODEL = "google://gemini-1.5-flash"
...
```

### 3. Automatic State Saving & Resuming

The application automatically saves its progress to allow resuming interrupted runs. The state is saved after each major step, indicated by the `last_completed_step` value within the state file:

1.  **`init`**: Saved right after initializing a new run or loading the state for resume, before any generation begins.
2.  **`outline`**: Saved after the main story outline is successfully generated.
3.  **`detect_chapters`**: Saved after the total number of chapters is detected.
4.  **`expand_chapters`**: Saved after expanding the main outline into per-chapter outlines (only if the `-ExpandOutline` feature is enabled).
5.  **`chapter_generation`**: Saved after *each* individual chapter is generated. This allows resuming mid-way through chapter writing.
6.  **`chapter_generation_complete`**: Saved once all chapters have been initially generated.
7.  **`post_processing`**: Saved just before starting the final editing, scrubbing, or translation steps.
8.  **`complete`**: Saved after the entire process finishes and the final output files are written.

The state is saved in a JSON file named `run.state.json`. By default, this file is located within the run-specific log directory:

```
Logs/Generation_YYYY-MM-DD_HH-MM-SS/run.state.json
```

Where `YYYY-MM-DD_HH-MM-SS` corresponds to the date and time the run was started.

To resume a run, use the `-Resume` command-line argument, providing the path to the specific `run.state.json` file you wish to continue from.

## 🧰 Architecture Overview

![Block Diagram](Docs/BlockDiagram.drawio.svg)

## 🛠️ Customization

- Experiment with different local models via Ollama: Try out various language models to find the best fit for your storytelling needs.
- Test various model combinations for different story components: Mix and match models for outline generation, chapter writing, and revisions to optimize output quality.

## 💪 What's Working Well

- Generating decent-length stories: The system consistently produces narratives of substantial length, suitable for novella or novel-length works.
- Character consistency: AI models maintain coherent character traits and development throughout the generated stories.
- Interesting story outlines: The initial outline generation creates compelling story structures that serve as strong foundations for the full narratives.

## 🔧 Areas for Improvement

- Reducing repetitive phrases: We're working on enhancing the language variety to create more natural-sounding prose.
- Improving chapter flow and connections: Efforts are ongoing to create smoother transitions between chapters and maintain narrative cohesion.
- Addressing pacing issues: Refinements are being made to ensure proper story pacing and focus on crucial plot points.
- Optimizing generation speed: We're continuously working on improving performance to reduce generation times without sacrificing quality.

## 🤝 Contributing

We're excited to hear from you! Your feedback and contributions are crucial to improving the AI Story Generator. Here's how you can get involved:

1. 🐛 **Open Issues**: Encountered a bug or have a feature request? [Open an issue](https://github.com/datacrystals/AIStoryWriter/issues) and let us know!

2. 💡 **Start Discussions**: Have ideas or want to brainstorm? [Start a discussion](https://github.com/datacrystals/AIStoryWriter/discussions) in our GitHub Discussions forum.

3. 🔬 **Experiment and Share**: Try different model combinations and share your results. Your experiments can help improve the system for everyone!

4. 🖊️ **Submit Pull Requests**: Ready to contribute code? We welcome pull requests for improvements and new features.

5. 💬 **Join our Discord**: For real-time chat, support, and community engagement, [join our Discord server](https://discord.gg/R2SySWDr2s).

Don't hesitate to reach out – your input is valuable, and we're here to help!

## 📄 License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). This means that if you modify the code and use it to provide a service over a network, you must make your modified source code available to the users of that service. For more details, see the [LICENSE](LICENSE) file in the repository or visit [https://www.gnu.org/licenses/agpl-3.0.en.html](https://www.gnu.org/licenses/agpl-3.0.en.html).

---

Join us in shaping the future of AI-assisted storytelling! 🖋️🤖
