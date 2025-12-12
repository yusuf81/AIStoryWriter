#!/usr/bin/env python3
"""
Auto Git Commit with Ollama-generated message
Usage: 
  python3 auto_commit.py           # Interactive mode (asks for confirmation)
  python3 auto_commit.py --auto    # Auto mode (no confirmation)
"""

import subprocess
import json
import urllib.request
import urllib.parse
import sys
import os
import logging

# Ollama Configuration
OLLAMA_HOST = "192.168.101.34"
OLLAMA_PORT = 11434
OLLAMA_MODEL = "qwen2.5-coder:32b"

def run_command(command, capture_output=True, allow_warnings=False):
    """Run shell command and return output"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=capture_output, 
            text=True, 
            check=False  # Don't raise exception on non-zero exit
        )
        
        # For git commands, warnings about CRLF are normal and shouldn't fail the operation
        if allow_warnings and result.returncode == 0:
            return result.stdout.strip() if capture_output else True
        elif not allow_warnings and result.returncode == 0:
            return result.stdout.strip() if capture_output else True
        elif result.returncode != 0:
            logging.error(f"Error running command: {command}")
            logging.error(f"Exit code: {result.returncode}")
            if result.stderr:
                logging.error(f"Error: {result.stderr}")
            return None
        
        return result.stdout.strip() if capture_output else True
    except Exception as e:
        logging.error(f"Exception running command: {command}")
        logging.error(f"Error: {e}")
        return None

def get_git_diff():
    """Get git diff for staged, unstaged changes, and new files"""
    print("📋 Getting git diff...")
    
    # Check if there are any changes
    status = run_command("git status --porcelain")
    if not status:
        print("❌ No changes detected. Nothing to commit.")
        return None
    
    print(f"📝 Found changes:\n{status}\n")
    
    diff_parts = []
    
    # Get diff of modified files (staged + unstaged)
    modified_diff = run_command("git diff HEAD")
    if modified_diff:
        diff_parts.append("=== MODIFIED FILES ===\n" + modified_diff)
    
    # Get diff of staged files if no HEAD diff
    if not modified_diff:
        staged_diff = run_command("git diff --cached")
        if staged_diff:
            diff_parts.append("=== STAGED FILES ===\n" + staged_diff)
    
    # Handle various file status changes
    status_lines = status.strip().split('\n')
    new_files = []
    added_files = []
    deleted_files = []
    renamed_files = []
    
    for line in status_lines:
        status_code = line[:2]
        filename = line[3:].strip()
        
        if status_code == '??':  # Untracked files
            new_files.append(filename)
        elif status_code.strip() == 'A':  # Added files
            added_files.append(filename)
        elif status_code.strip() == 'D':  # Deleted files
            deleted_files.append(filename)
        elif status_code.startswith('R'):  # Renamed files
            renamed_files.append(filename)
    
    # Get content of new files
    if new_files:
        new_files_content = []
        for filename in new_files:
            if os.path.isfile(filename):
                try:
                    # Check file size first
                    file_size = os.path.getsize(filename)
                    if file_size > 10000:  # Files larger than 10KB
                        new_files_content.append(f"--- NEW FILE: {filename} ---\n(Large file: {file_size} bytes)")
                        continue
                    
                    # Try to detect if file is binary
                    with open(filename, 'rb') as f:
                        chunk = f.read(1024)
                        if b'\x00' in chunk:  # Contains null bytes - likely binary
                            new_files_content.append(f"--- NEW FILE: {filename} ---\n(Binary file)")
                            continue
                    
                    # Read text file content (limit to reasonable size)
                    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(2000)  # Limit to 2000 chars
                        if len(content) == 2000:
                            content += "\n... (truncated)"
                    new_files_content.append(f"--- NEW FILE: {filename} ---\n{content}")
                except Exception as e:
                    new_files_content.append(f"--- NEW FILE: {filename} ---\n(Could not read: {e})")
        
        if new_files_content:
            diff_parts.append("=== NEW FILES ===\n" + "\n\n".join(new_files_content))
    
    # Handle added files (already staged)
    if added_files:
        added_content = []
        for filename in added_files:
            # Get diff for added files
            added_diff = run_command(f"git diff --cached -- {filename}")
            if added_diff:
                added_content.append(f"--- ADDED FILE: {filename} ---\n{added_diff}")
        
        if added_content:
            diff_parts.append("=== ADDED FILES ===\n" + "\n\n".join(added_content))
    
    # Handle deleted files
    if deleted_files:
        deleted_info = "\n".join([f"- {filename}" for filename in deleted_files])
        diff_parts.append(f"=== DELETED FILES ===\n{deleted_info}")
    
    # Handle renamed files
    if renamed_files:
        renamed_info = "\n".join([f"- {filename}" for filename in renamed_files])
        diff_parts.append(f"=== RENAMED FILES ===\n{renamed_info}")
    
    # Combine all diff parts
    if not diff_parts:
        print("❌ No diff content found. Make sure you have changes to commit.")
        return None
    
    final_diff = "\n\n".join(diff_parts)
    return final_diff

def call_ollama(prompt):
    """Call remote Ollama API to generate commit message"""
    print("🤖 Generating commit message with Ollama...")
    
    url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate"
    
    data = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        # Prepare request
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=json_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Make request
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('response', '').strip()
            
    except urllib.error.URLError as e:
        print(f"❌ Error connecting to Ollama at {OLLAMA_HOST}:{OLLAMA_PORT}")
        print(f"Error: {e}")
        return None
    except json.JSONDecodeError as e:
        print("❌ Error parsing Ollama response")
        print(f"Error: {e}")
        return None
    except Exception as e:
        print("❌ Unexpected error calling Ollama")
        print(f"Error: {e}")
        return None

def main():
    """Main function"""
    print("🚀 Auto Git Commit with Ollama")
    print("=" * 40)
    
    # Check if running in non-interactive mode
    auto_confirm = len(sys.argv) > 1 and sys.argv[1] == "--auto"
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not in a git repository. Please run this from a git repository root.")
        sys.exit(1)
    
    # Get git diff
    diff = get_git_diff()
    if not diff:
        sys.exit(1)
    
    # Prepare prompt for Ollama
    prompt = f"""Buatkan git commit message dalam bahasa Indonesia yang deskriptif berdasarkan perubahan berikut:

