"""Test that all imports work."""

print("Testing imports...")

try:
    from config import settings

    print(f"✅ Config imported - scenarios path: {settings.scenarios_path}")
except ImportError as e:
    print(f"❌ Config import failed: {e}")

try:
    from models.scenario import Scenario  # noqa: F401

    print("✅ Scenario model imported")
except ImportError as e:
    print(f"❌ Scenario model import failed: {e}")

try:
    from models.execution import Execution, ExecutionStatus  # noqa: F401

    print("✅ Execution models imported")
except ImportError as e:
    print(f"❌ Execution models import failed: {e}")

try:
    from models.events import AgentStartEvent, LogEvent  # noqa: F401

    print("✅ Event models imported")
except ImportError as e:
    print(f"❌ Event models import failed: {e}")

try:
    from services.scenario_discovery import ScenarioDiscoveryService  # noqa: F401

    print("✅ ScenarioDiscoveryService imported")
except ImportError as e:
    print(f"❌ ScenarioDiscoveryService import failed: {e}")

try:
    from services.process_manager import ProcessManager  # noqa: F401

    print("✅ ProcessManager imported")
except ImportError as e:
    print(f"❌ ProcessManager import failed: {e}")

try:
    from api.main import app  # noqa: F401

    print("✅ FastAPI app imported")
except ImportError as e:
    print(f"❌ FastAPI app import failed: {e}")

print("\n✅ All imports successful!")
