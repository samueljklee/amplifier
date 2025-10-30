# How to Create Your Own Multi-Stage Research Tool

This guide teaches you how to build sophisticated multi-stage research assistants like this one.

## Architecture Overview

The research assistant follows a **multi-stage pipeline architecture** with:

1. **State Management** - Tracks progress and enables resumability
2. **Stage Modules** - Self-contained processing units
3. **Pipeline Orchestrator** - Coordinates stage execution
4. **CLI Interface** - User interaction layer

## Key Design Patterns

### Pattern 1: State Management with Resume Capability

Every operation saves state immediately, enabling interruption and resumption.

**Implementation:**

```python
# state.py
@dataclass
class PipelineState:
    session_dir: Path
    current_phase: str = "initialized"
    completed_phases: list[str] = field(default_factory=list)
    # ... other fields

class StateManager:
    def __init__(self, session_dir: Path | None = None):
        if session_dir is None:
            # Create new session with timestamp + GUID
            session_dir = Path(f".data/tool/sessions/{timestamp}_{guid}")
        else:
            # Resume from existing session
            self.state = PipelineState.from_dict(read_json(state_file))
    
    def save(self):
        write_json_with_retry(self.state.to_dict(), self.state_file)
```

**Key Benefits:**
- Automatic recovery from interruptions
- Session isolation (each run in its own directory)
- Complete audit trail

### Pattern 2: Stage Modules

Each stage is a self-contained module with clear inputs/outputs.

**Structure:**
```
stage_name/
├── __init__.py      # Exports public interface
└── core.py          # Implementation
```

**Template:**

```python
# stage_name/core.py
from amplifier.ccsdk_toolkit import ClaudeSession, SessionOptions
from ..state import StateManager

class StageName:
    async def run(self, state_manager: StateManager) -> None:
        """Execute this stage.
        
        Args:
            state_manager: State manager for saving progress
        """
        # 1. Load previous stage outputs
        previous_data = state_manager.state.previous_output
        
        # 2. Process with Claude
        options = SessionOptions(
            system_prompt=self._get_system_prompt(),
            model="claude-sonnet-4-5-20250929",
        )
        
        async with ClaudeSession(options) as claude:
            result = await claude.query(f"Process: {previous_data}")
        
        # 3. Save results
        state_manager.state.current_output = result.content
        state_manager.save()
        
        # 4. Update phase
        state_manager.update_phase("next_phase")
```

### Pattern 3: Pipeline Orchestrator

Coordinates execution across all stages.

```python
# pipeline.py
class ResearchPipeline:
    def __init__(self, state_manager: StateManager):
        self.state = state_manager
    
    async def run(self) -> bool:
        # Execute stages based on current phase
        phase = self.state.state.current_phase
        
        if phase == "initialized":
            await self._phase_1()
            phase = self.state.state.current_phase
        
        if phase == "phase_1_complete":
            await self._phase_2()
            phase = self.state.state.current_phase
        
        # ... continue for all phases
        
        return phase == "complete"
```

### Pattern 4: CLI with Resume Support

```python
# main.py
@click.command()
@click.option("--question", help="Research question")
@click.option("--session-dir", help="Resume from session")
@add_describe_flag
def main(question: str | None, session_dir: Path | None):
    # Validate inputs
    if not session_dir and not question:
        logger.error("Either --question or --session-dir required")
        sys.exit(1)
    
    # Initialize or resume
    state_mgr = StateManager(session_dir)
    if question and not state_mgr.state.research_question_input:
        state_mgr.state.research_question_input = question
        state_mgr.save()
    
    # Run pipeline
    pipeline = ResearchPipeline(state_mgr)
    success = await pipeline.run()
```

## Building Your Own Tool

### Step 1: Define Your Stages

Map out your workflow:

```
1. Input Processing → Clean and validate input
2. Analysis → Extract insights
3. Synthesis → Combine findings
4. Output Generation → Create deliverable
```

### Step 2: Create State Model

Define what data flows between stages:

```python
@dataclass
class MyToolState:
    session_dir: Path
    current_phase: str = "initialized"
    completed_phases: list[str] = field(default_factory=list)
    
    # Stage outputs
    processed_input: dict | None = None
    analysis_results: list[dict] = field(default_factory=list)
    synthesis: str | None = None
    final_output: str | None = None
```

### Step 3: Implement Each Stage

For each stage:

1. Create directory: `mkdir -p my_tool/stage_name`
2. Add `__init__.py` with exports
3. Implement `core.py` with stage logic
4. Use ClaudeSession for AI reasoning
5. Save results to state after each operation

