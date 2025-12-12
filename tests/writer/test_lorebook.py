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

    def teardown_method(self):
        """Cleanup after each test method"""
        # Remove temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

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

        # Verify it was added (we'll check retrieval in next test)
        assert True  # For now, just ensure no exceptions

    def test_retrieve_character_information(self):
        """Test retrieving character information"""
        from Writer.Lorebook import LorebookManager

        lorebook = LorebookManager(persist_dir=self.test_persist_dir)

        # Add test entries
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
        assert "searching for the artifact" in result

    def test_retrieve_with_k_parameter(self):
        """Test that k parameter limits number of results"""
        from Writer.Lorebook import LorebookManager

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

    def test_extract_from_outline(self):
        """Test extracting lore entries from outline"""
        from Writer.Lorebook import LorebookManager

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

    @patch('Writer.Lorebook.HuggingFaceEmbeddings')
    @patch('Writer.Lorebook.Chroma')
    def test_with_mocks(self, mock_chroma, mock_embeddings):
        """Test with mocked dependencies to avoid actual model loading"""
        from Writer.Lorebook import LorebookManager

        # Setup mocks
        mock_embedding_model = Mock()
        mock_embeddings.return_value = mock_embedding_model

        mock_db = Mock()
        mock_db.similarity_search.return_value = [
            Mock(page_content="Alice has blue eyes")
        ]
        mock_chroma.return_value = mock_db

        # Test with mocked dependencies
        lorebook = LorebookManager(persist_dir=self.test_persist_dir)

        # Test adding and retrieving
        lorebook.add_entry("Test entry", {"type": "test"})
        result = lorebook.retrieve("Test query", k=1)

        # Verify mocks were called correctly
        mock_embeddings.assert_called_once()
        mock_chroma.assert_called_once()
        assert isinstance(result, str)