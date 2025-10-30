"""
Report generator core functionality.

Generates expense reports in markdown and PDF formats.
"""

from pathlib import Path
from typing import Any

from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """Generates expense reports in various formats."""

    async def generate_report(
        self,
        expenses: list[dict[str, Any]],
        time_entries: list[dict[str, Any]],
        output_path: Path,
        output_format: str = "markdown",
    ) -> Path | None:
        """Generate expense report.

        Args:
            expenses: List of categorized expenses
            time_entries: List of time entries
            output_path: Output file path
            output_format: Output format (markdown or pdf)

        Returns:
            Path to generated report or None if failed
        """
        logger.debug(f"Generating {output_format} report")

        try:
            # Generate markdown content
            markdown_content = self._generate_markdown(expenses, time_entries)

            if output_format == "markdown":
                # Write markdown directly
                output_path.write_text(markdown_content)
                logger.info(f"Markdown report saved to {output_path}")
                return output_path

            if output_format == "pdf":
                # For PDF, we'd need to convert markdown to PDF
                # Using a library like weasyprint or markdown2pdf
                # For now, save as markdown with .pdf extension warning
                logger.warning("PDF generation requires additional dependencies. Saving as markdown.")
                md_path = output_path.with_suffix(".md")
                md_path.write_text(markdown_content)
                logger.info(f"Report saved as markdown to {md_path}")
                return md_path

            logger.error(f"Unsupported output format: {output_format}")
            return None

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return None

    def _generate_markdown(self, expenses: list[dict[str, Any]], time_entries: list[dict[str, Any]]) -> str:
        """Generate markdown report content.

        Args:
            expenses: List of expenses
            time_entries: List of time entries

        Returns:
            Markdown formatted report
        """
        lines = []
        lines.append("# Rental Expense Report\n")

        # Summary section
        lines.append("## Summary\n")

        # Calculate totals by category
        category_totals: dict[str, float] = {}
        total_expenses = 0.0

        for exp in expenses:
            category = exp.get("category", "other")
            amount = exp.get("amount", 0)
            if isinstance(amount, int | float):
                category_totals[category] = category_totals.get(category, 0) + amount
                total_expenses += amount

        lines.append("### Expenses by Category\n")
        for category, total in sorted(category_totals.items()):
            lines.append(f"- **{category.title()}**: ${total:.2f}")

        lines.append(f"\n**Total Expenses**: ${total_expenses:.2f}\n")

        # Time summary
        if time_entries:
            total_hours = sum(
                entry.get("hours", 0) for entry in time_entries if isinstance(entry.get("hours"), int | float)
            )
            lines.append(f"**Total Hours**: {total_hours:.1f}\n")

        # Detailed expenses
        lines.append("\n## Detailed Expenses\n")

        # Group by category
        expenses_by_category: dict[str, list[dict[str, Any]]] = {}
        for exp in expenses:
            category = exp.get("category", "other")
            if category not in expenses_by_category:
                expenses_by_category[category] = []
            expenses_by_category[category].append(exp)

        for category in sorted(expenses_by_category.keys()):
            lines.append(f"### {category.title()}\n")
            lines.append("| Date | Vendor | Description | Amount | Source |")
            lines.append("|------|--------|-------------|--------|--------|")

            for exp in expenses_by_category[category]:
                date = exp.get("date", "N/A")
                vendor = exp.get("vendor", "Unknown")
                description = exp.get("description", "")
                amount = exp.get("amount", 0)
                currency = exp.get("currency", "USD")
                source = exp.get("source", "Unknown")

                # Truncate long descriptions
                if len(description) > 50:
                    description = description[:47] + "..."

                lines.append(f"| {date} | {vendor} | {description} | ${amount:.2f} {currency} | {source} |")

            lines.append("")

        # Time entries section
        if time_entries:
            lines.append("\n## Time Entries\n")
            lines.append("| Date | Person | Hours | Activity | Rate | Source |")
            lines.append("|------|--------|-------|----------|------|--------|")

            for entry in time_entries:
                date = entry.get("date", "N/A")
                person = entry.get("person", "Unknown")
                hours = entry.get("hours", 0)
                activity = entry.get("activity", "")
                rate = entry.get("rate", "N/A")
                currency = entry.get("currency", "")
                source = entry.get("source", "Unknown")

                # Truncate long activities
                if len(activity) > 50:
                    activity = activity[:47] + "..."

                rate_str = f"${rate:.2f} {currency}" if isinstance(rate, int | float) else "N/A"

                lines.append(f"| {date} | {person} | {hours:.1f} | {activity} | {rate_str} | {source} |")

        return "\n".join(lines)
