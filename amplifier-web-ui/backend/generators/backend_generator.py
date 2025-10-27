"""
Backend Code Generator

Generates Python scenario code from ScenarioSpec.
Creates complete, working scenario implementations following Amplifier patterns.
"""

import os
from pathlib import Path

from models.scenario_spec import (
    ScenarioSpec,
    StageSpec,
)
from pydantic_ai import Agent


class BackendGenerator:
    """Generates Python scenario code from specifications."""

    def __init__(self: "BackendGenerator") -> None:
        """Initialize the backend generator."""
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

        self.agent: Agent[None, str] = Agent(
            model=model,  # type: ignore[call-arg]
            system_prompt=self._build_system_prompt(),
        )

    def _build_system_prompt(self: "BackendGenerator") -> str:
        """Build the system prompt for code generation."""
        return """You are an expert Python code generator for the Amplifier AI agent toolkit.

You generate complete, working scenario implementations that follow these patterns:

STRUCTURE:
```
scenario_name/
├── __init__.py
├── __main__.py
├── main.py          # CLI and orchestration
├── state.py         # State management
├── stage1/
│   ├── __init__.py
│   └── core.py
├── stage2/
│   ├── __init__.py
│   └── core.py
└── README.md
```

KEY PATTERNS:

1. **Logging**:
```python
from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.logger import LogFormat
import os

log_format = LogFormat.JSON if os.getenv("AMPLIFIER_WEB_UI") else LogFormat.PLAIN
logger = ToolkitLogger(name="scenario_name", format=log_format)
```

2. **State Management**:
```python
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
import json

@dataclass
class State:
    stage: str = "initialized"
    iteration: int = 0
    # Add custom fields here

class StateManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.base_dir / "state.json"
        self.state = self._load()

    def _load(self) -> State:
        if self.path.exists():
            data = json.loads(self.path.read_text())
            return State(**data)
        return State()

    def save(self):
        self.path.write_text(json.dumps(asdict(self.state), indent=2))
```

3. **Stage Implementation**:
```python
from pydantic_ai import Agent

class StageNameProcessor:
    def __init__(self):
        self.agent = Agent(
            model="openai:gpt-4o",
            result_type=str,  # or specific model
            system_prompt="Your specialized prompt"
        )

    async def process(self, input_data: str) -> str:
        result = await self.agent.run(input_data)
        return result.data
```

4. **Main Orchestrator** (MULTI_STAGE):
```python
class Pipeline:
    def __init__(self, state_manager: StateManager):
        self.state = state_manager
        self.stage1 = Stage1Processor()
        self.stage2 = Stage2Processor()

    async def run(self, inputs) -> bool:
        stage = self.state.state.stage

        if stage == "initialized":
            await self._stage1()
        if stage == "stage1_complete":
            await self._stage2()

        return True

    async def _stage1(self):
        logger.info("Stage 1: Processing...")
        result = await self.stage1.process(data)
        self.state.state.stage = "stage1_complete"
        self.state.save()
```

5. **Main Orchestrator** (ITERATIVE):
```python
class Pipeline:
    async def run(self, inputs) -> bool:
        while self.state.state.iteration < MAX_ITERATIONS:
            await self._iteration()

            # Check exit condition
            if self.state.state.approved:
                break

            self.state.state.iteration += 1
            self.state.save()

        return True
```

6. **CLI with Click**:
```python
import click

@click.command()
@click.option("--input", type=click.Path(exists=True), required=True)
@click.option("--output", type=click.Path(), required=True)
def main(input: str, output: str):
    state_dir = Path(".data/scenario_name")
    state_manager = StateManager(state_dir)

    pipeline = Pipeline(state_manager)
    success = asyncio.run(pipeline.run(Path(input), Path(output)))

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
```

CRITICAL RULES:
- Use async/await for all LLM operations
- Import ToolkitLogger, not standard logging
- Check AMPLIFIER_WEB_UI env var for log format
- Save state after each stage
- Use dataclasses for state, not Pydantic
- Use Path objects for file operations
- Return bool from run() method
- Add docstrings to all classes/methods
- Follow blog_writer pattern exactly

Generate clean, working, production-ready code."""

    async def generate_code(self: "BackendGenerator", spec: ScenarioSpec, output_dir: Path) -> dict[str, str]:
        """Generate complete backend code for a scenario.

        Args:
            spec: ScenarioSpec to generate code from
            output_dir: Directory to write generated files

        Returns:
            Dict mapping file paths to generated content
        """
        files: dict[str, str] = {}

        files["__init__.py"] = self._generate_init(spec)
        files["__main__.py"] = self._generate_main_entry(spec)
        files["README.md"] = await self._generate_readme(spec)
        files["state.py"] = self._generate_state_manager(spec)
        files["main.py"] = await self._generate_main_orchestrator(spec)

        for stage in spec.stages:
            stage_files = await self._generate_stage_module(spec, stage)
            for path, content in stage_files.items():
                files[path] = content

        for file_path, content in files.items():
            full_path = output_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        return files

    def _generate_init(self: "BackendGenerator", spec: ScenarioSpec) -> str:
        """Generate __init__.py."""
        return f'''"""
{spec.display_name}

{spec.description}
"""

__version__ = "{spec.version}"
'''

    def _generate_main_entry(self: "BackendGenerator", spec: ScenarioSpec) -> str:
        """Generate __main__.py entry point."""
        return f'''"""Entry point for running {spec.display_name} as a module."""

from .main import main

if __name__ == "__main__":
    main()
'''

    def _generate_state_manager(self: "BackendGenerator", spec: ScenarioSpec) -> str:
        """Generate state.py."""
        state_fields = "\n    ".join([f'{field}: str = ""' for field in spec.state_management.state_fields])

        return f'''"""State management for {spec.name}."""

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
import json


@dataclass
class State:
    """Scenario state."""

    stage: str = "initialized"
    iteration: int = 0
    {state_fields if state_fields else "# No additional state fields"}


class StateManager:
    """Manages scenario state persistence."""

    def __init__(self: "StateManager", base_dir: Path) -> None:
        """Initialize state manager.

        Args:
            base_dir: Base directory for state files
        """
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.base_dir / "state.json"
        self.state = self._load()

    def _load(self: "StateManager") -> State:
        """Load state from disk."""
        if self.path.exists():
            data = json.loads(self.path.read_text())
            return State(**data)
        return State()

    def save(self: "StateManager") -> None:
        """Save state to disk."""
        self.path.write_text(json.dumps(asdict(self.state), indent=2))

    def reset(self: "StateManager") -> None:
        """Reset state to initial values."""
        self.state = State()
        self.save()
'''

    async def _generate_readme(self: "BackendGenerator", spec: ScenarioSpec) -> str:
        """Generate README.md."""
        inputs_section = "\n".join([f"- `--{inp.name}`: {inp.description}" for inp in spec.inputs])

        stages_section = "\n".join(
            [f"{i + 1}. **{stage.display_name}**: {stage.description}" for i, stage in enumerate(spec.stages)]
        )

        return f"""# {spec.display_name}

{spec.description}

## Usage

```bash
python -m scenarios.{spec.name} [OPTIONS]
```

## Options

{inputs_section}

## Workflow

{stages_section}

## Output

{", ".join([out.description for out in spec.outputs])}

## State Management

State is automatically saved to `.data/{spec.name}/` directory.
The tool can resume from the last completed stage if interrupted.
"""

    async def _generate_main_orchestrator(self: "BackendGenerator", spec: ScenarioSpec) -> str:
        """Generate main.py orchestrator.

        This uses the LLM to generate context-aware orchestration code.
        """
        prompt = f"""Generate the main.py orchestrator for this scenario:

Spec:
{spec.model_dump_json()}

Requirements:
1. Import all stage modules
2. Create Pipeline class with StateManager
3. Implement workflow based on type: {spec.workflow_type.value}
4. Add Click CLI with all inputs as options
5. Use ToolkitLogger with web UI format detection
6. Save state after each stage
7. Handle errors gracefully

Follow the system prompt patterns EXACTLY.
Return ONLY the Python code, no explanations."""

        result = await self.agent.run(prompt)
        return result.data if hasattr(result, "data") else str(result)  # type: ignore[attr-defined]

    async def _generate_stage_module(self: "BackendGenerator", spec: ScenarioSpec, stage: StageSpec) -> dict[str, str]:
        """Generate a stage module.

        Args:
            spec: Overall scenario spec
            stage: Stage specification

        Returns:
            Dict of file paths to content for this stage
        """
        module_dir = f"{stage.module_name}/"

        init_content = f'''"""
{stage.display_name}

{stage.description}
"""

from .core import {stage.class_name}

__all__ = ["{stage.class_name}"]
'''

        prompt = f"""Generate the core.py implementation for this stage:

Stage: {stage.display_name}
Description: {stage.description}
Module: {stage.module_name}
Class: {stage.class_name}
Method: {stage.method_name}

Overall scenario context:
{spec.description}

Input: {", ".join([inp.description for inp in spec.inputs])}
Output: {", ".join([out.description for out in spec.outputs])}

Requirements:
1. Create {stage.class_name} class
2. Implement {stage.method_name} async method
3. Use PydanticAI Agent for LLM operations
4. Return appropriate type (str, dict, list, etc.)
5. Add comprehensive docstrings
6. Include error handling

Follow the system prompt patterns EXACTLY.
Return ONLY the Python code, no explanations."""

        core_result = await self.agent.run(prompt)
        core_content = core_result.data if hasattr(core_result, "data") else str(core_result)  # type: ignore[attr-defined]

        return {f"{module_dir}__init__.py": init_content, f"{module_dir}core.py": core_content}
