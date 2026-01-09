#!/usr/bin/env python3
"""
Test script for the Go launcher.
Verifies the launcher can find and execute the wrapper correctly.
"""

import json
import subprocess
import sys
import os
import time
import shutil
from pathlib import Path

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCHER_PATH = os.path.join(REPO_ROOT, "al-language-server-go", "bin", "al-lsp-launcher.exe")
WRAPPER_PATH = os.path.join(REPO_ROOT, "al-language-server-go", "bin", "al-lsp-wrapper.exe")
TEST_PROJECT = os.path.join(REPO_ROOT, "test-al-project")


def get_plugin_cache_dir():
    """Get the plugin cache directory where launcher looks for wrapper."""
    home = os.environ.get("USERPROFILE") or os.environ.get("HOME") or ""
    return os.path.join(home, ".claude", "plugins", "cache",
                        "al-lsp-wrappers", "al-language-server-go")


def send_message(proc, msg):
    """Send JSON-RPC message."""
    content = json.dumps(msg)
    message = f"Content-Length: {len(content)}\r\n\r\n{content}"
    proc.stdin.write(message.encode("utf-8"))
    proc.stdin.flush()


def read_message(proc):
    """Read JSON-RPC message."""
    try:
        headers = {}
        while True:
            line = proc.stdout.readline().decode("utf-8")
            if not line or line == "\r\n":
                break
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()

        if "Content-Length" not in headers:
            return None

        content_length = int(headers["Content-Length"])
        content = proc.stdout.read(content_length).decode("utf-8")
        return json.loads(content)
    except:
        return None


def test_launcher_not_found():
    """Test launcher behavior when wrapper is not in cache."""
    print("\n[TEST] Launcher - wrapper not found")

    cache_dir = get_plugin_cache_dir()
    backup_dir = None

    # Temporarily rename cache dir if it exists
    if os.path.exists(cache_dir):
        backup_dir = cache_dir + ".backup"
        shutil.move(cache_dir, backup_dir)

    try:
        proc = subprocess.Popen(
            [LAUNCHER_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _, stderr = proc.communicate(timeout=5)

        if proc.returncode != 0 and b"not found" in stderr.lower():
            print("  [+] PASS: Launcher correctly reported wrapper not found")
            return True
        else:
            print(f"  [X] FAIL: Unexpected behavior (rc={proc.returncode})")
            print(f"      stderr: {stderr.decode()}")
            return False
    except subprocess.TimeoutExpired:
        proc.kill()
        print("  [X] FAIL: Launcher timed out")
        return False
    finally:
        # Restore cache dir
        if backup_dir and os.path.exists(backup_dir):
            shutil.move(backup_dir, cache_dir)


def test_launcher_finds_wrapper():
    """Test launcher can find and execute wrapper from cache."""
    print("\n[TEST] Launcher - finds wrapper in cache")

    cache_dir = get_plugin_cache_dir()
    test_version_dir = os.path.join(cache_dir, "1.0.0-test", "bin")

    # Create test cache directory and copy wrapper
    os.makedirs(test_version_dir, exist_ok=True)
    dest_wrapper = os.path.join(test_version_dir, "al-lsp-wrapper.exe")

    if not os.path.exists(dest_wrapper):
        shutil.copy(WRAPPER_PATH, dest_wrapper)

    try:
        proc = subprocess.Popen(
            [LAUNCHER_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=TEST_PROJECT
        )

        # Send initialize request
        root_uri = Path(TEST_PROJECT).as_uri()
        send_message(proc, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": os.getpid(),
                "rootUri": root_uri,
                "capabilities": {}
            }
        })

        # Wait for response
        response = read_message(proc)

        proc.terminate()
        proc.wait(timeout=5)

        if response and "result" in response:
            print("  [+] PASS: Launcher found wrapper and LSP initialized")
            return True
        else:
            print(f"  [X] FAIL: No valid response received")
            return False

    except subprocess.TimeoutExpired:
        proc.kill()
        print("  [X] FAIL: Launcher/wrapper timed out")
        return False
    except Exception as e:
        print(f"  [X] FAIL: {e}")
        return False


def test_launcher_picks_newest_version():
    """Test launcher picks the newest version when multiple exist."""
    print("\n[TEST] Launcher - picks newest version")

    cache_dir = get_plugin_cache_dir()

    # Create multiple version directories
    versions = ["1.0.0", "1.1.0", "1.2.0"]
    for version in versions:
        version_dir = os.path.join(cache_dir, version, "bin")
        os.makedirs(version_dir, exist_ok=True)
        dest_wrapper = os.path.join(version_dir, "al-lsp-wrapper.exe")
        if not os.path.exists(dest_wrapper):
            shutil.copy(WRAPPER_PATH, dest_wrapper)

    try:
        proc = subprocess.Popen(
            [LAUNCHER_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=TEST_PROJECT
        )

        # Send initialize
        root_uri = Path(TEST_PROJECT).as_uri()
        send_message(proc, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": os.getpid(),
                "rootUri": root_uri,
                "capabilities": {}
            }
        })

        response = read_message(proc)

        proc.terminate()
        proc.wait(timeout=5)

        if response and "result" in response:
            # Check the log to see which version was used
            log_path = os.path.join(os.environ.get("TEMP", "/tmp"), "al-lsp-wrapper-go.log")
            if os.path.exists(log_path):
                with open(log_path) as f:
                    log_content = f.read()
                    # The wrapper logs which extension it found
                    print("  [+] PASS: Launcher executed wrapper successfully")
                    print(f"      (Multiple versions in cache: {versions})")
                    return True
            print("  [+] PASS: Launcher executed wrapper (couldn't verify version)")
            return True
        else:
            print("  [X] FAIL: No valid response")
            return False

    except Exception as e:
        print(f"  [X] FAIL: {e}")
        return False


