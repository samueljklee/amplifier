"""
Term explainer core functionality.

Extracts and explains advanced or uncommon technical terms.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class TermExplainer:
    """Extracts and explains technical terms from posts."""

    async def explain_terms(self, posts: list[dict[str, Any]], analysis: dict[str, Any]) -> dict[str, Any]:
        """Extract and explain advanced technical terms.

        Args:
            posts: List of post dictionaries
            analysis: Analysis results

        Returns:
            Dictionary with term explanations
        """
        # Collect titles and key content
        content_samples = []
        for post in posts[:10]:  # Limit to first 10 for efficiency
            content_samples.append(post["title"])
            if post.get("text"):
                content_samples.append(post["text"][:300])

        content_text = "\n".join(content_samples)

        prompt = f"""Extract and explain advanced or uncommon technical terms from these HN posts:

=== CONTENT ===
{content_text}

Identify terms that would benefit from explanation (e.g., technical jargon, acronyms, new technologies).
Return a JSON object with:
{{
  "terms": [
    {{
      "term": "term name",
      "explanation": "clear, concise explanation",
      "context": "how it's used in these posts"
    }}
  ]
}}

Focus on:
- Technical terms that may not be familiar to everyone
- New or emerging technologies
- Industry-specific jargon
- Important acronyms

Limit to 10-15 most important terms.
Return ONLY valid JSON, no other text."""

        options = SessionOptions(
            system_prompt="You are a technical writer who explains complex terms clearly and concisely.",
            retry_attempts=2,
        )

        try:
            async with ClaudeSession(options) as session:
                response = await session.query(prompt)
                result = parse_llm_json(response.content)

                # Type guard - REQUIRED for defensive parsing
                if not isinstance(result, dict):
                    logger.error("Expected dict from LLM, got invalid format")
                    return {"terms": []}

                if "terms" not in result:
                    logger.warning("Missing 'terms' in result")
                    return {"terms": []}

                return result

        except Exception as e:
            logger.error(f"Term explanation failed: {e}")
            return {"terms": []}
