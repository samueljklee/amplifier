"""Process manager for executing Amplifier CLI scenarios."""

import asyncio
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from models.events import (
    AgentCompleteEvent,
    AgentProgressEvent,
    AgentStartEvent,
    ExecutionCompleteEvent,
    ExecutionErrorEvent,
    FileCreatedEvent,
    FileUpdatedEvent,
    InteractivePromptEvent,
    LogEvent,
    PreviewAvailableEvent,
    ProgressEvent,
    StageTransitionEvent,
    StreamOutputEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from models.execution import Execution, ExecutionStatus
from services.execution_store import ExecutionStore


class ProcessManager:
    """Manages CLI process execution and event streaming."""

    # Scenario ID to Make target mapping (for scenarios where they differ)
    SCENARIO_MAKE_TARGET_MAP = {
        "blog_writer": "blog-write",
        "article_illustrator": "illustrate",
        "tips_synthesizer": "tips-synthesizer",
        "transcribe": "transcribe",
        "web_to_md": "web-to-md",
    }

    # Parameter name mappings for Makefile (param_name -> MAKE_VAR)
    PARAMETER_NAME_MAP = {
        "blog_writer": {
            "writings_dir": "WRITINGS",
            "instructions": "INSTRUCTIONS",
        }
    }

    def __init__(self) -> None:
        self.executions: dict[str, Execution] = {}
        self.processes: dict[str, asyncio.subprocess.Process] = {}
        self.events: dict[str, list[Any]] = {}  # Track events separately from execution model
        self.websocket_connections: dict[str, list[Any]] = {}  # WebSocket connections per execution
        self.temp_dirs: dict[str, Path] = {}  # Track temp directories created for inline content
        self.pending_prompts: dict[str, dict[str, Any]] = {}  # Track pending interactive prompts
        self.execution_store = ExecutionStore()  # Persistence store
        self.session_dirs: dict[str, str] = {}  # Track session directory per execution
        self._scenario_discovery_service = None  # Lazy-loaded discovery service

    async def execute_scenario(self, scenario_id: str, parameters: dict[str, Any]) -> str:
        """Start scenario execution and return execution ID."""
        execution_id = str(uuid.uuid4())

        # Track temp directories for cleanup
        temp_dir = self._find_temp_dir(parameters)
        if temp_dir:
            self.temp_dirs[execution_id] = temp_dir

        # Create execution record
        execution = Execution(
            id=execution_id,
            scenario_id=scenario_id,
            parameters=parameters,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(),
        )
        self.executions[execution_id] = execution

        # Start process in background
        asyncio.create_task(self._run_process(execution_id, scenario_id, parameters))

        return execution_id

    def _find_temp_dir(self, parameters: dict[str, Any]) -> Optional[Path]:
        """Find temp directory from parameters for cleanup.

        Extracts the UUID-based temp directory from any parameter paths.
        E.g., /tmp/amplifier_scenario_inputs/{uuid}/file.md -> /tmp/amplifier_scenario_inputs/{uuid}
        E.g., /tmp/amplifier_scenario_inputs/{uuid}/dir -> /tmp/amplifier_scenario_inputs/{uuid}
        """
        for value in parameters.values():
            if isinstance(value, str) and value.startswith("/tmp/amplifier_scenario_inputs/"):
                path_parts = Path(value).parts
                # Find the UUID directory (index 3 after /, tmp, amplifier_scenario_inputs)
                if len(path_parts) >= 4:
                    return Path("/tmp/amplifier_scenario_inputs") / path_parts[3]
        return None

    def _find_session_dir(self, execution_id: str, scenario_id: str) -> Optional[str]:
        """Find scenario session directory from events.

        Args:
            execution_id: Execution ID
            scenario_id: Scenario ID

        Returns:
            Relative path to session directory or None
        """
        # Look for file.created events that indicate session directory
        for event in self.events.get(execution_id, []):
            if hasattr(event, "type") and event.type == "file.created":
                path = getattr(event, "path", "")
                # Extract session directory from draft path
                # E.g., ".data/blog_post_writer/20251022_220236/draft_iter_1.md" -> ".data/blog_post_writer/20251022_220236"
                if scenario_id == "blog_writer" and "blog_post_writer" in path:
                    parts = Path(path).parts
                    # Find blog_post_writer and take one more level
                    for i, part in enumerate(parts):
                        if part == "blog_post_writer" and i + 1 < len(parts):
                            session_dir = str(Path(*parts[: i + 2]))
                            return session_dir
        return None

    async def _run_process(self, execution_id: str, scenario_id: str, parameters: dict[str, Any]) -> None:
        """Run CLI process and emit events."""
        execution = self.executions[execution_id]

        try:
            # Build make command
            cmd = self._build_command(scenario_id, parameters)

            # Start process with environment variable for web UI detection
            import os

            env = os.environ.copy()
            env["AMPLIFIER_WEB_UI"] = "true"

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,  # Enable stdin for interactive prompts
                cwd=str(Path(__file__).parent.parent.parent.parent),
                env=env,
            )
            self.processes[execution_id] = process

            # Stream output
            await self._stream_output(execution_id, process)

            # Wait for completion
            exit_code = await process.wait()

            # Update execution
            execution.status = ExecutionStatus.COMPLETED if exit_code == 0 else ExecutionStatus.FAILED
            execution.completed_at = datetime.now()
            execution.exit_code = exit_code

            # Emit completion event
            await self._emit_event(
                execution_id,
                ExecutionCompleteEvent(
                    type="execution.complete",
                    execution_id=execution_id,
                    status=execution.status.value,
                    exit_code=exit_code,
                ),
            )

            # Persist completed executions
            if execution.status == ExecutionStatus.COMPLETED:
                session_dir = self._find_session_dir(execution_id, execution.scenario_id)
                self.execution_store.save_execution(execution, self.events.get(execution_id, []), session_dir)

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.completed_at = datetime.now()
            execution.error = str(e)

            await self._emit_event(
                execution_id,
                ExecutionErrorEvent(type="execution.error", execution_id=execution_id, error=str(e)),
            )

        finally:
            # Clean up temp directory for inline content
            await self._cleanup_temp_dir(execution_id)

    async def _cleanup_temp_dir(self, execution_id: str) -> None:
        """Clean up temporary directory created for inline content."""
        import shutil

        if execution_id in self.temp_dirs:
            temp_dir = self.temp_dirs[execution_id]
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"⚠️ Failed to clean up temp directory {temp_dir}: {e}")
            finally:
                del self.temp_dirs[execution_id]

    def _build_command(self, scenario_id: str, parameters: dict[str, Any]) -> list[str]:
        """Build command from scenario and parameters.

        Tries direct CLI invocation first (contract-based), falls back to Makefile.
        """
        # Check if this scenario should use Makefile (legacy scenarios)
        if scenario_id in self.SCENARIO_MAKE_TARGET_MAP:
            return self._build_makefile_command(scenario_id, parameters)

        # Default: Build direct CLI command (contract-based)
        cmd = ["uv", "run", "python", "-m", f"scenarios.{scenario_id}"]

        for key, value in parameters.items():
            if value is not None and value != "":
                # Convert parameter to CLI flag
                flag = f"--{key.replace('_', '-')}"
                cmd.append(flag)
                cmd.append(str(value))

        print(f"🔧 Built command: {' '.join(cmd)}")
        return cmd

    def _build_makefile_command(self, scenario_id: str, parameters: dict[str, Any]) -> list[str]:
        """Build make command for legacy scenarios."""
        make_target = self.SCENARIO_MAKE_TARGET_MAP.get(scenario_id, scenario_id.replace("_", "-"))
        cmd = ["make", make_target]

        # Get parameter name mapping for this scenario
        param_map = self.PARAMETER_NAME_MAP.get(scenario_id, {})

        for key, value in parameters.items():
            if value is not None:
                # Use mapped name if available, otherwise uppercase the key
                make_var = param_map.get(key, key.upper())
                cmd.append(f"{make_var}={value}")

        print(f"🔧 Built Makefile command: {' '.join(cmd)}")
        return cmd

    async def _stream_output(self, execution_id: str, process: asyncio.subprocess.Process) -> None:
        """Stream process output and parse into events."""
        if not process.stdout or not process.stderr:
            return

        async def read_stream(stream: asyncio.StreamReader, stream_name: str):
            """Read from a stream and emit events."""
            async for line in stream:
                try:
                    text = line.decode().strip()
                    if not text:
                        continue

                    # Parse line for agent activity
                    event = self._parse_line(execution_id, text)
                    if event:
                        await self._emit_event(execution_id, event)

                except Exception as e:
                    # Log parsing error but continue
                    await self._emit_event(
                        execution_id,
                        LogEvent(
                            type="log",
                            execution_id=execution_id,
                            level="error",
                            message=f"Parse error ({stream_name}): {e}",
                        ),
                    )

        # Read both stdout and stderr concurrently
        await asyncio.gather(
            read_stream(process.stdout, "stdout"), read_stream(process.stderr, "stderr"), return_exceptions=True
        )

    def _parse_line(self, execution_id: str, line: str) -> Optional[Any]:
        """Parse CLI output line into event."""
        # Try to parse as JSON first (structured output)
        if line.startswith("{"):
            try:
                data = json.loads(line)
                return self._parse_json_event(execution_id, data)
            except json.JSONDecodeError:
                pass

        # Parse agent activity patterns
        # Example: "[Agent: writer] Starting draft..."
        agent_match = re.search(r"\[Agent:\s*(\w+)\]\s*(.+)", line)
        if agent_match:
            agent_name = agent_match.group(1)
            message = agent_match.group(2)

            if "starting" in message.lower() or "begin" in message.lower():
                return AgentStartEvent(
                    type="agent.start",
                    execution_id=execution_id,
                    agent=agent_name,
                    message=message,
                )
            elif "complete" in message.lower() or "done" in message.lower():
                return AgentCompleteEvent(
                    type="agent.complete",
                    execution_id=execution_id,
                    agent=agent_name,
                    message=message,
                )
            else:
                return AgentProgressEvent(
                    type="agent.progress",
                    execution_id=execution_id,
                    agent=agent_name,
                    message=message,
                )

        # Default: log event
        return LogEvent(type="log", execution_id=execution_id, level="info", message=line)

    def _parse_json_event(self, execution_id: str, data: dict[str, Any]) -> Any:
        """Parse structured JSON event."""
        # Check if this is a ToolkitLogger structured event (uses 'context' field)
        context = data.get("context", {})
        metadata = data.get("metadata", {})  # Legacy support

        # Prefer context over metadata (context is what ToolkitLogger uses)
        event_metadata = context if context else metadata
        event_type = event_metadata.get("event_type")

        if event_type:
            return self._parse_toolkit_event(execution_id, data, event_metadata, event_type)

        # Fall back to legacy event parsing
        event_type = data.get("type", "log")

        if event_type == "agent.start":
            return AgentStartEvent(
                type="agent.start",
                execution_id=execution_id,
                agent=data["agent"],
                message=data.get("message", ""),
            )
        elif event_type == "agent.progress":
            return AgentProgressEvent(
                type="agent.progress",
                execution_id=execution_id,
                agent=data["agent"],
                message=data.get("message", ""),
                progress=data.get("progress"),
            )
        elif event_type == "agent.complete":
            return AgentCompleteEvent(
                type="agent.complete",
                execution_id=execution_id,
                agent=data["agent"],
                message=data.get("message", ""),
                result=data.get("result"),
            )
        else:
            return LogEvent(
                type="log",
                execution_id=execution_id,
                level=data.get("level", "info"),
                message=data.get("message", str(data)),
            )

    def _parse_toolkit_event(
        self, execution_id: str, data: dict[str, Any], metadata: dict[str, Any], event_type: str
    ) -> Any:
        """Parse ToolkitLogger structured event."""
        message = data.get("message", "")

        if event_type == "progress":
            return ProgressEvent(
                type="progress",
                execution_id=execution_id,
                message=message,
                current=metadata.get("progress_current", 0),
                total=metadata.get("progress_total", 100),
                percent=metadata.get("progress_percent", 0),
                metadata=metadata,
            )
        elif event_type == "file.created":
            # Track session directory from draft file paths
            file_path = metadata.get("file_path", "")
            if "blog_post_writer" in file_path and execution_id not in self.session_dirs:
                # Extract session dir from path like ".data/blog_post_writer/20251023_002817/draft_iter_1.md"
                parts = Path(file_path).parts
                for i, part in enumerate(parts):
                    if part == "blog_post_writer" and i + 1 < len(parts):
                        session_dir = str(Path(*parts[: i + 2]))
                        self.session_dirs[execution_id] = session_dir
                        print(f"🔍 DEBUG: Tracked session dir for {execution_id}: {session_dir}")
                        break

            return FileCreatedEvent(
                type="file.created",
                execution_id=execution_id,
                path=metadata.get("file_path", ""),
                metadata=metadata.get("file_metadata"),
                timestamp=datetime.now().isoformat(),
            )
        elif event_type == "file.updated":
            return FileUpdatedEvent(
                type="file.updated",
                execution_id=execution_id,
                path=metadata.get("file_path", ""),
                metadata=metadata.get("file_metadata"),
            )
        elif event_type == "interactive.prompt":
            # Track this as a pending prompt
            prompt_id = str(uuid.uuid4())
            self.pending_prompts[execution_id] = {
                "prompt_id": prompt_id,
                "timestamp": datetime.now().timestamp(),
                "prompt_data": {
                    "prompt_text": metadata.get("prompt_text", message),
                    "prompt_type": metadata.get("prompt_type", "text"),
                    "prompt_options": metadata.get("prompt_options", []),
                },
            }

            return InteractivePromptEvent(
                type="interactive.prompt",
                execution_id=execution_id,
                prompt_text=metadata.get("prompt_text", message),
                prompt_type=metadata.get("prompt_type", "text"),
                prompt_options=metadata.get("prompt_options", []),
                timestamp=datetime.now().isoformat(),
            )
        elif event_type == "stage.transition":
            return StageTransitionEvent(
                type="stage.transition",
                execution_id=execution_id,
                from_stage=metadata.get("from_stage"),
                to_stage=metadata.get("to_stage"),  # Can be None
                estimated_duration=metadata.get("estimated_duration"),
                timestamp=datetime.now().isoformat(),
            )
        elif event_type == "preview.available":
            return PreviewAvailableEvent(
                type="preview.available",
                execution_id=execution_id,
                preview_type=metadata.get("preview_type", "text"),
                preview_data=metadata.get("preview_data"),
                metadata=metadata,
            )
        elif event_type == "stream.output":
            return StreamOutputEvent(
                type="stream.output",
                execution_id=execution_id,
                text=metadata.get("text", ""),
                source=metadata.get("source", "assistant"),
                timestamp=datetime.now().isoformat(),
            )
        elif event_type == "tool.call":
            return ToolCallEvent(
                type="tool.call",
                execution_id=execution_id,
                tool_name=metadata.get("tool_name", ""),
                tool_input=metadata.get("tool_input"),
                tool_use_id=metadata.get("tool_use_id"),
                timestamp=datetime.now().isoformat(),
            )
        elif event_type == "tool.result":
            return ToolResultEvent(
                type="tool.result",
                execution_id=execution_id,
                tool_use_id=metadata.get("tool_use_id", ""),
                tool_name=metadata.get("tool_name", ""),
                result=metadata.get("result"),
                is_error=metadata.get("is_error", False),
                timestamp=datetime.now().isoformat(),
            )
        else:
            # Unknown event type - return as log
            return LogEvent(
                type="log",
                execution_id=execution_id,
                level=data.get("level", "info"),
                message=data.get("message", str(data)),
            )

    async def _emit_event(self, execution_id: str, event: Any) -> None:
        """Emit event to WebSocket clients and store in history."""
        # Store event in history
        if execution_id not in self.events:
            self.events[execution_id] = []
        self.events[execution_id].append(event)

        # Broadcast to all connected WebSocket clients in real-time
        if execution_id in self.websocket_connections:
            event_data = event.model_dump() if hasattr(event, "model_dump") else event
            disconnected = []

            for websocket in self.websocket_connections[execution_id]:
                try:
                    await websocket.send_json(event_data)
                except Exception:
                    # Mark for removal if send fails
                    disconnected.append(websocket)

            # Remove disconnected clients
            for ws in disconnected:
                self.websocket_connections[execution_id].remove(ws)

    def register_websocket(self, execution_id: str, websocket: Any) -> None:
        """Register a WebSocket connection for an execution."""
        if execution_id not in self.websocket_connections:
            self.websocket_connections[execution_id] = []
        self.websocket_connections[execution_id].append(websocket)

    def unregister_websocket(self, execution_id: str, websocket: Any) -> None:
        """Unregister a WebSocket connection."""
        if execution_id in self.websocket_connections:
            if websocket in self.websocket_connections[execution_id]:
                self.websocket_connections[execution_id].remove(websocket)
            if not self.websocket_connections[execution_id]:
                del self.websocket_connections[execution_id]

    def get_execution(self, execution_id: str) -> Optional[Execution]:
        """Get execution by ID.

        Checks in-memory executions first, then loads from disk if persisted.
        """
        # Check in-memory first
        if execution_id in self.executions:
            return self.executions[execution_id]

        # Try to load from disk
        metadata = self.execution_store.load_execution(execution_id)
        if metadata:
            # Reconstruct Execution object from metadata
            return Execution(
                id=metadata["execution_id"],
                scenario_id=metadata["scenario_id"],
                parameters=metadata["parameters"],
                status=ExecutionStatus(metadata["status"]),
                started_at=datetime.fromisoformat(metadata["started_at"]),
                completed_at=datetime.fromisoformat(metadata["completed_at"]) if metadata.get("completed_at") else None,
                exit_code=0,  # Persisted executions are always successful
            )

        return None

    def get_events(self, execution_id: str) -> list[Any]:
        """Get events for an execution.

        Returns in-memory events or reconstructed events from disk.
        """
        # Check in-memory first
        if execution_id in self.events:
            return self.events[execution_id]

        # Try to reconstruct from persisted execution
        return self.execution_store.reconstruct_events(execution_id)

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel running execution."""
        process = self.processes.get(execution_id)
        if process and process.returncode is None:
            process.terminate()
            await asyncio.sleep(0.5)
            if process.returncode is None:
                process.kill()

            execution = self.executions.get(execution_id)
            if execution:
                execution.status = ExecutionStatus.CANCELLED
                execution.completed_at = datetime.now()

            return True
        return False

    async def submit_prompt_response(self, execution_id: str, response: str, comments: str | None = None) -> bool:
        """Submit user response to interactive prompt.

        Args:
            execution_id: Execution ID
            response: User's response text (approve/revise/skip/done)
            comments: Optional revision comments to inject into draft file

        Returns:
            True if response was successfully sent, False otherwise
        """
        process = self.processes.get(execution_id)

        # Validate process exists and has stdin
        if not process or not process.stdin or process.returncode is not None:
            return False

        # Check if there's a pending prompt
        if execution_id not in self.pending_prompts:
            return False

        try:
            # Special handling for 'revise' with comments - inject into draft file
            if response == "revise" and comments:
                print(f"🔍 DEBUG: Attempting to inject comments: '{comments}'")

                # Find the current draft iteration from file.created events
                # The prompt shows review iteration (1), but we need to find the actual draft file (iter 0)
                draft_iteration = 0
                for event in reversed(self.events.get(execution_id, [])):
                    if hasattr(event, "type") and event.type == "file.created":
                        metadata = getattr(event, "metadata", None)
                        if metadata and metadata.get("type") == "draft":
                            draft_iteration = metadata.get("iteration", 0)
                            break

                print(f"🔍 DEBUG: Latest draft iteration: {draft_iteration}")

                # Use tracked session directory for this execution
                session_dir_str = self.session_dirs.get(execution_id)
                repo_root = Path(__file__).parent.parent.parent.parent

                if session_dir_str:
                    draft_file = repo_root / session_dir_str / f"draft_iter_{draft_iteration}.md"
                    print(f"🔍 DEBUG: Using tracked session: {session_dir_str}")
                    print(f"🔍 DEBUG: Looking for draft at: {draft_file}")

                    if draft_file.exists():
                        try:
                            draft_content = draft_file.read_text()
                            print(f"🔍 DEBUG: Read draft ({len(draft_content)} chars)")

                            # Clean up comments - remove newlines so regex can match
                            cleaned_comments = comments.replace("\n", " ").replace("\r", " ").strip()
                            print(f"🔍 DEBUG: Cleaned comment: [{cleaned_comments[:100]}...]")

                            # Add bracketed comment at the end
                            updated_content = f"{draft_content}\n\n[{cleaned_comments}]"
                            draft_file.write_text(updated_content)

                            # Ensure write is flushed to disk
                            import time

                            time.sleep(0.1)  # Small delay to ensure file write completes

                            # Verify the write succeeded (check for cleaned_comments, not original)
                            verification = draft_file.read_text()
                            if f"[{cleaned_comments}]" in verification:
                                print(f"🔍 DEBUG: ✅ Verified comment in file ({len(verification)} chars)")
                            else:
                                print("🔍 DEBUG: ⚠️ Comment NOT found after write!")
                                print(f"🔍 DEBUG: Last 200 chars: {verification[-200:]}")

                            print(f"🔍 DEBUG: Wrote updated draft ({len(updated_content)} chars)")

                            await self._emit_event(
                                execution_id,
                                LogEvent(
                                    type="log",
                                    execution_id=execution_id,
                                    level="info",
                                    message=f"✓ Injected revision comments into draft: [{cleaned_comments[:100]}{'...' if len(cleaned_comments) > 100 else ''}]",
                                ),
                            )

                            # Send "done" instead of "revise" since we've added the comments
                            response = "done"
                            print("🔍 DEBUG: Changed response from 'revise' to 'done'")
                        except Exception as e:
                            print(f"🔍 DEBUG: Error injecting comments: {e}")
                            await self._emit_event(
                                execution_id,
                                LogEvent(
                                    type="log",
                                    execution_id=execution_id,
                                    level="warning",
                                    message=f"⚠ Could not inject comments into draft: {e}",
                                ),
                            )
                    else:
                        print(f"🔍 DEBUG: Draft file does not exist: {draft_file}")
                else:
                    print(f"🔍 DEBUG: No session directory tracked for execution: {execution_id}")

            # Write response to subprocess stdin (with newline)
            process.stdin.write(f"{response}\n".encode())
            await process.stdin.drain()

            # Clear pending prompt
            self.pending_prompts.pop(execution_id, None)

            # Emit confirmation event
            await self._emit_event(
                execution_id,
                LogEvent(
                    type="log",
                    execution_id=execution_id,
                    level="info",
                    message=f"✓ User response submitted: {response}",
                ),
            )

            return True

        except Exception as e:
            # Emit error event
            await self._emit_event(
                execution_id,
                LogEvent(
                    type="log", execution_id=execution_id, level="error", message=f"✗ Failed to submit response: {e}"
                ),
            )
            return False
