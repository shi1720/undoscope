"""UndoScope: a single-store reference contract for effect-scoped recovery."""
from .store import Context, RecoveryStore
__all__ = ["Context", "RecoveryStore"]
