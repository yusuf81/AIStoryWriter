# Embedding System Integration

This document describes the unified embedding system that centralizes embeddings with the existing provider architecture.

## Overview

The embedding system has been unified with the existing provider model (ollama://, google://, openrouter://) to provide consistent configuration and usage patterns for both text generation and embeddings.

## Configuration

### Basic Setup

Add the embedding model configuration to `Writer/Config.py`:

```python
# Embedding Model Configuration
EMBEDDING_MODEL = "ollama://nomic-embed-text"  # Your embedding model
EMBEDDING_DIMENSIONS = 768                      # Default dimensions
EMBEDDING_CTX = 8192                           # Context window
EMBEDDING_FALLBACK_ENABLED = False              # Fail fast, no fallback
```

### Provider Examples

Choose your embedding provider:
- **Ollama (local)**: `EMBEDDING_MODEL = "ollama://nomic-embed-text"`
- **Google (cloud)**: `EMBEDDING_MODEL = "google://gemini-embedding-001"`
- **OpenRouter (cloud)**: `EMBEDDING_MODEL = "openrouter://text-embedding-3-small"`

## Usage in Lorebook

The lorebook automatically uses the configured embedding model:

```python
from Writer.Lorebook import LorebookManager

# The lorebook will use the configured EMBEDDING_MODEL automatically
lorebook = LorebookManager(persist_dir="./my_lorebook")

# Add entries
lorebook.add_entry("Elena is a skilled ice mage", {"type": "character"})

# Retrieve relevant information
relevant_lore = lorebook.retrieve("Elena's magical abilities", k=5)
```

## Direct API Usage

Generate embeddings directly using the Interface Wrapper:

```python
from Writer.Interface.Wrapper import Interface

interface = Interface()
interface.LoadModels([EMBEDDING_MODEL])  # Load the model

# Generate embeddings
texts = ["Hello world", "How are you?"]
embeddings, usage = interface.GenerateEmbedding(
    logger, texts, EMBEDDING_MODEL
)

print(f"Embeddings shape: {len(embeddings)} x {len(embeddings[0])}")
print(f"Token usage: {usage}")
```

## Migration Guide

### From HuggingFace Embeddings

If you were using HuggingFace embeddings directly:

```python
# OLD WAY (no longer needed)
from langchain_huggingface import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# NEW WAY
# Set EMBEDDING_MODEL in Config.py
EMBEDDING_MODEL = "ollama://nomic-embed-text"
```

### Dependencies Removed

The following dependencies are no longer required:
- `sentence-transformers` - Replaced by provider-based embeddings
- `langchain-huggingface` - No longer using HuggingFace embeddings

## Supported Providers

### Ollama

Features:
- Local processing (no API costs)
- Models: nomic-embed-text, mxbai-embed-large
- No token counting provided

Example:
```python
EMBEDDING_MODEL = "ollama://nomic-embed-text"
```

### Google Gemini

Features:
- Cloud-based (API costs)
- Flexible dimensions (128-3072)
- Advanced settings

Example:
```python
EMBEDDING_MODEL = "google://gemini-embedding-001"
```

### OpenRouter

Features:
- Multiple embedding models via marketplace
- OpenAI-compatible API
- Token usage tracking

Example:
```python
EMBEDDING_MODEL = "openrouter://text-embedding-3-small"
```

## Error Handling

The system follows a "fail-fast" approach:

1. If `EMBEDDING_MODEL` is not set, lorebook is disabled
2. If embedding model fails to load and `EMBEDDING_FALLBACK_ENABLED=False`, lorebook is disabled
3. Errors are logged with clear messages

To enable fallback (not recommended):
```python
EMBEDDING_FALLBACK_ENABLED = True
```

## Performance Considerations

### Token Usage Tracking

- Ollama: Estimated from word count
- Gemini: Estimated from word count
- OpenRouter: Actual token usage from API

### Caching

- Interface wrapper caches loaded models
- ChromaDB caches embeddings (vector database)

## Testing

Run embedding tests:

```bash
# Test the embedding functionality
pytest tests/writer/interface/test_wrapper_embedding.py -v

# Test lorebook integration (requires mocking)
pytest tests/writer/test_lorebook.py::TestLorebookManager::test_with_mocks -v
```

## Troubleshooting

### Common Issues

1. **"EMBEDDING_MODEL not configured"**
   - Set `EMBEDDING_MODEL` in Config.py
   - Use correct provider:// format

2. **"Provider not supported"**
   - Check provider is one of: ollama, google, openrouter
   - Verify provider is enabled in your environment

3. **"Lang dependencies missing"**
   - Run: `pip install -r requirements.txt`
   - Ensure all dependencies are installed

### Debug Mode

Enable logging to see embedding operations:

```python
from Writer.PrintUtils import Logger
logger = Logger()
# Embedding operations will be logged
```

## Examples

### Basic Embedding Generation

```python
from Writer.Config import EMBEDDING_MODEL
from Writer.Interface.Wrapper import Interface
from Writer.PrintUtils import Logger

# Initialize
interface = Interface()
logger = Logger()

# Load model
interface.LoadModels([EMBEDDING_MODEL])

# Generate embeddings for a list of texts
texts = [
    "The hero wielded a legendary sword",
    "Magic flowed through the ancient runes",
    "The dragon's scales gleamed in the moonlight"
]

embeddings, usage = interface.GenerateEmbedding(
    logger, texts, EBEDDING_MODEL
)

print(f"Generated {len(embeddings)} embeddings")
print(f"Usage: {usage}")
```

### Lorebook with Custom Provider

```python
import Writer.Config as Config

# Configure embedding model
Config.EMBEDDING_MODEL = "openrouter://text-embedding-ada-002"

# Use in lorebook
from Writer.Lorebook import LorebookManager

lorebook = LorebookManager()
lorebook.add_entry("King Aldric rules with wisdom", {"type": "character"})
lorebook.add_entry("The Crystal Tower holds ancient secrets", {"type": "location"})

# Retrieve relevant lore for chapter generation
context = lorebook.retrieve("Chapter about the Crystal Tower", k=3)
print(context)
```

### Provider-Specific Configuration

```python
import Writer.Config as Config

# Ollama with custom host
Config.EMBEDDING_MODEL = "ollama://nomic-embed-text@localhost:11435"

# Google with region settings (if needed)
Config.EMBEDDING_MODEL = "google://text-embedding-004"

# OpenRouter with specific model
Config.EMBEDDING_MODEL = "openrouter://openai/text-embedding-3-small"
```