# Writer/Lorebook.py - Vector-based lorebook management
import os
import re
import json
from datetime import datetime
from typing import Dict

# Import from langchain-chroma exclusively (no fallback to deprecated langchain_community)
from langchain_chroma import Chroma
try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.docstore.document import Document
LANGCHAIN_AVAILABLE = True
CHROMA_SOURCE = "langchain_chroma"
chroma_version = getattr(Chroma, '__version__', 'unknown')

from Writer import Config
from Writer import PrintUtils


class LorebookManager:
    """
    Manages story lore using vector embeddings for semantic retrieval.
    Provides character, world, and plot consistency across chapters.
    """

    def __init__(self, persist_dir: str = "./lorebook_db", config=None):
        """
        Initialize the LorebookManager

        Args:
            persist_dir (str): Directory to persist the vector database
            config: Configuration object (defaults to Writer.Config)
        """
        self.persist_dir = persist_dir
        self.config = config or Config

        # Initialize logger
        self.SysLogger = PrintUtils.Logger()

        # Check if embedding model is configured
        if not getattr(self.config, 'EMBEDDING_MODEL', ''):
            self.SysLogger.Log("EMBEDDING_MODEL not configured. Lorebook will be disabled.", 3)
            self.db = None
            self.embeddings = None
            return

        if not LANGCHAIN_AVAILABLE:
            self.SysLogger.Log("LangChain not available. Lorebook will be disabled.", 3)
            self.db = None
            self.embeddings = None
            return

        if not self.config.USE_LOREBOOK:
            self.SysLogger.Log("Lorebook disabled by configuration", 5)
            self.db = None
            self.embeddings = None
            return

        try:
            # Initialize embedder interface
            from Writer.Interface.Wrapper import Interface
            self.embedding_interface = Interface([])
            self.embedding_interface.LoadModels([self.config.EMBEDDING_MODEL])

            # Create custom embedding function
            self.embeddings = self._create_provider_embeddings(self.config.EMBEDDING_MODEL)

            # Ensure persist directory exists
            os.makedirs(self.persist_dir, exist_ok=True)

            # Initialize ChromaDB
            self.db = Chroma(
                collection_name="story_lore",
                embedding_function=self.embeddings,
                persist_directory=self.persist_dir
            )

            self.SysLogger.Log(f"Lorebook initialized with persist directory: {persist_dir}", 5)
            self.SysLogger.Log(f"Using embedding model: {self.config.EMBEDDING_MODEL}", 5)
            self.SysLogger.Log(f"Using Chroma from: {CHROMA_SOURCE}", 5)
        except Exception as e:
            self.SysLogger.Log(f"Failed to initialize Lorebook: {str(e)}", 3)
            if not getattr(self.config, 'EMBEDDING_FALLBACK_ENABLED', False):
                self.SysLogger.Log("EMBEDDING_FALLBACK_ENABLED is False. Lorebook will be disabled.", 3)
            else:
                self.SysLogger.Log("Embedding initialization failed, but fallback is DISABLED (fail-fast).", 3)
            self.db = None
            self.embeddings = None

    def add_entry(self, content: str, metadata: Dict[str, object]) -> str:
        """
        Add a lore entry to the vector store

        Args:
            content (str): The lore content
            metadata (Dict[str, any]): Metadata about the entry (type, character, etc.)

        Returns:
            str: The ID of the added entry
        """
        if self.db is None:
            self.SysLogger.Log("Cannot add entry: Lorebook not initialized", 6)
            self.SysLogger.Log(f"self.db is None: {self.db is None}, self.embeddings is None: {self.embeddings is None}", 6)
            return ""

        try:
            # Add timestamp to metadata for tracking
            metadata = metadata.copy()  # Don't modify original
            metadata["added_at"] = str(datetime.now())

            # Create document with content and metadata
            doc = Document(
                page_content=content,
                metadata=metadata
            )

            # Add to vector store
            doc_ids = self.db.add_documents([doc])

            self.SysLogger.Log(f"Added lore entry: {metadata.get('type', 'unknown')} - {metadata.get('name', 'unnamed')}", 5)

            return doc_ids[0] if doc_ids else ""

        except Exception as e:
            self.SysLogger.Log(f"Failed to add lore entry: {str(e)}", 2)
            return ""

    def retrieve(self, query: str, k: int = 5) -> str:
        """
        Retrieve relevant lore entries for a query

        Args:
            query (str): Query to search for
            k (int): Number of entries to retrieve (defaults to config.LOREBOOK_K_RETRIEVAL)

        Returns:
            str: Combined relevant lore entries
        """
        if self.db is None:
            self.SysLogger.Log("Cannot retrieve: Lorebook not initialized", 6)
            return ""

        if k is None:
            k = self.config.LOREBOOK_K_RETRIEVAL

        try:
            # Perform similarity search
            docs = self.db.similarity_search(query, k=k)

            if not docs:
                self.SysLogger.Log(f"No lore found for query: {query[:50]}...", 6)
                return ""

            # Combine retrieved documents
            results = []
            for doc in docs:
                # Format with metadata if available
                if doc.metadata:
                    metadata_str = " | ".join([f"{k}: {v}" for k, v in doc.metadata.items()])
                    results.append(f"{doc.page_content} ({metadata_str})")
                else:
                    results.append(doc.page_content)

            combined_result = "\n".join(results)

            self.SysLogger.Log(
                f"Retrieved {len(docs)} lore entries for query: {query[:50]}...",
                5
            )

            return combined_result

        except Exception as e:
            self.SysLogger.Log(f"Failed to retrieve lore: {str(e)}", 2)
            return ""

    def extract_from_outline(self, outline: str) -> None:
        """
        Extract lore entries from a story outline

        Args:
            outline (str): The story outline to parse
        """
        if self.db is None:
            self.SysLogger.Log("Cannot extract from outline: Lorebook not initialized", 6)
            return

        self.SysLogger.Log("Extracting lore from outline...", 5)

        # Extract characters
        self._extract_characters(outline)

        # Extract locations
        self._extract_locations(outline)

        # Extract world rules/magic system
        self._extract_world_rules(outline)

        # Extract plot points
        self._extract_plot_points(outline)

    def _extract_characters(self, text: str) -> None:
        """Extract character information from text"""
        # Look for character descriptions
        character_patterns = [
            r'([A-Z][a-z]+):\s*([^.\n]+(?:\.[^.\n]*)*)',  # Name: Description
            r'-\s*([A-Z][a-z]+):\s*([^.\n]+)',  # - Name: Description
            r'Characters?:\s*\n((?:.*\n)*?)\n\n',  # Characters: section
        ]

        for pattern in character_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    name = match[0]
                    description = match[1] if len(match) > 1 else ""

                    if len(description.strip()) > 10:  # Minimum length
                        self.add_entry(
                            content=f"{name}: {description}",
                            metadata={
                                "type": "character",
                                "name": name,
                                "source": "outline"
                            }
                        )

    def _extract_locations(self, text: str) -> None:
        """Extract location information from text"""
        location_patterns = [
            r'([A-Z][a-z]+\s*(?:Forest|City|Kingdom|Castle|Village|Mountain|River|Sea|Land|Realm)):\s*([^.\n]+)',
            r'Setting:?\s*\n((?:.*\n)*?)\n\n',
        ]

        for pattern in location_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    location = match[0]
                    description = match[1] if len(match) > 1 else ""

                    if len(description.strip()) > 10:
                        self.add_entry(
                            content=f"{location}: {description}",
                            metadata={
                                "type": "location",
                                "name": location,
                                "source": "outline"
                            }
                        )

    def _extract_world_rules(self, text: str) -> None:
        """Extract world rules and magic system information"""
        rule_patterns = [
            r'(?:Magic|System|Rules?):\s*\n((?:.*\n)*?)\n\n',
            r'(?:Magic|requirement|requires?)\s+([^.\n]+)',
            r'([^.!?]*(?:magic|spell|power|ability)[^.!?]*)',
        ]

        for pattern in rule_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                if isinstance(match, str) and len(match.strip()) > 10:
                    self.add_entry(
                        content=match.strip(),
                        metadata={
                            "type": "rule",
                            "category": "world",
                            "source": "outline"
                        }
                    )

    def _extract_plot_points(self, text: str) -> None:
        """Extract important plot points"""
        # Look for chapter summaries or plot outlines
        chapter_pattern = r'(?:Chapter\s+\d+|Chapter\s+[A-Z][a-z]+):\s*([^.\n]+(?:\.[^.\n]*)*)'

        matches = re.findall(chapter_pattern, text, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            if len(match.strip()) > 15:
                self.add_entry(
                    content=match.strip(),
                    metadata={
                        "type": "plot_point",
                        "source": "outline"
                    }
                )

    def extract_from_structured_data(self, story_elements, outline_output=None) -> None:
        """Extract lore from Pydantic objects directly (no string conversion)"""
        if not self.db:
            return

        # Extract from StoryElements object if provided
        if story_elements and hasattr(story_elements, 'extract_lorebook_entries'):
            for entry in story_elements.extract_lorebook_entries():
                self.add_entry(entry["content"], entry["metadata"])

        # Extract from OutlineOutput if provided
        if outline_output and hasattr(outline_output, 'extract_lorebook_entries'):
            for entry in outline_output.extract_lorebook_entries():
                self.add_entry(entry["content"], entry["metadata"])

    def clear(self) -> None:
        """Clear all lore entries"""
        if self.db is None:
            self.SysLogger.Log("Cannot clear: Lorebook not initialized", 6)
            return

        try:
            # Delete all documents
            self.db.delete_collection()

            # Reinitialize
            self.db = Chroma(
                collection_name="story_lore",
                embedding_function=self.embeddings,
                persist_directory=self.persist_dir
            )

            self.SysLogger.Log("Lorebook cleared", 5)

        except Exception as e:
            self.SysLogger.Log(f"Failed to clear lorebook: {str(e)}", 2)

    def _create_provider_embeddings(self, embedding_model: str):
        """
        Create a LangChain-compatible embeddings wrapper for our provider system
        """
        from langchain_core.embeddings import Embeddings

        class ProviderEmbeddings(Embeddings):
            def __init__(self, interface, model, logger):
                self.interface = interface
                self.model = model
                self.logger = logger

            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                embeddings, _ = self.interface.GenerateEmbedding(
                    self.logger, texts, self.model
                )
                return embeddings

            def embed_query(self, text: str) -> list[float]:
                embeddings, _ = self.interface.GenerateEmbedding(
                    self.logger, [text], self.model
                )
                return embeddings[0] if embeddings else []

        return ProviderEmbeddings(self.embedding_interface, embedding_model, self.SysLogger)

    def get_stats(self) -> Dict[str, object]:
        """
        Get statistics about the lorebook

        Returns:
            Dict[str, any]: Statistics including entry count and types
        """
        if not self.db:
            return {"initialized": False}

        try:
            # Get all documents
            all_docs = self.db.get()

            # Count by type
            type_counts = {}
            for metadata in all_docs.get('metadatas', []):
                entry_type = metadata.get('type', 'unknown')
                type_counts[entry_type] = type_counts.get(entry_type, 0) + 1

            return {
                "initialized": True,
                "total_entries": len(all_docs.get('ids', [])),
                "type_counts": type_counts,
                "persist_dir": self.persist_dir
            }

        except Exception as e:
            self.SysLogger.Log(f"Failed to get stats: {str(e)}", 2)
            return {"initialized": True, "error": str(e)}

    def get_all_entries(self) -> list:
        """
        Get all lorebook entries as serializable list

        Returns:
            list: List of dictionaries with id, text, and metadata
        """
        if self.db is None:
            return []

        try:
            # Get all documents from ChromaDB
            all_docs = self.db.get(include=["metadatas", "documents"])

            entries = []
            for i, doc_id in enumerate(all_docs["ids"]):
                entries.append({
                    "id": doc_id,
                    "text": all_docs["documents"][i],
                    "metadata": all_docs["metadatas"][i]
                })

            return entries
        except Exception as e:
            self.SysLogger.Log(f"Failed to get all entries: {str(e)}", 3)
            return []

    def save_entries_to_state(self, state_filepath: str) -> None:
        """
        Save all lorebook entries to state file

        Args:
            state_filepath (str): Path to the state file
        """
        if self.db is None:
            return

        try:
            # Read existing state
            state_data = {}
            if os.path.exists(state_filepath):
                with open(state_filepath, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)

            # Get all entries
            entries = self.get_all_entries()

            # Update or create lorebook_entries in state
            if "other_data" not in state_data:
                state_data["other_data"] = {}

            state_data["other_data"]["lorebook_entries"] = entries

            # Save state back to file (atomic save)
            temp_file = state_filepath + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)

            os.rename(temp_file, state_filepath)
            self.SysLogger.Log(f"Saved {len(entries)} lorebook entries to state", 5)

        except Exception as e:
            self.SysLogger.Log(f"Failed to save entries to state: {str(e)}", 3)

    def load_entries_from_state(self, state_filepath: str) -> None:
        """
        Load all lorebook entries from state file

        Args:
            state_filepath (str): Path to the state file
        """
        if self.db is None:
            return

        try:
            # Read state file
            if not os.path.exists(state_filepath):
                self.SysLogger.Log("State file not found, no lorebook entries to load", 5)
                return

            with open(state_filepath, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            # Get lorebook entries
            lorebook_entries = state_data.get("other_data", {}).get("lorebook_entries", [])

            if not lorebook_entries:
                self.SysLogger.Log("No lorebook entries found in state", 5)
                return

            # Clear existing entries and restore from state
            self.clear()

            loaded_count = 0
            for entry in lorebook_entries:
                self.add_entry(entry["text"], entry["metadata"])
                loaded_count += 1

            self.SysLogger.Log(f"Loaded {loaded_count} lorebook entries from state", 5)

        except Exception as e:
            self.SysLogger.Log(f"Failed to load entries from state: {str(e)}", 3)

    @staticmethod
    def save_lorebook_state(lorebook_instance, state_filepath: str) -> None:
        """
        Static method to save lorebook entries to state

        Args:
            lorebook_instance: LorebookManager instance
            state_filepath (str): Path to the state file
        """
        lorebook_instance.save_entries_to_state(state_filepath)

    @staticmethod
    def load_lorebook_state(lorebook_instance, state_filepath: str) -> None:
        """
        Static method to load lorebook entries from state

        Args:
            lorebook_instance: LorebookManager instance
            state_filepath (str): Path to the state file
        """
        lorebook_instance.load_entries_from_state(state_filepath)
