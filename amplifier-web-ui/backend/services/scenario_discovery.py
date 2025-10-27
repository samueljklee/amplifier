"""Scenario discovery service via CLI introspection.

This service automatically discovers scenarios by:
1. Scanning scenarios/ directory for main.py files
2. Executing --describe-parameters for each
3. Parsing the JSON response
4. Marking scenarios as available/unavailable based on introspection success
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)


class ScenarioDiscoveryService:
    """Discovers scenarios via CLI introspection."""

    def __init__(self, scenarios_dir: Path | None = None):
        """Initialize discovery service.

        Args:
            scenarios_dir: Path to scenarios directory (default: scenarios/)
        """
        if scenarios_dir is None:
            # Default to scenarios/ relative to project root
            self.scenarios_dir = Path("scenarios")
        else:
            self.scenarios_dir = Path(scenarios_dir)

    async def discover_scenarios(self) -> list[dict[str, Any]]:
        """Discover all scenarios by scanning directory (async parallel).

        Returns:
            List of scenario schemas with availability status
        """
        if not self.scenarios_dir.exists():
            logger.warning(f"Scenarios directory not found: {self.scenarios_dir}")
            return []

        # Collect introspection tasks
        tasks = []
        for scenario_dir in self.scenarios_dir.iterdir():
            if not scenario_dir.is_dir():
                continue
            if not (scenario_dir / "main.py").exists():
                continue

            logger.info(f"Discovered scenario: {scenario_dir.name}")
            tasks.append(self._introspect_scenario_async(scenario_dir.name))

        # Run all introspections in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and None values
        scenarios = cast(
            list[dict[str, Any]],
            [r for r in results if r is not None and not isinstance(r, Exception)],
        )

        logger.info(f"Successfully introspected {len(scenarios)} scenarios")
        return scenarios

    async def get_scenario(self, name: str) -> dict[str, Any] | None:
        """Get a single scenario by name (async).

        Args:
            name: Scenario name (directory name)

        Returns:
            Scenario schema or None if not found
        """
        scenario_dir = self.scenarios_dir / name

        if not scenario_dir.exists() or not (scenario_dir / "main.py").exists():
            logger.error(f"Scenario not found: {name}")
            return None

        return await self._introspect_scenario_async(name)

    async def _introspect_scenario_async(self, name: str) -> dict[str, Any] | None:
        """Introspect a scenario via --describe-parameters asynchronously.

        Args:
            name: Scenario name (directory name)

        Returns:
            Scenario schema with availability status
        """
        try:
            # Get project root (parent of amplifier-web-ui)
            project_root = Path(__file__).parent.parent.parent.parent

            process = await asyncio.create_subprocess_exec(
                "uv",
                "run",
                "python",
                "-m",
                f"scenarios.{name}",
                "--describe-parameters",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=project_root,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)

            if process.returncode == 0:
                schema = json.loads(stdout.decode())
                schema["name"] = schema.get("name", name)
                schema["available"] = True

                # Transform to frontend-compatible schema
                transformed = self._transform_to_frontend_schema(name, schema)

                logger.info(f"✅ {name}: introspection successful")
                return transformed
            else:
                logger.error(f"❌ {name}: introspection failed - {stderr.decode()}")
                return self._create_unavailable_schema(name, stderr.decode())

        except asyncio.TimeoutError:
            logger.error(f"❌ {name}: introspection timed out")
            return self._create_unavailable_schema(name, "Introspection timed out (>5s)")
        except json.JSONDecodeError as e:
            logger.error(f"❌ {name}: invalid JSON - {e}")
            return self._create_unavailable_schema(name, f"Invalid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"❌ {name}: unexpected error - {e}")
            return self._create_unavailable_schema(name, f"Unexpected error: {str(e)}")

    def _create_unavailable_schema(self, name: str, error: str) -> dict[str, Any]:
        """Create a frontend-compatible schema for unavailable scenarios.

        Args:
            name: Scenario name (directory name)
            error: Error message explaining why scenario is unavailable

        Returns:
            Frontend-compatible scenario schema with minimal fields
        """
        return {
            "id": name,
            "name": name.replace("_", " ").title(),
            "description": f"⚠️ Unavailable: {error}",
            "path": f"scenarios/{name}",
            "cli_command": f"scenarios.{name}",
            "parameters": [],
            "examples": [],
            "metadata": {
                "tags": [],
            },
            "available": False,
            "error": error,
        }

    def _transform_to_frontend_schema(self, name: str, cli_schema: dict[str, Any]) -> dict[str, Any]:
        """Transform CLI introspection schema to frontend-compatible schema.

        Args:
            name: Scenario name (directory name)
            cli_schema: Schema from CLI introspection (--describe-parameters)

        Returns:
            Frontend-compatible scenario schema
        """
        # Map CLI parameter types to frontend types
        type_mapping = {
            "string": "string",
            "path": "path",
            "integer": "number",
            "float": "number",
            "boolean": "boolean",
        }

        # Transform parameters
        parameters = []
        for param in cli_schema.get("parameters", []):
            # Extract type from CLI format (may be "choice:opt1,opt2")
            param_type = param.get("type", "string")
            if param_type.startswith("choice:"):
                param_type = "string"  # Choices are strings in frontend

            frontend_param = {
                "name": param["name"],
                "type": type_mapping.get(param_type, "string"),
                "required": param.get("required", False),
                "description": param.get("help", ""),
            }

            # Add default if present
            if "default" in param and param["default"] is not None:
                frontend_param["default"] = param["default"]

            parameters.append(frontend_param)

        # Build frontend-compatible schema
        return {
            "id": name,  # Use name as id
            "name": cli_schema.get("display_name", name.replace("_", " ").title()),
            "description": cli_schema.get("description", ""),
            "path": f"scenarios/{name}",
            "cli_command": f"scenarios.{name}",
            "parameters": parameters,
            "examples": [],  # No examples from CLI introspection
            "metadata": {
                "version": cli_schema.get("version", "1.0"),
                "tags": [],  # No tags from CLI introspection
            },
            "available": cli_schema.get("available", True),
        }
