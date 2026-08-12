"""Backward-compatible import for the canonical batch pipeline.

New code should import ``run_batch`` from ``src.backend.batch_runner``. Keeping
this module as a thin alias prevents the old, divergent implementation from
silently producing a different output contract.
"""

from src.backend.batch_runner import run_batch

__all__ = ["run_batch"]
