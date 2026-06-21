python
// workers/__init__.py
"""Background workers package.

Background processing (Celery / ARQ / RQ / Dramatiq) is intentionally deferred
to a later phase. This module exposes the import surface so callers can depend
on it today and the worker implementation can drop in without churn.
"""

