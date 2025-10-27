# Scenario Generator System

Automatically generates working Amplifier scenario tools from specifications.

## Quick Start

### Generate a Scenario

```bash
# Activate virtual environment
cd amplifier-web-ui/backend
source .venv/bin/activate

# Generate from spec
python generators/simple_generator.py /path/to/spec.json [output_dir]

# Example:
python generators/simple_generator.py \
    /Users/samule/repo/amplifier/.data/test_scenarios/email_to_actions_spec.json
```

### Validate Generated Code

```bash
# Validate all generated scenarios
python generators/validate_generated.py
```

## Components

### 1. `scenario_spec.py` - Specification Schema

Pydantic models defining the scenario contract:

- `ScenarioSpec` - Complete scenario specification
- `InputSpec` - Input parameters
- `OutputSpec` - Generated outputs
- `StageSpec` - Processing stages
- `WorkflowType` - SINGLE_PASS, MULTI_STAGE, ITERATIVE

### 2. `simple_generator.py` - Template Generator

Generates code using proven templates:

- **Inputs:** ScenarioSpec (JSON or Pydantic model)
- **Outputs:** Complete working scenario
- **Files Generated:**
  - `__init__.py` - Package initialization
  - `__main__.py` - Entry point
  - `main.py` - CLI and orchestration
  - `state.py` - State management
  - `stage_*/core.py` - Stage implementations
  - `README.md` - Documentation

### 3. `validation_pipeline.py` - Quality Checks

Multi-stage validation:

- **Structure** - Required files present
- **Imports** - All imports resolve
- **Syntax** - Valid Python code

### 4. `spec_generator.py` - LLM Spec Generation

Converts natural language to specs:

- Uses PydanticAI
- Comprehensive system prompts
- Requires OpenAI API key

### 5. `backend_generator.py` - LLM Code Generation

Generates code using LLM:

- More flexible than templates
- Context-aware generation
- Requires OpenAI API key

## Workflow Types

### SINGLE_PASS

Sequential execution, no state transitions:

```python
async def run(self):
    await self._stage1()
    await self._stage2()
    return True
```

**Example:** Email to Action Items

### MULTI_STAGE

Stage-based with resume capability:

```python
async def run(self):
    if self.state.state.stage == "initialized":
        await self._stage1()
    if self.state.state.stage == "stage1_complete":
        await self._stage2()
    return True
```

**Example:** Report Generator

### ITERATIVE

Repeating cycle with exit conditions:

```python
async def run(self):
    while self.state.state.iteration < max_iterations:
        await self._stage1()
        await self._stage2()

        if condition_met:
            break

        self.state.state.iteration += 1
    return True
```

**Example:** Document Simplifier

## Creating a Spec

### Minimal Example

```json
{
  "name": "my_tool",
  "display_name": "My Tool",
  "description": "What it does",
  "version": "0.1.0",
  "workflow_type": "single_pass",
  "inputs": [
    {
      "name": "input_file",
      "type": "file",
      "description": "Input file",
      "required": true,
      "cli_flag": "--input",
      "validate_exists": true
    }
  ],
  "outputs": [
    {
      "name": "output",
      "type": "file",
      "description": "Output file",
      "default_path": "output.json"
    }
  ],
  "stages": [
    {
      "name": "process",
      "display_name": "Process",
      "description": "Process the input",
      "module_name": "processor",
      "class_name": "Processor",
      "method_name": "process",
      "state_output_key": "result",
      "updates_stage_name": "completed"
    }
  ]
}
```

### Full Example

See `.data/test_scenarios/*.json` for complete examples of all workflow types.

## Generated Code Structure

```
my_scenario/
├── __init__.py          # Package metadata
├── __main__.py          # Entry point
├── main.py              # CLI + orchestration
├── state.py             # State management
├── README.md            # Generated docs
├── stage1/
│   ├── __init__.py
│   └── core.py          # Stage implementation
└── stage2/
    ├── __init__.py
    └── core.py
```

