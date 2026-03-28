coverage-report
===============

Template-driven directive that expands into a full coverage report section.

Inserts a ``coverage-results`` table and a ``needtable`` of all
``coverage-module`` nodes matching the given tag.

.. code-block:: rst

   .. coverage-report:: path/to/coverage.xml
      :id: CR_001
      :title: My Coverage Report
      :tags: backend

Options
-------

``:id:``
    ID used as the tag filter in the expanded ``needtable``.

``:title:``
    Section heading. Defaults to ``Coverage Report: <filepath>``.

``:tags:``
    Additional sphinx-needs tags. Defaults to the value of ``:id:``.

Template
--------

The default template lives at
``sphinxcontrib/coverage_report/directives/coverage_report_template.txt``.
Override globally with ``cr_report_template = "/path/to/template.txt"`` in
``conf.py``.
