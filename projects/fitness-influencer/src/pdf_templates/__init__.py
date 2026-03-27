"""
PDF Template Registry.
Import all templates here so they register with the engine on import.
"""

from pathlib import Path
import importlib.util
import sys

# Auto-import all *_template.py files in this directory
_dir = Path(__file__).parent
for _f in sorted(_dir.glob("*_template.py")):
    _name = _f.stem
    try:
        _spec = importlib.util.spec_from_file_location(_name, str(_f))
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
    except Exception:
        pass
