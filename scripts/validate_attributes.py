#!/usr/bin/env python3
"""
Comprehensive attribute validation script.
Ensures all attributes used in the codebase actually exist in their respective modules.
"""
import subprocess
import re
import sys
import os

def find_attribute_usage(pattern, description):
    """Find all attribute usage matching a pattern."""
    print(f"\n🔍 {description}")
    print("=" * 60)
    
    try:
        # Use grep to find all occurrences
        result = subprocess.run(
            ['grep', '-r', pattern, 'Writer/'],
            capture_output=True, text=True, cwd='/var/www/AIStoryWriter'
        )
        
        if result.returncode == 0:
            # Extract attribute names using regex
            if 'Config\\.' in pattern:
                attr_pattern = r'Config\.([A-Z_][A-Z_0-9]*)'
            elif 'ActivePrompts\\.' in pattern:
                attr_pattern = r'ActivePrompts\.([A-Z_][A-Z_0-9]*)'
            else:
                return set()
            
            attributes = set(re.findall(attr_pattern, result.stdout))
            print(f"Found {len(attributes)} unique attributes:")
            for attr in sorted(attributes):
                print(f"  - {attr}")
            return attributes
        else:
            print("No matches found")
            return set()
            
    except Exception as e:
        print(f"Error: {e}")
        return set()

def validate_attributes(module_name, attributes, description):
    """Validate that all attributes exist in the given module."""
    print(f"\n✅ Validating {description}")
    print("=" * 60)
    
    try:
        # Import the module
        module = __import__(module_name, fromlist=[''])
        
        missing = []
        present = []
        
        for attr in sorted(attributes):
            if hasattr(module, attr):
                present.append(attr)
            else:
                missing.append(attr)
        
        print(f"Present: {len(present)}")
        for attr in present:
            print(f"  ✅ {attr}")
        
        if missing:
            print(f"\nMissing: {len(missing)}")
            for attr in missing:
                print(f"  ❌ {attr}")
            return False
        else:
            print(f"\n🎉 All {len(present)} attributes are present!")
            return True
            
    except Exception as e:
        print(f"Error importing {module_name}: {e}")
        return False

def main():
    print("🚀 Comprehensive Attribute Validation")
    print("=" * 60)
    
    all_passed = True
    
    # 1. Validate Config attributes
    config_attrs = find_attribute_usage('Config\\.', "Config Attributes Usage")
    if config_attrs:
        passed = validate_attributes('Writer.Config', config_attrs, "Writer.Config attributes")
        all_passed = all_passed and passed
    
    # 2. Validate ActivePrompts attributes (English)
    prompts_attrs = find_attribute_usage('ActivePrompts\\.', "ActivePrompts Attributes Usage")
    if prompts_attrs:
        passed = validate_attributes('Writer.Prompts', prompts_attrs, "Writer.Prompts (English) attributes")
        all_passed = all_passed and passed
        
        passed = validate_attributes('Writer.Prompts_id', prompts_attrs, "Writer.Prompts_id (Indonesian) attributes")
        all_passed = all_passed and passed
    
    # 3. Test dynamic loading compatibility
    print(f"\n🔍 Testing Multi-Language Compatibility")
    print("=" * 60)
    
    try:
        # Test Indonesian loading
        import Writer.Config
        original_lang = Writer.Config.NATIVE_LANGUAGE
        Writer.Config.NATIVE_LANGUAGE = 'id'
        
        import Write
        def mock_log(x): pass
        
        id_prompts = Write.load_active_prompts('id', mock_log, mock_log, mock_log)
        print(f"✅ Indonesian prompts loaded: {id_prompts.__name__}")
        
        # Test critical modules import with Indonesian prompts
        import Writer.Chapter.ChapterDetector
        import Writer.Pipeline
        print("✅ Critical modules import successfully with Indonesian prompts")
        
        # Restore original language
        Writer.Config.NATIVE_LANGUAGE = original_lang
        
    except Exception as e:
        print(f"❌ Multi-language compatibility test failed: {e}")
        all_passed = False
    
    # Final result
    print(f"\n📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("✅ No missing Config attributes")
        print("✅ No missing Prompts attributes")
        print("✅ Multi-language compatibility works")
        return 0
    else:
        print("💥 SOME VALIDATIONS FAILED!")
        print("❌ There are missing attributes that need to be added")
        return 1

if __name__ == "__main__":
    sys.exit(main())