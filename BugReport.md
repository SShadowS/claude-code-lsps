# Bug: LSP workspaceSymbol operation sends empty query parameter

## Description

The Claude Code LSP tool's `workspaceSymbol` operation does not pass a search query to the language server, making it non-functional. The tool sends `{"query": ""}` (empty string) instead of a user-provided search term.

## Expected Behavior

`workspaceSymbol` should accept a search query parameter (e.g., "Customer", "Sales") and pass it to the language server to search for symbols across the workspace.

## Actual Behavior

The LSP tool sends an empty query:
```json
{"query": ""}
```

This results in no symbols being found, regardless of the codebase content.

## Evidence

From the AL Language Server wrapper logs:
```
handle_workspace_symbol called
DEBUG params: {'query': ''}
Workspace symbol query: ''
```

## Root Cause

The LSP tool interface appears designed for file+position operations (filePath, line, character), which work correctly for:
- `findReferences` - find usages at a position
- `goToDefinition` - jump to definition at a position
- `documentSymbol` - list symbols in a file
- `hover` - get info at a position

However, `workspaceSymbol` requires a different parameter - a search query string - which isn't exposed in the current tool interface.

## Suggested Fix

Add a `query` parameter to the LSP tool for `workspaceSymbol` operations. Example interface:

```
LSP(operation: "workspaceSymbol", query: "Customer")
```

Or alternatively, repurpose an existing parameter when operation is `workspaceSymbol`.

## Workaround

Users can use `documentSymbol` to list symbols in a specific file, or use `Grep` to search for symbol names across the workspace.

## Environment

- Claude Code version: Latest
- Language Server: AL Language Server (Microsoft Dynamics 365 Business Central)
- OS: Windows 11

## Reproduction Steps

1. Open a project with an LSP configured (e.g., AL Language Server)
2. Ask Claude to use `workspaceSymbol` to find symbols
3. Observe that 0 symbols are returned
4. Check language server logs to confirm empty query is sent
