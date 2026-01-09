# AL Language Server Wrapper - TODO

## Current State

The AL LSP wrapper (`al_lsp_wrapper.py`) provides integration between Claude Code and the Microsoft AL Language Server from the VS Code extension.

### Working Features

- **documentSymbol**: Returns full symbol tree with tables, fields, procedures, etc.
- **Hover**: Returns markdown-formatted hover info (wrapper works, but Claude Code may have parsing issues)
- **goToDefinition**: Works! Returns file URI and range for symbol definitions
- **Initialization**: Properly initializes with AL-specific params, opens app.json, sets active workspace
- **Auto-detection**: Automatically finds AL projects by searching for app.json in workspace
- **Multi-project support**: Routes requests to correct project based on file URI (walks up to find app.json)

### Known Issues

#### 1. Claude Code Hover Parsing Error
- Error: `undefined is not an Object. (evaluating '"kind"in H')`
- Wrapper returns valid LSP hover format: `{"contents": {"kind": "markdown", "value": "..."}}`
- Issue is in Claude Code's response parser, not the wrapper
- **Workaround**: None currently - need Claude Code fix or response transformation

## Potential Improvements

### High Priority

1. **Handle findReferences**
   - AL LSP supports `referencesProvider: true`
   - Add `handle_references()` with file opening

### Medium Priority

4. **Normalize hover response**
   - If Claude Code can't parse hover, transform response format
   - May need to flatten or restructure the response

5. **Add completion support**
   - AL LSP supports completions with triggers: `.`, `:`, `"`, `/`, `<`
   - Add `handle_completion()` with file opening

6. **Improve logging**
   - Add log levels (debug, info, error)
   - Log to stderr for debugging while keeping stdout clean for LSP

### Low Priority

7. **Handle workspace/configuration requests**
   - AL LSP may request configuration dynamically
   - Currently only sent during post-initialization

## Testing

Run the test script:
```bash
cd test-al-project
python test_lsp.py
```

Check wrapper log:
```bash
cat "$TEMP/al-lsp-wrapper.log"
```

## References

- Serena AL implementation: `U:\Git\serena\src\solidlsp\language_servers\al_language_server.py`
- LSP Specification: https://microsoft.github.io/language-server-protocol/
- AL Language Extension: `ms-dynamics-smb.al` in VS Code marketplace
