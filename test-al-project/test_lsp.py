#!/usr/bin/env python3
"""Test script to simulate Claude Code LSP calls to the AL wrapper."""

import json
import subprocess
import sys
import os
import time
from pathlib import Path

# Path to wrapper - use local repo copy for testing
WRAPPER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "al-language-server-python", "al_lsp_wrapper.py"
)

def send_message(proc, msg):
    """Send JSON-RPC message to process."""
    content = json.dumps(msg)
    message = f"Content-Length: {len(content)}\r\n\r\n{content}"
    proc.stdin.write(message.encode("utf-8"))
    proc.stdin.flush()
    print(f">>> SENT: {msg.get('method', msg.get('id', 'unknown'))}")

def read_message(proc, timeout=30):
    """Read JSON-RPC message from process."""
    # Read headers
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

def main():
    print("=" * 60)
    print("AL LSP Wrapper Test Script")
    print("=" * 60)

    # Check wrapper exists
    if not os.path.exists(WRAPPER_PATH):
        print(f"ERROR: Wrapper not found at {WRAPPER_PATH}")
        sys.exit(1)

    print(f"Using wrapper: {WRAPPER_PATH}")

    # Start wrapper process
    print("\nStarting wrapper process...")
    proc = subprocess.Popen(
        [sys.executable, WRAPPER_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=r"U:\Git\claude-code-lsps\test-al-project"
    )

    try:
        # 1. Send initialize
        print("\n--- Step 1: Initialize ---")
        root_path = r"U:\Git\claude-code-lsps"
        root_uri = Path(root_path).as_uri()

        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": os.getpid(),
                "rootPath": root_path,
                "rootUri": root_uri,
                "capabilities": {}
            }
        }
        send_message(proc, init_request)

        print("Waiting for initialize response...")
        response = read_message(proc)
        print(f"<<< RESPONSE: {json.dumps(response, indent=2)[:500]}...")

        # 2. Send initialized notification
        print("\n--- Step 2: Initialized ---")
        initialized_notif = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        send_message(proc, initialized_notif)
        time.sleep(3)  # Give it time to load project

        # Test file
        test_file = r"U:\Git\claude-code-lsps\test-al-project\src\Tables\Customer.Table.al"
        file_uri = Path(test_file).as_uri()

        # 3. Test hover (line 188 has "CustomerMgt: Codeunit CustomerMgt")
        print("\n--- Step 3: Hover ---")
        hover_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "textDocument/hover",
            "params": {
                "textDocument": {"uri": file_uri},
                "position": {"line": 187, "character": 30}  # 0-indexed, on "CustomerMgt"
            }
        }
        send_message(proc, hover_request)
        print("Waiting for hover response...")
        response = read_message(proc, timeout=30)
        print(f"<<< HOVER RESPONSE:\n{json.dumps(response, indent=2)}")

        # 4. Test goToDefinition on CustomerType enum (line 77: "Enum CustomerType")
        print("\n--- Step 4: Go To Definition (on Enum CustomerType) ---")
        definition_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "textDocument/definition",
            "params": {
                "textDocument": {"uri": file_uri},
                "position": {"line": 76, "character": 45}  # 0-indexed, on "CustomerType"
            }
        }
        send_message(proc, definition_request)
        print("Waiting for definition response...")
        response = read_message(proc, timeout=30)
        print(f"<<< DEFINITION RESPONSE:\n{json.dumps(response, indent=2)}")

        # 5. Test documentSymbol (known to work)
        print("\n--- Step 5: Document Symbol ---")
        symbol_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "textDocument/documentSymbol",
            "params": {
                "textDocument": {"uri": file_uri}
            }
        }
        send_message(proc, symbol_request)
        print("Waiting for documentSymbol response...")
        response = read_message(proc, timeout=60)
        print(f"<<< SYMBOL RESPONSE (truncated):\n{json.dumps(response, indent=2)[:1000]}...")

        print("\n--- Test Complete ---")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nTerminating wrapper...")
        proc.terminate()
        proc.wait(timeout=5)

        # Show wrapper log
        log_path = os.path.join(os.environ.get("TEMP", "/tmp"), "al-lsp-wrapper.log")
        if os.path.exists(log_path):
            print("\n--- Wrapper Log (last 50 lines) ---")
            with open(log_path) as f:
                lines = f.readlines()
                print("".join(lines[-50:]))

if __name__ == "__main__":
    main()
