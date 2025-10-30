"""Requirements clarification module.

Interacts with user to clarify research requirements and refine the query.
"""

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit import ToolkitLogger

from ..state import StateManager

logger = ToolkitLogger()


class RequirementsClarifier:
    """Clarifies research requirements through interactive dialogue."""

    async def clarify_requirements(self, initial_query: str | None, state_manager: StateManager) -> dict:
        """Clarify research requirements with the user.

        Args:
            initial_query: Initial research question
            state_manager: State manager for saving progress

        Returns:
            Dictionary with clarified requirements:
            - research_question: Refined research question
            - research_type: Type of research (exploratory, analytical, etc.)
            - researcher_persona: Who is conducting this research
            - research_depth: How deep to go (survey, detailed, comprehensive)
            - output_format: Desired output format
        """
        logger.info("Clarifying research requirements...")

        # Create session for requirements gathering
        options = SessionOptions(
            system_prompt=self._get_system_prompt(),
            model="claude-sonnet-4-5-20250929",
            cwd=str(state_manager.state.session_dir.parent.parent.parent),
        )

        async with ClaudeSession(options) as claude:
            # Start conversation
            if initial_query:
                prompt = f"""
I want to conduct research on the following question:

"{initial_query}"

Please help me clarify:
1. Is this question clear and specific enough?
2. What type of research is this (exploratory, analytical, comparative, etc.)?
3. What level of depth should I aim for?
4. What would be the most appropriate output format?

Ask me any clarifying questions to better understand my needs.
"""
            else:
                prompt = """
I'd like to conduct research but I'm not sure what to research yet.

Can you help me identify a good research topic? Ask me about:
- My interests or field
- What problems I'm trying to solve
- What I want to learn about
"""

            response = await claude.query(prompt)
            logger.info(f"Clarifier: {response.content}")

            # Interactive dialogue until requirements are clear
            # For now, proceed with reasonable defaults if user provided a query
            if initial_query:
                requirements = {
                    "research_question": initial_query,
                    "research_type": "comprehensive",
                    "researcher_persona": "general researcher",
                    "research_depth": "detailed",
                    "output_format": "markdown_report",
                }
            else:
                # No query provided, need user input
                raise ValueError(
                    "No research question provided. Please provide a --question or resume an existing session."
                )

        return requirements

    def _get_system_prompt(self) -> str:
        """Get system prompt for requirements clarification."""
        return """
You are an expert research assistant helping to clarify research requirements.

Your role is to:
1. Understand the user's research goals
2. Ask clarifying questions to refine the research question
3. Identify the type and depth of research needed
4. Suggest appropriate output formats

Be conversational, insightful, and help the user articulate what they really want to discover.
"""
