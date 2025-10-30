"""
Time parser core functionality.

Extracts time/hours information from text using LLM.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class TimeParser:
    """Parses time/hours information from text."""

    async def parse_time_entries(self, text: str, source_name: str) -> list[dict[str, Any]]:
        """Parse time entries from extracted text.

        Args:
            text: Extracted text from PDF
            source_name: Name of source file

        Returns:
            List of time entry dictionaries
        """
        logger.debug(f"Parsing time entries from {source_name}")

        system_prompt = """You are a time tracking assistant. Extract time/hours information from documents.

For each time entry found, extract:
- hours: The number of hours worked (as a number)
- date: The date of work (YYYY-MM-DD format if possible, or as written)
- person: The person/contractor who worked
- activity: Description of the activity/work performed
- rate: Hourly rate if mentioned (as a number)
- currency: Currency for the rate if mentioned

Return a JSON array of time entry objects. If no time entries are found, return an empty array []."""

        prompt = f"""Extract all time/hours entries from this document:

{text}

Return a JSON array of time entry objects. Only include entries if there are clear time/hours references."""

        options = SessionOptions(system_prompt=system_prompt)

        async with ClaudeSession(options) as claude:
            response = await claude.query(prompt)
            parsed = parse_llm_json(response.content)

            # Type guard - CRITICAL for defensive parsing
            if not isinstance(parsed, list):
                logger.error(f"Expected list from LLM, got {type(parsed).__name__}")
                return []

            # Add source metadata to each time entry
            time_entries = []
            for item in parsed:
                if isinstance(item, dict):
                    item["source"] = source_name
                    time_entries.append(item)
                else:
                    logger.warning(f"Skipping non-dict time entry: {item}")

            return time_entries
