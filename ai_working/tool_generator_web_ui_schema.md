# Tool Generator Web UI Schema Design

**Status:** 🚧 PLANNING - Design Discussion in Progress
**Last Updated:** 2025-10-26
**Related:** [tool_generator_web_ui_integration_STATUS.md](tool_generator_web_ui_integration_STATUS.md)

---

## Executive Summary

This document proposes a new UI-first schema system that separates **user-facing inputs** (what users see in the Web UI) from **CLI implementation details** (flags, paths, verbose modes). This enables:

- **Cleaner UI** - Show only relevant inputs (file upload, text box), hide technical details (output dirs, cache settings)
- **Compound inputs** - Single UI widget that maps to multiple CLI flags (file OR text → `--input-file` or `--input-text`)
- **Node-based UI ready** - Schema includes metadata for React Flow integration (sockets, ports, connections)
- **Backward compatible** - V1 tools (`@add_describe_flag`) continue working

---

## The Problem We're Solving

### Current Limitation: 1:1 CLI-to-UI Mapping

**Today's pattern** (`@add_describe_flag`):
```python
@add_describe_flag(version="1.0", display_name="Document Analyzer")
@click.command()
@click.option("--input-file", type=click.Path())
@click.option("--input-text", type=str)
@click.option("--output-dir", default=".data/results")
@click.option("--verbose", is_flag=True)
@click.option("--cache-enabled", default=True)
def main(input_file, input_text, output_dir, verbose, cache_enabled):
    pass
```

