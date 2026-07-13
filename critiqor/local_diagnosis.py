"""Compatibility import for the local diagnosis pipeline."""

from .diagnosis import generate_diagnosis as build_local_diagnosis

__all__ = ["build_local_diagnosis"]
