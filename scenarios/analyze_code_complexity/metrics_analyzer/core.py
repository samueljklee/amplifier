"""Code metrics analyzer using LLM."""

from pathlib import Path

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json
from amplifier.ccsdk_toolkit.logger import LogFormat

logger = ToolkitLogger(name="metrics_analyzer", format=LogFormat.PLAIN)


class MetricsAnalyzer:
    """Analyzes code complexity metrics using LLM."""

    def __init__(self):
        """Initialize metrics analyzer."""
        self.system_prompt = """You are an expert code complexity analyzer. Your task is to analyze code files and calculate various complexity metrics.

For each code file, you must analyze:
1. Cyclomatic complexity - number of independent paths through the code
2. Lines of code metrics (total lines, code lines, comment lines, blank lines)
3. Function/method length analysis
4. Nesting depth (maximum level of nested blocks)
5. Maintainability index (scale of 0-100, higher is better)

Return your analysis as a JSON object with the following structure:
{
    "file": "filename",
    "language": "language name",
    "metrics": {
        "cyclomatic_complexity": number,
        "total_lines": number,
        "code_lines": number,
        "comment_lines": number,
        "blank_lines": number,
        "max_function_length": number,
        "average_function_length": number,
        "max_nesting_depth": number,
        "maintainability_index": number
    },
    "functions": [
        {
            "name": "function_name",
            "line_start": number,
            "line_end": number,
            "complexity": number,
            "length": number
        }
    ],
    "summary": "Brief summary of complexity findings"
}

Be precise and accurate. Calculate real numbers based on the code structure."""

    async def analyze_metrics(self, files: list[dict]) -> list[dict]:
        """Analyze complexity metrics for all files.

        Args:
            files: List of file dictionaries from scanner

        Returns:
            List of metrics results
        """
        results = []

        # Analyze files in batches to show progress
        batch_size = 5
        for i in range(0, len(files), batch_size):
            batch = files[i : i + batch_size]
            logger.info(f"Analyzing metrics: {i + 1}-{min(i + batch_size, len(files))} of {len(files)}")

            for file_info in batch:
                try:
                    metrics = await self._analyze_file(file_info)
                    if metrics:
                        results.append(metrics)
                except Exception as e:
                    logger.error(f"Failed to analyze {file_info['name']}: {e}")
                    continue

        return results

    async def _analyze_file(self, file_info: dict) -> dict | None:
        """Analyze a single file.

        Args:
            file_info: File dictionary with path and metadata

        Returns:
            Metrics result dictionary or None if failed
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

        prompt = f"""Analyze the following {file_info["language"]} code file and calculate complexity metrics.

File: {file_info["name"]}
Language: {file_info["language"]}

Code:
```{file_info["language"].lower()}
{content}
```

Provide detailed metrics analysis as JSON."""

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
