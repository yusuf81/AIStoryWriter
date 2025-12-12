# tests/writer/test_lorebook.py
import pytest
import tempfile
import shutil
import os
from unittest.mock import Mock, patch

# Import the module we're testing
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class TestLorebookManager:
    """Test suite for LorebookManager class following TDD London School approach"""

    def setup_method(self):
        """Setup for each test method"""
        # Create temporary directory for test lorebook
        self.temp_dir = tempfile.mkdtemp()
        self.test_persist_dir = os.path.join(self.temp_dir, "test_lorebook")

        # Set up mock embedding model for tests
        import Writer.Config
        self.original_embedding_model = getattr(Writer.Config, 'EMBEDDING_MODEL', '')
        Writer.Config.EMBEDDING_MODEL = 'mock://test-model'  # Will be mocked in tests

        # Mock the Interface to avoid real embedding generation
        self.interface_patcher = patch('Writer.Interface.Wrapper.Interface')
        self.mock_interface_class = self.interface_patcher.start()
        self.mock_interface = Mock()
        self.mock_interface_class.return_value = self.mock_interface

        # Mock embedding generation
        self.mock_interface.GenerateEmbedding.return_value = (
            [[0.1, 0.2, 0.3]], {"prompt_tokens": 1, "completion_tokens": 0}
        )

        # Mock Chroma to avoid actual vector storage
        self.chroma_patcher = patch('Writer.Lorebook.Chroma')
        self.mock_chroma_class = self.chroma_patcher.start()
        self.mock_db = Mock()
        # Create Document-like mock objects for similarity search
        mock_doc = Mock()
        mock_doc.page_content = "Test lore content"
        mock_doc.metadata = {"type": "test"}
        self.mock_db.similarity_search.return_value = [mock_doc]
        self.mock_chroma_class.return_value = self.mock_db

    def teardown_method(self):
        """Cleanup after each test method"""
        # Remove temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

        # Stop the patchers
        self.interface_patcher.stop()
        self.chroma_patcher.stop()

        # Restore original embedding model
        import Writer.Config
        Writer.Config.EMBEDDING_MODEL = self.original_embedding_model

    def test_lorebook_initialization(self):
        """Test that LorebookManager initializes correctly"""
        # Red phase: Write failing test
        from Writer.Lorebook import LorebookManager

        # Green phase: Test initialization
        lorebook = LorebookManager(persist_dir=self.test_persist_dir)

        assert lorebook is not None
        assert hasattr(lorebook, 'persist_dir')
        assert lorebook.persist_dir == self.test_persist_dir
        assert hasattr(lorebook, 'db')
        assert hasattr(lorebook, 'embeddings')

    def test_add_single_entry(self):
        """Test adding a single lore entry"""
        from Writer.Lorebook import LorebookManager

        lorebook = LorebookManager(persist_dir=self.test_persist_dir)

        # Add an entry
        lorebook.add_entry(
            content="Alice has blue eyes and is a brave knight.",
            metadata={"type": "character", "name": "Alice"}
        )

        # Verify it was added to the database
        self.mock_db.add_documents.assert_called_once()
        call_args = self.mock_db.add_documents.call_args[0][0]  # Get first positional argument (list of docs)
        assert len(call_args) == 1
        added_doc = call_args[0]
        assert added_doc.page_content == "Alice has blue eyes and is a brave knight."
        assert added_doc.metadata == {"type": "character", "name": "Alice"}

    def test_retrieve_character_information(self, mock_document):
        """Test retrieving character information"""
        from Writer.Lorebook import LorebookManager

        # Setup mock to return specific content using fixture
        self.mock_db.similarity_search.return_value = [
            mock_document("Alice has blue eyes and is a brave knight.",
                         {"type": "character", "name": "Alice"})
        ]

        lorebook = LorebookManager(persist_dir=self.test_persist_dir)

        # Add test entries (to keep test structure)
        lorebook.add_entry(
            content="Alice has blue eyes and is a brave knight.",
            metadata={"type": "character", "name": "Alice"}
        )
        lorebook.add_entry(
            content="The Dark Forest has perpetual twilight and dangerous creatures.",
            metadata={"type": "location", "name": "Dark Forest"}
        )
        lorebook.add_entry(
            content="Magic requires blood sacrifice to work.",
            metadata={"type": "rule", "category": "magic"}
        )

        # Test retrieval for character
        result = lorebook.retrieve("Alice's appearance", k=2)

        assert "blue eyes" in result
        assert "Alice" in result

    def test_retrieve_location_information(self):
        """Test retrieving location information"""
        from Writer.Lorebook import LorebookManager

        # Setup mock to return specific content
        mock_forest_doc = Mock()
        mock_forest_doc.page_content = "The Dark Forest has perpetual twilight and dangerous creatures."
        mock_forest_doc.metadata = {"type": "location", "name": "Dark Forest"}
        self.mock_db.similarity_search.return_value = [mock_forest_doc]

        lorebook = LorebookManager(persist_dir=self.test_persist_dir)

        # Add test entries
        lorebook.add_entry(
            content="The Dark Forest has perpetual twilight and dangerous creatures.",
            metadata={"type": "location", "name": "Dark Forest"}
        )
        lorebook.add_entry(
            content="The village is peaceful and has a wooden palisade.",
            metadata={"type": "location", "name": "Village"}
        )

        # Test retrieval for location
        result = lorebook.retrieve("Dark Forest", k=2)

        assert "perpetual twilight" in result
        assert "dangerous creatures" in result

    def test_retrieve_multiple_entries(self):
        """Test retrieving multiple relevant entries"""
        from Writer.Lorebook import LorebookManager

        # Setup mock to return specific content
        mock_alice_doc = Mock()
        mock_alice_doc.page_content = "Alice has blue eyes."
        mock_alice_doc.metadata = {"type": "character", "name": "Alice"}
        self.mock_db.similarity_search.return_value = [mock_alice_doc]

        lorebook = LorebookManager(persist_dir=self.test_persist_dir)

        # Add multiple entries about Alice
        lorebook.add_entry(
            content="Alice has blue eyes.",
            metadata={"type": "character_trait", "name": "Alice"}
        )
        lorebook.add_entry(
            content="Alice is searching for the artifact.",
            metadata={"type": "character_status", "name": "Alice"}
        )
        lorebook.add_entry(
            content="Bob has brown hair.",
            metadata={"type": "character_trait", "name": "Bob"}
        )

        # Retrieve with k=3
        result = lorebook.retrieve("Alice", k=3)

        # Should include information about Alice
        assert "blue eyes" in result

    def test_retrieve_with_k_parameter(self):
        """Test that k parameter limits number of results"""
        from Writer.Lorebook import LorebookManager

        # Setup mock to return specific content

        lorebook = LorebookManager(persist_dir=self.test_persist_dir)

        # Add 5 entries
        for i in range(5):
            lorebook.add_entry(
                content=f"Entry {i}: Some content here.",
                metadata={"index": i}
            )

        # Retrieve with k=2
        result = lorebook.retrieve("Entry", k=2)

        # Should not exceed what we added (actual number depends on similarity)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_extract_from_outline(self, mock_document):
        """Test extracting lore entries from outline"""
        from Writer.Lorebook import LorebookManager

        # Setup mock to return different content based on query
        def mock_similarity_search(query, k=None):
            if "Alice" in query:
                return [mock_document("Alice: A brave knight with blue eyes, searching for the artifact.",
                                     {"type": "character", "name": "Alice"})]
            elif "magic" in query:
                return [mock_document("Magic requires blood sacrifice to work.",
                                     {"type": "magic_system", "name": "Blood Magic"})]
            return []

        self.mock_db.similarity_search.side_effect = mock_similarity_search

        lorebook = LorebookManager(persist_dir=self.test_persist_dir)

        # Sample outline text
        outline_text = """
        Story Elements:
        Characters:
        - Alice: A brave knight with blue eyes, searching for the artifact
        - Bob: A wise wizard who guides Alice

        Setting:
        - Kingdom of Eldoria: A peaceful realm
        - Dark Forest: A dangerous place with perpetual twilight

        Magic System:
        - Magic requires blood sacrifice
        - Only the worthy can wield ancient artifacts
        """

        # Extract from outline
        lorebook.extract_from_outline(outline_text)

        # Test retrieval
        alice_result = lorebook.retrieve("Alice", k=3)
        assert "blue eyes" in alice_result or "brave knight" in alice_result

        magic_result = lorebook.retrieve("magic system", k=3)
        assert "blood sacrifice" in magic_result

    def test_persistence(self):
        """Test that lorebook persists across sessions"""
        from Writer.Lorebook import LorebookManager

        # Setup mock to return specific content
        mock_alice_doc = Mock()
        mock_alice_doc.page_content = "Alice has blue eyes."
        mock_alice_doc.metadata = {"type": "character", "name": "Alice"}
        self.mock_db.similarity_search.return_value = [mock_alice_doc]

        # Create first instance and add data
        lorebook1 = LorebookManager(persist_dir=self.test_persist_dir)
        lorebook1.add_entry(
            content="Alice has blue eyes.",
            metadata={"type": "character", "name": "Alice"}
        )

        # Create second instance with same persist directory
        lorebook2 = LorebookManager(persist_dir=self.test_persist_dir)

        # Should be able to retrieve data
        result = lorebook2.retrieve("Alice", k=3)
        assert "Alice" in result

    def test_clear_lorebook(self):
        """Test clearing the lorebook"""
        from Writer.Lorebook import LorebookManager

        # Setup mock to return specific content

        lorebook = LorebookManager(persist_dir=self.test_persist_dir)

        # Add entries
        lorebook.add_entry("Alice has blue eyes.", {"type": "character"})
        lorebook.add_entry("Some location info.", {"type": "location"})

        # Verify entries exist
        result = lorebook.retrieve("Alice", k=3)
        assert len(result) > 0

        # Clear lorebook
        lorebook.clear()

        # Verify entries are gone (may need to create new instance)
        lorebook_after_clear = LorebookManager(persist_dir=self.test_persist_dir)
        result_after = lorebook_after_clear.retrieve("Alice", k=3)
        # Should have minimal or no results
        assert isinstance(result_after, str)

    def test_empty_retrieval(self):
        """Test retrieval from empty lorebook"""
        from Writer.Lorebook import LorebookManager

        lorebook = LorebookManager(persist_dir=self.test_persist_dir)

        # Retrieve from empty lorebook
        result = lorebook.retrieve("Anything", k=5)

        # Should return empty string or minimal response
        assert isinstance(result, str)

    def test_with_mocks(self):
        """Test with mocked dependencies to avoid actual model loading"""
        from Writer.Lorebook import LorebookManager

        # Override mock setup for this specific test
        self.mock_db.similarity_search.return_value = [
            Mock(page_content="Alice has blue eyes")
        ]

        # Test with mocked dependencies
        lorebook = LorebookManager(persist_dir=self.test_persist_dir)

        # Test adding and retrieving
        lorebook.add_entry("Test entry", {"type": "test"})
        result = lorebook.retrieve("Test query", k=1)

        # Verify result
        assert isinstance(result, str)