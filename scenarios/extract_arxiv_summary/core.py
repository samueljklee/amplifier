"""
Core functionality for extracting arXiv paper summaries.

Fetches arXiv papers and extracts key points relevant to AI engineers.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.defensive import parse_llm_json


async def extract_arxiv_summary(arxiv_url: str, focus_area: str, output_path: Path, logger: ToolkitLogger) -> bool:
    """Extract summary and key points from an arXiv paper.

    Args:
        arxiv_url: URL to the arXiv paper
        focus_area: Area of focus for key points extraction
        output_path: Path to save the summary JSON
        logger: Logger instance for progress tracking

    Returns:
        True if successful, False otherwise
    """
    # Create session directory for runtime data
    session_dir = _create_session_dir()
    logger.info(f"📁 Session directory: {session_dir}")

    # Step 1: Fetch paper content
    logger.stage_transition(None, "fetch_paper", estimated_duration=10)
    logger.info("📥 Fetching arXiv paper...")

    paper_content = await _fetch_arxiv_paper(arxiv_url, logger)
    if not paper_content:
        logger.error("Failed to fetch paper content")
        return False

    logger.info(f"✓ Fetched paper (approx {len(paper_content)} characters)")

    # Save raw paper content to session
    raw_paper_file = session_dir / "raw_paper.txt"
    raw_paper_file.write_text(paper_content)
    logger.info(f"💾 Saved raw paper to: {raw_paper_file}")

    # Step 2: Extract summary and key points
    logger.stage_transition("fetch_paper", "extract_summary", estimated_duration=60)
    logger.info("🔍 Extracting summary and key points...")

    summary_data = await _extract_summary_with_llm(paper_content, focus_area, logger)
    if not summary_data:
        logger.error("Failed to extract summary")
        return False

    logger.info(f"✓ Extracted {len(summary_data.get('key_points', []))} key points")

    # Step 3: Save results
    logger.stage_transition("extract_summary", "save_results", estimated_duration=5)
    logger.info("💾 Saving results...")

    # Add metadata
    summary_data["metadata"] = {
        "arxiv_url": arxiv_url,
        "focus_area": focus_area,
        "extracted_at": datetime.now().isoformat(),
        "session_dir": str(session_dir),
    }

    # Save to output path
    output_path.write_text(json.dumps(summary_data, indent=2))
    logger.info(f"✓ Results saved to: {output_path}")

    # Also save to session directory
    session_output = session_dir / "summary.json"
    session_output.write_text(json.dumps(summary_data, indent=2))
    logger.info(f"✓ Session copy saved to: {session_output}")

    return True


async def _fetch_arxiv_paper(url: str, logger: ToolkitLogger) -> str | None:
    """Fetch arXiv paper content from URL.

    Args:
        url: arXiv paper URL
        logger: Logger instance

    Returns:
        Paper content as string, or None if failed
    """
    try:
        # Extract arXiv ID from URL
        arxiv_id = _extract_arxiv_id(url)
        if not arxiv_id:
            logger.error("Could not extract arXiv ID from URL")
            return None

        logger.info(f"arXiv ID: {arxiv_id}")

        # Use Claude's web fetch capability to get the paper
        # We'll fetch the abstract page which contains title, authors, abstract
        abs_url = f"https://arxiv.org/abs/{arxiv_id}"

        prompt = f"""Fetch and extract the complete content from this arXiv paper page.

URL: {abs_url}

Extract:
1. Title
2. Authors
3. Complete abstract
4. Submission info (dates, versions)
5. Any additional metadata available

Return the extracted information in a clear, structured format."""

        options = SessionOptions(
            system_prompt="You are an expert at extracting academic paper information from web pages.",
            retry_attempts=2,
        )

        async with ClaudeSession(options) as session:
            response = await session.query(prompt)
            content = response.content.strip()

            # Validate we got meaningful content
            if len(content) < 100:
                logger.error("Fetched content too short, likely failed")
                return None

            return content

    except Exception as e:
        logger.error(f"Error fetching paper: {e}")
        return None


def _extract_arxiv_id(url: str) -> str | None:
    """Extract arXiv ID from URL.

    Args:
        url: arXiv URL

    Returns:
        arXiv ID or None if not found
    """
    # Match patterns like:
    # https://arxiv.org/abs/2401.12345
    # https://arxiv.org/pdf/2401.12345.pdf
    # arxiv.org/abs/2401.12345v1
    pattern = r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)"
    match = re.search(pattern, url)
    if match:
        return match.group(1).replace(".pdf", "")
    return None


async def _extract_summary_with_llm(
    paper_content: str, focus_area: str, logger: ToolkitLogger
) -> dict[str, Any] | None:
    """Extract structured summary using LLM.

    Args:
        paper_content: Full paper content
        focus_area: Focus area for key points
        logger: Logger instance

    Returns:
        Dictionary with summary and key points, or None if failed
    """
    prompt = f"""Analyze this arXiv paper and extract key information.

=== PAPER CONTENT ===
{paper_content}

=== FOCUS AREA ===
{focus_area}

Extract the following information in JSON format:

{{
  "title": "Paper title",
  "authors": ["Author 1", "Author 2"],
  "summary": "A concise 2-3 paragraph summary of the paper's main contributions and findings",
  "key_points_for_ai_engineers": [
    "Point 1: Specific finding or technique relevant to {focus_area}",
    "Point 2: Practical application or implication",
    "Point 3: Technical detail or methodology of interest",
    "Point 4: Limitations or future work mentioned"
  ],
  "technical_details": [
    "Important algorithm or method",
    "Key metrics or results",
    "Novel techniques introduced"
  ],
  "practical_implications": [
    "How this applies to real-world software engineering",
    "Potential use cases or applications",
    "Implementation considerations"
  ],
  "relevance_score": "1-10 score of relevance to {focus_area}",
  "tags": ["tag1", "tag2", "tag3"]
}}

Focus on extracting points most relevant to software engineers working in AI.
Be specific and actionable in the key points.
Return ONLY valid JSON, no additional text."""

    options = SessionOptions(
        system_prompt="You are an expert at analyzing academic papers and extracting insights for software engineers.",
        retry_attempts=2,
    )

    try:
        async with ClaudeSession(options) as session:
            response = await session.query(prompt)
            content = response.content.strip()

            # Use defensive parsing
            summary_data = parse_llm_json(content)

            # Validate we got a dict
            if not isinstance(summary_data, dict):
                logger.error("Expected JSON object from LLM")
                return None

            # Validate required fields
            required_fields = ["summary", "key_points_for_ai_engineers"]
            for field in required_fields:
                if field not in summary_data:
                    logger.error(f"Missing required field: {field}")
                    return None

            # Ensure key_points is a list
            if not isinstance(summary_data.get("key_points_for_ai_engineers"), list):
                logger.error("key_points_for_ai_engineers must be a list")
                return None

            return summary_data

    except Exception as e:
        logger.error(f"Error extracting summary: {e}")
        return None


def _create_session_dir() -> Path:
    """Create session directory for runtime data.

    Returns:
        Path to session directory
    """
    import uuid
    from datetime import datetime

    # Create session directory in .data/
    base_dir = Path.cwd() / ".data" / "extract_arxiv_summary" / "sessions"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    guid = uuid.uuid4().hex[:8]
    session_dir = base_dir / f"{timestamp}_{guid}"
    session_dir.mkdir(parents=True, exist_ok=True)

    # Create 'latest' symlink for easy resume
    latest_link = base_dir / "latest"
    if latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(session_dir.name)

    return session_dir
