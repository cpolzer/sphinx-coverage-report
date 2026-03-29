coverage-package
================

Creates a sphinx-needs node for a package with aggregated coverage stats.

.. code-block:: rst

   .. coverage-package:: path/to/coverage.xml
      :package: mypackage
      :id: CP_001

Options
-------

``:id:``, ``:status:``, ``:tags:``, ``:links:``, ``:package:``
    Same as :doc:`coverage-module`.

``:expand:``
    Flag. When set, auto-generates a ``coverage-module`` node for every
    module in the package, linked back to this package node.

Fields populated
----------------

``line_rate``, ``branch_rate``, ``lines_valid``, ``lines_covered``,
``branches_valid``, ``branches_covered``, ``package``.
