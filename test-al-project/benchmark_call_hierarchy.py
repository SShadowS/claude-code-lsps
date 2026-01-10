#!/usr/bin/env python3
"""
Benchmark call hierarchy performance on large workspaces.
Records timing for before/after optimization comparison.

Usage:
    python benchmark_call_hierarchy.py [--label LABEL] [--workspace PATH]

Examples:
    python benchmark_call_hierarchy.py --label baseline
    python benchmark_call_hierarchy.py --label optimized_v1
"""

import argparse
import json
import subprocess
import sys
import os
import time
import statistics
from pathlib import Path
from datetime import datetime

# Default configuration
DEFAULT_WORKSPACE = "U:/Git/DO.Support-Zendesk"
AL_CALL_HIERARCHY = os.path.join(
    os.path.dirname(__file__),
    "..", "al-language-server-go-windows", "bin", "al-call-hierarchy.exe"
)
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "benchmark_results")

# Test files to benchmark (variety of sizes/locations)
TEST_FILES = [
    "Core/Cloud/Specialization/ManualSetupManagement.Codeunit.al",
    "BC/BaseApp/Source/Base Application/Sales/Posting/SalesPostPrepayments.Codeunit.al",
    "BC/System Application/Source/System Application/Caption Class/src/CaptionClassImpl.Codeunit.al",
    "BC/BaseApp/Source/Base Application/Utilities/DocumentErrorsMgt.Codeunit.al",
]

# Iterations per operation for statistical accuracy
ITERATIONS = 5


class LSPClient:
    """Simple LSP client for benchmarking."""

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
        headers = {}
        while True:
            line = self.proc.stdout.readline().decode()
            if line == '\r\n':
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()

        content_length = int(headers.get('Content-Length', 0))
        content = self.proc.stdout.read(content_length).decode()
        return json.loads(content)

    def close(self):
        try:
            self.send_request("shutdown", None)
            self.read_response()
        except:
            pass
        self.proc.terminate()
        self.proc.wait()


def path_to_uri(path):
    """Convert file path to LSP URI."""
    abs_path = os.path.abspath(path)
    return "file:///" + abs_path.replace("\\", "/")


def count_al_files(workspace):
    """Count AL files in workspace."""
    count = 0
    for root, dirs, files in os.walk(workspace):
        for f in files:
            if f.endswith('.al'):
                count += 1
    return count


def benchmark_operation(client, method, params, iterations=ITERATIONS):
    """Run operation multiple times and return timing stats."""
    times = []
    results = []
    for i in range(iterations):
        start = time.perf_counter()
        client.send_request(method, params)
        response = client.read_response()
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        results.append(response)

    return {
        "times_ms": times,
        "min_ms": round(min(times), 2),
        "max_ms": round(max(times), 2),
        "avg_ms": round(statistics.mean(times), 2),
        "median_ms": round(statistics.median(times), 2),
        "stdev_ms": round(statistics.stdev(times), 2) if len(times) > 1 else 0,
        "sample_result": results[0] if results else None,
    }