**Web UI shows ALL parameters:**
- ❌ Input File (user needs this)
- ❌ Input Text (user needs this)
- ❌ Output Directory (implementation detail - user doesn't care)
- ❌ Verbose (implementation detail)
- ❌ Cache Enabled (implementation detail)

**What we actually want:**
- ✅ **Upload file OR paste text** (single compound input)
- ✅ That's it! Everything else automatic.

### Real-World Example

**Scenario:** Document Analyzer tool

**User's mental model:**
> "I have a document. I want to analyze it. Let me upload it or paste the text."

**Current UI forces users to:**
1. Choose between `--input-file` and `--input-text` (why two fields?)
2. Configure `--output-dir` (I don't care where it saves!)
3. Toggle `--verbose` (what does this even mean?)
4. Enable/disable `--cache-enabled` (just make it fast!)

**Better UI:**
1. **One input:** Upload file OR paste text
2. **Done.** Tool handles the rest.

---

## Proposed Solution: UI Schema with CLI Mapping

### New Decorator: `@ui_schema`

```python
from amplifier.ccsdk_toolkit.ui_schema import ui_schema, UIInput

@ui_schema(
    version="2.0",
    display_name="Document Analyzer",
    description="Analyze documents for sentiment, entities, or summaries",
    inputs=[
        UIInput(
            id="content",
            label="Document Content",
            type="file_or_text",  # Compound input type
            file_accept=[".txt", ".md", ".pdf"],
            text_placeholder="Or paste your document text here...",
            text_multiline=True,
            required=True,
            # How this maps to CLI invocation
            cli_mapping={
                "file": "--input-file {value}",
                "text": "--input-text {value}",
            }
        ),
        UIInput(
            id="analysis_type",
            label="Analysis Type",
            type="choice",
            choice_options=["sentiment", "summary", "entities"],
            default="summary",
            cli_mapping="--analysis-type {value}"
        ),
    ],
    # CLI-only options (not shown in UI, always included)
    cli_options=[
        "--output-dir .data/analyzer/sessions/{session_id}",
        "--cache-enabled",
        "--format json",
    ]
)
@click.command()
@click.option("--input-file", type=click.Path())
@click.option("--input-text", type=str)
@click.option("--analysis-type", type=click.Choice(["sentiment", "summary", "entities"]))
@click.option("--output-dir", default=".data/analyzer")
@click.option("--cache-enabled", is_flag=True, default=True)
@click.option("--format", default="json")
def main(input_file, input_text, analysis_type, output_dir, cache_enabled, format):
    # Implementation...
    pass
```

### What the Web UI Sees

**Backend queries:** `python -m scenarios.document_analyzer --describe-ui-schema`

**Returns (JSON):**
```json
{
  "version": "2.0",
  "display_name": "Document Analyzer",
  "description": "Analyze documents for sentiment, entities, or summaries",
  "inputs": [
    {
      "id": "content",
      "label": "Document Content",
      "type": "file_or_text",
      "required": true,
      "file_accept": [".txt", ".md", ".pdf"],
      "text_placeholder": "Or paste your document text here...",
      "text_multiline": true,
      "cli_mapping": {
        "file": "--input-file {value}",
        "text": "--input-text {value}"
      }
    },
    {
      "id": "analysis_type",
      "label": "Analysis Type",
      "type": "choice",
      "choice_options": ["sentiment", "summary", "entities"],
      "default": "summary",
      "cli_mapping": "--analysis-type {value}"
    }
  ],
  "cli_options": [
    "--output-dir .data/analyzer/sessions/{session_id}",
    "--cache-enabled",
    "--format json"
  ]
}
```

### How CLI Invocation Works

**User interacts with UI:**
```javascript
// User uploads file.txt and selects "sentiment"
const uiValues = {
  content: { type: "file", value: "/uploads/file.txt" },
  analysis_type: "sentiment"
};
```

**Backend translates to CLI command:**
```python
from amplifier.ccsdk_toolkit.cli_builder import build_cli_command

schema = get_ui_schema("document_analyzer")
cli_parts = build_cli_command(schema, ui_values, session_id="20251026_123456")

# Result:
# [
#   "--input-file", "/uploads/file.txt",
#   "--analysis-type", "sentiment",
#   "--output-dir", ".data/analyzer/sessions/20251026_123456",
#   "--cache-enabled",
#   "--format", "json"
# ]

# Execute:
# python -m scenarios.document_analyzer --input-file /uploads/file.txt --analysis-type sentiment --output-dir .data/analyzer/sessions/20251026_123456 --cache-enabled --format json
```

---

## UI Input Types

### Basic Types

| Type | UI Widget | Example |
|------|-----------|---------|
| `file` | File picker | Upload button |
| `text` | Text input | Single-line field |
| `text` (multiline) | Text area | Multi-line editor |
| `choice` | Dropdown/Select | Options list |
| `integer` | Number input | Numeric field |
| `boolean` | Checkbox/Toggle | On/off switch |
| `directory` | Directory picker | Folder selector |

### Compound Types (New)

| Type | UI Widget | Maps To |
|------|-----------|---------|
| `file_or_text` | Toggle + File picker OR Text area | `--input-file` or `--input-text` |
| `file_or_url` | Toggle + File picker OR URL input | `--input-file` or `--url` |
| `text_or_select` | Toggle + Text input OR Dropdown | `--custom-value` or `--preset` |

### Example: File or Text Input

```python
UIInput(
    id="source",
    label="Input Source",
    type="file_or_text",
    file_accept=[".txt", ".md"],
    text_placeholder="Or paste content here...",
    text_multiline=True,
    cli_mapping={
        "file": "--input-file {value}",
        "text": "--input-text {value}"
    }
)
```

**Renders in UI:**
```
┌─────────────────────────────────────┐
│ Input Source                        │
│ ┌─────────┬─────────┐              │
│ │ 📁 File │   Text  │              │
│ └─────────┴─────────┘              │
│                                     │
│ ┌─────────────────────────────────┐│
│ │  Click to upload or drag file   ││
│ │       (.txt, .md files)         ││
│ └─────────────────────────────────┘│
└─────────────────────────────────────┘

(Toggle to Text mode)

┌─────────────────────────────────────┐
│ Input Source                        │
│ ┌─────────┬─────────┐              │
│ │  File   │ 📝 Text │              │
│ └─────────┴─────────┘              │
│                                     │
│ ┌─────────────────────────────────┐│
│ │ Or paste content here...        ││
│ │                                 ││
│ │                                 ││
│ │                                 ││
│ └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

---

## Node-Based UI Support (React Flow)

### Extended Schema with Node Metadata

```python
@ui_schema(
    version="2.0",
    display_name="Document Analyzer",
    inputs=[...],  # Same as before

    # NEW: Node-based UI configuration
    node_config={
        "category": "analysis",  # Category in node palette
        "icon": "document-search",  # Icon name
        "color": "#4A90E2",  # Node color
        "width": 280,  # Default node width
        "height": 120,  # Default node height

        # Input ports (handles on left side)
        "input_ports": [
            {
                "id": "content",
                "label": "Document",
                "socket_type": "text|file",  # What can connect
                "position": "left",
            }
        ],

        # Output ports (handles on right side)
        "output_ports": [
            {
                "id": "result",
                "label": "Analysis",
                "socket_type": "json",
                "position": "right",
            },
            {
                "id": "summary",
                "label": "Summary",
                "socket_type": "text",
                "position": "right",
            }
        ]
    }
)
```

### React Flow Visualization

```
┌─────────────────────────────────────────────┐
│         📄 Document Analyzer (Node)         │
│                                             │
│  ●─┤ Document  │                            │
│                 │  [Analysis: sentiment]    │
│                 │                   Result ├─●
│                 │                            │
│                 │                  Summary ├─●
└─────────────────────────────────────────────┘

Connections:
  File Input Node (output) → Document Analyzer (content input)
  Document Analyzer (result output) → Chart Visualizer (data input)
  Document Analyzer (summary output) → Text Display (text input)
```

### Flow Execution Model

**User creates flow:**
```tsx
const nodes = [
  { id: "1", type: "file_input", data: { label: "Upload" } },
  { id: "2", type: "tool", data: {
      tool: "document_analyzer",
      inputs: { analysis_type: "sentiment" }
  }},
  { id: "3", type: "chart", data: { chartType: "bar" } }
];

const edges = [
  { source: "1", target: "2", sourceHandle: "file", targetHandle: "content" },
  { source: "2", target: "3", sourceHandle: "result", targetHandle: "data" }
];
```

**Execution flow:**
1. **Topological sort** - Determine execution order (1 → 2 → 3)
2. **For each node:**
   - Resolve input connections (substitute `{{node_id.output}}` references)
   - Build CLI command from schema + resolved inputs
   - Execute tool via subprocess
   - Parse outputs (JSON events → structured data)
   - Store outputs for downstream nodes
3. **Data flows** through edges to next nodes

**Backend execution:**
```python
async def execute_flow(nodes: list[Node], edges: list[Edge]) -> dict:
    """Execute a node-based workflow."""

    # Sort nodes by dependencies
    execution_order = topological_sort(nodes, edges)
    results = {}

    for node in execution_order:
        if node.type == "tool":
            # Get schema
            schema = get_ui_schema(node.data.tool)

            # Resolve inputs from connected nodes
            resolved_inputs = {}
            for edge in edges:
                if edge.target == node.id:
                    source_result = results[edge.source]
                    resolved_inputs[edge.targetHandle] = source_result[edge.sourceHandle]

            # Merge with node's local inputs
            all_inputs = {**node.data.inputs, **resolved_inputs}

            # Build CLI command
            cli_command = build_cli_command(schema, all_inputs)

            # Execute
            result = await execute_tool(node.data.tool, cli_command)
            results[node.id] = result

    return results
```

---

## Implementation Plan

### Phase 1: Core UI Schema System

**New file:** `amplifier/ccsdk_toolkit/ui_schema.py`

```python
"""UI-first schema system for Web UI integration.

Separates user-facing inputs from CLI implementation details.
"""

from dataclasses import dataclass, field
from typing import Literal, Any

@dataclass
class UIInput:
    """Defines a single user-facing input in the Web UI."""

    # Core properties
    id: str  # Unique identifier
    label: str  # Display label
    type: Literal["file", "text", "file_or_text", "file_or_url", "choice", "integer", "boolean", "directory"]
    required: bool = False
    default: Any = None
    help: str = ""

    # File input options
    file_accept: list[str] | None = None  # e.g., [".txt", ".md", ".pdf"]

    # Text input options
    text_placeholder: str | None = None
    text_multiline: bool = False

    # Choice input options
    choice_options: list[str] | None = None

    # CLI mapping
    cli_mapping: str | dict[str, str] = ""
    # Examples:
    #   Simple: "--input-file {value}"
    #   Compound: {"file": "--input-file {value}", "text": "--input-text {value}"}

    # Node-based UI
    socket_type: str = "any"  # For React Flow connections

@dataclass
class NodeConfig:
    """Configuration for node-based UI (React Flow)."""

    category: str = "general"  # Category in node palette
    icon: str = "tool"  # Icon name
    color: str = "#6B7280"  # Node color
    width: int = 280
    height: int = 120

    input_ports: list[dict[str, Any]] = field(default_factory=list)
    output_ports: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class UISchema:
    """Complete UI schema for a tool."""

    version: str
    display_name: str
    description: str
    inputs: list[UIInput]

    # CLI-only options (not shown in UI)
    cli_options: list[str] = field(default_factory=list)

    # Node-based UI configuration
    node_config: NodeConfig | None = None

def ui_schema(**kwargs):
    """Decorator to define UI schema separate from CLI.

    Usage:
        @ui_schema(
            version="2.0",
            display_name="My Tool",
            inputs=[UIInput(...)],
            cli_options=["--cache-enabled"]
        )
        @click.command()
        def main(...):
            pass
    """
    def decorator(func):
        # Store schema on function
        func._ui_schema = UISchema(**kwargs)

        # Add --describe-ui-schema flag
        if hasattr(func, 'params'):
            # Already a Click command, add option
            from click import Option
            describe_option = Option(
                ["--describe-ui-schema"],
                is_flag=True,
                is_eager=True,
                expose_value=False,
                help="Output UI schema as JSON and exit",
                callback=lambda ctx, param, value: _describe_ui_callback(ctx, func._ui_schema, value)
            )
            func.params.insert(0, describe_option)
        else:
            # Store for later (when Click decorates it)
            func._pending_ui_schema = True

        return func
    return decorator

def _describe_ui_callback(ctx, schema: UISchema, value: bool):
    """Callback for --describe-ui-schema flag."""
    if value:
        import json
        from dataclasses import asdict
        click.echo(json.dumps(asdict(schema), indent=2))
        ctx.exit(0)
```

### Phase 2: CLI Command Builder

**New file:** `amplifier/ccsdk_toolkit/cli_builder.py`

```python
"""Build CLI commands from UI schema and user inputs."""

from typing import Any
from .ui_schema import UISchema

def build_cli_command(
    schema: UISchema,
    ui_values: dict[str, Any],
    session_id: str | None = None
) -> list[str]:
    """Build CLI command from UI schema and user inputs.

    Args:
        schema: Tool's UI schema
        ui_values: Values from UI
        session_id: Optional session ID for output paths

    Returns:
        CLI command parts (e.g., ["--input-file", "test.txt", "--cache-enabled"])

    Example:
        schema = UISchema(inputs=[UIInput(id="content", cli_mapping={"file": "--input-file {value}"})])
        ui_values = {"content": {"type": "file", "value": "test.txt"}}
        result = build_cli_command(schema, ui_values)
        # ["--input-file", "test.txt"]
    """
    cmd_parts = []

    # Process user inputs
    for input_def in schema.inputs:
        value = ui_values.get(input_def.id)
        if value is None:
            continue

        # Handle compound inputs (file_or_text, file_or_url)
        if isinstance(input_def.cli_mapping, dict):
            # value is {"type": "file", "value": "test.txt"}
            if isinstance(value, dict) and "type" in value:
                mapping = input_def.cli_mapping.get(value["type"])
                if mapping:
                    cmd_parts.extend(_expand_mapping(mapping, value["value"]))
        else:
            # Simple mapping: "--flag {value}"
            cmd_parts.extend(_expand_mapping(input_def.cli_mapping, value))

    # Add CLI-only options (with session_id substitution)
    if schema.cli_options:
        for option in schema.cli_options:
            if session_id and "{session_id}" in option:
                option = option.replace("{session_id}", session_id)
            cmd_parts.extend(option.split())

    return cmd_parts

def _expand_mapping(mapping: str, value: Any) -> list[str]:
    """Expand a CLI mapping template.

    Args:
        mapping: Template like "--input-file {value}"
        value: Value to substitute

    Returns:
        List of command parts
    """
    expanded = mapping.format(value=value)
    return expanded.split()
```

### Phase 3: Backend Integration

**Modify:** `amplifier-web-ui/backend/services/scenario_discovery.py`

```python
def discover_tool_schema(tool_path: Path) -> dict:
    """Discover tool schema with V2 (UI schema) support.

    Returns:
        Schema dict with version field:
        - version "2.0" = UI schema (new)
        - version "1.0" = Parameter schema (old)
    """

    # Try V2 UI schema first
    try:
        result = subprocess.run(
            ["uv", "run", "python", "-m", f"scenarios.{tool_path.name}", "--describe-ui-schema"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            schema = json.loads(result.stdout)
            if schema.get("version") == "2.0":
                return schema  # V2 schema
    except Exception:
        pass  # Fall back to V1

    # Fallback to V1 parameter schema
    result = subprocess.run(
        ["uv", "run", "python", "-m", f"scenarios.{tool_path.name}", "--describe-parameters"],
        capture_output=True,
        text=True,
        timeout=5
    )

    if result.returncode == 0:
        v1_schema = json.loads(result.stdout)
        # Auto-convert V1 to V2 format (all params → inputs)
        return convert_v1_to_v2(v1_schema)

    raise ValueError(f"Could not discover schema for {tool_path.name}")

def convert_v1_to_v2(v1_schema: dict) -> dict:
    """Convert V1 parameter schema to V2 UI schema.

    Assumes all CLI parameters should be shown in UI.
    """
    inputs = []
    for param in v1_schema.get("parameters", []):
        inputs.append({
            "id": param["name"],
            "label": param["name"].replace("_", " ").title(),
            "type": _map_v1_type(param["type"]),
            "required": param["required"],
            "default": param.get("default"),
            "help": param.get("help", ""),
            "cli_mapping": f"{param['cli_flag']} {{value}}"
        })

    return {
        "version": "2.0",
        "display_name": v1_schema.get("display_name", v1_schema["name"]),
        "description": v1_schema.get("description", ""),
        "inputs": inputs,
        "cli_options": []
    }
```

### Phase 4: Frontend Components

**New:** `amplifier-web-ui/frontend/src/components/inputs/FileOrTextInput.tsx`

```tsx
import React, { useState } from 'react';
import { Box, ToggleButtonGroup, ToggleButton, TextField } from '@mui/material';
import { FilePicker } from './FilePicker';

interface FileOrTextInputProps {
  value: {type: 'file' | 'text', value: string} | null;
  onChange: (value: {type: 'file' | 'text', value: string}) => void;
  fileAccept?: string[];
  textPlaceholder?: string;
  textMultiline?: boolean;
  label?: string;
}

export const FileOrTextInput: React.FC<FileOrTextInputProps> = ({
  value,
  onChange,
  fileAccept = [],
  textPlaceholder = "Enter text...",
  textMultiline = false,
  label = "Input"
}) => {
  const [mode, setMode] = useState<'file' | 'text'>(value?.type || 'file');

  const handleModeChange = (newMode: 'file' | 'text') => {
    if (newMode) {
      setMode(newMode);
      // Reset value when switching modes
      onChange({type: newMode, value: ''});
    }
  };

  const handleFileChange = (file: string) => {
    onChange({type: 'file', value: file});
  };

  const handleTextChange = (text: string) => {
    onChange({type: 'text', value: text});
  };

  return (
    <Box>
      <Box mb={1}>
        <ToggleButtonGroup
          value={mode}
          exclusive
          onChange={(_, val) => handleModeChange(val)}
          size="small"
        >
          <ToggleButton value="file">📁 Upload File</ToggleButton>
          <ToggleButton value="text">📝 Paste Text</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {mode === 'file' ? (
        <FilePicker
          value={value?.type === 'file' ? value.value : ''}
          accept={fileAccept}
          onChange={handleFileChange}
        />
      ) : (
        <TextField
          fullWidth
          multiline={textMultiline}
          rows={textMultiline ? 10 : 1}
          placeholder={textPlaceholder}
          value={value?.type === 'text' ? value.value : ''}
          onChange={(e) => handleTextChange(e.target.value)}
        />
      )}
    </Box>
  );
};
```

**Modify:** `amplifier-web-ui/frontend/src/components/ScenarioForm.tsx`

```tsx
import { FileOrTextInput } from './inputs/FileOrTextInput';

// In renderInput function, add case for compound types:
const renderInput = (input: UIInput) => {
  switch (input.type) {
    case 'file_or_text':
      return (
        <FileOrTextInput
          value={formValues[input.id]}
          onChange={(value) => handleInputChange(input.id, value)}
          fileAccept={input.file_accept}
          textPlaceholder={input.text_placeholder}
          textMultiline={input.text_multiline}
          label={input.label}
        />
      );

    // ... other cases (file, text, choice, etc.)
  }
};
```

### Phase 5: Tool Generator Integration

**Modify:** `scenarios/tool_generator/delegation/task_writer.py`

Add UI schema instructions to generation prompts:

```python
WEB UI SCHEMA (V2 - RECOMMENDED):
For modern tools, use @ui_schema to separate user-facing inputs from CLI details:

```python
from amplifier.ccsdk_toolkit.ui_schema import ui_schema, UIInput

@ui_schema(
    version="2.0",
    display_name="{spec.tool_name.replace('_', ' ').title()}",
    description="Brief description of what this tool does",
    inputs=[
        UIInput(
            id="input_source",
            label="Input Source",
            type="file_or_text",  # Compound input
            file_accept=[".txt", ".md"],
            text_placeholder="Or paste content here...",
            text_multiline=True,
            required=True,
            cli_mapping={{
                "file": "--input-file {{value}}",
                "text": "--input-text {{value}}"
            }}
        ),
        # Add more user-facing inputs...
    ],
    # CLI implementation details (hidden from UI)
    cli_options=[
        "--output-dir .data/{spec.tool_name}/sessions/{{session_id}}",
        "--cache-enabled",
        "--format json"
    ]
)
@click.command()
@click.option("--input-file", type=click.Path())
@click.option("--input-text", type=str)
@click.option("--output-dir", default=".data/{spec.tool_name}")
@click.option("--cache-enabled", is_flag=True, default=True)
@click.option("--format", default="json")
def main(input_file, input_text, output_dir, cache_enabled, format):
    # Implementation...
    pass
```

BACKWARD COMPATIBILITY:
Still support @add_describe_flag for simpler tools. Backend auto-converts V1 → V2.
```

### Phase 6: Node-Based UI (React Flow)

**New:** `amplifier-web-ui/frontend/src/components/FlowEditor.tsx`

```tsx
import React, { useState, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  addEdge,
  Connection
} from 'reactflow';
import 'reactflow/dist/style.css';
import { ToolNode } from './nodes/ToolNode';
import { FileInputNode } from './nodes/FileInputNode';
import { OutputNode } from './nodes/OutputNode';

const nodeTypes = {
  tool: ToolNode,
  file_input: FileInputNode,
  text_input: TextInputNode,
  output: OutputNode,
};

export const FlowEditor: React.FC = () => {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    []
  );

  const executeFlow = async () => {
    setIsExecuting(true);

    try {
      // Send flow to backend for execution
      const response = await fetch('/api/flows/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nodes, edges })
      });

      const result = await response.json();

      // Update nodes with results
      setNodes((nds) =>
        nds.map((node) => ({
          ...node,
          data: { ...node.data, result: result.outputs[node.id] }
        }))
      );
    } catch (error) {
      console.error('Flow execution failed:', error);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <Box sx={{ width: '100%', height: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={setNodes}
        onEdgesChange={setEdges}
        onConnect={onConnect}
      >
        <Controls />
        <Background />
        <Panel position="top-right">
          <Button
            variant="contained"
            onClick={executeFlow}
            disabled={isExecuting}
          >
            {isExecuting ? 'Running...' : 'Run Flow'}
          </Button>
        </Panel>
      </ReactFlow>
    </Box>
  );
};
```

**Backend flow execution:** `amplifier-web-ui/backend/api/flows.py`

```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class FlowExecutionRequest(BaseModel):
    nodes: list[dict]
    edges: list[dict]

@router.post("/execute")
async def execute_flow(request: FlowExecutionRequest):
    """Execute a node-based workflow."""

    # Topological sort
    execution_order = topological_sort(request.nodes, request.edges)

    results = {}
    for node in execution_order:
        if node["type"] == "tool":
            # Get schema
            tool_name = node["data"]["tool"]
            schema = get_ui_schema(tool_name)

            # Resolve inputs from connections
            resolved_inputs = resolve_node_inputs(node, request.edges, results)

            # Build CLI command
            cli_command = build_cli_command(schema, resolved_inputs)

            # Execute tool
            execution = await execute_tool(tool_name, cli_command)
            results[node["id"]] = execution.outputs

    return {"outputs": results}
```

---

## Migration Strategy

### Backward Compatibility

**V1 Tools (existing)** - Continue working:
```python
@add_describe_flag(version="1.0", display_name="Old Tool")
@click.command()
@click.option("--input", required=True)
def main(input: str):
    pass
```

**Web UI behavior:**
- Queries `--describe-parameters` (V1)
- Auto-converts to V2 format
- Shows all CLI parameters in form

**V2 Tools (new)** - Enhanced UI:
```python
@ui_schema(version="2.0", inputs=[...], cli_options=[...])
@click.command()
@click.option("--input", required=True)
@click.option("--verbose", is_flag=True)  # Hidden from UI
def main(input: str, verbose: bool):
    pass
```

**Web UI behavior:**
- Queries `--describe-ui-schema` (V2)
- Shows only defined inputs
- Automatically includes cli_options when executing

### Hybrid Approach (during transition)

```python
@ui_schema(version="2.0", inputs=[...])  # V2 - preferred
@add_describe_flag(version="1.0", display_name="Tool")  # V1 - fallback
@click.command()
def main(...):
    pass
```

**Web UI tries V2 first, falls back to V1.**

---

## Open Questions & Design Decisions

### 1. Should V2 be mandatory for new tools?

**Option A:** Encourage but don't require
- ✅ Easier migration
- ❌ Inconsistent UI quality

**Option B:** Require V2 for tool_generator output
- ✅ Consistent high-quality UI
- ❌ Harder for manual tool creation

**Recommendation:** Option B - tool_generator always uses V2, manual tools can use either.

### 2. How to handle dynamic inputs?

**Use case:** User selects "sentiment analysis" → shows additional "language" dropdown

**Potential solution:** Conditional inputs
```python
UIInput(
    id="language",
    label="Language",
    type="choice",
    choice_options=["en", "es", "fr"],
    show_when={"analysis_type": "sentiment"}  # Only show if condition met
)
```

**Status:** Not in Phase 1, can add later.

### 3. Node-based UI vs Form UI - when to use which?

**Form UI (current):**
- ✅ Simple, single-step tools
- ✅ Familiar interface
- ❌ Can't compose multiple tools

**Node-based UI (future):**
- ✅ Multi-step workflows
- ✅ Visual pipeline building
- ❌ Steeper learning curve

**Recommendation:** Support both. Let users choose their preferred interface.

---

## Next Steps

### Immediate (Phase 1)
1. ✅ Document design (this file)
2. ⏳ Implement `ui_schema.py` and `cli_builder.py`
3. ⏳ Update backend to support V2 schemas
4. ⏳ Build `FileOrTextInput` React component
5. ⏳ Test with one existing tool (e.g., blog_writer)

### Short-term (Phases 2-3)
1. Update tool_generator to emit V2 schemas
2. Build remaining compound input components
3. Add validation for V2 schemas
4. Documentation and examples

### Long-term (Phases 4-6)
1. Experiment with node-based UI
2. Add conditional inputs
3. Rich metadata (icons, categories)
4. Visual workflow builder

---

## Appendix: Complete Example

### Tool Implementation

```python
#!/usr/bin/env python3
"""
Document Analyzer - Example V2 UI Schema Tool
"""

import asyncio
import os
from pathlib import Path
import click

from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.logger import LogFormat
from amplifier.ccsdk_toolkit.ui_schema import ui_schema, UIInput

# Environment detection
log_format = LogFormat.JSON if os.getenv("AMPLIFIER_WEB_UI") else LogFormat.PLAIN
logger = ToolkitLogger("document_analyzer", format=log_format)

@ui_schema(
    version="2.0",
    display_name="Document Analyzer",
    description="Analyze documents for sentiment, entities, or summaries",
    inputs=[
        UIInput(
            id="content",
            label="Document Content",
            type="file_or_text",
            file_accept=[".txt", ".md", ".pdf"],
            text_placeholder="Or paste your document text here...",
            text_multiline=True,
            required=True,
            cli_mapping={
                "file": "--input-file {value}",
                "text": "--input-text {value}",
            }
        ),
        UIInput(
            id="analysis_type",
            label="Analysis Type",
            type="choice",
            choice_options=["sentiment", "summary", "entities"],
            default="summary",
            help="Choose the type of analysis to perform",
            cli_mapping="--analysis-type {value}"
        ),
    ],
    cli_options=[
        "--output-dir .data/document_analyzer/sessions/{session_id}",
        "--cache-enabled",
        "--format json",
    ]
)
@click.command()
@click.option("--input-file", type=click.Path(exists=True))
@click.option("--input-text", type=str)
@click.option("--analysis-type", type=click.Choice(["sentiment", "summary", "entities"]), default="summary")
@click.option("--output-dir", type=click.Path(), default=".data/document_analyzer")
@click.option("--cache-enabled", is_flag=True, default=True)
@click.option("--format", type=click.Choice(["json", "text"]), default="json")
def main(
    input_file: str | None,
    input_text: str | None,
    analysis_type: str,
    output_dir: str,
    cache_enabled: bool,
    format: str
):
    """Analyze documents for sentiment, entities, or summaries."""

    # Load content
    if input_file:
        content = Path(input_file).read_text()
        logger.info(f"Loaded file: {input_file}")
    elif input_text:
        content = input_text
        logger.info("Using provided text input")
    else:
        logger.error("Must provide either --input-file or --input-text")
        return

    # Perform analysis
    logger.stage_transition(None, "analyzing", estimated_duration=10)
    result = asyncio.run(analyze(content, analysis_type))

    # Save output
    output_path = Path(output_dir) / f"result.{format}"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result)

    logger.file_created(str(output_path), metadata={"type": "result"})
    logger.info(f"✅ Analysis complete: {output_path}")

async def analyze(content: str, analysis_type: str) -> str:
    """Perform the actual analysis."""
    # Implementation here...
    pass

if __name__ == "__main__":
    main()
```

### Web UI Usage

**User flow:**
1. Opens "Document Analyzer" in scenarios list
2. Sees clean form:
   - **Document Content** [Toggle: File | Text]
     - File mode: Drag & drop or browse (.txt, .md, .pdf)
     - Text mode: Large text area "Or paste your document text here..."
   - **Analysis Type** [Dropdown: sentiment, summary, entities]
3. Uploads file.txt, selects "sentiment"
4. Clicks "Run"

**Backend execution:**
```bash
python -m scenarios.document_analyzer \
  --input-file /uploads/file.txt \
  --analysis-type sentiment \
  --output-dir .data/document_analyzer/sessions/20251026_123456 \
  --cache-enabled \
  --format json
```

User never sees `--output-dir`, `--cache-enabled`, `--format` - they're automatically included!

---

## Summary

**What this design enables:**

✅ **Cleaner UI** - Show only what users need
✅ **Smarter inputs** - Compound widgets (file OR text, not two fields)
✅ **Hidden complexity** - CLI details invisible to users
✅ **Node-based workflows** - Visual pipeline building with React Flow
✅ **Backward compatible** - V1 tools continue working
✅ **Progressive enhancement** - Start simple (V1), upgrade to V2 when needed

**Philosophy alignment:**

✅ **Ruthless simplicity** - Hide unnecessary complexity from users
✅ **Single source of truth** - Schema defines both UI and CLI
✅ **Build for composability** - Tools as nodes in larger workflows

**Status:** 🚧 Design complete, ready for Phase 1 implementation when prioritized.
