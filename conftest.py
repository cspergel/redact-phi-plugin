"""Pytest configuration for redact-phi-plugin tests."""
import sys
from pathlib import Path

# Add plugin root to path (for 'server.*' imports)
plugin_root = Path(__file__).parent
sys.path.insert(0, str(plugin_root))

# Add parent project root to path (for 'redactiphi.*' imports)
project_root = plugin_root.parent
sys.path.insert(0, str(project_root))