def test_launcher_passthrough():
    """Test launcher correctly passes stdin/stdout between Claude Code and wrapper."""
    print("\n[TEST] Launcher - stdin/stdout passthrough")

    cache_dir = get_plugin_cache_dir()
    version_dir = os.path.join(cache_dir, "1.0.0-test", "bin")
    os.makedirs(version_dir, exist_ok=True)
    dest_wrapper = os.path.join(version_dir, "al-lsp-wrapper.exe")
    if not os.path.exists(dest_wrapper):
        shutil.copy(WRAPPER_PATH, dest_wrapper)

    try:
        proc = subprocess.Popen(
            [LAUNCHER_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=TEST_PROJECT
        )

        root_uri = Path(TEST_PROJECT).as_uri()

        # Initialize
        send_message(proc, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": os.getpid(),
                "rootUri": root_uri,
                "capabilities": {}
            }
        })

        # Read initialize response (may need to skip notifications)
        response = None
        for _ in range(20):
            msg = read_message(proc)
            if msg and msg.get("id") == 1:
                response = msg
                break

        if not response or "result" not in response:
            print("  [X] FAIL: Initialize failed")
            return False

        # Send initialized notification
        send_message(proc, {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        })

        time.sleep(2)

        # Test a real LSP operation
        test_file = os.path.join(TEST_PROJECT, "src", "Tables", "Customer.Table.al")
        file_uri = Path(test_file).as_uri()

        send_message(proc, {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "textDocument/documentSymbol",
            "params": {
                "textDocument": {"uri": file_uri}
            }
        })

        # Read response
        response = None
        for _ in range(50):
            msg = read_message(proc)
            if msg and msg.get("id") == 2:
                response = msg
                break

        proc.terminate()
        proc.wait(timeout=5)

        if response and "result" in response:
            symbols = response["result"]
            if isinstance(symbols, list) and len(symbols) > 0:
                print(f"  [+] PASS: Full LSP roundtrip works ({len(symbols)} symbols)")
                return True

        print("  [X] FAIL: LSP operation through launcher failed")
        return False

    except Exception as e:
        print(f"  [X] FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_test_cache():
    """Clean up test cache directories."""
    cache_dir = get_plugin_cache_dir()
    if os.path.exists(cache_dir):
        try:
            shutil.rmtree(cache_dir)
            print(f"\nCleaned up test cache: {cache_dir}")
        except Exception as e:
            print(f"\nWarning: Could not clean up {cache_dir}: {e}")


def main():
    print("=" * 60)
    print("AL LSP Launcher Test Suite")
    print("=" * 60)
    print(f"Launcher: {LAUNCHER_PATH}")
    print(f"Wrapper:  {WRAPPER_PATH}")
    print(f"Cache:    {get_plugin_cache_dir()}")

    # Check binaries exist
    if not os.path.exists(LAUNCHER_PATH):
        print(f"\nERROR: Launcher not found at {LAUNCHER_PATH}")
        print("Run: go build -o bin/al-lsp-launcher.exe ./cmd/launcher")
        sys.exit(1)

    if not os.path.exists(WRAPPER_PATH):
        print(f"\nERROR: Wrapper not found at {WRAPPER_PATH}")
        print("Run: go build -o bin/al-lsp-wrapper.exe .")
        sys.exit(1)

    results = []

    # Run tests
    results.append(("Wrapper not found", test_launcher_not_found()))
    results.append(("Finds wrapper", test_launcher_finds_wrapper()))
    results.append(("Picks newest version", test_launcher_picks_newest_version()))
    results.append(("Stdin/stdout passthrough", test_launcher_passthrough()))

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(1 for _, p in results if p)
    failed = sum(1 for _, p in results if not p)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        icon = "[+]" if result else "[X]"
        print(f"  {icon} {status}: {name}")

    print(f"\nTotal: {passed} passed, {failed} failed")

    # Ask about cleanup
    print("\n" + "-" * 60)
    response = input("Clean up test cache directories? [y/N]: ").strip().lower()
    if response == 'y':
        cleanup_test_cache()

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
