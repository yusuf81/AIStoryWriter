#!/usr/bin/env python3
"""
Test which Ollama API endpoints are available on Runpod proxy.

Usage:
    1. Update RUNPOD_URL and MODEL_NAME
    2. Run: python3 test_runpod_endpoints.py
"""

# ============ CONFIG ============
RUNPOD_URL = "http://srcx9z0xd8djkb-11434.proxy.runpod.net"
MODEL_NAME = "aisingapore/Qwen-SEA-LION-v4-32B-IT:latest"
# ================================

import ollama
import sys


def test_endpoint(client, endpoint_name, test_func):
    """Test a specific Ollama API endpoint."""
    print(f"\n{'='*60}")
    print(f"Testing: {endpoint_name}")
    print('='*60)

    try:
        result = test_func(client)
        print(f"✅ {endpoint_name} WORKS")
        return True
    except ollama._types.ResponseError as e:
        if "405" in str(e):
            print(f"❌ {endpoint_name} BLOCKED (405 method not allowed)")
        else:
            print(f"❌ {endpoint_name} FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ {endpoint_name} ERROR: {type(e).__name__}: {e}")
        return False


def main():
    print("="*60)
    print("OLLAMA RUNPOD ENDPOINT TESTER")
    print("="*60)
    print(f"URL: {RUNPOD_URL}")
    print(f"Model: {MODEL_NAME}")

    try:
        client = ollama.Client(host=RUNPOD_URL)
        print(f"\n✅ Client created: {client._client.base_url}")
    except Exception as e:
        print(f"\n❌ Failed to create client: {e}")
        return

    results = {}

    # Test 1: GET /api/tags (list models)
    def test_list(c):
        return c.list()
    results['list'] = test_endpoint(client, "GET /api/tags (list models)", test_list)

    # Test 2: POST /api/show (model info)
    def test_show(c):
        return c.show(MODEL_NAME)
    results['show'] = test_endpoint(client, "POST /api/show (model info)", test_show)

    # Test 3: POST /api/chat (conversation)
    def test_chat(c):
        return c.chat(
            model=MODEL_NAME,
            messages=[{'role': 'user', 'content': 'Say "OK"'}],
            options={'num_predict': 5}
        )
    results['chat'] = test_endpoint(client, "POST /api/chat (conversation)", test_chat)

    # Test 4: POST /api/generate (completion)
    def test_generate(c):
        return c.generate(
            model=MODEL_NAME,
            prompt='Say "OK"',
            options={'num_predict': 5}
        )
    results['generate'] = test_endpoint(client, "POST /api/generate (completion)", test_generate)

    # Test 5: POST /api/embeddings (embeddings)
    def test_embeddings(c):
        return c.embeddings(
            model=MODEL_NAME,
            prompt='test'
        )
    results['embeddings'] = test_endpoint(client, "POST /api/embeddings (embeddings)", test_embeddings)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    working = [name for name, status in results.items() if status]
    blocked = [name for name, status in results.items() if not status]

    if working:
        print("\n✅ Working endpoints:")
        for name in working:
            print(f"   - {name}")

    if blocked:
        print("\n❌ Blocked/Failed endpoints:")
        for name in blocked:
            print(f"   - {name}")

    # Recommendations
    print("\n📝 Recommendations:")

    if results.get('chat'):
        print("   ✅ Current code should work (chat endpoint available)")
    elif results.get('generate'):
        print("   ⚠️  Need to modify code to use generate() instead of chat()")
        print("      (chat endpoint blocked, but generate works)")
    else:
        print("   ❌ Neither chat nor generate works - check Runpod configuration")

    if not results.get('embeddings'):
        print("   ⚠️  Embeddings blocked - lorebook features may not work")
        print("      Consider using local embedding model or disabling lorebook")

    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled")
        sys.exit(1)
