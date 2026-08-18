"""
Reconciliation Module
Merges multiple per-document extraction JSONs into one authoritative product record.
"""

from .reconciler import reconcile, reconcile_from_files, save_merged

__all__ = ["reconcile", "reconcile_from_files", "save_merged"]
