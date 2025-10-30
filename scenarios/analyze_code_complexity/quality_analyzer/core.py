"""Code quality analyzer using LLM."""

from pathlib import Path

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json
from amplifier.ccsdk_toolkit.logger import LogFormat

logger = ToolkitLogger(name="quality_analyzer", format=LogFormat.PLAIN)


class QualityAnalyzer:
    """Analyzes code quality and security issues using LLM."""

    def __init__(self):
        """Initialize quality analyzer."""
        self.system_prompt = """You are an expert code quality and security analyzer. Your task is to identify code smells, security vulnerabilities, and quality issues in code files.

For each code file, analyze for:
1. Code duplication - repeated code patterns
2. Code smells - long methods, large classes, feature envy, etc.
3. Security issues - SQL injection, XSS, hardcoded secrets, etc.
4. Best practice violations - naming conventions, error handling, etc.
5. Technical debt indicators

Return your analysis as a JSON object with the following structure:
{
    "file": "filename",
    "language": "language name",
    "issues": [
        {
            "type": "code_smell" | "security" | "duplication" | "best_practice",
            "severity": "critical" | "high" | "medium" | "low",
            "title": "Brief issue title",
            "description": "Detailed description",
            "line_start": number or null,
            "line_end": number or null,
            "recommendation": "How to fix this issue"
        }
    ],
    "duplication_score": number (0-100, higher means more duplication),
    "quality_score": number (0-100, higher is better),
    "summary": "Overall quality assessment"
}

Be thorough but focus on actionable issues. Avoid false positives."""

    async def analyze_quality(self, files: list[dict]) -> list[dict]:
        """Analyze code quality for all files.

        Args:
            files: List of file dictionaries from scanner

        Returns:
            List of quality analysis results
        """
        results = []

        # Analyze files in batches to show progress
        batch_size = 5
        for i in range(0, len(files), batch_size):
            batch = files[i : i + batch_size]
            logger.info(f"Analyzing quality: {i + 1}-{min(i + batch_size, len(files))} of {len(files)}")

            for file_info in batch:
                try:
                    quality = await self._analyze_file(file_info)
                    if quality:
                        results.append(quality)
                except Exception as e:
                    logger.error(f"Failed to analyze {file_info['name']}: {e}")
                    continue

        return results

    async def _analyze_file(self, file_info: dict) -> dict | None:
        """Analyze a single file for quality issues.

        Args:
            file_info: File dictionary with path and metadata

        Returns:
            Quality analysis result or None if failed
        """
        file_path = Path(file_info["path"])

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Cannot read {file_path}: {e}")
            return None

        # Truncate very long files for LLM analysis
        max_chars = 10000
        if len(content) > max_chars:
            content = content[:max_chars] + "\n... (truncated)"

        prompt = f"""Analyze the following {file_info["language"]} code file for quality issues, code smells, and security vulnerabilities.

File: {file_info["name"]}
Language: {file_info["language"]}

Code:
```{file_info["language"].lower()}
{content}
```

Provide detailed quality analysis as JSON, focusing on actionable issues."""

        options = SessionOptions(system_prompt=self.system_prompt)

        async with ClaudeSession(options) as claude:
            response = await claude.query(prompt)

            # Parse LLM response with defensive parsing
            result = parse_llm_json(response.content)

            # REQUIRED: Type guard before using as dict
            if not isinstance(result, dict):
                logger.error(f"Expected dict from LLM for {file_info['name']}, got invalid format")
                return None

            # Add file metadata
            result["file_info"] = file_info

            return result
