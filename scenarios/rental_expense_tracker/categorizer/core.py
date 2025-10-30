"""
Categorizer core functionality.

Categorizes expenses into predefined categories using LLM.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)

EXPENSE_CATEGORIES = [
    "cleaning",
    "maintenance",
    "utilities",
    "platform fees",
    "contractor payments",
    "supplies",
    "other",
]


class Categorizer:
    """Categorizes expenses into predefined categories."""

    async def categorize_expenses(self, expenses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Categorize expenses into predefined categories.

        Args:
            expenses: List of expense dictionaries

        Returns:
            List of expenses with added 'category' field
        """
        if not expenses:
            return []

        logger.debug(f"Categorizing {len(expenses)} expenses")

        # Build expenses summary for LLM
        expenses_summary = []
        for i, exp in enumerate(expenses):
            summary = {
                "id": i,
                "vendor": exp.get("vendor", "Unknown"),
                "description": exp.get("description", ""),
                "amount": exp.get("amount", 0),
                "category_hint": exp.get("category_hint", ""),
            }
            expenses_summary.append(summary)

        system_prompt = f"""You are an expense categorization assistant for short-term rental properties.

Categorize expenses into these categories:
{", ".join(EXPENSE_CATEGORIES)}

Return a JSON array where each object has:
- id: The expense ID (from input)
- category: The chosen category (must be one of the allowed categories)
- confidence: Your confidence level (high/medium/low)"""

        prompt = f"""Categorize these expenses:

{expenses_summary}

Return a JSON array with id, category, and confidence for each expense."""

        options = SessionOptions(system_prompt=system_prompt)

        async with ClaudeSession(options) as claude:
            response = await claude.query(prompt)
            parsed = parse_llm_json(response.content)

            # Type guard - CRITICAL for defensive parsing
            if not isinstance(parsed, list):
                logger.error(f"Expected list from LLM, got {type(parsed).__name__}")
                # Fallback: use category hints or "other"
                for exp in expenses:
                    exp["category"] = exp.get("category_hint", "other")
                    exp["confidence"] = "low"
                return expenses

            # Apply categories to expenses
            category_map = {}
            for item in parsed:
                if isinstance(item, dict) and "id" in item and "category" in item:
                    category_map[item["id"]] = {
                        "category": item["category"],
                        "confidence": item.get("confidence", "unknown"),
                    }

            # Update expenses with categories
            for i, exp in enumerate(expenses):
                if i in category_map:
                    exp["category"] = category_map[i]["category"]
                    exp["confidence"] = category_map[i]["confidence"]
                else:
                    # Fallback to hint or "other"
                    exp["category"] = exp.get("category_hint", "other")
                    exp["confidence"] = "low"

            return expenses
