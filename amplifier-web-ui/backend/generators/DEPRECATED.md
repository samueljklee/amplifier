# DEPRECATED: Web UI Generators

**Status:** DEPRECATED as of 2025-01-24
**Replacement:** Use `scenarios/scenario_generator/` (unified generator)

## Why Deprecated

These generators were duplicate implementations that lacked critical features:
- ❌ No `pyproject.toml` generation
- ❌ No dependency installation
- ❌ No Makefile updates
- ❌ Incomplete code with TODOs and stubs

## Migration Complete

The web UI now uses the **unified scenario generator** at `scenarios/scenario_generator/`:

### What Changed

**Before (Web UI):**
```python
# amplifier-web-ui/backend/services/generation_session.py
from generators.simple_generator import SimpleGenerator

generator = SimpleGenerator()
files = generator.generate(spec, output_dir)
# ❌ Missing: pyproject.toml, dependencies, Makefile updates
```

**After (Unified):**
```python
# amplifier-web-ui/backend/services/generation_session.py
from scenarios.scenario_generator.incremental_generator import IncrementalGenerator

generator = IncrementalGenerator()
await generator.generate(requirements, output_dir)
# ✅ Includes: pyproject.toml, uv add, Makefile, validation
```

### Benefits

1. **Single Source of Truth** - CLI and Web UI use same generator
2. **Full Feature Parity** - Dependencies auto-installed, Makefile updated
3. **Battle-Tested** - Uses proven incremental generation with validation
4. **Maintainable** - One codebase to maintain, not two

## Files To Remove

These files are no longer used and should be removed:

- `amplifier-web-ui/backend/generators/simple_generator.py` (DEPRECATED - has TODOs/stubs)
- `amplifier-web-ui/backend/generators/backend_generator.py` (DEPRECATED)
- `amplifier-web-ui/backend/generators/test_generator.py` (DEPRECATED)
- `amplifier-web-ui/backend/generators/validation_pipeline.py` (DEPRECATED - replaced by ValidationStage)

**NOTE:** These deprecated files are excluded from stub checking in pyproject.toml

## Current Status

✅ **COMPLETE** - Web UI now uses unified generator
✅ **TESTED** - Integration verified in `generation_session.py`
✅ **DOCUMENTED** - This file + updated code comments

## See Also

- `/scenarios/scenario_generator/` - The unified generator
- `/amplifier-web-ui/backend/services/generation_session.py` - Web UI integration
- `AGENTS.md` - Project guidelines on avoiding duplication
