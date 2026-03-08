"""Service package initializer.

Exports the `services` module to be importable as `src.services` and keeps the
public API simple for the UI layer.
"""

from . import services  # re-export the services module
