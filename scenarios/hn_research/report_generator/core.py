"""
Report generator core functionality.

Compiles comprehensive markdown reports from analysis results.
"""

from datetime import datetime
from typing import Any

from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """Generates markdown reports from analysis results."""

    async def generate_report(
        self,
        posts: list[dict[str, Any]],
        analysis: dict[str, Any],
        terms: dict[str, Any],
        diagram: str,
    ) -> str:
        """Generate comprehensive markdown report.

        Args:
            posts: Original posts
            analysis: Analysis results
            terms: Term explanations
            diagram: Mermaid diagram

        Returns:
            Markdown report content
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        report_lines = []

        # Header
        report_lines.append("# Hacker News Research Report")
        report_lines.append(f"*Generated: {date_str}*")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Executive Summary
        report_lines.append("## Executive Summary")
        report_lines.append("")
        report_lines.append(
            f"Analysis of the top {len(posts)} posts on Hacker News reveals the following key trends and topics:"
        )
        report_lines.append("")

        key_trends = analysis.get("key_trends", [])
        for trend in key_trends:
            report_lines.append(f"- {trend}")

        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Topic Relationships Diagram
        report_lines.append("## Topic Relationships")
        report_lines.append("")
        report_lines.append(diagram)
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Topic Categories
        report_lines.append("## Topic Categories")
        report_lines.append("")

        categories = analysis.get("categories", {})
        for cat_name, cat_data in categories.items():
            report_lines.append(f"### {cat_name.replace('_', ' ').title()}")
            report_lines.append("")
            report_lines.append(f"**Description:** {cat_data.get('description', 'N/A')}")
            report_lines.append("")
            report_lines.append(f"**Why Trending:** {cat_data.get('trending_reason', 'N/A')}")
            report_lines.append("")

            # List related posts
            post_indices = cat_data.get("post_indices", [])
            if post_indices:
                report_lines.append("**Related Posts:**")
                for idx in post_indices[:5]:  # Limit to 5 posts per category
                    if 0 < idx <= len(posts):
                        post = posts[idx - 1]
                        title = post["title"]
                        score = post["score"]
                        url = post.get("url", "")
                        if url:
                            report_lines.append(f"- [{title}]({url}) ({score} points)")
                        else:
                            report_lines.append(f"- {title} ({score} points)")

            report_lines.append("")

        report_lines.append("---")
        report_lines.append("")

        # Notable Developments
        report_lines.append("## Notable Developments")
        report_lines.append("")

        developments = analysis.get("notable_developments", [])
        for dev in developments:
            report_lines.append(f"- {dev}")

        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Term Glossary
        report_lines.append("## Technical Terms Glossary")
        report_lines.append("")

        term_list = terms.get("terms", [])
        if term_list:
            for term_data in term_list:
                term_name = term_data.get("term", "")
                explanation = term_data.get("explanation", "")
                context = term_data.get("context", "")

                report_lines.append(f"### {term_name}")
                report_lines.append("")
                report_lines.append(f"**Explanation:** {explanation}")
                report_lines.append("")
                if context:
                    report_lines.append(f"**Context:** {context}")
                    report_lines.append("")
        else:
            report_lines.append("*No advanced terms identified in this analysis.*")
            report_lines.append("")

        report_lines.append("---")
        report_lines.append("")

        # Post Index
        report_lines.append("## Complete Post Index")
        report_lines.append("")

        for idx, post in enumerate(posts, 1):
            title = post["title"]
            score = post["score"]
            by = post.get("by", "unknown")
            url = post.get("url", "")

            if url:
                report_lines.append(f"{idx}. [{title}]({url})")
            else:
                report_lines.append(f"{idx}. {title}")

            report_lines.append(f"   - **Score:** {score} points | **By:** {by}")
            report_lines.append("")

        report_lines.append("---")
        report_lines.append("")
        report_lines.append(f"*Report generated by HN Research on {date_str}*")

        return "\n".join(report_lines)
