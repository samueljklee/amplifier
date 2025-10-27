"""Generation session management."""

import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add parent repo to path to import scenarios.scenario_generator
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import the UNIFIED ValidationStage (same as CLI)
from models.generation import ConversationMessage, GenerationEvent, GenerationStatus, MessageRole, SessionState
from models.scenario_spec import (
    InputSpec,
    InputType,
    OutputSpec,
    OutputType,
    ScenarioSpec,
    StageSpec,
    WorkflowType,
)

# Import the REAL scenario generator (single source of truth)
from scenarios.scenario_generator.incremental_generator import IncrementalGenerator  # noqa: E402
from scenarios.scenario_generator.stages import ValidationStage  # noqa: E402


class StreamCapture:
    """Captures stdout/stderr and processes lines in real-time."""

    def __init__(self: "StreamCapture", callback: callable, original_stream) -> None:  # type: ignore[valid-type]
        """Initialize stream capture.

        Args:
            callback: Function to call for each line
            original_stream: Original stdout/stderr stream
        """
        self.callback = callback
        self.original_stream = original_stream
        self.buffer = ""

    def write(self: "StreamCapture", text: str) -> int:
        """Write text and process complete lines.

        Args:
            text: Text to write

        Returns:
            Number of characters written
        """
        # Write to original stream for debugging
        self.original_stream.write(text)
        self.original_stream.flush()

        # Buffer incomplete lines
        self.buffer += text

        # Process complete lines
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            if line.strip():
                self.callback(line)

        return len(text)

    def flush(self: "StreamCapture") -> None:
        """Flush the stream."""
        self.original_stream.flush()
        # Process any remaining buffered content
        if self.buffer.strip():
            self.callback(self.buffer)
            self.buffer = ""


