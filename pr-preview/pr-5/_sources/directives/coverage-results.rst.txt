coverage-results
================

Renders a standalone coverage table with no sphinx-needs dependency.

.. code-block:: rst

   .. coverage-results:: path/to/coverage.xml

Options
-------

``:package:``
    Filter to a single package by name.

Example
-------

.. code-block:: rst

   .. coverage-results:: coverage.xml
      :package: mypackage
