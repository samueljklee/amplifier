# Design Philosophy Explorer

Explore design philosophies and analyze implementations for improvement opportunities.

## Purpose

This tool helps you:
- **Understand design concepts** like color theory, motion, accessibility, responsiveness, themes, and animations
- **Explore design philosophies** through interactive guidance
- **Analyze existing implementations** to identify patterns and gaps
- **Get actionable recommendations** for improving your designs

## Quick Start

### Explore a Design Question

```bash
python -m scenarios.design_philosophy_explorer \
    --question "How do I create engaging animations?"
```

### Analyze a Directory

```bash
python -m scenarios.design_philosophy_explorer \
    --question "How can I improve my web app's design?" \
    --directory ./my-web-app/
```

### With Custom Output Path

```bash
python -m scenarios.design_philosophy_explorer \
    --question "What makes a great user experience?" \
    --directory ./my-app/ \
    --output ./reports/design-analysis.md
```

## Features

### 1. Philosophy Exploration
Deeply explores design concepts relevant to your question:
- Color theory and color systems
- Motion and animation principles
- Accessibility considerations
- Responsive design patterns
- Theming and consistency
- User experience fundamentals

### 2. Implementation Analysis
When you provide a directory, the tool analyzes:
- Design patterns used (color systems, animations, accessibility features)
- Strengths in the current implementation
- Gaps and missing considerations
- Overall design maturity

### 3. Actionable Critique
Provides prioritized recommendations:
- Critical improvements (high priority)
- Enhancement opportunities (medium priority)
- Future considerations (long-term)
- Resources and next steps

### 4. Comprehensive Report
Generates a markdown report with:
- Design concepts explained
- Implementation analysis (if directory provided)
- Prioritized recommendations
- Summary and key action items

## Command-Line Options

```
--question TEXT         Your design question [required]
--directory PATH        Optional directory to analyze
--output PATH          Output path for report
--resume               Resume from saved state
--reset                Reset state and start fresh
--verbose              Enable verbose logging
--help                 Show this message and exit
```

## Examples

### Example 1: Learn About Color Theory

```bash
python -m scenarios.design_philosophy_explorer \
    --question "How do I choose colors for my app?"
```

Generates a report explaining:
- Color theory fundamentals
- Practical guidance for color selection
- Accessibility considerations
- Examples from real products

### Example 2: Analyze Your React App

```bash
python -m scenarios.design_philosophy_explorer \
    --question "How accessible is my application?" \
    --directory ./src/components/
```

Analyzes your code for:
- ARIA attributes and semantic HTML
- Keyboard navigation support
- Color contrast ratios
- Responsive patterns
- Provides specific improvement suggestions

### Example 3: Motion Design Guidance

```bash
python -m scenarios.design_philosophy_explorer \
    --question "What makes animations feel natural?"
```

Explores:
- Animation timing and easing
- Motion design principles
- User perception psychology
- Performance considerations

## Output

The tool generates a comprehensive markdown report including:

```markdown
# Design Philosophy Exploration Report

## Design Concepts Explored
Core concepts, practical guidance, philosophy, and examples

## Implementation Analysis (if directory provided)
Patterns found, strengths, and gaps

## Recommendations & Next Steps
Prioritized suggestions with impact and effort estimates

## Summary
Key takeaways and action items
```

## Resume Capability

The tool automatically saves state, allowing you to:

```bash
# Start exploration
python -m scenarios.design_philosophy_explorer --question "..."

# Resume if interrupted
python -m scenarios.design_philosophy_explorer --question "..." --resume
```

State is saved in `.data/design_philosophy_explorer/sessions/`

## File Analysis

When analyzing directories, the tool looks for:
- CSS/SCSS files (`**/*.css`, `**/*.scss`)
- React/JSX files (`**/*.tsx`, `**/*.jsx`)
- Vue files (`**/*.vue`)
- HTML files (`**/*.html`)
- JavaScript files (`**/*.js`)

Uses **recursive glob patterns** to find files in subdirectories.

## Design Concepts Covered

- **Color Theory**: Palettes, contrast, accessibility
- **Motion**: Timing, easing, choreography, performance
- **Accessibility**: WCAG compliance, semantic HTML, keyboard navigation
- **Responsiveness**: Breakpoints, fluid layouts, mobile-first
- **Theming**: CSS variables, theme switching, consistency
- **Typography**: Hierarchy, readability, scale
- **Layout**: Grid systems, spacing, visual hierarchy
- **Components**: Reusability, composition, patterns

## Troubleshooting

### No Files Found
If directory analysis finds no files:
- Check that the directory contains design-related files (CSS, JSX, Vue, etc.)
- Verify the path is correct
- Ensure files are readable

### Analysis Timeout
For large directories:
- The tool samples up to 10 files to prevent context overflow
- Focus on specific subdirectories for deeper analysis

### LLM Errors
If AI queries fail:
- The tool provides fallback responses
- Check internet connectivity
- Retry with `--reset` flag

## Philosophy

This tool embodies:
- **Ruthless Simplicity**: Clear, focused analysis without over-engineering
- **User-Centered**: Prioritizes accessibility and usability
- **Actionable**: Provides concrete next steps, not just theory
- **Educational**: Explains the "why" behind recommendations

## Related Resources

- [Amplifier Design Philosophy](../../ai_context/DESIGN-PHILOSOPHY.md)
- [Design Principles](../../ai_context/DESIGN-PRINCIPLES.md)
- [Design Framework](../../ai_context/design/DESIGN-FRAMEWORK.md)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
