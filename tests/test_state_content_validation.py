#!/usr/bin/env python3
"""
State content validation tests.
Tests that ensure state files contain valid and expected data structures.
"""
import pytest
from pytest_mock import MockerFixture
import json
import tempfile
import os
import sys
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from Write import save_state, load_state


class TestStateDataStructureValidation:
    """Test validation of state data structures."""

    def test_minimal_valid_state_structure(self):
        """Test that minimal valid state structure is preserved."""
        minimal_state = {
            "last_completed_step": "init",
            "status": "in_progress"
        }
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            save_state(minimal_state, temp_path)
            loaded_state = load_state(temp_path)
            
            assert loaded_state == minimal_state
            assert "last_completed_step" in loaded_state
            assert "status" in loaded_state
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_complete_state_structure_outline_stage(self):
        """Test complete state structure after outline stage."""
        outline_state = {
            "last_completed_step": "outline",
            "status": "in_progress",
            "log_directory": "Logs/Generation_2025-08-02_12-00-00",
            "state_filepath": "/path/to/run.state.json",
            "full_outline": "# Story Outline\n\nThis is a comprehensive story outline...",
            "story_elements": "Characters: John, Mary\nSetting: Modern city\nTheme: Redemption",
            "rough_chapter_outline": "Chapter 1: Introduction\nChapter 2: Conflict",
            "base_context": "Important background context for the story",
            "config": {
                "SEED": 42,
                "NATIVE_LANGUAGE": "en",
                "OUTLINE_QUALITY": 85,
                "EXPAND_OUTLINE": True
            }
        }
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            save_state(outline_state, temp_path)
            loaded_state = load_state(temp_path)
            
            # Verify all required fields are preserved
            assert loaded_state["last_completed_step"] == "outline"
            assert loaded_state["full_outline"] == outline_state["full_outline"]
            assert loaded_state["story_elements"] == outline_state["story_elements"]
            assert loaded_state["config"]["SEED"] == 42
            assert loaded_state["config"]["NATIVE_LANGUAGE"] == "en"
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_complete_state_structure_chapter_generation(self):
        """Test complete state structure during chapter generation."""
        chapter_state = {
            "last_completed_step": "chapter_generation",
            "status": "in_progress",
            "total_chapters": 5,
            "completed_chapters": [
                {
                    "number": 1,
                    "title": "The Beginning",
                    "text": "Chapter 1 content goes here...",
                    "word_count": 1500,
                    "generation_time": 45.6
                },
                {
                    "number": 2,
                    "title": "The Conflict",
                    "text": "Chapter 2 content goes here...",
                    "word_count": 1800,
                    "generation_time": 52.1
                }
            ],
            "next_chapter_index": 3,
            "expanded_chapter_outlines": [
                "Detailed outline for chapter 1",
                "Detailed outline for chapter 2",
                "Detailed outline for chapter 3",
                "Detailed outline for chapter 4",
                "Detailed outline for chapter 5"
            ],
            "full_outline": "Complete story outline",
            "base_context": "Story context",
            "config": {
                "CHAPTER_MAX_REVISIONS": 3,
                "CHAPTER_QUALITY": 85,
                "SCENE_GENERATION_PIPELINE": True
            }
        }
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            save_state(chapter_state, temp_path)
            loaded_state = load_state(temp_path)
            
            # Verify chapter data structure
            assert loaded_state["total_chapters"] == 5
            assert len(loaded_state["completed_chapters"]) == 2
            assert loaded_state["completed_chapters"][0]["number"] == 1
            assert loaded_state["completed_chapters"][0]["title"] == "The Beginning"
            assert loaded_state["completed_chapters"][1]["word_count"] == 1800
            assert loaded_state["next_chapter_index"] == 3
            
            # Verify outline data
            assert len(loaded_state["expanded_chapter_outlines"]) == 5
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_state_with_complex_nested_data(self):
        """Test state with deeply nested data structures."""
        complex_state = {
            "last_completed_step": "post_processing_complete",
            "generation_metadata": {
                "start_time": "2025-08-02T12:00:00Z",
                "end_time": "2025-08-02T15:30:00Z",
                "total_duration": 12600,
                "stages": {
                    "outline": {"duration": 300, "retries": 1},
                    "chapter_generation": {"duration": 10800, "retries": 0},
                    "post_processing": {"duration": 1500, "retries": 0}
                }
            },
            "model_usage": {
                "outline_model": {
                    "name": "ollama://gemma3:27b@10.23.82.116",
                    "total_tokens": 15000,
                    "total_cost": 0.0,
                    "calls": 5
                },
                "chapter_model": {
                    "name": "ollama://gemma3:27b@10.23.82.116", 
                    "total_tokens": 150000,
                    "total_cost": 0.0,
                    "calls": 25
                }
            },
            "quality_metrics": {
                "outline_quality": 87,
                "average_chapter_quality": 85.5,
                "final_word_count": 25000,
                "readability_score": 82.3
            }
        }
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            save_state(complex_state, temp_path)
            loaded_state = load_state(temp_path)
            
            # Verify nested structure preservation
            assert loaded_state["generation_metadata"]["total_duration"] == 12600
            assert loaded_state["generation_metadata"]["stages"]["outline"]["retries"] == 1
            assert loaded_state["model_usage"]["outline_model"]["total_tokens"] == 15000
            assert loaded_state["quality_metrics"]["final_word_count"] == 25000
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestStateDataTypeValidation:
    """Test validation of data types in state."""

    def test_state_preserves_all_json_types(self):
        """Test that all JSON-compatible data types are preserved."""
        typed_state = {
            "string_field": "test string",
            "integer_field": 42,
            "float_field": 3.14159,
            "boolean_true": True,
            "boolean_false": False,
            "null_field": None,
            "empty_string": "",
            "zero_integer": 0,
            "zero_float": 0.0,
            "list_field": [1, "two", 3.0, True, None],
            "nested_dict": {
                "inner_string": "nested",
                "inner_list": [{"deep": "value"}]
            }
        }
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            save_state(typed_state, temp_path)
            loaded_state = load_state(temp_path)
            
            # Verify all types are preserved
            assert isinstance(loaded_state["string_field"], str)
            assert isinstance(loaded_state["integer_field"], int)
            assert isinstance(loaded_state["float_field"], float)
            assert isinstance(loaded_state["boolean_true"], bool)
            assert isinstance(loaded_state["boolean_false"], bool)
            assert loaded_state["null_field"] is None
            assert isinstance(loaded_state["list_field"], list)
            assert isinstance(loaded_state["nested_dict"], dict)
            
            # Verify values are exact
            assert loaded_state["string_field"] == "test string"
            assert loaded_state["integer_field"] == 42
            assert loaded_state["float_field"] == 3.14159
            assert loaded_state["boolean_true"] is True
            assert loaded_state["boolean_false"] is False
            assert loaded_state["list_field"][3] is True
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_state_unicode_handling(self):
        """Test that Unicode characters are properly handled."""
        unicode_state = {
            "english": "Hello World",
            "chinese": "你好世界",
            "japanese": "こんにちは世界",
            "arabic": "مرحبا بالعالم",
            "emoji": "🌍🚀✨🎭",
            "mixed": "Hello 世界 🌍",
            "special_chars": "àáâãäåæçèéêëìíîïñòóôõöùúûüý",
            "quotes": 'String with "quotes" and \'apostrophes\'',
            "newlines": "Line 1\nLine 2\nLine 3"
        }
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            save_state(unicode_state, temp_path)
            loaded_state = load_state(temp_path)
            
            # Verify all Unicode is preserved exactly
            for key, value in unicode_state.items():
                assert loaded_state[key] == value
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestStateRequiredFields:
    """Test validation of required fields in state."""

    def test_valid_checkpoint_steps(self):
        """Test that all valid checkpoint steps are accepted."""
        valid_steps = [
            "init",
            "outline", 
            "detect_chapters",
            "refine_global_outline",
            "expand_chapters",
            "chapter_generation",
            "chapter_generation_complete",
            "post_processing_started",
            "post_processing_edit_complete",
            "post_processing_scrub_complete",
            "post_processing_final_translate_complete",
            "complete"
        ]
        
        for step in valid_steps:
            state = {"last_completed_step": step}
            
            with tempfile.NamedTemporaryFile(delete=False) as f:
                temp_path = f.name
            
            try:
                save_state(state, temp_path)
                loaded_state = load_state(temp_path)
                
                assert loaded_state["last_completed_step"] == step
                
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_state_with_required_chapter_fields(self):
        """Test state with all required fields for chapter generation."""
        chapter_required_state = {
            "last_completed_step": "chapter_generation",
            "total_chapters": 5,
            "full_outline": "Story outline content",
            "base_context": "Story context",
            "completed_chapters": [],
            "next_chapter_index": 1
        }
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            save_state(chapter_required_state, temp_path)
            loaded_state = load_state(temp_path)
            
            # Verify all required fields are present
            required_fields = [
                "last_completed_step", "total_chapters", "full_outline", 
                "base_context", "completed_chapters", "next_chapter_index"
            ]
            
            for field in required_fields:
                assert field in loaded_state
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestStateConsistencyValidation:
    """Test consistency between different state fields."""

    def test_chapter_count_consistency(self):
        """Test consistency between total_chapters and completed_chapters."""
        consistent_state = {
            "last_completed_step": "chapter_generation",
            "total_chapters": 5,
            "completed_chapters": [
                {"number": 1, "title": "Ch1", "text": "Content1"},
                {"number": 2, "title": "Ch2", "text": "Content2"},
                {"number": 3, "title": "Ch3", "text": "Content3"}
            ],
            "next_chapter_index": 4
        }
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            save_state(consistent_state, temp_path)
            loaded_state = load_state(temp_path)
            
            # Verify consistency rules
            assert loaded_state["total_chapters"] == 5
            assert len(loaded_state["completed_chapters"]) == 3
            assert loaded_state["next_chapter_index"] == 4
            
            # Verify next_chapter_index is reasonable
            assert loaded_state["next_chapter_index"] <= loaded_state["total_chapters"]
            assert loaded_state["next_chapter_index"] > len(loaded_state["completed_chapters"])
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_config_preservation_validation(self):
        """Test that configuration data is properly preserved."""
        config_state = {
            "last_completed_step": "outline",
            "config": {
                "SEED": 42,
                "NATIVE_LANGUAGE": "en",
                "OUTLINE_QUALITY": 85,
                "CHAPTER_QUALITY": 85,
                "EXPAND_OUTLINE": True,
                "SCENE_GENERATION_PIPELINE": False,
                "TRANSLATE_LANGUAGE": "",
                "models": {
                    "outline": "ollama://gemma3:27b@10.23.82.116",
                    "chapter": "ollama://gemma3:27b@10.23.82.116"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            save_state(config_state, temp_path)
            loaded_state = load_state(temp_path)
            
            # Verify config structure is preserved
            assert "config" in loaded_state
            config = loaded_state["config"]
            
            assert config["SEED"] == 42
            assert config["NATIVE_LANGUAGE"] == "en"
            assert config["EXPAND_OUTLINE"] is True
            assert config["SCENE_GENERATION_PIPELINE"] is False
            assert config["TRANSLATE_LANGUAGE"] == ""
            assert "models" in config
            assert "outline" in config["models"]
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestStateSizeAndPerformance:
    """Test state file size and performance characteristics."""

    def test_large_state_file_handling(self):
        """Test handling of large state files."""
        # Create a state with large text content
        large_text = "Lorem ipsum dolor sit amet. " * 10000  # ~280KB
        large_chapters = []
        
        for i in range(50):  # 50 chapters
            large_chapters.append({
                "number": i + 1,
                "title": f"Chapter {i + 1}",
                "text": large_text,
                "word_count": len(large_text.split())
            })
        
        large_state = {
            "last_completed_step": "chapter_generation_complete",
            "total_chapters": 50,
            "completed_chapters": large_chapters,
            "full_outline": large_text * 2,  # Even larger outline
            "base_context": large_text
        }
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            # Test that large state can be saved and loaded
            save_state(large_state, temp_path)
            
            # Verify file exists and has reasonable size
            assert os.path.exists(temp_path)
            file_size = os.path.getsize(temp_path)
            assert file_size > 1024 * 1024  # Should be > 1MB
            
            # Test loading large state
            loaded_state = load_state(temp_path)
            
            # Verify data integrity
            assert loaded_state["total_chapters"] == 50
            assert len(loaded_state["completed_chapters"]) == 50
            assert loaded_state["completed_chapters"][0]["text"] == large_text
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_state_file_json_formatting(self):
        """Test that state files are properly formatted JSON."""
        formatted_state = {
            "last_completed_step": "complete",
            "nested": {
                "level1": {
                    "level2": ["item1", "item2", "item3"]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            save_state(formatted_state, temp_path)
            
            # Read file as text to verify formatting
            with open(temp_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Verify it's valid JSON
            parsed = json.loads(file_content)
            assert parsed == formatted_state
            
            # Verify it's formatted (has indentation)
            assert "    " in file_content  # Should have 4-space indentation
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)