"""Programs — the runnable, indexed HK open-data function library.

One function = one capability, grouped into department/org subpackages (e.g.
``programs/lcsd/facility.py``). Each function returns JSON-serializable data and
**never prints** — the calling agent prints when composing.

Functions are indexed by ``reindex`` (see ``hkdata.programs``) and retrieved by
``programs-search``. To answer a question the agent retrieves a function's
**source**, inlines it into a terminal heredoc, and runs it — this package is the
canonical source and write-back target, not an import surface.

See ``_template.py`` for the docstring contract every function must follow.
"""
