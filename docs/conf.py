# docs/conf.py
project = "sphinx-coverage-report"
author = "~chrstian polzer"
release = "0.1.0"

extensions = [
    "sphinx_needs",
    "sphinxcontrib.coverage_report",
]

html_theme = "furo"
needs_id_regex = ".*"
cr_warn_no_data = True
