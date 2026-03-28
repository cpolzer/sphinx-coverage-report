coverage-function
=================

Creates a sphinx-needs node for a single function or method.

.. code-block:: rst

   .. coverage-function:: path/to/coverage.xml
      :package: mypackage
      :module: module.py
      :function: my_function
      :id: CF_001

Options
-------

``:id:``, ``:status:``, ``:tags:``, ``:links:``, ``:package:``, ``:module:``
    Same as :doc:`coverage-module`.

``:function:``
    Function name to look up. Returns the first match if omitted.

Fields populated
----------------

``hits``, ``line_start``, ``filename``, ``package``.

.. note::

   Function-level data is only available from JSON and lcov formats.
   Cobertura XML does not carry reliable function hit counts.
