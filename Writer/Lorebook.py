# Writer/Lorebook.py - Vector-based lorebook management
import os
import re
from typing import Dict

try:
    # Try new imports first
    from langchain_chroma import Chroma
    # Removed HuggingFaceEmbeddings - using provider-based embeddings
    try:
        from langchain_core.documents import Document
    except ImportError:
        from langchain.docstore.document import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    # Fall back to old imports
    try:
        from langchain_community.vectorstores import Chroma
        # Removed HuggingFaceEmbeddings - using provider-based embeddings
        try:
            from langchain_core.documents import Document
        except ImportError:
            from langchain.docstore.document import Document
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False

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
        except Exception as e:
            self.SysLogger.Log(f"Failed to initialize Lorebook: {str(e)}", 3)
            if not getattr(self.config, 'EMBEDDING_FALLBACK_ENABLED', False):
                self.SysLogger.Log("EMBEDDING_FALLBACK_ENABLED is False. Lorebook will be disabled.", 3)
            else:
                self.SysLogger.Log("Embedding initialization failed, but fallback is DISABLED (fail-fast).", 3)
            self.db = None
            self.embeddings = None

    def add_entry(self, content: str, metadata: Dict[str, object]) -> None:
        """
        Add a lore entry to the vector store

        Args:
            content (str): The lore content
            metadata (Dict[str, any]): Metadata about the entry (type, character, etc.)
        """
        if self.db is None:
            self.SysLogger.Log("Cannot add entry: Lorebook not initialized", 6)
            self.SysLogger.Log(f"self.db is None: {self.db is None}, self.embeddings is None: {self.embeddings is None}", 6)
            return

        try:
            # Create document with content and metadata
            doc = Document(
                page_content=content,
                metadata=metadata
            )

            # Add to vector store
            self.db.add_documents([doc])

            self.SysLogger.Log(f"Added lore entry: {content[:50]}...", 5)

        except Exception as e:
            self.SysLogger.Log(f"Failed to add lore entry: {str(e)}", 2)

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
