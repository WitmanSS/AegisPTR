"""Top-level package shim that exposes backend/app as the `app` package for tests.

This file inserts the real `backend/app` folder into this package's __path__
so imports like `import app.api.routes` resolve to `backend/app/api/routes.py`.
"""
from __future__ import annotations
import pathlib
import os

# Compute path to backend/app relative to repository root (one level up)
HERE = pathlib.Path(__file__).resolve().parent
BACKEND_APP = HERE.joinpath('..', 'backend', 'app').resolve()
if BACKEND_APP.exists():
    # Prepend so it takes precedence
    __path__.insert(0, str(BACKEND_APP))
