#!/usr/bin/env python3
"""
Test al-call-hierarchy LSP server directly.
Tests prepareCallHierarchy, incomingCalls, and outgoingCalls.
"""

import json
import subprocess
import sys
import os

# Path to al-call-hierarchy executable
AL_CALL_HIERARCHY = os.path.join(
    os.path.dirname(__file__),
    "..", "al-language-server-go-windows", "bin", "al-call-hierarchy.exe"
)

# Test workspace
TEST_WORKSPACE = os.path.dirname(__file__)


class LSPClient:
    def __init__(self, exe_path):
        self.proc = subprocess.Popen(
            [exe_path],
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

    def read_response(self):
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
    print("Testing al-call-hierarchy LSP Server")
    print("=" * 60)

    if not os.path.exists(AL_CALL_HIERARCHY):
        print(f"ERROR: al-call-hierarchy not found at {AL_CALL_HIERARCHY}")
        print("Run build.sh first to build the executable")
        return False

    print(f"Executable: {AL_CALL_HIERARCHY}")
    print(f"Workspace: {TEST_WORKSPACE}")
    print()

    passed = 0
    failed = 0

    client = LSPClient(AL_CALL_HIERARCHY)

    try:
        # Initialize
        print("Test: Initialize")
        workspace_uri = path_to_uri(TEST_WORKSPACE)
        client.send_request("initialize", {
            "processId": None,
            "capabilities": {},
            "rootUri": workspace_uri,
            "workspaceFolders": [{
                "uri": workspace_uri,
                "name": "test-al-project"
            }]
        })
        resp = client.read_response()

        if "result" in resp and resp["result"].get("capabilities"):
            caps = resp["result"]["capabilities"]
            if caps.get("callHierarchyProvider"):
                print("  [+] PASS: Server supports callHierarchyProvider")
                passed += 1
            else:
                print("  [-] FAIL: callHierarchyProvider not in capabilities")
                failed += 1
        else:
            print(f"  [-] FAIL: Bad response: {resp}")
            failed += 1

        # Send initialized notification
        client.send_notification("initialized", {})

        # Wait for indexing - server needs time to parse all files
        import time
        print("  Waiting for indexing...")
        time.sleep(2)

        # Test prepareCallHierarchy
        print("\nTest: prepareCallHierarchy")
        test_file = os.path.join(TEST_WORKSPACE, "src", "Codeunits", "CustomerMgt.Codeunit.al")
        if os.path.exists(test_file):
            file_uri = path_to_uri(test_file)
            # Line 10 in file = line 9 (0-indexed), CreateNewCustomer procedure
            # Character 15 is inside the procedure name
            client.send_request("textDocument/prepareCallHierarchy", {
                "textDocument": {"uri": file_uri},
                "position": {"line": 9, "character": 15}  # CreateNewCustomer procedure
            })
            resp = client.read_response()

            if "result" in resp and resp["result"]:
                items = resp["result"]
                print(f"  [+] PASS: Found {len(items)} call hierarchy item(s)")
                for item in items:
                    print(f"      - {item.get('name')} ({item.get('kind')})")
                passed += 1

                # Test outgoingCalls
                print("\nTest: outgoingCalls")
                client.send_request("callHierarchy/outgoingCalls", {
                    "item": items[0]
                })
                resp = client.read_response()

                if "result" in resp:
                    calls = resp["result"] or []
                    print(f"  [+] PASS: Found {len(calls)} outgoing call(s)")
                    for call in calls[:5]:
                        print(f"      -> {call.get('to', {}).get('name', 'unknown')}")
                    passed += 1
                else:
                    print(f"  [-] FAIL: {resp.get('error', resp)}")
                    failed += 1

                # Test incomingCalls
                print("\nTest: incomingCalls")
                client.send_request("callHierarchy/incomingCalls", {
                    "item": items[0]
                })
                resp = client.read_response()

                if "result" in resp:
                    calls = resp["result"] or []
                    print(f"  [+] PASS: Found {len(calls)} incoming call(s)")
                    for call in calls[:5]:
                        print(f"      <- {call.get('from', {}).get('name', 'unknown')}")
                    passed += 1
                else:
                    print(f"  [-] FAIL: {resp.get('error', resp)}")
                    failed += 1
            else:
                print(f"  [-] FAIL: No items returned")
                print(f"      Response: {json.dumps(resp, indent=2)}")
                print(f"      File URI: {file_uri}")
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