class GenerationSession:
    """Manages a scenario generation session."""

    def __init__(
        self: "GenerationSession", session_id: str, description: str, scenario_name: str | None = None
    ) -> None:
        """Initialize generation session.

        Args:
            session_id: Unique session ID
            description: User's description of what to build
            scenario_name: Optional scenario name
        """
        self.session_id = session_id
        self.description = description
        self.scenario_name = scenario_name or self._generate_name_from_description(description)
        self.state_dir = Path(".data/ultrathink/sessions") / session_id
        self.state_file = self.state_dir / "state.json"
        self.output_dir = self.state_dir / "generated"
        self.events: list[GenerationEvent] = []

        self.state = SessionState(
            id=session_id,
            status=GenerationStatus.ASKING_QUESTIONS,
            description=description,
            scenario_name=self.scenario_name,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self.questions = [
            "What inputs does your scenario need? (files, text, URLs, etc.)",
            "What should it output?",
            "Should it run once or iterate with user feedback?",
            "Any other requirements or constraints?",
        ]

        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._save_state()

    def _generate_name_from_description(self: "GenerationSession", description: str) -> str:
        """Generate a scenario name from description.

        Args:
            description: User's description

        Returns:
            Snake-case scenario name
        """
        words = description.lower().split()[:3]
        name = "_".join(w for w in words if w.isalnum())
        return name or "custom_scenario"

    def _save_state(self: "GenerationSession") -> None:
        """Save session state to disk."""
        self.state.updated_at = datetime.now()
        self.state_file.write_text(self.state.model_dump_json(indent=2))

    def _emit_event(self: "GenerationSession", event_type: str, message: str, data: dict | None = None) -> None:
        """Emit an event.

        Args:
            event_type: Type of event
            message: Event message
            data: Optional event data
        """
        event = GenerationEvent(type=event_type, timestamp=datetime.now(), message=message, data=data)
        self.events.append(event)

    def start_conversation(self: "GenerationSession") -> None:
        """Start the conversation by asking the first question."""
        self.state.conversation.append(
            ConversationMessage(role=MessageRole.SYSTEM, content=f"User wants to build: {self.description}")
        )

        if self.state.current_question_index < len(self.questions):
            question = self.questions[self.state.current_question_index]
            self.state.conversation.append(ConversationMessage(role=MessageRole.ASSISTANT, content=question))
            self._save_state()
            self._emit_event("conversation.question", question)

    def handle_user_response(self: "GenerationSession", response: str) -> bool:
        """Handle user response and ask next question or generate spec.

        Args:
            response: User's answer

        Returns:
            True if more questions remain, False if ready for spec generation
        """
        self.state.conversation.append(ConversationMessage(role=MessageRole.USER, content=response))
        self.state.current_question_index += 1
        self._save_state()

        if self.state.current_question_index < len(self.questions):
            question = self.questions[self.state.current_question_index]
            self.state.conversation.append(ConversationMessage(role=MessageRole.ASSISTANT, content=question))
            self._save_state()
            self._emit_event("conversation.question", question)
            return True
        else:
            self._emit_event("conversation.complete", "All questions answered")
            return False

    async def generate_spec(self: "GenerationSession") -> None:
        """Generate a spec from conversation history.

        For now, creates a simple single-stage scenario spec.
        Future: Use LLM to parse conversation into full spec.
        """
        self._emit_event("spec.generating", "Creating scenario specification from conversation...")

        await asyncio.sleep(0.5)

        spec = self._create_spec_from_conversation()
        self.state.spec_json = json.loads(spec.model_dump_json())
        self.state.status = GenerationStatus.SPEC_READY
        self._save_state()

        self._emit_event("spec.ready", "Specification ready for review", data={"spec": self.state.spec_json})

    def _create_spec_from_conversation(self: "GenerationSession") -> ScenarioSpec:
        """Create spec from conversation history.

        Returns:
            ScenarioSpec based on conversation answers
        """
        return self._create_basic_spec()

    def _create_basic_spec(self: "GenerationSession") -> ScenarioSpec:
        """Create a basic scenario spec from description.

        Returns:
            Basic ScenarioSpec
        """
        spec = ScenarioSpec(  # type: ignore[call-arg]
            name=self.scenario_name,
            display_name=self.scenario_name.replace("_", " ").title(),
            description=self.description,
            version="0.1.0",
            workflow_type=WorkflowType.SINGLE_PASS,
            inputs=[
                InputSpec(  # type: ignore[call-arg]
                    name="input_text",
                    type=InputType.TEXT,
                    description="Input text to process",
                    required=True,
                    cli_flag="--input",
                )
            ],
            outputs=[
                OutputSpec(  # type: ignore[call-arg]
                    name="output",
                    type=OutputType.TEXT,
                    description="Processed output",
                    default_path=f"{self.scenario_name}_output.txt",
                )
            ],
            stages=[
                StageSpec(  # type: ignore[call-arg]
                    name="process",
                    display_name="Process Input",
                    description="Process the input text",
                    module_name="processor",
                    class_name="Processor",
                    method_name="process",
                )
            ],
        )
        return spec

    def _process_log_line(self: "GenerationSession", line: str) -> None:
        """Process a single log line in real-time.

        Args:
            line: Log line to process
        """
        if not line.strip():
            return

        # Try to parse as JSON log entry
        try:
            log_entry = json.loads(line)
            # Emit as event
            self._emit_event(
                f"log.{log_entry.get('level', 'info').lower()}",
                log_entry.get("message", ""),
                data=log_entry,
            )
        except json.JSONDecodeError:
            # Not JSON, emit as plain log
            self._emit_event("log.info", line)

    async def generate_code(self: "GenerationSession") -> None:
        """Generate code using the unified scenario_generator (single source of truth).

        This uses the SAME generator as the CLI, ensuring:
        - pyproject.toml generation with dependencies
        - Automatic dependency installation via uv add
        - Makefile updates with scenario targets
        - Module-by-module incremental generation with validation
        """
        if not self.state.spec_json:
            raise ValueError("No spec available")

        self.state.status = GenerationStatus.GENERATING_CODE
        self._save_state()
        self._emit_event("code.generating", "Generating scenario code with unified generator...")

        # Convert web UI spec format to scenario_generator requirements format
        # The IncrementalGenerator expects a requirements dict with these keys:
        # - scenario_type, purpose, interactive, inputs, outputs, additional_notes
        requirements = self._convert_spec_to_requirements(self.state.spec_json)

        # Set environment variable to enable JSON logging
        import os

        original_env = os.environ.get("AMPLIFIER_WEB_UI")
        os.environ["AMPLIFIER_WEB_UI"] = "1"

        try:
            # Use the unified incremental generator (same as CLI)
            generator = IncrementalGenerator()

            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Capture logs in REAL-TIME by wrapping stdout/stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr

            try:
                # Create real-time stream captures
                sys.stdout = StreamCapture(self._process_log_line, old_stdout)
                sys.stderr = StreamCapture(self._process_log_line, old_stderr)

                # This will:
                # 1. Generate all Python modules
                # 2. Create pyproject.toml with dependencies
                # 3. Install dependencies via uv add
                # 4. Update Makefile
                # 5. Validate generated code
                # Logs stream in real-time via _process_log_line callback
                await generator.generate(requirements, self.output_dir)

            finally:
                # Restore stdout/stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            # Read generated files for storage
            generated_files = {}
            for file_path in self.output_dir.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(self.output_dir)
                    generated_files[str(rel_path)] = file_path.read_text()

            self.state.generated_files = generated_files
            self._save_state()

            self._emit_event(
                "code.generated",
                f"Generated {len(generated_files)} files with dependencies installed",
                data={"files": list(generated_files.keys())},
            )

        finally:
            # Restore original environment
            if original_env is None:
                os.environ.pop("AMPLIFIER_WEB_UI", None)
            else:
                os.environ["AMPLIFIER_WEB_UI"] = original_env

    def _convert_spec_to_requirements(self: "GenerationSession", spec_json: dict) -> dict:
        """Convert web UI spec format to scenario_generator requirements format.

        Args:
            spec_json: Web UI ScenarioSpec as dict

        Returns:
            Requirements dict for scenario_generator
        """
        spec = ScenarioSpec(**spec_json)

        return {
            "scenario_type": spec.display_name,
            "purpose": spec.description,
            "interactive": spec.workflow_type != WorkflowType.SINGLE_PASS,
            "inputs": [f"{inp.name} ({inp.type.value})" for inp in spec.inputs],
            "outputs": [f"{out.name} ({out.type.value})" for out in spec.outputs],
            "additional_notes": f"Workflow: {spec.workflow_type.value}. Stages: {', '.join(s.display_name for s in spec.stages)}",
        }

    async def validate(self: "GenerationSession") -> None:
        """Validate generated code using the unified ValidationStage (same as CLI).

        This uses the SAME validation as the CLI, which:
        - Runs make check on generated code
        - Auto-fixes errors using AI (up to 3 iterations)
        - Much more robust than simple syntax validation
        """
        if not self.output_dir.exists():
            raise ValueError("No generated code to validate")

        self.state.status = GenerationStatus.VALIDATING
        self._save_state()
        self._emit_event("validation.started", "Validating generated code with auto-fix...")

        # Capture logs during validation in REAL-TIME
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        try:
            # Create real-time stream captures
            sys.stdout = StreamCapture(self._process_log_line, old_stdout)
            sys.stderr = StreamCapture(self._process_log_line, old_stderr)

            # Use the unified ValidationStage (same as CLI)
            # Logs stream in real-time via _process_log_line callback
            validation_stage = ValidationStage(scenario_dir=self.output_dir, max_iterations=3)
            validation_result = await validation_stage.run()

        finally:
            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        # Convert ValidationResult to web UI format
        results = []
        if validation_result.success:
            results.append(
                {
                    "stage": "validation",
                    "passed": True,
                    "message": f"Validation passed after {validation_result.iterations} iteration(s)",
                    "details": {
                        "iterations": validation_result.iterations,
                        "duration_seconds": validation_result.total_duration_seconds,
                    },
                }
            )
        else:
            results.append(
                {
                    "stage": "validation",
                    "passed": False,
                    "message": f"Validation failed after {validation_result.iterations} iterations",
                    "details": {
                        "iterations": validation_result.iterations,
                        "error_count": len(validation_result.final_errors),
                        "errors": [
                            {
                                "file": str(err.file_path),
                                "line": err.line_number,
                                "message": err.message,
                                "code": err.code,
                            }
                            for err in validation_result.final_errors[:10]  # Limit to first 10
                        ],
                    },
                }
            )

        self.state.validation_results = results

        if validation_result.success:
            self.state.status = GenerationStatus.COMPLETE
            self._emit_event(
                "validation.passed", f"Validation passed after {validation_result.iterations} iteration(s)"
            )
        else:
            self.state.status = GenerationStatus.FAILED
            self._emit_event(
                "validation.failed", f"Validation failed with {len(validation_result.final_errors)} errors"
            )

        self._save_state()

    async def run_full_generation(self: "GenerationSession") -> None:
        """Run the complete generation pipeline."""
        try:
            await self.generate_spec()
            await self.generate_code()
            await self.validate()
        except Exception as e:
            self.state.status = GenerationStatus.FAILED
            self.state.error = str(e)
            self._save_state()
            self._emit_event("error", f"Generation failed: {e}")

    def get_state(self: "GenerationSession") -> SessionState:
        """Get current session state.

        Returns:
            Current session state
        """
        return self.state

    def get_events(self: "GenerationSession") -> list[GenerationEvent]:
        """Get all events.

        Returns:
            List of events
        """
        return self.events

    def get_files(self: "GenerationSession") -> dict[str, str]:
        """Get generated files.

        Returns:
            Dict of filename to content
        """
        if not self.state.generated_files:
            return {}

        return self.state.generated_files

    def install_scenario(self: "GenerationSession") -> bool:
        """Write generated files to scenarios/{name}/ directory.

        Returns:
            True if successful
        """
        if not self.state.generated_files:
            return False

        try:
            # Get scenarios directory from config
            from config import settings

            scenarios_dir = Path(settings.scenarios_path)
            target_dir = scenarios_dir / self.scenario_name

            # Create target directory
            target_dir.mkdir(parents=True, exist_ok=True)

            # Write all generated files
            for file_path_str, content in self.state.generated_files.items():
                # Get relative path (remove the generated output dir prefix)
                file_path = Path(file_path_str)

                # If it's an absolute path within output_dir, make it relative
                if file_path.is_absolute():
                    try:
                        file_path = file_path.relative_to(self.output_dir)
                    except ValueError:
                        # If not within output_dir, just use the filename
                        file_path = Path(file_path.name)

                target_file = target_dir / file_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(content)

            return True

        except Exception as e:
            # Log error but don't raise
            print(f"Error installing scenario: {e}")
            return False

    @staticmethod
    def load(session_id: str) -> "GenerationSession | None":
        """Load existing session from disk.

        Args:
            session_id: Session ID to load

        Returns:
            GenerationSession or None if not found
        """
        state_file = Path(".data/ultrathink/sessions") / session_id / "state.json"
        if not state_file.exists():
            return None

        state_data = json.loads(state_file.read_text())
        state = SessionState(**state_data)

        session = GenerationSession.__new__(GenerationSession)
        session.session_id = session_id
        session.description = state.description
        session.scenario_name = state.scenario_name or "unnamed"
        session.state_dir = Path(".data/ultrathink/sessions") / session_id
        session.state_file = state_file
        session.output_dir = session.state_dir / "generated"
        session.state = state
        session.events = []

        return session


class GenerationSessionManager:
    """Manages multiple generation sessions."""

    def __init__(self: "GenerationSessionManager") -> None:
        """Initialize session manager."""
        self.sessions: dict[str, GenerationSession] = {}

    def create_session(
        self: "GenerationSessionManager", description: str, name: str | None = None
    ) -> GenerationSession:
        """Create a new generation session.

        Args:
            description: User's description
            name: Optional scenario name

        Returns:
            New GenerationSession
        """
        session_id = str(uuid.uuid4())
        session = GenerationSession(session_id, description, name)
        self.sessions[session_id] = session
        return session

    def get_session(self: "GenerationSessionManager", session_id: str) -> GenerationSession | None:
        """Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            GenerationSession or None if not found
        """
        if session_id in self.sessions:
            return self.sessions[session_id]

        session = GenerationSession.load(session_id)
        if session:
            self.sessions[session_id] = session
        return session
