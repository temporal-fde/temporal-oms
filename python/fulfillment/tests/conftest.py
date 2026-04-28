"""Configure sys.path so tests can import generated types and src modules."""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_GENERATED = _REPO_ROOT / "python" / "generated"
_GENERATED_PYDANTIC = _GENERATED / "pydantic"
_FULFILLMENT_ROOT = _REPO_ROOT / "python" / "fulfillment"

for _p in [str(_GENERATED), str(_GENERATED_PYDANTIC), str(_FULFILLMENT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