## Making Generated Code Functional

Generated stages have TODO markers:

```python
# stage_name/core.py
async def process(self):
    logger.info("Processing...")

    # TODO: Implement actual logic
    # Example:
    # session = ClaudeSession()
    # result = await session.send_message("Your prompt")
    # return result

    return "placeholder_result"
```

Replace TODOs with actual implementation using ClaudeSession or other logic.

## Validation

Run validation after generation:

```bash
python generators/validate_generated.py
```

**Checks:**
- ✅ Structure - All required files
- ✅ Imports - No import errors
- ✅ Syntax - Valid Python

**Output:**
```
============================================================
Validating 3 Generated Scenarios
============================================================

--- my_scenario ---

=== Validation Results ===

✅ PASS structure: All required files present
✅ PASS imports: All imports valid
✅ PASS syntax: All Python syntax valid

✅ ALL CHECKS PASSED
```

## Testing Generated Scenarios

```bash
# Run generated scenario
python -m scenarios._test_generated.my_scenario --help

# With arguments
python -m scenarios._test_generated.my_scenario \
    --input test.txt \
    --output result.json
```

## Architecture

```
User Description
    ↓
[spec_generator.py]
    ↓
ScenarioSpec (JSON)
    ↓
[simple_generator.py]
    ↓
Generated Files
    ↓
[validation_pipeline.py]
    ↓
✅ Working Scenario
```

## Generator Comparison

### Template-Based (simple_generator.py)

**Pros:**
- ✅ Reliable and deterministic
- ✅ No API keys required
- ✅ Proven patterns
- ✅ Fast generation

**Cons:**
- ❌ Less flexible
- ❌ Can't adapt to edge cases
- ❌ Requires good specs

**Status:** ✅ Production Ready

### LLM-Based (backend_generator.py)

**Pros:**
- ✅ More flexible
- ✅ Context-aware
- ✅ Can handle edge cases
- ✅ Natural language input

**Cons:**
- ❌ Requires API keys
- ❌ Less predictable
- ❌ Slower
- ❌ Costs money

**Status:** 🚧 Implemented, not tested

## Best Practices

### Spec Design

1. **One stage = one responsibility**
2. **Clear stage names** (verbs: extract, analyze, generate)
3. **Explicit dependencies** (use depends_on)
4. **State fields** for important data
5. **Validation rules** on inputs

### Generated Code

1. **Keep TODOs visible** until implemented
2. **Add error handling** in stages
3. **Use ClaudeSession** for LLM operations
4. **Test incrementally** (stage by stage)
5. **Update README** with examples

### Workflow Choice

- **SINGLE_PASS:** Simple A → B transformations
- **MULTI_STAGE:** Complex pipelines with checkpoints
- **ITERATIVE:** Refinement loops with exit conditions

## Troubleshooting

### "Module not found" errors

Ensure you're in the venv:
```bash
source .venv/bin/activate
```

### Validation fails

Check the validation output for specific errors:
- Structure: Missing files
- Imports: Import errors
- Syntax: Python syntax errors

### Generated code won't run

1. Check validation passes
2. Implement TODO markers
3. Add required dependencies
4. Test with simple inputs first

## Examples

See `scenarios/_test_generated/` for complete working examples:

- **email_to_actions** - SINGLE_PASS workflow
- **report_generator** - MULTI_STAGE workflow
- **document_simplifier** - ITERATIVE workflow

All pass validation and are ready for implementation.

## Next Steps

1. **Generate more scenarios** from specs
2. **Implement stage logic** in generated code
3. **Test with real data**
4. **Integrate with web UI**
5. **Add frontend generation**

## Support

For questions or issues, see:
- `/Users/samule/repo/amplifier/SCENARIO_GENERATOR_COMPLETE.md` - Full documentation
- `.data/test_scenarios/` - Example specs
- `scenarios/_test_generated/` - Generated examples
