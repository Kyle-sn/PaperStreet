from __future__ import annotations

from pathlib import Path
import sys

# Support running from repository root while the real package source lives in research/ercot.
_this_root = Path(__file__).resolve().parent.parent
_research_ercot = _this_root / "research" / "ercot"
if str(_research_ercot) not in sys.path:
    sys.path.insert(0, str(_research_ercot))

# Make module search inside this package include the research copy.
__path__.insert(0, str(_research_ercot))
