#!/usr/bin/env python3
"""
Script untuk testing koneksi Ollama ke Runpod.io

Usage:
    1. Update RUNPOD_URL di bawah dengan URL runpod kamu
    2. Jalankan: python3 test_ollama_runpod.py

Akan test berbagai format URL untuk cari yang benar.
"""

# ============ CONFIG - GANTI INI ============
RUNPOD_URL = "va1svwhxs18emy-11434.proxy.runpod.net"
MODEL_NAME = "aisingapore/Qwen-SEA-LION-v4-32B-IT:latest"
TIMEOUT_SECONDS = 10  # Timeout untuk setiap test
# ============================================

import ollama
import sys
import signal
from contextlib import contextmanager


class TimeoutError(Exception):
    """Timeout exception."""
    pass


@contextmanager
def timeout(seconds):
    """Context manager untuk timeout."""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    # Set alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        # Reset alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def test_connection(host_url, description):
    """Test koneksi ke Ollama dengan URL tertentu."""
    print(f"\n{'='*60}")
    print(f"Test: {description}")
    print(f"URL: {host_url}")
    print(f"Timeout: {TIMEOUT_SECONDS}s")
    print('='*60)

    try:
        with timeout(TIMEOUT_SECONDS):
            # Create client
            client = ollama.Client(host=host_url)
            print(f"✅ Client created successfully")
            print(f"   Base URL: {client._client.base_url}")

            # Test list models
            print("   Testing list() API...")
            models_response = client.list()
            models = models_response.get('models', [])
            print(f"✅ Models listed: {len(models)} models found")

            # Show first 3 model names
            if models:
                print("   Available models:")
                for model in models[:3]:
                    print(f"     - {model.get('name', 'unknown')}")
                if len(models) > 3:
                    print(f"     ... and {len(models)-3} more")

            # Test show() for specific model
            if MODEL_NAME:
                print(f"\n   Testing show() for {MODEL_NAME}...")
                try:
                    model_info = client.show(MODEL_NAME)
                    print(f"✅ Model found: {MODEL_NAME}")
                    print(f"   Size: {model_info.get('size', 'unknown')} bytes")
                except Exception as e:
                    print(f"⚠️  Model not found: {MODEL_NAME}")
                    print(f"   Error: {e}")

            print(f"\n🎉 SUCCESS - This URL works!")
            return True

    except TimeoutError as e:
        print(f"⏱️  TIMEOUT")
        print(f"   {e}")
        print(f"   Connection took longer than {TIMEOUT_SECONDS} seconds")
        return False

    except Exception as e:
        print(f"❌ FAILED")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {e}")
        return False


def main():
    print("="*60)
    print("OLLAMA RUNPOD CONNECTION TESTER")
    print("="*60)
    print(f"Runpod URL: {RUNPOD_URL}")
    print(f"Model to check: {MODEL_NAME}")

    # Test berbagai format URL
    test_cases = [
        (RUNPOD_URL, "Plain hostname (no scheme, no port)"),
        (f"http://{RUNPOD_URL}", "HTTP scheme (no port)"),
        (f"http://{RUNPOD_URL}:80", "HTTP with explicit :80 port"),
        (f"https://{RUNPOD_URL}", "HTTPS scheme (no port)"),
        (f"https://{RUNPOD_URL}:443", "HTTPS with explicit :443 port"),
    ]

    results = {}
    for url, desc in test_cases:
        success = test_connection(url, desc)
        results[desc] = (url, success)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    successful = [desc for desc, (url, success) in results.items() if success]

    if successful:
        print("\n✅ Working configurations:")
        for desc in successful:
            url, _ = results[desc]
            print(f"   - {desc}")
            print(f"     URL: {url}")

        print("\n📝 Recommended Config.py setting:")
        best_url, _ = results[successful[0]]
        print(f'   OLLAMA_HOST = "{best_url}"')
    else:
        print("\n❌ No working configuration found!")
        print("\nPossible issues:")
        print("   1. Runpod instance tidak running")
        print("   2. Firewall blocking connection")
        print("   3. URL salah")
        print("   4. Port mapping salah")

        print("\n💡 Tips:")
        print("   - Cek di Runpod dashboard apakah instance running")
        print("   - Test dengan curl: curl http://{RUNPOD_URL}/api/tags")
        print("   - Pastikan Ollama service running di Runpod")

    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test dibatalkan oleh user")
        sys.exit(1)
