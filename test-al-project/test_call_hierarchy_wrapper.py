#!/usr/bin/env python3
"""
Test call hierarchy through the Python wrapper.
Tests prepareCallHierarchy, incomingCalls, and outgoingCalls via al_lsp_wrapper.
"""

import json
import subprocess
import sys
import os
import time

# Path to Python wrapper
WRAPPER_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "al-language-server-python", "al_lsp_wrapper.py"
)

# Test workspace
TEST_WORKSPACE = os.path.dirname(__file__)


class LSPClient:
    def __init__(self, wrapper_path):
        self.proc = subprocess.Popen(
            [sys.executable, wrapper_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.req_id = 0

    def send_request(self, method, params):
        self.req_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.req_id,
            "method": method,
            "params": params or {}
        }
        content = json.dumps(request)
        message = f"Content-Length: {len(content)}\r\n\r\n{content}"
        self.proc.stdin.write(message.encode())
        self.proc.stdin.flush()
        return self.req_id

    def send_notification(self, method, params):
        notif = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        content = json.dumps(notif)
        message = f"Content-Length: {len(content)}\r\n\r\n{content}"
        self.proc.stdin.write(message.encode())
        self.proc.stdin.flush()

    def read_response(self, timeout=30):
        import select
        # Read headers
        headers = {}
        while True:
            line = self.proc.stdout.readline().decode()
            if line == '\r\n':
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()

        # Read content
        content_length = int(headers.get('Content-Length', 0))
        content = self.proc.stdout.read(content_length).decode()
        return json.loads(content)

    def close(self):
        self.send_request("shutdown", None)
        try:
            self.read_response()
        except:
            pass
        self.proc.terminate()
        self.proc.wait()


def path_to_uri(path):
    """Convert file path to LSP URI."""
    abs_path = os.path.abspath(path)
    return "file:///" + abs_path.replace("\\", "/")


def run_tests():
    print("=" * 60)
    print("Testing Call Hierarchy via Python Wrapper")
    print("=" * 60)

    if not os.path.exists(WRAPPER_PATH):
        print(f"ERROR: wrapper not found at {WRAPPER_PATH}")
        return False

    print(f"Wrapper: {WRAPPER_PATH}")
    print(f"Workspace: {TEST_WORKSPACE}")
    print()

    passed = 0
    failed = 0

    client = LSPClient(WRAPPER_PATH)

    try:
        # Initialize
        print("Test: Initialize")
        workspace_uri = path_to_uri(TEST_WORKSPACE)
        client.send_request("initialize", {
            "processId": None,
            "capabilities": {},
            "rootUri": workspace_uri,
            "rootPath": TEST_WORKSPACE,
            "workspaceFolders": [{
                "uri": workspace_uri,
                "name": "test-al-project"
            }]
        })
        resp = client.read_response()

        if "result" in resp:
            print("  [+] PASS: Wrapper initialized")
            passed += 1
        else:
            print(f"  [-] FAIL: Bad response: {resp}")
            failed += 1
            return False

        # Send initialized notification
        client.send_notification("initialized", {})

        # Wait for wrapper to initialize (including call hierarchy server)
        print("  Waiting for call hierarchy server...")
        time.sleep(3)

        # Test prepareCallHierarchy
        print("\nTest: prepareCallHierarchy via wrapper")
        test_file = os.path.join(TEST_WORKSPACE, "src", "Codeunits", "CustomerMgt.Codeunit.al")
        if os.path.exists(test_file):
            file_uri = path_to_uri(test_file)
            # Line 10 in file = line 9 (0-indexed), CreateNewCustomer procedure
            client.send_request("textDocument/prepareCallHierarchy", {
                "textDocument": {"uri": file_uri},
                "position": {"line": 9, "character": 15}
            })
            resp = client.read_response()

            if "error" in resp:
                print(f"  [-] FAIL: {resp['error'].get('message', resp['error'])}")
                failed += 1
            elif "result" in resp and resp["result"]:
                items = resp["result"]
                print(f"  [+] PASS: Found {len(items)} call hierarchy item(s)")
                for item in items:
                    print(f"      - {item.get('name')} ({item.get('kind')})")
                passed += 1

                # Test outgoingCalls
                print("\nTest: outgoingCalls via wrapper")
                client.send_request("callHierarchy/outgoingCalls", {
                    "item": items[0]
                })
                resp = client.read_response()

                if "error" in resp:
                    print(f"  [-] FAIL: {resp['error'].get('message', resp['error'])}")
                    failed += 1
                elif "result" in resp:
                    calls = resp["result"] or []
                    print(f"  [+] PASS: Found {len(calls)} outgoing call(s)")
                    for call in calls[:5]:
                        print(f"      -> {call.get('to', {}).get('name', 'unknown')}")
                    passed += 1
                else:
                    print(f"  [-] FAIL: Unexpected response: {resp}")
                    failed += 1

                # Test incomingCalls
                print("\nTest: incomingCalls via wrapper")
                client.send_request("callHierarchy/incomingCalls", {
                    "item": items[0]
                })
                resp = client.read_response()

                if "error" in resp:
                    print(f"  [-] FAIL: {resp['error'].get('message', resp['error'])}")
                    failed += 1
                elif "result" in resp:
                    calls = resp["result"] or []
                    print(f"  [+] PASS: Found {len(calls)} incoming call(s)")
                    for call in calls[:5]:
                        print(f"      <- {call.get('from', {}).get('name', 'unknown')}")
                    passed += 1
                else:
                    print(f"  [-] FAIL: Unexpected response: {resp}")
                    failed += 1
            else:
                print(f"  [-] FAIL: No items returned")
                print(f"      Response: {json.dumps(resp, indent=2)}")
                failed += 1
        else:
            print(f"  [SKIP] Test file not found: {test_file}")

    except Exception as e:
        print(f"  [-] ERROR: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
    finally:
        client.close()

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
