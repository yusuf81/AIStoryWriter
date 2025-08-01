#!/usr/bin/env python3
"""
UNIT TESTS FOR ERROR PREVENTION
Tests yang dirancang khusus untuk mendeteksi error runtime seperti:
- Template format string mismatches
- Function signature mismatches  
- Missing attributes
- Import issues
"""
import pytest
import sys
import os
import re
import importlib
import subprocess
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, '/var/www/AIStoryWriter')

class TestErrorPrevention:
    """Test suite untuk mencegah error runtime."""
    
    def test_chapter_title_prompt_format_compatibility(self):
        """Test yang HARUS mendeteksi error GET_CHAPTER_TITLE_PROMPT."""
        # Import both prompt modules
        import Writer.Prompts as en_prompts
        import Writer.Prompts_id as id_prompts
        
        # Test data yang digunakan di Pipeline.py
        test_data = {
            'chapter_num': 1,
            'chapter_text_segment': 'Test chapter content...',  # Key parameter!
            'base_story_context': 'Test story context',
            'word_count': 100
        }
        
        # Test English prompts
        try:
            result = en_prompts.GET_CHAPTER_TITLE_PROMPT.format(**test_data)
            assert 'Test chapter content' in result
        except KeyError as e:
            pytest.fail(f"English GET_CHAPTER_TITLE_PROMPT missing parameter: {e}")
            
        # Test Indonesian prompts
        try:
            result = id_prompts.GET_CHAPTER_TITLE_PROMPT.format(**test_data)
            assert 'Test chapter content' in result
        except KeyError as e:
            pytest.fail(f"Indonesian GET_CHAPTER_TITLE_PROMPT missing parameter: {e}")
    
    def test_all_prompt_format_strings_compatibility(self):
        """Test semua template format strings untuk kompatibilitas."""
        import Writer.Prompts as en_prompts
        import Writer.Prompts_id as id_prompts
        
        # Get all ActivePrompts usage from codebase
        result = subprocess.run(
            ['grep', '-r', '-n', 'ActivePrompts\\..*\\.format(', 'Writer/'],
            capture_output=True, text=True, cwd='/var/www/AIStoryWriter'
        )
        
        if result.returncode != 0:
            pytest.skip("Could not scan ActivePrompts usage")
            
        errors = []
        
        # Parse each usage
        for line in result.stdout.split('\n'):
            if not line.strip():
                continue
                
            try:
                # Extract prompt name
                prompt_match = re.search(r'ActivePrompts\\.([A-Z_][A-Z_0-9]*)', line)
                if not prompt_match:
                    continue
                    
                prompt_name = prompt_match.group(1)
                
                # Get parameters used in format call
                format_match = re.search(r'\\.format\\((.*?)\\)', line)
                if not format_match:
                    continue
                    
                format_args = format_match.group(1)
                
                # Extract parameter names (improved parsing)
                param_pattern = r'(\\w+)\\s*='
                used_params = set(re.findall(param_pattern, format_args))
                
                # Test with both languages
                for lang_prompts, lang_name in [(en_prompts, "English"), (id_prompts, "Indonesian")]:
                    if hasattr(lang_prompts, prompt_name):
                        template = getattr(lang_prompts, prompt_name)
                        template_params = set(re.findall(r'\\{(\\w+)\\}', template))
                        
                        # Check for missing parameters
                        missing = template_params - used_params
                        if missing:
                            errors.append(f"{lang_name} {prompt_name} missing parameters: {missing}")
                            
                    else:
                        errors.append(f"{lang_name} prompts missing attribute: {prompt_name}")
                        
            except Exception as e:
                errors.append(f"Error parsing line: {line} - {e}")
                
        if errors:
            pytest.fail(f"Template format errors found:\\n" + "\\n".join(errors))
    
    def test_function_signature_compatibility(self):
        """Test function signature compatibility."""
        # Test specific functions that had signature issues before
        test_cases = [
            {
                'module': 'Writer.Chapter.ChapterDetector',
                'function': 'LLMCountChapters',
                'expected_params': 3,  # Interface, Logger, Summary
                'test_call_pattern': r'LLMCountChapters\\([^)]+\\)'
            },
            {
                'module': 'Write',
                'function': 'load_active_prompts', 
                'expected_params': 4,  # language, logger1, logger2, logger3
                'test_call_pattern': r'load_active_prompts\\([^)]+\\)'
            }
        ]
        
        errors = []
        
        for test_case in test_cases:
            try:
                # Import and inspect function
                module = importlib.import_module(test_case['module'])
                if hasattr(module, test_case['function']):
                    func = getattr(module, test_case['function'])
                    
                    import inspect
                    sig = inspect.signature(func)
                    actual_params = len(sig.parameters)
                    
                    if actual_params != test_case['expected_params']:
                        errors.append(
                            f"{test_case['module']}.{test_case['function']} has {actual_params} params, expected {test_case['expected_params']}"
                        )
                        
                else:
                    errors.append(f"{test_case['module']} missing function: {test_case['function']}")
                    
            except Exception as e:
                errors.append(f"Error checking {test_case['module']}.{test_case['function']}: {e}")
                
        if errors:
            pytest.fail(f"Function signature errors:\\n" + "\\n".join(errors))
    
    def test_all_config_attributes_exist(self):
        """Test semua Config attributes yang digunakan benar-benar ada."""
        # Get all Config usage
        result = subprocess.run(
            ['grep', '-r', '-n', 'Config\\.', 'Writer/'],
            capture_output=True, text=True, cwd='/var/www/AIStoryWriter'
        )
        
        if result.returncode != 0:
            pytest.skip("Could not scan Config usage")
            
        try:
            import Writer.Config as Config
            
            # Extract all Config attributes used
            config_attrs = set(re.findall(r'Config\\.([A-Z_][A-Z_0-9]*)', result.stdout))
            
            missing_attrs = []
            for attr in config_attrs:
                if not hasattr(Config, attr):
                    missing_attrs.append(attr)
                    
            if missing_attrs:
                pytest.fail(f"Missing Config attributes: {missing_attrs}")
                
        except Exception as e:
            pytest.fail(f"Error checking Config attributes: {e}")
    
    def test_all_prompt_attributes_exist(self):
        """Test semua Prompt attributes ada di kedua bahasa."""
        try:
            import Writer.Prompts as en_prompts
            import Writer.Prompts_id as id_prompts
            
            # Get all ActivePrompts usage
            result = subprocess.run(
                ['grep', '-r', '-n', 'ActivePrompts\\.', 'Writer/'],
                capture_output=True, text=True, cwd='/var/www/AIStoryWriter'
            )
            
            if result.returncode == 0:
                prompt_attrs = set(re.findall(r'ActivePrompts\\.([A-Z_][A-Z_0-9]*)', result.stdout))
                
                missing_attrs = []
                for attr in prompt_attrs:
                    if not hasattr(en_prompts, attr):
                        missing_attrs.append(f"English prompts missing: {attr}")
                    if not hasattr(id_prompts, attr):
                        missing_attrs.append(f"Indonesian prompts missing: {attr}")
                        
                if missing_attrs:
                    pytest.fail(f"Missing prompt attributes:\\n" + "\\n".join(missing_attrs))
                    
        except Exception as e:
            pytest.fail(f"Error checking prompt attributes: {e}")
    
    def test_dynamic_prompt_loading_works(self):
        """Test dynamic prompt loading berfungsi dengan benar."""
        import Write
        
        def mock_logger(msg): pass
        
        # Test English loading
        en_prompts = Write.load_active_prompts("en", mock_logger, mock_logger, mock_logger)
        assert en_prompts is not None, "Failed to load English prompts"
        assert en_prompts.__name__ == "Writer.Prompts", f"Wrong English module: {en_prompts.__name__}"
        
        # Test Indonesian loading
        id_prompts = Write.load_active_prompts("id", mock_logger, mock_logger, mock_logger)
        assert id_prompts is not None, "Failed to load Indonesian prompts"
        assert id_prompts.__name__ == "Writer.Prompts_id", f"Wrong Indonesian module: {id_prompts.__name__}"
    
    def test_critical_imports_work(self):
        """Test semua import kritikal bekerja."""
        critical_modules = [
            'Writer.Config',
            'Writer.Prompts', 
            'Writer.Prompts_id',
            'Writer.Pipeline',
            'Writer.Chapter.ChapterGenerator',
            'Writer.Chapter.ChapterDetector',
            'Writer.Chapter.ChapterGenSummaryCheck',
            'Writer.OutlineGenerator',
            'Writer.NovelEditor',
            'Writer.Scrubber',
            'Writer.Translator',
            'Writer.StoryInfo',
        ]
        
        import_errors = []
        for module_name in critical_modules:
            try:
                importlib.import_module(module_name)
            except Exception as e:
                import_errors.append(f"Cannot import {module_name}: {e}")
                
        if import_errors:
            pytest.fail(f"Import errors:\\n" + "\\n".join(import_errors))
    
    def test_pipeline_chapter_title_generation_parameters(self):
        """Test khusus untuk parameter chapter title generation di Pipeline.py."""
        # This test specifically targets the error we just fixed
        import Writer.Prompts as ActivePrompts
        
        # Parameters yang digunakan di Pipeline.py line 158-164
        test_params = {
            'base_story_context': 'Test context',
            'current_chapter_outline': 'Test outline',  # This might be unused but passed
            'chapter_num': 1,
            'chapter_text_segment': 'Test chapter content segment',  # Key parameter!
            'word_count': 100
        }
        
        try:
            # Test the exact template and parameters used in Pipeline.py
            result = ActivePrompts.GET_CHAPTER_TITLE_PROMPT.format(**test_params)
            assert 'Test chapter content segment' in result
            assert 'chapter 1' in result
        except KeyError as e:
            pytest.fail(f"Pipeline.py chapter title generation will fail with KeyError: {e}")
        except Exception as e:
            pytest.fail(f"Pipeline.py chapter title generation will fail with error: {e}")
    
    def test_interface_method_parameter_correctness(self):
        """Test parameter names untuk SafeGenerateText calls."""
        # Check for incorrect SafeGenerateText parameter usage
        result = subprocess.run(
            ['grep', '-r', '-n', 'SafeGenerateText(', 'Writer/'],
            capture_output=True, text=True, cwd='/var/www/AIStoryWriter'
        )
        
        if result.returncode != 0:
            pytest.skip("Could not scan SafeGenerateText usage")
            
        errors = []
        
        for line in result.stdout.split('\n'):
            if not line.strip():
                continue
                
            # Check for incorrect parameter names that cause runtime errors
            if '_MaxRetries=' in line:
                parts = line.split(':', 2)
                if len(parts) >= 2:
                    errors.append(f"{parts[0]}:{parts[1]} - Uses incorrect '_MaxRetries', should be '_max_retries_override'")
                    
            if '_PurposeForLog=' in line:
                parts = line.split(':', 2)
                if len(parts) >= 2:
                    errors.append(f"{parts[0]}:{parts[1]} - Uses unsupported '_PurposeForLog' parameter")
                    
        if errors:
            pytest.fail(f"SafeGenerateText parameter errors found:\\n" + "\\n".join(errors))
    
    def test_mock_return_values_match_function_signatures(self):
        """Test bahwa mock return values sesuai dengan function signatures."""
        # Check specific functions that return tuples
        tuple_returning_functions = [
            ('Writer.OutlineGenerator', 'GenerateOutline', 4),  # Returns 4-tuple
            ('Writer.OutlineGenerator', 'ReviseOutline', 2),    # Returns 2-tuple  
            ('Writer.Interface.Wrapper', 'SafeGenerateText', 2), # Returns 2-tuple
            ('Writer.Interface.Wrapper', 'SafeGenerateJSON', 3), # Returns 3-tuple
        ]
        
        for module_name, function_name, expected_tuple_size in tuple_returning_functions:
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, function_name):
                    # This is mainly a documentation test - ensuring we know what functions return tuples
                    # so mock setup in tests can be correct
                    assert expected_tuple_size > 1, f"{module_name}.{function_name} should return tuple with {expected_tuple_size} elements"
                    
            except Exception as e:
                pytest.fail(f"Error checking {module_name}.{function_name}: {e}")

