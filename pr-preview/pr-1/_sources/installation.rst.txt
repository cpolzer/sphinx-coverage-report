Installation
============

Install via pip::

    pip install sphinx-coverage-report

Add to your Sphinx ``conf.py``::

    extensions = [
        "sphinx_needs",
        "sphinxcontrib.coverage_report",
    ]

``sphinx-needs`` must be listed before ``sphinxcontrib.coverage_report``.

Requirements
------------

- Python >= 3.10
- Sphinx > 4.0
- sphinx-needs >= 6.0.0
