"""PTY manager for Claude Code CLI terminal sessions."""

import asyncio
import fcntl
import os
import pty
import select
import struct
import termios
from typing import Optional


class PTYManager:
    """Manages PTY sessions for Claude Code CLI."""

    def __init__(self) -> None:
        self.sessions: dict[str, dict] = {}  # session_id -> {master_fd, pid, websocket, output_buffer}

    async def create_session(
        self, session_id: str, initial_prompt: Optional[str] = None, cwd: Optional[str] = None
    ) -> dict:
        """Create a new PTY session running Claude CLI.

        Args:
            session_id: Unique session identifier
            initial_prompt: Optional initial prompt to send to Claude
            cwd: Working directory for Claude session (defaults to amplifier root)

        Returns:
            dict with 'master_fd' and 'pid'
        """
        # Prepare prompt (trim trailing newlines so multi-line content is preserved)
        sanitized_prompt: Optional[str] = None
        if initial_prompt:
            sanitized_prompt = initial_prompt.rstrip("\r\n")

        # Create PTY
        master_fd, slave_fd = pty.openpty()

        # Fork process
        pid = os.fork()

        if pid == 0:  # Child process
            # Close master fd in child
            os.close(master_fd)

            # Set up slave as stdin/stdout/stderr
            os.dup2(slave_fd, 0)  # stdin
            os.dup2(slave_fd, 1)  # stdout
            os.dup2(slave_fd, 2)  # stderr

            # Close original slave fd
            os.close(slave_fd)

            # Set environment for Claude CLI
            env = os.environ.copy()
            env["TERM"] = "xterm-256color"  # Standard terminal type
            env["COLUMNS"] = "120"
            env["LINES"] = "30"

            # Disable fancy TUI features that don't work well in web terminals
            env["NO_COLOR"] = "1"  # Disable color if it causes issues (optional)
            del env["NO_COLOR"]  # Actually, keep color - it looks nice

            # Note: Claude Code uses full TUI which includes screen clearing
            # Users may need to scroll up to see earlier output

            # Change to specified working directory (or amplifier root by default)
            if cwd:
                os.chdir(cwd)
            else:
                # Default to amplifier root (4 levels up from backend)
                amplifier_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
                os.chdir(amplifier_root)

            # Start Claude in interactive mode (pass prompt directly if provided)
            args = ["claude"]
            if sanitized_prompt:
                args.append(sanitized_prompt)

            os.execvpe("claude", args, env)

        else:  # Parent process
            # Close slave fd in parent
            os.close(slave_fd)

            # Set non-blocking mode on master fd
            flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
            fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            if sanitized_prompt:
                preview = sanitized_prompt.replace("\r", "\\r").replace("\n", "\\n")
                print(f"📝 Launching Claude with initial prompt: {preview[:80]}...")

            # Store session with output buffer
            self.sessions[session_id] = {
                "master_fd": master_fd,
                "pid": pid,
                "websocket": None,
                "output_buffer": bytearray(),  # Buffer output until WebSocket connects
            }

            print(f"✅ Created PTY session {session_id} (pid={pid})")

            # Start background task to capture output immediately
            # This ensures we don't miss Claude's initial output before WebSocket connects
            asyncio.create_task(self._buffer_initial_output(session_id))

            # Give the buffer task a moment to start
            await asyncio.sleep(0.1)

            # Wait for Claude to emit initial output (up to 1 second)
            print("⏳ Waiting for Claude to start up...")
            for attempt in range(10):  # 10 * 0.1s = 1 second
                if len(self.sessions[session_id]["output_buffer"]) > 0:
                    print(f"✅ Claude started (saw {len(self.sessions[session_id]['output_buffer'])} bytes)")
                    break
                await asyncio.sleep(0.1)
            else:
                print("⚠️ Claude didn't output anything in 1 second, proceeding anyway")

            return {"master_fd": master_fd, "pid": pid}

    async def _buffer_initial_output(self, session_id: str) -> None:
        """Buffer PTY output until WebSocket connects.

        This prevents losing Claude's initial output (welcome screen, etc.)
        before the WebSocket connection is established.

        Args:
            session_id: Session identifier
        """
        print(f"📥 Starting output buffering for session {session_id}")

        while True:
            session = self.sessions.get(session_id)
            if not session:
                print(f"⚠️ Session {session_id} ended during buffering")
                return

            # Stop buffering once WebSocket connects
            if session.get("websocket"):
                print(f"🔌 WebSocket connected for {session_id}, stopping buffering")
                return

            # Read and buffer output
            data = await self.read_output(session_id)
            if data:
                session["output_buffer"].extend(data)
                # Debug: Show first 100 chars of what we're buffering
                preview = data.decode("utf-8", errors="replace")[:100].replace("\n", "\\n").replace("\r", "\\r")
                buffer_total = len(session["output_buffer"])
                print(f"📦 Buffered {len(data)} bytes for {session_id} (total: {buffer_total}): {preview}")

            await asyncio.sleep(0.01)  # Small delay to avoid busy-wait

    async def read_output(self, session_id: str) -> Optional[bytes]:
        """Read output from PTY (non-blocking).

        Args:
            session_id: Session identifier

        Returns:
            bytes of output or None if no data available
        """
        session = self.sessions.get(session_id)
        if not session:
            return None

        master_fd = session["master_fd"]

        # Non-blocking read
        try:
            r, _, _ = select.select([master_fd], [], [], 0)
            if r:
                return os.read(master_fd, 4096)
        except OSError:
            # PTY closed
            return None

        return None

    async def write_input(self, session_id: str, data: bytes) -> bool:
        """Write input to PTY.

        Args:
            session_id: Session identifier
            data: Input data to write

        Returns:
            True if successful, False otherwise
        """
        session = self.sessions.get(session_id)
        if not session:
            return False

        master_fd = session["master_fd"]
        remaining = memoryview(data)

        try:
            while len(remaining) > 0:
                try:
                    written = os.write(master_fd, remaining)
                    if written == 0:
                        # Yield and retry if no progress
                        await asyncio.sleep(0.01)
                        continue
                    remaining = remaining[written:]
                except BlockingIOError:
                    # PTY not ready yet; wait briefly and retry
                    await asyncio.sleep(0.01)
                except OSError as e:
                    print(f"⚠️ Failed to write to PTY: {e}")
                    return False

            return True

        finally:
            # Release the memoryview
            remaining.release()

    async def resize_terminal(self, session_id: str, rows: int, cols: int) -> bool:
        """Resize PTY terminal.

        Args:
            session_id: Session identifier
            rows: Number of rows
            cols: Number of columns

        Returns:
            True if successful, False otherwise
        """
        session = self.sessions.get(session_id)
        if not session:
            return False

        try:
            # Set terminal size (TIOCSWINSZ)
            size = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(session["master_fd"], termios.TIOCSWINSZ, size)
            print(f"🔧 Resized terminal {session_id} to {rows}x{cols}")
            return True
        except OSError as e:
            print(f"⚠️ Failed to resize terminal: {e}")
            return False

    async def close_session(self, session_id: str) -> None:
        """Close PTY session and kill process.

        Args:
            session_id: Session identifier
        """
        session = self.sessions.get(session_id)
        if not session:
            return

        try:
            # Kill process
            os.kill(session["pid"], 9)  # SIGKILL
            print(f"🔪 Killed process {session['pid']}")
        except (OSError, ProcessLookupError):
            pass

        try:
            # Close PTY
            os.close(session["master_fd"])
        except OSError:
            pass

        # Remove from sessions
        del self.sessions[session_id]
        print(f"🧹 Cleaned up session {session_id}")

    async def stream_output(self, session_id: str, websocket) -> None:
        """Stream PTY output to WebSocket (continuous read loop).

        Args:
            session_id: Session identifier
            websocket: WebSocket connection
        """
        # Wait for session to be created (with timeout)
        session = None
        for attempt in range(20):  # Try for up to 2 seconds
            session = self.sessions.get(session_id)
            if session:
                break
            print(f"⏳ Waiting for session {session_id} to be created (attempt {attempt + 1}/20)")
            await asyncio.sleep(0.1)

        if not session:
            print(f"❌ Session {session_id} not found after 2 second timeout")
            return

        session["websocket"] = websocket
        print(f"📡 Starting output stream for session {session_id}")

        # Flush any buffered output first
        buffered_output = session["output_buffer"]
        if len(buffered_output) > 0:
            print(f"🚀 Flushing {len(buffered_output)} bytes of buffered output")
            await websocket.send_bytes(bytes(buffered_output))
            buffered_output.clear()

        try:
            buffer = bytearray()

            while True:
                # Read from PTY
                data = await self.read_output(session_id)

                if data:
                    buffer.extend(data)
                    # Send immediately for real-time streaming
                    print(f"📤 Sending {len(buffer)} bytes to WebSocket for {session_id}")
                    await websocket.send_bytes(bytes(buffer))
                    buffer.clear()
                else:
                    # Small sleep to avoid busy-wait when no data
                    await asyncio.sleep(0.01)

        except Exception as e:
            print(f"⚠️ PTY stream error for {session_id}: {e}")
        finally:
            await self.close_session(session_id)