def run_benchmark(workspace, label):
    """Run full benchmark suite."""
    print("=" * 70)
    print(f"AL Call Hierarchy Benchmark")
    print(f"Label: {label}")
    print(f"Workspace: {workspace}")
    print("=" * 70)

    # Verify executable exists
    if not os.path.exists(AL_CALL_HIERARCHY):
        print(f"ERROR: al-call-hierarchy not found at {AL_CALL_HIERARCHY}")
        return None

    # Count files
    print("\nCounting AL files...")
    file_count = count_al_files(workspace)
    print(f"  Found {file_count} AL files")

    results = {
        "label": label,
        "timestamp": datetime.now().isoformat(),
        "workspace": workspace,
        "file_count": file_count,
        "executable": AL_CALL_HIERARCHY,
        "iterations": ITERATIONS,
        "init_time_ms": 0,
        "index_stats": {},
        "operations": {},
    }

    # Start client and measure initialization
    print("\nInitializing al-call-hierarchy...")
    start = time.perf_counter()
    client = LSPClient(AL_CALL_HIERARCHY)

    workspace_uri = path_to_uri(workspace)
    client.send_request("initialize", {
        "processId": os.getpid(),
        "capabilities": {},
        "rootUri": workspace_uri,
        "workspaceFolders": [{
            "uri": workspace_uri,
            "name": os.path.basename(workspace)
        }]
    })
    init_response = client.read_response()
    client.send_notification("initialized", {})

    # Wait for indexing
    print("  Waiting for indexing to complete...")
    time.sleep(3)  # Give time for indexing

    init_time = (time.perf_counter() - start) * 1000
    results["init_time_ms"] = round(init_time, 2)
    print(f"  Initialization took {init_time:.0f}ms")

    # Benchmark each test file
    print(f"\nBenchmarking {len(TEST_FILES)} test files ({ITERATIONS} iterations each)...")

    for test_file in TEST_FILES:
        file_path = os.path.join(workspace, test_file)
        if not os.path.exists(file_path):
            print(f"  SKIP: {test_file} (not found)")
            continue

        file_uri = path_to_uri(file_path)
        print(f"\n  File: {test_file}")

        # prepareCallHierarchy
        print("    prepareCallHierarchy...", end=" ", flush=True)
        prepare_result = benchmark_operation(client, "textDocument/prepareCallHierarchy", {
            "textDocument": {"uri": file_uri},
            "position": {"line": 10, "character": 15}
        })
        print(f"{prepare_result['avg_ms']:.1f}ms avg")

        file_results = {
            "prepareCallHierarchy": prepare_result,
        }

        # If we got items, benchmark incoming/outgoing calls
        sample = prepare_result.get("sample_result", {})
        if sample and "result" in sample and sample["result"]:
            item = sample["result"][0]

            # incomingCalls
            print("    incomingCalls...", end=" ", flush=True)
            incoming_result = benchmark_operation(client, "callHierarchy/incomingCalls", {
                "item": item
            })
            print(f"{incoming_result['avg_ms']:.1f}ms avg")
            file_results["incomingCalls"] = incoming_result

            # outgoingCalls
            print("    outgoingCalls...", end=" ", flush=True)
            outgoing_result = benchmark_operation(client, "callHierarchy/outgoingCalls", {
                "item": item
            })
            print(f"{outgoing_result['avg_ms']:.1f}ms avg")
            file_results["outgoingCalls"] = outgoing_result
        else:
            print("    (no call hierarchy item found, skipping incoming/outgoing)")

        results["operations"][test_file] = file_results

    # Close client
    client.close()

    # Save results
    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = os.path.join(RESULTS_DIR, f"{label}_{timestamp}.json")

    with open(result_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n{'=' * 70}")
    print(f"Results saved to: {result_file}")
    print_summary(results)

    # Update comparison file
    update_comparison()

    return results


def print_summary(results):
    """Print summary of benchmark results."""
    print(f"\n{'=' * 70}")
    print(f"SUMMARY: {results['label']}")
    print(f"{'=' * 70}")
    print(f"Workspace: {results['workspace']}")
    print(f"Files: {results['file_count']}")
    print(f"Init time: {results['init_time_ms']:.0f}ms")
    print()

    print(f"{'Operation':<30} {'Min':>10} {'Avg':>10} {'Max':>10} {'Median':>10}")
    print("-" * 70)

    for file_name, ops in results["operations"].items():
        print(f"\n{file_name[:50]}...")
        for op_name, stats in ops.items():
            if isinstance(stats, dict) and "avg_ms" in stats:
                print(f"  {op_name:<28} {stats['min_ms']:>9.1f} {stats['avg_ms']:>9.1f} {stats['max_ms']:>9.1f} {stats['median_ms']:>9.1f}")


def update_comparison():
    """Generate comparison markdown from all result files."""
    if not os.path.exists(RESULTS_DIR):
        return

    result_files = sorted([f for f in os.listdir(RESULTS_DIR) if f.endswith('.json')])
    if not result_files:
        return

    comparison_file = os.path.join(RESULTS_DIR, "comparison.md")

    with open(comparison_file, "w") as f:
        f.write("# Call Hierarchy Benchmark Comparison\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")

        # Load all results
        all_results = []
        for rf in result_files:
            with open(os.path.join(RESULTS_DIR, rf)) as jf:
                all_results.append(json.load(jf))

        # Summary table
        f.write("## Summary\n\n")
        f.write("| Label | Init (ms) | Files | Timestamp |\n")
        f.write("|-------|-----------|-------|----------|\n")
        for r in all_results:
            f.write(f"| {r['label']} | {r['init_time_ms']:.0f} | {r['file_count']} | {r['timestamp'][:19]} |\n")

        f.write("\n## Detailed Results\n\n")

        # Per-operation comparison
        for r in all_results:
            f.write(f"\n### {r['label']}\n\n")
            f.write("| File | Operation | Avg (ms) | Min | Max |\n")
            f.write("|------|-----------|----------|-----|-----|\n")
            for file_name, ops in r.get("operations", {}).items():
                short_name = file_name.split("/")[-1][:30]
                for op_name, stats in ops.items():
                    if isinstance(stats, dict) and "avg_ms" in stats:
                        f.write(f"| {short_name} | {op_name} | {stats['avg_ms']:.1f} | {stats['min_ms']:.1f} | {stats['max_ms']:.1f} |\n")

    print(f"Comparison updated: {comparison_file}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark call hierarchy performance")
    parser.add_argument("--label", default="benchmark", help="Label for this benchmark run")
    parser.add_argument("--workspace", default=DEFAULT_WORKSPACE, help="Workspace path to benchmark")
    args = parser.parse_args()

    run_benchmark(args.workspace, args.label)


if __name__ == "__main__":
    main()
