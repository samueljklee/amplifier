"""
Sentiment analysis and actionability scoring.

Analyzes customer reviews for sentiment and identifies the most actionable feedback.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class SentimentAnalyzer:
    """Analyzes sentiment and scores reviews for actionability."""

    async def analyze(self, review_text: str) -> dict[str, Any] | None:
        """Analyze reviews for sentiment and actionability.

        Args:
            review_text: Full text of all reviews

        Returns:
            Analysis results with sentiment and top actionable reviews,
            or None if analysis fails
        """
        logger.info("Analyzing sentiment and actionability...")

        prompt = f"""Analyze these customer reviews and identify the most actionable feedback.

=== CUSTOMER REVIEWS ===
{review_text}

=== YOUR TASK ===
1. Determine the overall sentiment across all reviews (positive, negative, mixed, neutral)
2. Identify individual reviews or feedback items within the text
3. Score each review/feedback item for actionability (0-100) based on:
   - Specificity (concrete suggestions vs vague complaints)
   - Impact potential (could lead to meaningful product/service improvements)
   - Feasibility (realistic to address)
   - Clarity (easy to understand what needs fixing/improving)
4. Select the TOP 3 most actionable reviews/feedback items

Return your analysis in JSON format:
{{
  "overall_sentiment": "positive|negative|mixed|neutral",
  "sentiment_summary": "Brief explanation of overall sentiment (2-3 sentences)",
  "total_reviews_analyzed": <number>,
  "top_actionable_reviews": [
    {{
      "rank": 1,
      "actionability_score": <0-100>,
      "review_text": "The actual review text or excerpt",
      "why_actionable": "Brief explanation of why this is actionable",
      "suggested_action": "Concrete action the business could take"
    }},
    {{
      "rank": 2,
      "actionability_score": <0-100>,
      "review_text": "The actual review text or excerpt",
      "why_actionable": "Brief explanation of why this is actionable",
      "suggested_action": "Concrete action the business could take"
    }},
    {{
      "rank": 3,
      "actionability_score": <0-100>,
      "review_text": "The actual review text or excerpt",
      "why_actionable": "Brief explanation of why this is actionable",
      "suggested_action": "Concrete action the business could take"
    }}
  ]
}}

Return ONLY valid JSON, no other text."""

        options = SessionOptions(
            system_prompt="You are an expert at analyzing customer feedback and identifying actionable insights for businesses.",
            retry_attempts=2,
        )

        try:
            async with ClaudeSession(options) as session:
                response = await session.query(prompt)
                result = parse_llm_json(response.content)

                # CRITICAL: Type guard before using dict operations
                if not isinstance(result, dict):
                    logger.error("Expected dict from LLM, got invalid format")
                    return None

                # Validate required fields
                if "overall_sentiment" not in result:
                    logger.error("Missing required field: overall_sentiment")
                    return None

                if "top_actionable_reviews" not in result:
                    logger.error("Missing required field: top_actionable_reviews")
                    return None

                # Ensure we have reviews list
                reviews = result.get("top_actionable_reviews")
                if not isinstance(reviews, list):
                    logger.error("top_actionable_reviews must be a list")
                    return None

                logger.info(
                    f"Analysis complete: {result.get('overall_sentiment')} sentiment, {len(reviews)} actionable reviews"
                )

                return result

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return None
