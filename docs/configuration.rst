Configuration
=============

All configuration values are set in your Sphinx ``conf.py``.

Root directory
--------------

.. code-block:: python

   cr_rootdir = "."  # default: Sphinx confdir

Base directory for resolving relative paths in directives.

Import encoding
---------------

.. code-block:: python

   cr_import_encoding = "utf-8"

Extra options
-------------

.. code-block:: python

   cr_extra_options = []

List of additional field names to register with sphinx-needs.

Need type configuration
-----------------------

Each coverage level maps to a sphinx-needs type. The format is
``[directive-name, type-id, title-prefix, id-prefix, color, style]``.

.. code-block:: python

   cr_report   = ["coverage-report",   "coveragereport",   "Coverage Report",   "CR_", "#4a90d9", "node"]
   cr_package  = ["coverage-package",  "coveragepackage",  "Coverage Package",  "CP_", "#7ab648", "folder"]
   cr_module   = ["coverage-module",   "coveragemodule",   "Coverage Module",   "CM_", "#f0ad4e", "rectangle"]
   cr_function = ["coverage-function", "coveragefunction", "Coverage Function", "CF_", "#cccccc", "rectangle"]

Thresholds
----------

.. code-block:: python

   cr_threshold_line_rate   = 0.80  # default
   cr_threshold_branch_rate = 0.75  # default

   # per-level overrides (optional)
   cr_threshold_report  = {}
   cr_threshold_package = {}
   cr_threshold_module  = {}

A need's ``status`` is set to ``"failing"`` if either rate falls below the threshold.

ID hash lengths
---------------

.. code-block:: python

   cr_module_id_length  = 5
   cr_package_id_length = 3

JSON mapping
------------

.. code-block:: python

   cr_json_mapping = { ... }  # see source for full default

Controls how coverage.py JSON keys map to normalized fields.

Warnings
--------

.. code-block:: python

   cr_warn_no_data = True

Emit Sphinx warnings when a directive references missing coverage data.
