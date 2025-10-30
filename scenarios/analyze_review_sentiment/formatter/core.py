"""
Report formatting functionality.

Formats analysis results into a markdown report.
"""

from typing import Any

from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class ReportFormatter:
    """Formats analysis results into markdown reports."""

    def format_report(self, analysis: dict[str, Any]) -> str:
        """Format analysis results as a markdown report.

        Args:
            analysis: Analysis results from SentimentAnalyzer

        Returns:
            Formatted markdown report
        """
        logger.info("Formatting markdown report...")

        # Extract data with defaults
        sentiment = analysis.get("overall_sentiment", "unknown")
        summary = analysis.get("sentiment_summary", "No summary available")
        total_reviews = analysis.get("total_reviews_analyzed", "unknown")
        top_reviews = analysis.get("top_actionable_reviews", [])

        # Build report
        lines = []
        lines.append("# Customer Review Sentiment Analysis")
        lines.append("")
        lines.append("## Overall Sentiment")
        lines.append("")
        lines.append(f"**Sentiment:** {sentiment.title()}")
        lines.append("")
        lines.append(f"**Total Reviews Analyzed:** {total_reviews}")
        lines.append("")
        lines.append(f"**Summary:** {summary}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Top 3 Most Actionable Reviews")
        lines.append("")
        lines.append(
            "These reviews contain the most specific, impactful, and feasible feedback "
            "that could drive meaningful improvements to your product or service."
        )
        lines.append("")

        # Format each actionable review
        for review in top_reviews:
            rank = review.get("rank", "?")
            score = review.get("actionability_score", 0)
            text = review.get("review_text", "No text available")
            why = review.get("why_actionable", "No explanation available")
            action = review.get("suggested_action", "No suggestion available")

            lines.append(f"### Rank #{rank} - Actionability Score: {score}/100")
            lines.append("")
            lines.append("**Review:**")
            lines.append(f"> {text}")
            lines.append("")
            lines.append(f"**Why This is Actionable:** {why}")
            lines.append("")
            lines.append(f"**Suggested Action:** {action}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Footer
        lines.append("## Next Steps")
        lines.append("")
        lines.append("1. Review each actionable item with your team")
        lines.append("2. Prioritize based on your current roadmap and resources")
        lines.append("3. Create action items for the highest-priority feedback")
        lines.append("4. Follow up with customers who provided this feedback")
        lines.append("")

        report = "\n".join(lines)
        logger.info(f"Report formatted: {len(lines)} lines, {len(report)} characters")
        return report
