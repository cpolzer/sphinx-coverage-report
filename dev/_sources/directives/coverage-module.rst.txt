coverage-module
===============

Creates a sphinx-needs node for a single source file.

.. code-block:: rst

   .. coverage-module:: path/to/coverage.xml
      :package: mypackage
      :module: module.py
      :id: CM_001

Options
-------

``:id:``
    Explicit sphinx-needs ID. Auto-generated from a hash if omitted.

``:status:``
    Override computed status (``passing`` or ``failing``).

``:tags:``
    Comma-separated sphinx-needs tags.

``:links:``
    Comma-separated IDs to link to (e.g. test-case nodes).

``:package:``
    Package name to look up in the coverage file.

``:module:``
    Module filename (``module.py`` or ``mypackage/module.py``).

Fields populated
----------------

``line_rate``, ``branch_rate``, ``lines_valid``, ``lines_covered``,
``branches_valid``, ``branches_covered``, ``missed_lines``,
``filename``, ``package``, ``complexity``.
