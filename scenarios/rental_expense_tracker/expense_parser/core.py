"""
Expense parser core functionality.

Extracts expense information from text using LLM.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class ExpenseParser:
    """Parses expense information from text."""

    async def parse_expenses(self, text: str, source_name: str) -> list[dict[str, Any]]:
        """Parse expenses from extracted text.

        Args:
            text: Extracted text from PDF
            source_name: Name of source file

        Returns:
            List of expense dictionaries
        """
        logger.debug(f"Parsing expenses from {source_name}")

        system_prompt = """You are an expense extraction assistant. Extract expense information from receipts and invoices.

For each expense found, extract:
- amount: The monetary amount (as a number)
- currency: The currency code (e.g., USD, EUR)
- date: The date of the expense (YYYY-MM-DD format if possible, or as written)
- vendor: The vendor/merchant name
- description: Description of the expense
- category_hint: Your best guess at the category (cleaning, maintenance, utilities, platform fees, contractor payments, supplies, other)

Return a JSON array of expense objects. If no expenses are found, return an empty array []."""

        prompt = f"""Extract all expenses from this receipt/invoice:

{text}

Return a JSON array of expense objects."""

        options = SessionOptions(system_prompt=system_prompt)

        async with ClaudeSession(options) as claude:
            response = await claude.query(prompt)
            parsed = parse_llm_json(response.content)

            # Type guard - CRITICAL for defensive parsing
            if not isinstance(parsed, list):
                logger.error(f"Expected list from LLM, got {type(parsed).__name__}")
                return []

            # Add source metadata to each expense
            expenses = []
            for item in parsed:
                if isinstance(item, dict):
                    item["source"] = source_name
                    expenses.append(item)
                else:
                    logger.warning(f"Skipping non-dict expense item: {item}")

            return expenses