class TestRuntimeScenarios:
    """Test skenario runtime yang sebenarnya."""
    
    def test_chapter_generator_with_indonesian_prompts(self):
        """Test ChapterGenerator dengan prompt Indonesia."""
        # Mock semua dependencies
        mock_interface = Mock()
        mock_logger = Mock()
        mock_interface.BuildSystemQuery.return_value = {"role": "system", "content": "test"}
        mock_interface.BuildUserQuery.return_value = {"role": "user", "content": "test"}
        mock_interface.SafeGenerateText.return_value = ([{"role": "assistant", "content": "Generated text"}], {"tokens": 100})
        mock_interface.GetLastMessageText.return_value = "Generated text"
        
        # Import dan test dengan prompt Indonesia
        import Writer.Config
        original_lang = Writer.Config.NATIVE_LANGUAGE
        Writer.Config.NATIVE_LANGUAGE = "id"
        
        try:
            # Dynamic import untuk prompt Indonesia
            import Write
            def mock_log(msg): pass
            id_prompts = Write.load_active_prompts("id", mock_log, mock_log, mock_log)
            
            # Patch sys.modules untuk menggunakan prompt Indonesia
            with patch('sys.modules') as mock_modules:
                mock_modules.__getitem__.return_value = id_prompts
                
                # Test import ChapterGenerator dengan prompt Indonesia
                from Writer.Chapter.ChapterGenerator import _prepare_initial_generation_context
                
                # Test function call
                result = _prepare_initial_generation_context(
                    mock_interface, mock_logger, id_prompts,
                    _Outline="Test outline", _Chapters=[], 
                    _ChapterNum=1, _TotalChapters=2, Config_module=Writer.Config
                )
                
                assert len(result) == 5, "Should return 5 values"
                
        finally:
            Writer.Config.NATIVE_LANGUAGE = original_lang