{diff}

Perhatikan:
- Jika ada file baru (NEW FILES/ADDED FILES), gunakan kata "tambah" atau "buat"
- Jika ada file yang diubah (MODIFIED FILES), gunakan kata "ubah", "perbarui", atau "perbaiki"
- Jika ada file yang dihapus (DELETED FILES), gunakan kata "hapus" atau "buang"
- Jika ada file yang direname (RENAMED FILES), gunakan kata "ganti nama" atau "pindah"

Kembalikan hanya message nya saja tanpa kalimat awalan atau akhiran apapun. 
Format: kata kerja + deskripsi singkat perubahan (maksimal 72 karakter)."""
    
    # Generate commit message
    commit_message = call_ollama(prompt)
    if not commit_message:
        print("❌ Failed to generate commit message")
        sys.exit(1)
    
    # Clean up the message (remove any extra quotes or formatting)
    commit_message = commit_message.strip().strip('"').strip("'")
    
    print("💬 Generated commit message:")
    print(f"   '{commit_message}'")
    print()
    
    # Ask for confirmation (skip if auto mode)
    if not auto_confirm:
        try:
            confirm = input("❓ Proceed with this commit message? (y/N): ").lower().strip()
            if confirm not in ['y', 'yes']:
                print("❌ Commit cancelled.")
                sys.exit(0)
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Commit cancelled.")
            sys.exit(0)
    else:
        print("🔄 Auto-confirming commit...")
    
    # Stage all changes
    print("📦 Staging all changes...")
    # Git add warnings about CRLF are normal and shouldn't fail
    if run_command("git add .", capture_output=False, allow_warnings=True) is None:
        print("❌ Failed to stage changes")
        sys.exit(1)
    
    # Commit with generated message
    print("💾 Creating commit...")
    commit_command = f'git commit -m "{commit_message}"'
    if run_command(commit_command, capture_output=False, allow_warnings=True) is None:
        print("❌ Failed to create commit")
        sys.exit(1)
    
    print("✅ Commit created successfully!")
    
    # Show recent commits
    print("\n📋 Recent commits:")
    recent_commits = run_command("git log --oneline -5")
    if recent_commits:
        print(recent_commits)

if __name__ == "__main__":
    main()
