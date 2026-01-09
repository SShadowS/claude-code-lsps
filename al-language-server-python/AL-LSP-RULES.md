# AL Language Server Protocol Rules

This document describes how the VS Code AL extension communicates with the AL Language Server, based on analysis of `ms-dynamics-smb.al-17.0.1998613`.

## Custom AL LSP Commands

The AL Language Server uses many custom commands beyond standard LSP:

### Core Commands
| Command | Type | Description |
|---------|------|-------------|
| `al/gotodefinition` | Request | Go to definition (instead of standard `textDocument/definition`) |
| `al/setActiveWorkspace` | Request | Set active workspace folder |
| `al/hasProjectClosureLoadedRequest` | Request | Check if project is fully loaded |
| `al/loadManifest` | Request | Load app.json manifest |
| `al/didChangeWorkspaceFolders` | Notification | Notify of workspace folder changes |
| `al/didChangeActiveDocument` | Notification | Notify of active document change |

### Symbol Commands
| Command | Type | Description |
|---------|------|-------------|
| `al/symbolSearch` | Request | Search for symbols across project |
| `al/checkSymbols` | Request | Check/validate symbols |
| `al/downloadSymbols` | Request | Download dependency symbols |
| `al/downloadSymbolsFromGlobalSources` | Request | Download from global NuGet sources |
| `al/refreshsymbolreferencesrequest` | Request | Refresh symbol references |

### Build/Publish Commands
| Command | Type | Description |
|---------|------|-------------|
| `al/publish` | Request | Publish extension |
| `al/fullDependencyPublish` | Request | Publish with all dependencies |
| `al/createPackage` | Request | Create .app package |

### Notifications (Server → Client)
| Command | Description |
|---------|-------------|
| `al/manifestMissing` | app.json not found |
| `al/symbolsMissing` | Required symbols not downloaded |
| `al/progressNotification` | Progress updates |
| `al/refreshExplorerObjects` | Refresh object explorer |
| `al/updateTests` | Test discovery updates |
| `al/projectsLoadedNotification` | Projects finished loading |
| `al/activeProjectLoaded` | Active project loaded |

## Request Parameter Patterns

### al/gotodefinition

The extension uses TWO patterns for go-to-definition:

#### Pattern 1: Text Document Position (standard navigation)
```javascript
const params = getAlParams();
params.textDocumentPositionParams = languageClient.asTextDocumentPositionParams(document, position);
// Result: params = {
//   textDocumentPositionParams: {
//     textDocument: { uri: "file:///path/to/file.al" },
//     position: { line: 10, character: 25 }
//   },
//   // ... other AL params from getAlParams()
// }
const result = await sendRequest(config, "al/gotodefinition", params);
```

#### Pattern 2: Symbol ID (explorer navigation)
```javascript
const result = await sendRequest("al/gotodefinition", { symbolId: symbolId });
```

### al/setActiveWorkspace

```javascript
const params = {
  currentWorkspaceFolderPath: {
    uri: workspaceUri,
    name: workspaceName,
    index: 0
  },
  settings: getWorkspaceSettings()
};
```

### Workspace Settings (via didChangeConfiguration)

```javascript
{
  settings: {
    workspacePath: "/path/to/project",
    alResourceConfigurationSettings: {
      assemblyProbingPaths: ["./.netpackages"],
      codeAnalyzers: [],
      enableCodeAnalysis: false,
      backgroundCodeAnalysis: "Project",  // or "None", "File"
      packageCachePaths: ["./.alpackages"],
      ruleSetPath: null,
      enableCodeActions: true,
      incrementalBuild: false,
      outputAnalyzerStatistics: true,
      enableExternalRulesets: true,
      // Optional compilation options:
      generateReportLayout: true,
      parallelBuild: true,
      maxDegreeOfParallelism: 4,
      outFolder: "./output"
    },
    setActiveWorkspace: true,
    dependencyParentWorkspacePath: null,
    expectedProjectReferenceDefinitions: [],
    activeWorkspaceClosure: ["/path/to/project"]
  }
}
```

## Initialization Sequence

The VS Code extension follows this sequence:

1. **Start Language Server** - spawn `Microsoft.Dynamics.Nav.EditorServices.Host.exe`

2. **Initialize** - send standard LSP `initialize` with capabilities

3. **Initialized Notification** - send `initialized` notification

4. **Set Active Workspace** - after server is running:
   ```javascript
   await setActiveWorkspace();  // Called on state change to Running
   await progressNotificationService.createProgress("Loading Workspace...");
   ```

5. **Wait for Project Load** - poll or wait for:
   - `al/projectsLoadedNotification`
   - `al/activeProjectLoaded`
   - Or use `al/hasProjectClosureLoadedRequest`

6. **Open Files** - files must be opened with `textDocument/didOpen` before:
   - Document symbols work correctly
   - Go-to-definition works
   - Hover works

## Key Insights for Wrapper Implementation

### 1. Definition Provider is Disabled
The AL LSP reports `"definitionProvider": false` in capabilities. The extension registers its own `AlDefinitionProvider` that:
- Uses `al/gotodefinition` instead of `textDocument/definition`
- Requires files to be opened first
- Needs the project to be fully loaded

### 2. Project Must Be Loaded
Before `al/gotodefinition` returns results:
- Workspace settings must be sent
- app.json must be opened/loaded
- `al/setActiveWorkspace` must be called
- May need to wait for `al/hasProjectClosureLoadedRequest` to return true

### 3. File Opening is Required
Unlike standard LSP servers, the AL LSP requires explicit `textDocument/didOpen` before:
- Symbol operations work
- Navigation works
- Hover works

### 4. getAlParams() Function
The extension has a `getAlParams()` function that builds base parameters including:
- Workspace configuration
- Package paths
- Code analysis settings

These are merged with operation-specific params like `textDocumentPositionParams`.

## Response Formats

### al/gotodefinition Response
```javascript
{
  uri: "file:///path/to/definition.al",  // or .dal for external
  range: {
    start: { line: 10, character: 0 },
    end: { line: 10, character: 20 }
  }
}
```

Note: `.dal` files are virtual files for external/dependency symbols.

### Hover Response (standard LSP format)
```javascript
{
  contents: {
    kind: "markdown",
    value: "```al\nCodeunit CustomerMgt\n```\n\n"
  }
}
```

## MCP Integration (v17+)

The AL extension now includes MCP (Model Context Protocol) support:
- `al/mcp/startSession`
- `al/mcp/stopSession`
- `al/mcp/listTools`
- `al/mcp/invokeTool`
- `al/mcp/listResources`
- `al/mcp/readResource`
- `al/mcp/listPrompts`
- `al/mcp/getPrompt`
- `al/mcp/sendMessages`

This enables AI assistants to interact with the AL language server for code analysis, navigation, and generation.

## References

- Extension path: `~/.vscode/extensions/ms-dynamics-smb.al-{version}/`
- Main code: `dist/extension.js` (minified)
- Binary: `bin/{platform}/Microsoft.Dynamics.Nav.EditorServices.Host.exe`
