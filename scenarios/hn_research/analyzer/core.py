"""
Analyzer core functionality.

Analyzes posts to identify topics, trends, and relationships.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class Analyzer:
    """Analyzes HN posts for trends and relationships."""

    async def analyze_posts(self, posts: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze posts to identify topics, trends, and relationships.

        Args:
            posts: List of post dictionaries

        Returns:
            Analysis dictionary with categories, trends, and relationships
        """
        # Prepare post summaries for analysis
        post_summaries = []
        for idx, post in enumerate(posts, 1):
            summary = f"{idx}. [{post['score']} pts] {post['title']}"
            if post.get("url"):
                summary += f" ({post['url']})"

            # Add top comment if available
            if post.get("comments"):
                top_comment = post["comments"][0]["text"][:200]
                summary += f"\n   Top comment: {top_comment}..."

            post_summaries.append(summary)

        posts_text = "\n\n".join(post_summaries)

        prompt = f"""Analyze these top Hacker News posts to identify trends, topics, and relationships:

=== POSTS ===
{posts_text}

Analyze and return a JSON object with:
{{
  "categories": {{
    "category_name": {{
      "description": "brief description",
      "post_indices": [1, 3, 5],
      "trending_reason": "why this is trending"
    }}
  }},
  "relationships": [
    {{
      "posts": [1, 2],
      "relationship": "description of how they relate"
    }}
  ],
  "key_trends": [
    "trend 1 observation",
    "trend 2 observation"
  ],
  "notable_developments": [
    "what's new or significant"
  ]
}}

Focus on:
- Grouping related posts by topic/theme
- Identifying emerging trends
- Finding connections between seemingly different posts
- Highlighting what's new and noteworthy

Return ONLY valid JSON, no other text."""

        options = SessionOptions(
            system_prompt="You are an expert analyst specializing in technology trends and Hacker News culture.",
            retry_attempts=2,
        )

        try:
            async with ClaudeSession(options) as session:
                response = await session.query(prompt)
                result = parse_llm_json(response.content)

                # Type guard - REQUIRED for defensive parsing
                if not isinstance(result, dict):
                    logger.error("Expected dict from LLM, got invalid format")
                    return self._fallback_analysis(posts)

                # Validate required fields
                if "categories" not in result:
                    logger.warning("Missing 'categories' in analysis, adding fallback")
                    result["categories"] = {}

                if "relationships" not in result:
                    result["relationships"] = []

                if "key_trends" not in result:
                    result["key_trends"] = []

                if "notable_developments" not in result:
                    result["notable_developments"] = []

                return result

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._fallback_analysis(posts)

    def _fallback_analysis(self, posts: list[dict[str, Any]]) -> dict[str, Any]:
        """Basic analysis when AI fails.

        Args:
            posts: List of posts

        Returns:
            Minimal analysis dictionary
        """
        return {
            "categories": {
                "general": {
                    "description": "Top posts",
                    "post_indices": list(range(1, len(posts) + 1)),
                    "trending_reason": "Popular on HN",
                }
            },
            "relationships": [],
            "key_trends": ["Multiple topics trending on Hacker News"],
            "notable_developments": ["See individual posts for details"],
        }
