#!/usr/bin/env python3
"""
COMPREHENSIVE ERROR DETECTION SCRIPT
Deteksi SEMUA kemungkinan error yang bisa terjadi di runtime.
"""
import sys
import os
import re
import importlib
import subprocess
from typing import List, Dict, Set, Tuple
import traceback

# Add project root to path
sys.path.insert(0, '/var/www/AIStoryWriter')

class ComprehensiveErrorChecker:
    def __init__(self):
        self.errors_found = []
        self.warnings_found = []
        
    def log_error(self, category: str, message: str, severity: str = "ERROR"):
        error_info = {
            'category': category,
            'message': message,
            'severity': severity
        }
        if severity == "ERROR":
            self.errors_found.append(error_info)
        else:
            self.warnings_found.append(error_info)
        
        print(f"🚨 {severity} [{category}]: {message}")
    
    def check_template_format_strings(self):
        """Check all format strings in prompts for missing parameters."""
        print("\n🔍 CHECKING: Template format strings compatibility...")
        
        # Get all ActivePrompts usage from codebase
        result = subprocess.run(
            ['grep', '-r', '-n', 'ActivePrompts\\..*\\.format(', 'Writer/'],
            capture_output=True, text=True, cwd='/var/www/AIStoryWriter'
        )
        
        if result.returncode != 0:
            self.log_error("TEMPLATE_CHECK", "Could not scan ActivePrompts usage", "WARNING")
            return
            
        # Parse each usage
        for line in result.stdout.split('\n'):
            if not line.strip():
                continue
                
            try:
                # Extract file, line, and format call
                parts = line.split(':', 2)
                if len(parts) < 3:
                    continue
                    
                file_path = parts[0]
                line_num = parts[1]
                code_line = parts[2]
                
                # Extract prompt name and parameters
                prompt_match = re.search(r'ActivePrompts\.([A-Z_][A-Z_0-9]*)', code_line)
                if not prompt_match:
                    continue
                    
                prompt_name = prompt_match.group(1)
                
                # Get parameters used in format call
                format_match = re.search(r'\.format\((.*)\)', code_line)
                if not format_match:
                    continue
                    
                format_args = format_match.group(1)
                
                # Extract parameter names (basic parsing)
                param_pattern = r'(\w+)='
                used_params = set(re.findall(param_pattern, format_args))
                
                # Test this template with both English and Indonesian prompts
                for lang, lang_name in [("en", "English"), ("id", "Indonesian")]:
                    try:
                        if lang == "en":
                            import Writer.Prompts as prompts_module
                        else:
                            import Writer.Prompts_id as prompts_module
                        
                        if hasattr(prompts_module, prompt_name):
                            template = getattr(prompts_module, prompt_name)
                            
                            # Find all template parameters
                            template_params = set(re.findall(r'\{(\w+)\}', template))
                            
                            # Check for missing parameters
                            missing_params = template_params - used_params
                            if missing_params:
                                self.log_error(
                                    "TEMPLATE_MISMATCH",
                                    f"{file_path}:{line_num} - {lang_name} {prompt_name} missing parameters: {missing_params}"
                                )
                                
                            # Check for extra parameters  
                            extra_params = used_params - template_params
                            if extra_params:
                                self.log_error(
                                    "TEMPLATE_EXTRA",
                                    f"{file_path}:{line_num} - {lang_name} {prompt_name} extra parameters: {extra_params}",
                                    "WARNING"
                                )
                        else:
                            self.log_error(
                                "MISSING_PROMPT",
                                f"{lang_name} prompts missing attribute: {prompt_name}"
                            )
                            
                    except Exception as e:
                        self.log_error(
                            "TEMPLATE_CHECK_ERROR",
                            f"Error checking {lang_name} {prompt_name}: {e}"
                        )
                        
            except Exception as e:
                self.log_error("TEMPLATE_PARSE_ERROR", f"Error parsing line: {line} - {e}")
    
    def check_function_signatures(self):
        """Check all function calls match their signatures."""
        print("\n🔍 CHECKING: Function signature mismatches...")
        
        # Key functions to check
        functions_to_check = [
            ('Writer.Chapter.ChapterDetector', 'LLMCountChapters'),
            ('Writer.OutlineGenerator', 'ReviseOutline'),
            ('Writer.OutlineGenerator', 'GeneratePerChapterOutline'),
            ('Writer.NovelEditor', 'EditNovel'),
            ('Writer.Scrubber', 'ScrubChapter'),
            ('Writer.Translator', 'TranslateChapter'),
            ('Writer.StoryInfo', 'GenerateStoryInfo'),
            ('Writer.Interface.Wrapper', 'SafeGenerateText'),
            ('Writer.Interface.Wrapper', 'SafeGenerateJSON'),
        ]
        
        for module_name, function_name in functions_to_check:
            try:
                # Import the module
                module = importlib.import_module(module_name)
                if hasattr(module, function_name):
                    func = getattr(module, function_name)
                    
                    # Get function signature
                    import inspect
                    sig = inspect.signature(func)
                    expected_params = list(sig.parameters.keys())
                    
                    # Search for calls to this function
                    search_pattern = f"{function_name}\\("
                    result = subprocess.run(
                        ['grep', '-r', '-n', search_pattern, 'Writer/'],
                        capture_output=True, text=True, cwd='/var/www/AIStoryWriter'
                    )
                    
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if not line.strip() or 'def ' in line:
                                continue
                                
                            # Basic check - count parameters (simplified)
                            paren_content = re.search(r'{}\\(([^)]+)\\)'.format(function_name), line)
                            if paren_content:
                                args = [arg.strip() for arg in paren_content.group(1).split(',')]
                                args = [arg for arg in args if arg]  # Remove empty
                                
                                if len(args) != len(expected_params):
                                    parts = line.split(':', 2)
                                    if len(parts) >= 2:
                                        self.log_error(
                                            "SIGNATURE_MISMATCH",
                                            f"{parts[0]}:{parts[1]} - {function_name} called with {len(args)} args, expects {len(expected_params)}"
                                        )
                                        
            except Exception as e:
                self.log_error("SIGNATURE_CHECK_ERROR", f"Error checking {module_name}.{function_name}: {e}")
    
    def check_interface_method_calls(self):
        """Check Interface method calls for correct parameters."""
        print("\n🔍 CHECKING: Interface method parameter usage...")
        
        # Check SafeGenerateText calls
        result = subprocess.run(
            ['grep', '-r', '-n', 'SafeGenerateText(', 'Writer/'],
            capture_output=True, text=True, cwd='/var/www/AIStoryWriter'
        )
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if not line.strip():
                    continue
                    
                # Check for incorrect parameter names
                if '_MaxRetries=' in line:
                    parts = line.split(':', 2)
                    if len(parts) >= 2:
                        self.log_error(
                            "INTERFACE_PARAM_ERROR",
                            f"{parts[0]}:{parts[1]} - SafeGenerateText uses incorrect parameter '_MaxRetries', should be '_max_retries_override'"
                        )
                        
                if '_PurposeForLog=' in line:
                    parts = line.split(':', 2)
                    if len(parts) >= 2:
                        self.log_error(
                            "INTERFACE_PARAM_ERROR", 
                            f"{parts[0]}:{parts[1]} - SafeGenerateText uses unsupported parameter '_PurposeForLog'"
                        )
    
    def check_import_integrity(self):
        """Check all imports work correctly."""
        print("\n🔍 CHECKING: Import integrity...")
        
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
        
        for module_name in critical_modules:
            try:
                module = importlib.import_module(module_name)
                print(f"✅ {module_name}: OK")
            except Exception as e:
                self.log_error("IMPORT_ERROR", f"Cannot import {module_name}: {e}")
    
    def check_config_attributes(self):
        """Check all Config attributes are accessible."""
        print("\n🔍 CHECKING: Config attributes...")
        
        # Get all Config usage
        result = subprocess.run(
            ['grep', '-r', '-n', 'Config\\.', 'Writer/'],
            capture_output=True, text=True, cwd='/var/www/AIStoryWriter'
        )
        
        if result.returncode == 0:
            try:
                import Writer.Config as Config
                
                config_attrs = set(re.findall(r'Config\\.([A-Z_][A-Z_0-9]*)', result.stdout))
                
                for attr in config_attrs:
                    if not hasattr(Config, attr):
                        self.log_error("MISSING_CONFIG", f"Config.{attr} does not exist")
                        
            except Exception as e:
                self.log_error("CONFIG_CHECK_ERROR", f"Error checking Config attributes: {e}")
    
    def check_prompt_attributes(self):
        """Check all Prompt attributes exist in both languages."""
        print("\n🔍 CHECKING: Prompt attributes parity...")
        
        try:
            import Writer.Prompts as en_prompts
            import Writer.Prompts_id as id_prompts
            
            # Get all prompt usage
            result = subprocess.run(
                ['grep', '-r', '-n', 'ActivePrompts\\.', 'Writer/'],
                capture_output=True, text=True, cwd='/var/www/AIStoryWriter'
            )
            
            if result.returncode == 0:
                prompt_attrs = set(re.findall(r'ActivePrompts\\.([A-Z_][A-Z_0-9]*)', result.stdout))
                
                for attr in prompt_attrs:
                    if not hasattr(en_prompts, attr):
                        self.log_error("MISSING_EN_PROMPT", f"English prompts missing: {attr}")
                    if not hasattr(id_prompts, attr):
                        self.log_error("MISSING_ID_PROMPT", f"Indonesian prompts missing: {attr}")
                        
        except Exception as e:
            self.log_error("PROMPT_CHECK_ERROR", f"Error checking prompt attributes: {e}")
    
    def check_dynamic_loading(self):
        """Test dynamic prompt loading."""
        print("\n🔍 CHECKING: Dynamic prompt loading...")
        
        try:
            # Test Write.py dynamic loading
            import Write
            
            def mock_logger(msg): pass
            
            # Test English loading
            en_prompts = Write.load_active_prompts("en", mock_logger, mock_logger, mock_logger)
            if en_prompts is None:
                self.log_error("DYNAMIC_LOAD", "Failed to load English prompts")
            elif en_prompts.__name__ != "Writer.Prompts":
                self.log_error("DYNAMIC_LOAD", f"English prompts loaded wrong module: {en_prompts.__name__}")
                
            # Test Indonesian loading
            id_prompts = Write.load_active_prompts("id", mock_logger, mock_logger, mock_logger)
            if id_prompts is None:
                self.log_error("DYNAMIC_LOAD", "Failed to load Indonesian prompts")
            elif id_prompts.__name__ != "Writer.Prompts_id":
                self.log_error("DYNAMIC_LOAD", f"Indonesian prompts loaded wrong module: {id_prompts.__name__}")
                
        except Exception as e:
            self.log_error("DYNAMIC_LOAD_ERROR", f"Error testing dynamic loading: {e}")
    
    def run_comprehensive_check(self):
        """Run all checks."""
        print("🚀 STARTING COMPREHENSIVE ERROR CHECK")
        print("=" * 60)
        
        self.check_import_integrity()
        self.check_config_attributes() 
        self.check_prompt_attributes()
        self.check_template_format_strings()
        self.check_function_signatures()
        self.check_interface_method_calls()
        self.check_dynamic_loading()
        
        print("\n" + "=" * 60)
        print("📊 FINAL REPORT")
        print("=" * 60)
        
        if self.errors_found:
            print(f"🚨 CRITICAL ERRORS FOUND: {len(self.errors_found)}")
            for error in self.errors_found:
                print(f"   ❌ [{error['category']}] {error['message']}")
        else:
            print("✅ NO CRITICAL ERRORS FOUND!")
            
        if self.warnings_found:
            print(f"\n⚠️  WARNINGS: {len(self.warnings_found)}")
            for warning in self.warnings_found:
                print(f"   ⚠️  [{warning['category']}] {warning['message']}")
        else:
            print("✅ NO WARNINGS!")
            
        return len(self.errors_found) == 0

if __name__ == "__main__":
    checker = ComprehensiveErrorChecker()
    success = checker.run_comprehensive_check()
    sys.exit(0 if success else 1)