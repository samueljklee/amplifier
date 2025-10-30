"""FastAPI server for Amplifier Web UI."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env from backend directory before importing config
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# ruff: noqa: E402
from config import settings
from fastapi import FastAPI, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from models.execution import ExecutionRequest, ExecutionStatus
from services.process_manager import ProcessManager
from services.pty_manager import PTYManager
from services.scenario_discovery import ScenarioDiscoveryService

# Global instances
process_manager = ProcessManager()
pty_manager = PTYManager()
scenario_discovery = ScenarioDiscoveryService(settings.scenarios_path)

# WebSocket connections
websocket_connections: dict[str, list[WebSocket]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """Application lifespan manager."""
    import time
    from pathlib import Path

    # Startup
    print("🚀 Amplifier Web UI starting...")
    print(f"📁 Scenarios path: {settings.scenarios_path}")

    # Discover scenarios
    scenarios = await scenario_discovery.discover_scenarios()
    print(f"✅ Found {len(scenarios)} scenarios")

    # Clean up old uploads and scenario inputs (> 24 hours)
    import shutil

    current_time = time.time()

    for temp_base_path in ["/tmp/amplifier_uploads", "/tmp/amplifier_scenario_inputs"]:
        temp_base = Path(temp_base_path)
        if temp_base.exists():
            for temp_dir in temp_base.iterdir():
                if temp_dir.is_dir():
                    dir_age = current_time - temp_dir.stat().st_mtime
                    if dir_age > 86400:  # 24 hours in seconds
                        try:
                            shutil.rmtree(temp_dir)
                            print(f"🧹 Cleaned up old temp directory: {temp_dir.name}")
                        except Exception as e:
                            print(f"⚠️ Failed to clean up {temp_dir.name}: {e}")

    yield

    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title="Amplifier Web UI",
    description="Beautiful web interface for Amplifier AI agent workflows",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# REST API Endpoints


async def preprocess_parameters(params: dict[str, Any], scenario_id: str | None = None) -> dict[str, Any]:
    """Convert inline content to temp files.

    Handles:
    - Single file inline content (param="__INLINE__", param_content="...")
    - Multi-file inline content (param="__INLINE__", param_files=[{content, filename}])

    Args:
        params: Request parameters that may contain inline content markers
        scenario_id: Optional scenario ID to include in temp directory path for compartmentalization

    Returns:
        Processed parameters with temp file paths replacing inline content
    """
    import uuid
    from pathlib import Path

    processed = {}
    # Include scenario_id in path for better compartmentalization
    scenario_part = f"/{scenario_id}" if scenario_id else ""
    temp_dir = Path(f"/tmp/amplifier_scenario_inputs{scenario_part}/{uuid.uuid4()}")
    temp_dir.mkdir(parents=True, exist_ok=True)

    for key, value in params.items():
        if key.endswith("_content") or key.endswith("_files"):
            continue

        if value == "__INLINE__":
            if f"{key}_content" in params:
                content = params[f"{key}_content"]
                file_path = temp_dir / f"{key}.md"
                file_path.write_text(content)
                processed[key] = str(file_path)

            elif f"{key}_files" in params:
                files_dir = temp_dir / key
                files_dir.mkdir(exist_ok=True)

                for file_info in params[f"{key}_files"]:
                    file_path = files_dir / file_info["filename"]
                    file_path.write_text(file_info["content"])

                processed[key] = str(files_dir)
        else:
            processed[key] = value

    return processed


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Amplifier Web UI API", "version": "0.1.0"}


@app.get("/api/scenarios")
async def list_scenarios() -> dict[str, Any]:
    """List all available scenarios."""
    scenarios = await scenario_discovery.discover_scenarios()
    return {"scenarios": scenarios}


@app.get("/api/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str) -> dict[str, Any]:
    """Get scenario details."""
    scenario = await scenario_discovery.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    return scenario


@app.delete("/api/scenarios/{scenario_id}")
async def delete_scenario(scenario_id: str) -> dict[str, str]:
    """Delete a scenario from the scenarios directory.

    Args:
        scenario_id: ID of scenario to delete

    Returns:
        Status message
    """
    import shutil

    # Get scenario to verify it exists
    scenario = await scenario_discovery.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")

    # Build path to scenario directory
    scenario_path = settings.scenarios_path / scenario_id

    if not scenario_path.exists():
        raise HTTPException(status_code=404, detail=f"Scenario directory not found: {scenario_path}")

    # Delete the scenario directory
    try:
        shutil.rmtree(scenario_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete scenario: {str(e)}")

    return {"status": "deleted", "scenario_id": scenario_id}


@app.post("/api/scenarios/{scenario_id}/execute")
async def execute_scenario(scenario_id: str, request: ExecutionRequest) -> dict[str, str]:
    """Start scenario execution."""
    # Verify scenario exists
    scenario = await scenario_discovery.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")

    # Pre-process parameters to handle inline content
    # Pass scenario_id for compartmentalized temp directories
    processed_params = await preprocess_parameters(request.parameters, scenario_id=scenario_id)

    # Use scenario_id from URL, not request body
    execution_id = await process_manager.execute_scenario(scenario_id, processed_params)

    return {"execution_id": execution_id, "status": "started"}


@app.get("/api/executions")
async def list_executions(limit: int = 50) -> dict[str, Any]:
    """List recent executions."""
    executions = process_manager.execution_store.list_executions(limit=limit)
    return {"executions": executions, "total": len(executions)}


@app.get("/api/executions/{execution_id}")
async def get_execution(execution_id: str) -> dict[str, Any]:
    """Get execution status."""
    execution = process_manager.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found")

    return {
        "id": execution.id,
        "scenario_id": execution.scenario_id,
        "status": execution.status.value,
        "started_at": execution.started_at.isoformat(),
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "exit_code": execution.exit_code,
        "error": execution.error,
    }


@app.delete("/api/executions/{execution_id}")
async def delete_execution(execution_id: str, force: bool = False) -> dict[str, str]:
    """Delete execution metadata.

    Args:
        execution_id: ID of execution to delete
        force: If True, cancel running execution before deleting

    Returns:
        Status message
    """
    # Check if execution is running
    execution = process_manager.get_execution(execution_id)

    if execution and execution.status == ExecutionStatus.RUNNING:
        if force:
            # Cancel running execution first
            await process_manager.cancel_execution(execution_id)
        else:
            raise HTTPException(
                status_code=400, detail="Cannot delete running execution. Cancel it first or use force=true"
            )

    # Delete metadata
    success = process_manager.execution_store.delete_execution(execution_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found")

    return {"status": "deleted"}


@app.post("/api/executions/{execution_id}/respond")
async def submit_prompt_response(execution_id: str, request: dict[str, Any]) -> dict[str, Any]:
    """Submit user response to interactive prompt.

    Request body:
        {"response": "approve"}
        or
        {"response": "revise", "comments": "User's revision comments"}

    Returns:
        Status and submitted response
    """
    response = request.get("response")
    if not response:
        raise HTTPException(status_code=400, detail="Response is required")

    comments = request.get("comments")

    success = await process_manager.submit_prompt_response(execution_id, response, comments)

    if not success:
        raise HTTPException(status_code=404, detail="Execution not found, not awaiting input, or already completed")

    return {"status": "submitted", "response": response, "comments": comments}


@app.get("/api/files/read")
async def read_file(path: str) -> dict[str, str]:
    """Read a file and return its contents."""
    from pathlib import Path

    try:
        file_path = Path(path)

        # If path is relative, make it relative to repo root
        if not file_path.is_absolute():
            repo_root = Path(__file__).parent.parent.parent.parent
            file_path = repo_root / path

        # Security: Only allow reading files in specific directories
        # Check if path is within allowed directories (amplifier repo or its subdirectories)
        repo_root = Path(__file__).parent.parent.parent.parent
        try:
            file_path.resolve().relative_to(repo_root.resolve())
        except ValueError:
            # Also allow reading from .data directories (where tools store their outputs)
            resolved_path = file_path.resolve()
            data_dir = (repo_root / ".data").resolve()
            try:
                resolved_path.relative_to(data_dir)
            except ValueError:
                raise HTTPException(status_code=403, detail="Access denied: File is outside allowed directories")

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {path}")

        if not file_path.is_file():
            raise HTTPException(status_code=400, detail=f"Path is not a file: {path}")

        # Read file content
        content = file_path.read_text(encoding="utf-8")

        return {"path": str(file_path), "content": content, "filename": file_path.name}
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not a text file or uses unsupported encoding")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@app.get("/api/files/browse")
async def browse_directory(path: str = "/") -> dict[str, Any]:
    """Browse directory contents.

    Args:
        path: Directory path to browse (defaults to amplifier repo root)

    Returns:
        Directory listing with files and subdirectories
    """
    from pathlib import Path

    try:
        # Get repo root
        repo_root = Path(__file__).parent.parent.parent.parent

        # Default to repo root if path is "/"
        if path == "/":
            dir_path = repo_root
        else:
            dir_path = Path(path)

        # Security: Only allow browsing within amplifier repo
        try:
            resolved_path = dir_path.resolve()
            resolved_path.relative_to(repo_root.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied: Path is outside allowed directories")

        if not resolved_path.exists():
            raise HTTPException(status_code=404, detail=f"Directory not found: {path}")

        if not resolved_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")

        # Get parent path (None if at repo root)
        parent_path = None
        if resolved_path != repo_root:
            parent_path = str(resolved_path.parent)

        # List directory contents
        items = []
        for item in sorted(resolved_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            item_info: dict[str, Any] = {
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "path": str(item),
            }

            # Add size for files
            if item.is_file():
                try:
                    item_info["size"] = item.stat().st_size
                except Exception:
                    item_info["size"] = 0

            items.append(item_info)

        return {"current_path": str(resolved_path), "parent_path": parent_path, "items": items}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Error browsing directory: {str(e)}")


@app.post("/api/files/upload")
async def upload_file(file: UploadFile) -> dict[str, Any]:
    """Upload a file to temporary storage.

    Returns:
        Temporary file path that can be used by scenarios
    """
    import uuid
    from pathlib import Path

    try:
        # Create upload directory
        upload_base = Path("/tmp/amplifier_uploads")
        upload_dir = upload_base / str(uuid.uuid4())
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")

        file_path = upload_dir / file.filename

        # Write uploaded file
        content = await file.read()
        file_path.write_bytes(content)

        return {"path": str(file_path), "filename": file.filename, "size": len(content)}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


# WebSocket for real-time updates


@app.websocket("/api/ws/executions/{execution_id}")
async def websocket_endpoint(websocket: WebSocket, execution_id: str) -> None:
    """WebSocket endpoint for real-time execution updates."""
    await websocket.accept()

    # Register with process manager for real-time event broadcasting
    process_manager.register_websocket(execution_id, websocket)

    try:
        # Send initial connection message
        await websocket.send_json({"type": "connected", "execution_id": execution_id})

        # Get execution
        execution = process_manager.get_execution(execution_id)
        if not execution:
            await websocket.send_json({"type": "error", "message": "Execution not found"})
            await websocket.close()
            return

        # Send any existing events (for reconnection or late joiners)
        events = process_manager.get_events(execution_id)
        for event in events:
            await websocket.send_json(event.model_dump() if hasattr(event, "model_dump") else event)

        # Check if execution is already completed
        execution = process_manager.get_execution(execution_id)
        is_completed = execution and execution.status in [
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        ]

        # Keep connection alive
        # Events are now sent in real-time via process_manager._emit_event()
        if is_completed:
            # For completed executions, send a final status message and wait briefly before closing
            # This gives the client time to process all events
            await websocket.send_json(
                {
                    "type": "execution.status",
                    "execution_id": execution_id,
                    "status": execution.status.value if execution else "completed",
                    "final": True,
                }
            )
            await asyncio.sleep(0.5)  # Brief wait to ensure client processes events
        else:
            # For running executions, keep connection alive with heartbeats
            while True:
                # Check execution status
                execution = process_manager.get_execution(execution_id)
                if execution and execution.status in [
                    ExecutionStatus.COMPLETED,
                    ExecutionStatus.FAILED,
                    ExecutionStatus.CANCELLED,
                ]:
                    break

                # Send periodic heartbeat
                await websocket.send_json({"type": "heartbeat", "execution_id": execution_id})
                await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
    finally:
        # Unregister from process manager
        process_manager.unregister_websocket(execution_id, websocket)


# Claude Code Terminal Endpoints


@app.post("/api/claude/execute")
async def execute_claude(request: dict[str, Any]) -> dict[str, str]:
    """Start a Claude CLI session in PTY mode.

    Request body:
        {
            "execution_id": "uuid",
            "prompt": "initial prompt text"
        }

    Returns:
        {"execution_id": "uuid", "status": "started"}
    """
    execution_id = request.get("execution_id")
    prompt = request.get("prompt")

    if not execution_id:
        raise HTTPException(status_code=400, detail="execution_id required")

    # Create PTY session
    await pty_manager.create_session(execution_id, prompt)

    return {"execution_id": execution_id, "status": "started"}


@app.websocket("/ws/claude/{execution_id}")
async def claude_terminal(websocket: WebSocket, execution_id: str) -> None:
    """WebSocket for Claude CLI terminal I/O.

    Handles bidirectional communication:
    - Binary messages: Terminal I/O (PTY <-> xterm.js)
    - Text messages (JSON): Control messages (resize)
    """
    await websocket.accept()

    try:
        # Start output streaming task (PTY → WebSocket)
        output_task = asyncio.create_task(pty_manager.stream_output(execution_id, websocket))

        # Handle input from WebSocket (WebSocket → PTY)
        while True:
            message = await websocket.receive()

            if "bytes" in message:
                # User keyboard input → PTY
                await pty_manager.write_input(execution_id, message["bytes"])

            elif "text" in message:
                # Control message (e.g., resize)
                import json

                data = json.loads(message["text"])

                if data.get("type") == "resize":
                    await pty_manager.resize_terminal(execution_id, data["rows"], data["cols"])

    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected for {execution_id}")
    except Exception as e:
        print(f"⚠️ WebSocket error for {execution_id}: {e}")
    finally:
        # Clean up
        output_task.cancel()
        await pty_manager.close_session(execution_id)


# Health check
@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