### Step 4: Create Pipeline Orchestrator

```python
class MyToolPipeline:
    async def run(self):
        if phase == "initialized":
            await self._stage_1()
        if phase == "stage_1_complete":
            await self._stage_2()
        # ... continue
```

### Step 5: Add CLI Interface

```python
@add_describe_flag(
    version="1.0",
    display_name="My Tool",
    description="Tool description"
)
@click.command()
@click.option("--input", required=False)
@click.option("--session-dir", default=None)
def main(input: str | None, session_dir: Path | None):
    # Initialize and run
```

## Advanced Patterns

### User Feedback Loops

For stages that need user input:

```python
async def _stage_with_feedback(self):
    # Generate draft
    draft = await self._generate_draft()
    
    # Save and show to user
    self.state.state.draft = draft
    self.state.save()
    logger.info(f"Draft ready at: {self.state.session_dir}/draft.md")
    
    # Wait for user feedback (they edit the file or provide input)
    feedback = input("Provide feedback (or press Enter to continue): ")
    
    if feedback:
        # Incorporate feedback
        revised = await self._revise_with_feedback(draft, feedback)
        self.state.state.final_version = revised
    else:
        self.state.state.final_version = draft
    
    self.state.save()
```

### Web Research Integration

Using browser-use MCP server:

```python
async def _web_research_stage(self):
    # Use MCP tools for web browsing
    options = SessionOptions(
        system_prompt="You are a web researcher",
        model="claude-sonnet-4-5-20250929",
        allowed_tools=["mcp__browser-use__*"],
    )
    
    async with ClaudeSession(options) as claude:
        result = await claude.query(
            f"Research this topic on the web: {self.state.state.topic}"
        )
    
    # Save findings
    self.state.state.web_findings = parse_llm_json(result.content)
    self.state.save()
```

### Parallel Processing

Process multiple items in parallel:

```python
async def _batch_analysis_stage(self):
    items = self.state.state.items_to_analyze
    
    # Process in parallel
    tasks = [self._analyze_single(item) for item in items]
    results = await asyncio.gather(*tasks)
    
    # Save results
    self.state.state.analysis_results = results
    self.state.save()
```

## Testing Your Tool

### Basic Test

```python
# test_my_tool.py
def test_basic_flow():
    state_mgr = StateManager()
    state_mgr.state.input = "test input"
    
    pipeline = MyToolPipeline(state_mgr)
    result = await pipeline.run()
    
    assert result == True
    assert state_mgr.state.final_output is not None
```

### Resume Test

```python
def test_resume_capability():
    # Start first session
    state_mgr1 = StateManager()
    state_mgr1.state.input = "test"
    # ... run partially
    
    # Resume from same directory
    state_mgr2 = StateManager(session_dir=state_mgr1.session_dir)
    assert state_mgr2.state.current_phase == state_mgr1.state.current_phase
```

## Common Pitfalls

### ❌ Don't: Lose State on Error

```python
# Bad - state lost if error occurs
result = await process()
self.state.save()  # Never reached if process() throws
```

```python
# Good - state saved even on error
try:
    result = await process()
    self.state.result = result
finally:
    self.state.save()
```

### ❌ Don't: Skip Phase Tracking

```python
# Bad - can't resume properly
await self._stage_1()
await self._stage_2()
```

```python
# Good - track completion
await self._stage_1()
self.state.update_phase("stage_1_complete")

if self.state.current_phase == "stage_1_complete":
    await self._stage_2()
    self.state.update_phase("stage_2_complete")
```

### ❌ Don't: Hardcode Paths

```python
# Bad
output_file = "/tmp/output.txt"
```

```python
# Good
output_file = self.state.session_dir / "output.txt"
```

## Next Steps

1. **Study this implementation** - Read through all modules
2. **Modify for your needs** - Adapt stages to your workflow
3. **Add custom stages** - Create specialized processing steps
4. **Test thoroughly** - Validate resume capability
5. **Document well** - Help others understand your tool

## Resources

- [blog_writer](../blog_writer/) - Another exemplar tool
- [CCSDK Developer Guide](../../amplifier/ccsdk_toolkit/DEVELOPER_GUIDE.md) - API reference
- [Implementation Philosophy](../../ai_context/IMPLEMENTATION_PHILOSOPHY.md) - Design principles

## Questions?

- Check existing tools for patterns
- Read DISCOVERIES.md for known issues
- Experiment with small modifications first
