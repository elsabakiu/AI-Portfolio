"""Backward-compatible Gradio entrypoint.

Prefer `python -m news_summariser.gradio_app`.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from news_summariser.gradio_app import main
except ModuleNotFoundError:
    # Support direct execution of this file (python path/to/main.py).
    src_root = Path(__file__).resolve().parents[1]
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    from news_summariser.gradio_app import main

raise SystemExit(main())
