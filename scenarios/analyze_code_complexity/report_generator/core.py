"""Markdown report generator for code complexity analysis."""

from datetime import datetime

from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.logger import LogFormat

logger = ToolkitLogger(name="report_generator", format=LogFormat.PLAIN)


class ReportGenerator:
    """Generates comprehensive markdown reports."""

    async def generate_report(
        self,
        files: list[dict],
        metrics_results: list[dict],
        quality_results: list[dict],
    ) -> str:
        """Generate comprehensive markdown report.

        Args:
            files: List of discovered files
            metrics_results: Metrics analysis results
            quality_results: Quality analysis results

        Returns:
            Markdown report content
        """
        # Calculate summary statistics
        summary = self._calculate_summary(files, metrics_results, quality_results)

        # Generate report sections
        report_parts = [
            self._generate_header(),
            self._generate_executive_summary(summary),
            self._generate_metrics_overview(metrics_results),
            self._generate_quality_overview(quality_results),
            self._generate_detailed_findings(metrics_results, quality_results),
            self._generate_recommendations(quality_results),
            self._generate_file_list(files),
        ]

        return "\n\n".join(report_parts)

    def _generate_header(self) -> str:
        """Generate report header."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""# Code Complexity Analysis Report

**Generated:** {timestamp}

---
"""

    def _generate_executive_summary(self, summary: dict) -> str:
        """Generate executive summary section."""
        return f"""## Executive Summary

- **Total Files Analyzed:** {summary["total_files"]}
- **Total Lines of Code:** {summary["total_lines"]:,}
- **Programming Languages:** {", ".join(summary["languages"])}
- **Average Cyclomatic Complexity:** {summary["avg_complexity"]:.1f}
- **Average Maintainability Index:** {summary["avg_maintainability"]:.1f}/100
- **Total Issues Found:** {summary["total_issues"]}
  - Critical: {summary["critical_issues"]}
  - High: {summary["high_issues"]}
  - Medium: {summary["medium_issues"]}
  - Low: {summary["low_issues"]}
"""

    def _generate_metrics_overview(self, metrics_results: list[dict]) -> str:
        """Generate metrics overview section."""
        lines = ["## Complexity Metrics Overview\n"]

        if not metrics_results:
            return "## Complexity Metrics Overview\n\nNo metrics data available.\n"

        # Table of files by complexity
        lines.append("### Files by Cyclomatic Complexity\n")
        lines.append("| File | Language | Complexity | Lines | Maintainability |")
        lines.append("|------|----------|------------|-------|-----------------|")

        # Sort by complexity (descending)
        sorted_results = sorted(
            metrics_results, key=lambda r: r.get("metrics", {}).get("cyclomatic_complexity", 0), reverse=True
        )[:20]  # Top 20 most complex files

        for result in sorted_results:
            metrics = result.get("metrics", {})
            file_info = result.get("file_info", {})

            name = file_info.get("name", "Unknown")
            lang = file_info.get("language", "Unknown")
            complexity = metrics.get("cyclomatic_complexity", 0)
            lines_count = metrics.get("total_lines", 0)
            maintainability = metrics.get("maintainability_index", 0)

            lines.append(f"| {name} | {lang} | {complexity} | {lines_count} | {maintainability:.0f}/100 |")

        return "\n".join(lines)

    def _generate_quality_overview(self, quality_results: list[dict]) -> str:
        """Generate quality overview section."""
        lines = ["## Code Quality Overview\n"]

        if not quality_results:
            return "## Code Quality Overview\n\nNo quality data available.\n"

        # Count issues by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        all_issues = []

        for result in quality_results:
            issues = result.get("issues", [])
            all_issues.extend(issues)
            for issue in issues:
                severity = issue.get("severity", "low")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

        lines.append("### Issues by Severity\n")
        lines.append(f"- **Critical:** {severity_counts['critical']} issues")
        lines.append(f"- **High:** {severity_counts['high']} issues")
        lines.append(f"- **Medium:** {severity_counts['medium']} issues")
        lines.append(f"- **Low:** {severity_counts['low']} issues")

        # Top issues by severity
        if severity_counts["critical"] > 0 or severity_counts["high"] > 0:
            lines.append("\n### Critical and High Priority Issues\n")

            critical_high = [i for i in all_issues if i.get("severity") in ["critical", "high"]]
            critical_high.sort(key=lambda i: 0 if i.get("severity") == "critical" else 1)

            for issue in critical_high[:10]:  # Top 10
                severity = issue.get("severity", "unknown")
                title = issue.get("title", "Unknown issue")
                lines.append(f"- **[{severity.upper()}]** {title}")

        return "\n".join(lines)

    def _generate_detailed_findings(
        self,
        metrics_results: list[dict],
        quality_results: list[dict],
    ) -> str:
        """Generate detailed findings section."""
        lines = ["## Detailed Findings\n"]

        # Merge results by file
        files_map = {}

        for result in metrics_results:
            file_info = result.get("file_info", {})
            path = file_info.get("relative_path", "Unknown")
            files_map[path] = {"metrics": result, "quality": None}

        for result in quality_results:
            file_info = result.get("file_info", {})
            path = file_info.get("relative_path", "Unknown")
            if path in files_map:
                files_map[path]["quality"] = result

        # Generate findings for each file
        for path, data in sorted(files_map.items())[:15]:  # Top 15 files
            metrics_result = data.get("metrics", {})
            quality_result = data.get("quality", {})

            if not metrics_result:
                continue

            lines.append(f"\n### {path}\n")

            # Metrics
            metrics = metrics_result.get("metrics", {})
            if metrics:
                lines.append("**Complexity Metrics:**")
                lines.append(f"- Cyclomatic Complexity: {metrics.get('cyclomatic_complexity', 'N/A')}")
                lines.append(f"- Lines of Code: {metrics.get('code_lines', 'N/A')}")
                lines.append(f"- Max Function Length: {metrics.get('max_function_length', 'N/A')}")
                lines.append(f"- Max Nesting Depth: {metrics.get('max_nesting_depth', 'N/A')}")
                lines.append(f"- Maintainability Index: {metrics.get('maintainability_index', 'N/A')}/100")

            # Quality issues
            if quality_result:
                issues = quality_result.get("issues", [])
                if issues:
                    lines.append("\n**Quality Issues:**")
                    for issue in issues[:5]:  # Top 5 issues per file
                        severity = issue.get("severity", "unknown")
                        title = issue.get("title", "Unknown")
                        lines.append(f"- [{severity.upper()}] {title}")

        return "\n".join(lines)

    def _generate_recommendations(self, quality_results: list[dict]) -> str:
        """Generate recommendations section."""
        lines = ["## Recommendations\n"]

        # Collect all recommendations
        recommendations = set()

        for result in quality_results:
            issues = result.get("issues", [])
            for issue in issues:
                if issue.get("severity") in ["critical", "high"]:
                    rec = issue.get("recommendation", "")
                    if rec:
                        recommendations.add(rec)

        if recommendations:
            lines.append("Based on the analysis, here are the top recommendations:\n")
            for i, rec in enumerate(sorted(recommendations)[:10], 1):
                lines.append(f"{i}. {rec}")
        else:
            lines.append("No critical recommendations at this time. Continue monitoring code quality.")

        return "\n".join(lines)

    def _generate_file_list(self, files: list[dict]) -> str:
        """Generate complete file list section."""
        lines = ["## Analyzed Files\n"]

        # Group by language
        by_language = {}
        for f in files:
            lang = f.get("language", "Unknown")
            if lang not in by_language:
                by_language[lang] = []
            by_language[lang].append(f)

        for lang in sorted(by_language.keys()):
            files_list = by_language[lang]
            lines.append(f"\n### {lang} ({len(files_list)} files)\n")

            for f in sorted(files_list, key=lambda x: x.get("relative_path", ""))[:50]:
                path = f.get("relative_path", "Unknown")
                loc = f.get("lines", 0)
                lines.append(f"- `{path}` ({loc} lines)")

        return "\n".join(lines)

    def _calculate_summary(
        self,
        files: list[dict],
        metrics_results: list[dict],
        quality_results: list[dict],
    ) -> dict:
        """Calculate summary statistics.

        Args:
            files: List of files
            metrics_results: Metrics results
            quality_results: Quality results

        Returns:
            Summary statistics dictionary
        """
        # Collect languages
        languages = {f.get("language", "Unknown") for f in files}

        # Calculate total lines
        total_lines = sum(f.get("lines", 0) for f in files)

        # Calculate average complexity
        complexities = [r.get("metrics", {}).get("cyclomatic_complexity", 0) for r in metrics_results]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0

        # Calculate average maintainability
        maintainability = [r.get("metrics", {}).get("maintainability_index", 0) for r in metrics_results]
        avg_maintainability = sum(maintainability) / len(maintainability) if maintainability else 0

        # Count issues by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for result in quality_results:
            issues = result.get("issues", [])
            for issue in issues:
                severity = issue.get("severity", "low")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "total_files": len(files),
            "total_lines": total_lines,
            "languages": sorted(languages),
            "avg_complexity": avg_complexity,
            "avg_maintainability": avg_maintainability,
            "total_issues": sum(severity_counts.values()),
            "critical_issues": severity_counts["critical"],
            "high_issues": severity_counts["high"],
            "medium_issues": severity_counts["medium"],
            "low_issues": severity_counts["low"],
        }
