"""AI-powered conversation manager for workflow creation."""

import json
import os
from pathlib import Path

from models.workflow import (
    ConversationRequest,
    ConversationResponse,
    ConversationState,
    Message,
    NodeType,
    NodeUIConfig,
    UIStyle,
    WorkflowNode,
    WorkflowSpec,
)
from pydantic_ai import Agent


class ConversationManager:
    """Manages AI conversations for workflow creation."""

    def __init__(self) -> None:
        """Initialize conversation manager."""
        # Use Claude Sonnet 4.5 by default
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

        self.agent: Agent[None, str] = Agent(  # type: ignore[call-arg]
            model=model,  # PydanticAI auto-detects anthropic: prefix from API key
            system_prompt=self._build_system_prompt(),
        )

        # Session storage
        self.storage_dir = Path(__file__).parent.parent.parent.parent / ".data" / "workflow_sessions"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Active sessions in memory
        self.sessions: dict[str, ConversationState] = {}

    def _build_system_prompt(self) -> str:
        """Build system prompt for workflow creation."""
        return """You are an expert workflow designer helping users create data processing workflows through conversation.

Your role is to:
1. Ask clarifying questions to understand the user's needs
2. Suggest appropriate workflow structures
3. Help design node-by-node processing pipelines
4. Recommend UI configurations based on user preferences
5. Validate that the workflow is complete and ready to generate

CONVERSATION FLOW:

1. UNDERSTAND THE GOAL
   - What problem are they solving?
   - What are inputs and outputs?
   - Ask about data formats

2. DESIGN THE WORKFLOW
   - Break down into logical processing steps
   - Suggest node types (input, process, output)
   - Recommend connections between nodes

3. CONFIGURE UI
   - Ask how they want to interact with each node
   - Suggest appropriate UI styles (drag-drop, forms, dashboards)
   - Customize based on their preferences

4. VALIDATE & GENERATE
   - Check if all requirements are clear
   - Confirm the workflow is complete
   - Signal when ready to generate code

GUIDELINES:
- Ask 1-2 questions at a time, not overwhelming lists
- Be specific in recommendations
- Use examples to clarify options
- Show enthusiasm for their workflow ideas
- Keep responses concise and actionable

FORMAT YOUR RESPONSES AS JSON:
{
  "message": "Your conversational response to the user",
  "actions": {
    "add_nodes": [{"type": "input", "name": "csv_reader", "description": "..."}],
    "update_workflow": {"input_format": "CSV", "output_requirements": ["dashboard"]},
    "questions": ["What columns are in your CSV?"],
    "ready": false
  }
}

Always include the "message" field. Include "actions" when you want to update the workflow structure.
"""

    async def start_conversation(self, request: ConversationRequest) -> ConversationResponse:
        """Start or continue a workflow creation conversation.

        Args:
            request: User's message and optional session ID

        Returns:
            AI response with updated workflow state
        """
        # Load or create session
        if request.session_id and request.session_id in self.sessions:
            state = self.sessions[request.session_id]
        elif request.session_id:
            # Try to load from disk
            state = self._load_session(request.session_id)
            if not state:
                # Session not found, create new
                state = self._create_new_session()
        else:
            state = self._create_new_session()

        # Add user message to history
        state.history.append(Message(role="user", content=request.message))

        # Build prompt with conversation history
        prompt = self._build_conversation_prompt(state)

        # Get AI response
        result = await self.agent.run(prompt)

        # Extract text from AgentRunResult (PydanticAI uses 'output' attribute)
        if hasattr(result, "output"):
            ai_response_text = str(result.output)
        elif hasattr(result, "data"):
            ai_response_text = str(result.data)  # type: ignore[attr-defined]
        else:
            ai_response_text = str(result)

        # Clean up markdown code blocks if present
        if "```json" in ai_response_text:
            # Extract JSON from markdown code block
            start = ai_response_text.find("```json") + 7
            end = ai_response_text.find("```", start)
            ai_response_text = ai_response_text[start:end].strip()
        elif "```" in ai_response_text:
            # Generic code block
            start = ai_response_text.find("```") + 3
            end = ai_response_text.find("```", start)
            ai_response_text = ai_response_text[start:end].strip()

        # Parse AI response
        try:
            ai_response = json.loads(ai_response_text)
        except json.JSONDecodeError:
            # Fallback if AI doesn't return JSON
            ai_response = {"message": ai_response_text, "actions": {}}

        # Extract message and actions
        ai_message = ai_response.get("message", "")
        actions = ai_response.get("actions", {})

        # Update workflow based on actions
        if actions:
            self._apply_actions(state.workflow, actions)
            state.workflow.ready_to_generate = actions.get("ready", False)

        # Add AI message to history
        state.history.append(Message(role="assistant", content=ai_message))

        # Save session
        self.sessions[state.session_id] = state
        self._save_session(state)

        # Build response
        return ConversationResponse(
            session_id=state.session_id,
            ai_message=ai_message,
            workflow_preview=state.workflow,
            ready_to_generate=state.workflow.ready_to_generate,
            suggested_actions=actions.get("questions", []),
        )

    def _create_new_session(self) -> ConversationState:
        """Create a new conversation session."""
        workflow = WorkflowSpec(
            name="new_workflow",
            display_name="New Workflow",
            description="Workflow being designed",
        )

        return ConversationState(workflow=workflow)

    def _build_conversation_prompt(self, state: ConversationState) -> str:
        """Build prompt from conversation history."""
        # Format conversation history
        history_text = "\n".join(
            [f"{msg.role.upper()}: {msg.content}" for msg in state.history[-10:]]  # Last 10 messages
        )

        # Format current workflow state
        workflow_json = state.workflow.model_dump_json(indent=2)

        return f"""Current workflow state:
{workflow_json}

Conversation history:
{history_text}

Respond with your next message and any workflow updates as JSON."""

    def _apply_actions(self, workflow: WorkflowSpec, actions: dict) -> None:
        """Apply AI-suggested actions to workflow.

        Args:
            workflow: Workflow to update
            actions: Actions from AI response
        """
        # Add nodes
        if "add_nodes" in actions:
            for node_data in actions["add_nodes"]:
                node = WorkflowNode(
                    type=NodeType(node_data.get("type", "process")),
                    name=node_data["name"],
                    display_name=node_data.get("display_name", node_data["name"]),
                    description=node_data.get("description", ""),
                )

                # Auto-position nodes in a row
                node.position = {"x": len(workflow.nodes) * 200, "y": 100}

                # Connect to previous node if this isn't first
                if workflow.nodes:
                    prev_node = workflow.nodes[-1]
                    prev_node.outputs.append(node.id)
                    node.inputs.append(prev_node.id)

                workflow.nodes.append(node)

        # Update workflow metadata
        if "update_workflow" in actions:
            updates = actions["update_workflow"]
            if "name" in updates:
                workflow.name = updates["name"]
            if "display_name" in updates:
                workflow.display_name = updates["display_name"]
            if "description" in updates:
                workflow.description = updates["description"]
            if "input_format" in updates:
                workflow.input_format = updates["input_format"]
            if "output_requirements" in updates:
                workflow.output_requirements = updates["output_requirements"]
            if "processing_steps" in updates:
                workflow.processing_steps = updates["processing_steps"]

        # Update node UI configs
        if "configure_ui" in actions:
            for node_config in actions["configure_ui"]:
                node_id = node_config.get("node_id")
                if not node_id:
                    continue

                # Find node
                node = next((n for n in workflow.nodes if n.id == node_id), None)
                if not node:
                    continue

                # Create UI config
                ui_style = UIStyle(node_config.get("style", "custom"))
                node.ui_config = NodeUIConfig(
                    style=ui_style,
                    show_preview=node_config.get("show_preview", False),
                    allow_parameter_tuning=node_config.get("allow_parameter_tuning", False),
                    metadata=node_config.get("metadata", {}),
                )

    def _save_session(self, state: ConversationState) -> None:
        """Save session to disk."""
        session_file = self.storage_dir / f"{state.session_id}.json"
        session_file.write_text(state.model_dump_json(indent=2))

    def _load_session(self, session_id: str) -> ConversationState | None:
        """Load session from disk."""
        session_file = self.storage_dir / f"{session_id}.json"
        if not session_file.exists():
            return None

        try:
            return ConversationState.model_validate_json(session_file.read_text())
        except Exception as e:
            print(f"Failed to load session {session_id}: {e}")
            return None

    def get_session(self, session_id: str) -> ConversationState | None:
        """Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session state or None if not found
        """
        if session_id in self.sessions:
            return self.sessions[session_id]

        return self._load_session(session_id)
