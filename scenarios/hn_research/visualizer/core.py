"""
Visualizer core functionality.

Generates Mermaid diagrams showing topic relationships.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class Visualizer:
    """Generates Mermaid diagrams for topic relationships."""

    async def generate_diagram(self, analysis: dict[str, Any]) -> str:
        """Generate Mermaid diagram showing topic relationships.

        Args:
            analysis: Analysis results with categories and relationships

        Returns:
            Mermaid diagram code
        """
        categories = analysis.get("categories", {})
        relationships = analysis.get("relationships", [])

        # Prepare data for diagram generation
        category_list = [
            {"name": name, "post_count": len(data.get("post_indices", []))} for name, data in categories.items()
        ]

        relationship_list = [
            {"posts": rel.get("posts", []), "description": rel.get("relationship", "")} for rel in relationships
        ]

        prompt = f"""Generate a Mermaid diagram showing topic relationships from this HN analysis:

=== CATEGORIES ===
{category_list}

=== RELATIONSHIPS ===
{relationship_list}

Create a Mermaid graph diagram that:
1. Shows each category as a node (use short labels)
2. Shows relationships between related topics
3. Uses a clear, readable layout
4. Includes a title "HN Topic Relationships"

Example format:
```mermaid
graph TD
    A[AI/ML] --> B[Cloud]
    A --> C[Security]
    B --> C
    style A fill:#e1f5ff
    style B fill:#ffe1e1
```

Return ONLY the Mermaid code (including ```mermaid markers), no other text."""

        options = SessionOptions(
            system_prompt="You are an expert at creating clear, informative Mermaid diagrams.", retry_attempts=2
        )

        try:
            async with ClaudeSession(options) as session:
                response = await session.query(prompt)
                diagram = response.content.strip()

                # Ensure it has mermaid markers
                if "```mermaid" not in diagram:
                    diagram = f"```mermaid\n{diagram}\n```"

                return diagram

        except Exception as e:
            logger.error(f"Diagram generation failed: {e}")
            return self._fallback_diagram(categories)

    def _fallback_diagram(self, categories: dict[str, Any]) -> str:
        """Generate a basic diagram when AI fails.

        Args:
            categories: Category dictionary

        Returns:
            Basic Mermaid diagram
        """
        nodes = []
        for idx, name in enumerate(list(categories.keys())[:5], 1):
            nodes.append(f"    {chr(64 + idx)}[{name}]")

        diagram = "```mermaid\ngraph TD\n"
        diagram += "\n".join(nodes)
        diagram += "\n```"

        return diagram
