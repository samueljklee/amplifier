"""Scenario base utilities for parameter discovery and introspection.

This module provides decorators and utilities that enable scenarios to expose
their parameters programmatically, allowing the Web UI to discover and build
forms dynamically without hardcoding parameter knowledge.
"""

import json
from typing import Any

import click


def get_parameter_schema(
    command: click.Command, version: str = "1.0", display_name: str | None = None
) -> dict[str, Any]:
    """Extract parameter schema from a Click command.

    Args:
        command: The Click command to introspect
        version: Schema version
        display_name: Human-readable name

    Returns:
        Dictionary containing:
        - version: Schema version
        - name: Command name
        - display_name: Human-readable name
        - description: Command help text
        - parameters: List of parameter definitions with:
          - name: Parameter name
          - type: Parameter type (string, path, integer, boolean, etc.)
          - required: Whether parameter is required
          - default: Default value if any
          - help: Help text
          - cli_flag: The CLI flag (e.g., "--input")
    """
    params = []
    for param in command.params:
        if isinstance(param, click.Option) and param.name != "describe_parameters":
            # Convert Path objects to strings for JSON serialization
            default_value = param.default
            if default_value is not None and hasattr(default_value, "__fspath__"):
                # This is a Path-like object, convert to string
                default_value = str(default_value)

            param_def = {
                "name": param.name,
                "type": _map_click_type(param.type),
                "required": param.required,
                "default": default_value,
                "help": param.help or "",
                "cli_flag": param.opts[0] if param.opts else f"--{param.name}",
            }
            params.append(param_def)

    return {
        "version": version,
        "name": command.name or "main",
        "display_name": display_name or _extract_display_name(command),
        "description": command.help or "",
        "parameters": params,
    }


def _extract_display_name(command: click.Command) -> str:
    """Extract display name from command docstring or name.

    Args:
        command: The Click command to extract display name from

    Returns:
        Display name derived from first line of docstring or titlecased command name
    """
    if command.help:
        # Use first line of docstring
        return command.help.split("\n")[0].strip()
    # Fallback to titlecased command name
    return (command.name or "main").replace("_", " ").title()


def _map_click_type(click_type: Any) -> str:
    """Map Click parameter types to simple type strings.

    Args:
        click_type: The Click type object

    Returns:
        Simple type string: "path", "directory", "string", "integer", "boolean", "choice:val1,val2"
    """
    if isinstance(click_type, click.Path):
        # Distinguish between directory-only paths and file/mixed paths
        # file_okay=False means it must be a directory
        if not click_type.file_okay and click_type.dir_okay:
            return "directory"
        return "path"
    if isinstance(click_type, click.Choice):
        return f"choice:{','.join(click_type.choices)}"
    # Check type name for built-in types (click.INT, click.BOOL, etc. are instances)
    type_name = type(click_type).__name__
    if type_name == "IntParamType":
        return "integer"
    if type_name == "BoolParamType":
        return "boolean"
    if type_name == "FloatParamType":
        return "float"
    return "string"


def add_describe_flag(func: Any = None, *, version: str = "1.0", display_name: str | None = None):
    """Decorator that adds --describe-parameters flag with version/display_name support.

    This flag enables programmatic discovery of command parameters.
    When invoked with --describe-parameters, the command outputs a JSON
    schema of all parameters and exits.

    Supports both usage patterns:
        @add_describe_flag  # Old style (backward compatible)
        @add_describe_flag(version="1.0", display_name="Blog Post Writer")  # New style

    Args:
        func: The Click command function to decorate (for old style usage)
        version: Schema version (default: "1.0")
        display_name: Human-readable name (default: derived from docstring)

    Usage:
        @add_describe_flag(version="1.0", display_name="Blog Post Writer")
        @click.command()
        @click.option("--input", required=True, help="Input file")
        def main(input: str):
            '''Transform ideas into polished blog posts.'''
            pass  # Implementation here

    Then:
        python -m scenarios.my_scenario --describe-parameters
        # Outputs JSON schema with version and display_name

    Returns:
        Decorator function that adds parameter discovery support
    """

    def decorator(f: Any) -> Any:
        # Get the Click command object
        if hasattr(f, "callback"):
            # Already a Click command
            command = f
        else:
            # Not yet a Click command, will be decorated after this
            # Store metadata for later introspection
            f._pending_describe_flag = True
            f._schema_version = version
            f._display_name = display_name
            return f

        # Store metadata on command
        command._schema_version = version
        command._display_name = display_name or _extract_display_name(command)

        # Create a new describe-parameters option that doesn't require other params
        describe_option = click.Option(
            ["--describe-parameters"],
            is_flag=True,
            is_eager=True,  # Process this before other options
            expose_value=False,  # Don't pass to callback
            help="Output parameter schema as JSON and exit",
            callback=lambda ctx, param, value: _describe_callback(ctx, command, value, version, command._display_name),
        )

        # Add at the beginning of params list so it's processed first
        command.params.insert(0, describe_option)

        return command

    # Support both @add_describe_flag and @add_describe_flag()
    if func is not None:
        # Called as @add_describe_flag (without parentheses)
        return decorator(func)
    # Called as @add_describe_flag(...) (with arguments)
    return decorator


def _describe_callback(
    ctx: click.Context, command: click.Command, value: bool, version: str, display_name: str | None
) -> None:
    """Callback for --describe-parameters flag.

    Args:
        ctx: Click context
        command: The command to describe
        value: Flag value (True if set)
        version: Schema version
        display_name: Human-readable name
    """
    if value:
        schema = get_parameter_schema(command, version, display_name)
        click.echo(json.dumps(schema, indent=2))
        ctx.exit(0)
