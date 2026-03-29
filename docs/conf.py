# docs/conf.py
import os
from pathlib import Path

project = "sphinx-coverage-report"
author = "~christian polzer"
version = release = os.environ.get("DOCS_VERSION", "local")

extensions = [
    "sphinx_needs",
    "sphinxcontrib.coverage_report",
    "myst_parser",
]

html_theme = "furo"
needs_id_regex = ".*"
cr_rootdir = Path(__file__).parent
cr_warn_no_data = True
exclude_patterns = ['superpowers/**/*']