"""
Projects package — enables `from projects.[tower].src import [module]`.

Tower directories use hyphens (ai-systems) but Python needs underscores (ai_systems).
This init injects aliases into sys.modules so both naming conventions work.

    from projects.lead_generation.src import daily_loop
    from projects.personal_assistant.src import gmail_api
"""

import importlib.util
import sys
import types
from pathlib import Path

_PROJECTS_DIR = Path(__file__).parent

_TOWER_MAP = {
    "ai_systems": "ai-systems",
    "amazon_seller": "amazon-seller",
    "fitness_influencer": "fitness-influencer",
    "lead_generation": "lead-generation",
    "mcp_services": "mcp-services",
    "personal_assistant": "personal-assistant",
}

# Pre-register tower packages so Python can find them
for _underscore, _hyphen in _TOWER_MAP.items():
    _tower_dir = _PROJECTS_DIR / _hyphen
    _src_dir = _tower_dir / "src"

    # Register projects.[tower_underscore]
    _tower_mod_name = f"projects.{_underscore}"
    if _tower_mod_name not in sys.modules:
        _mod = types.ModuleType(_tower_mod_name)
        _mod.__path__ = [str(_tower_dir)]
        _mod.__file__ = str(_tower_dir / "__init__.py")
        _mod.__package__ = _tower_mod_name
        sys.modules[_tower_mod_name] = _mod

    # Register projects.[tower_underscore].src
    _src_mod_name = f"projects.{_underscore}.src"
    if _src_mod_name not in sys.modules and _src_dir.exists():
        _src_mod = types.ModuleType(_src_mod_name)
        _src_mod.__path__ = [str(_src_dir)]
        _src_mod.__file__ = str(_src_dir / "__init__.py")
        _src_mod.__package__ = _src_mod_name
        sys.modules[_src_mod_name] = _src_mod
