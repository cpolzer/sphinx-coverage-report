# docs/conf.py
import os

project = "sphinx-coverage-report"
author = "~chrstian polzer"
release = "0.1.0"

extensions = [
    "sphinx_needs",
    "sphinxcontrib.coverage_report",
]

html_theme = "furo"
needs_id_regex = ".*"
cr_rootdir = os.path.dirname(__file__)
cr_warn_no_data = True
