# sphinxcontrib/coverage_report/coverage_report.py
"""Sphinx extension setup for sphinx-coverage-report."""
import os

import sphinx_needs
from packaging.version import Version
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.util import logging
from sphinx_needs.api import add_dynamic_function, add_need_type

try:
    from sphinx_needs.api import add_field as _add_field

    def _register_field(app, name, schema=None):
        _add_field(name, name, schema=schema)  # name used as description placeholder
except ImportError:
    from sphinx_needs.api import add_extra_option as _add_extra_option

    def _register_field(app, name, schema=None):
        _add_extra_option(app, name, **({} if schema is None else {"schema": schema}))

from sphinxcontrib.coverage_report.environment import install_styles_static_files
from sphinxcontrib.coverage_report.functions import cr_link

logger = logging.getLogger(__name__)

VERSION = "0.1.0"

_DEFAULT_JSON_MAPPING = {
    "json_config": {
        "report": {
            "line_rate": ([], "0"),
            "branch_rate": ([], "0"),
            "lines_valid": (["totals", "num_statements"], "0"),
            "lines_covered": (["totals", "covered_lines"], "0"),
            "branches_valid": (["totals", "num_branches"], "0"),
            "branches_covered": (["totals", "covered_branches"], "0"),
            "timestamp": (["meta", "timestamp"], "unknown"),
            "version": (["meta", "version"], "unknown"),
        },
        "module": {
            "name": ([], "unknown"),
            "filename": ([], "unknown"),
            "line_rate": (["summary", "percent_covered"], "0"),
            "branch_rate": (["summary", "percent_branches_covered"], "0"),
            "lines_valid": (["summary", "num_statements"], "0"),
            "lines_covered": (["summary", "covered_lines"], "0"),
            "branches_valid": (["summary", "num_branches"], 0),
            "branches_covered": (["summary", "covered_branches"], 0),
            "missed_lines": (["missing_lines"], []),
        },
        "function": {
            "name": ([], "unknown"),
            "line_start": (["start_line"], 0),
            "hits": ([], 0),
        },
    }
}

_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "directives", "coverage_report_template.txt"
)


def setup(app: Sphinx):
    """Register the sphinx-coverage-report extension with Sphinx."""
    app.add_config_value("cr_rootdir", app.confdir, "html")
    app.add_config_value("cr_import_encoding", "utf-8", "html")
    app.add_config_value("cr_extra_options", [], "env")
    app.add_config_value("cr_warn_no_data", True, "html")

    app.add_config_value(
        "cr_report",
        ["coverage-report", "coveragereport", "Coverage Report", "CR_", "#4a90d9", "node"],
        "html",
    )
    app.add_config_value(
        "cr_package",
        ["coverage-package", "coveragepackage", "Coverage Package", "CP_", "#7ab648", "folder"],
        "html",
    )
    app.add_config_value(
        "cr_module",
        ["coverage-module", "coveragemodule", "Coverage Module", "CM_", "#f0ad4e", "rectangle"],
        "html",
    )
    app.add_config_value(
        "cr_function",
        ["coverage-function", "coveragefunction", "Coverage Function", "CF_", "#cccccc", "rectangle"],
        "html",
    )

    app.add_config_value("cr_threshold_line_rate", 0.80, "html")
    app.add_config_value("cr_threshold_branch_rate", 0.75, "html")
    app.add_config_value("cr_threshold_report", {}, "html")
    app.add_config_value("cr_threshold_package", {}, "html")
    app.add_config_value("cr_threshold_module", {}, "html")
    app.add_config_value("cr_module_id_length", 5, "html")
    app.add_config_value("cr_package_id_length", 3, "html")
    app.add_config_value("cr_json_mapping", _DEFAULT_JSON_MAPPING, "html", types=[dict])
    app.add_config_value("cr_report_template", _TEMPLATE_PATH, "html")

    app.connect("config-inited", _sphinx_needs_update)
    app.connect("builder-inited", install_styles_static_files)
    app.connect("builder-inited", _register_directives)

    return {"version": VERSION, "parallel_read_safe": True, "parallel_write_safe": True}


def _sphinx_needs_update(app: Sphinx, config: Config) -> None:
    """Register coverage fields and need types with sphinx-needs."""
    needs_version = Version(sphinx_needs.__version__)
    use_schema = needs_version >= Version("6.0.0")

    fields = [
        ("line_rate",        {"type": "number"}),
        ("branch_rate",      {"type": "number"}),
        ("lines_valid",      {"type": "integer"}),
        ("lines_covered",    {"type": "integer"}),
        ("branches_valid",   {"type": "integer"}),
        ("branches_covered", {"type": "integer"}),
        ("missed_lines",     {"type": "string"}),
        ("filename",         {"type": "string"}),
        ("package",          {"type": "string"}),
        ("complexity",       {"type": "number"}),
        ("hits",             {"type": "integer"}),
        ("line_start",       {"type": "integer"}),
    ]

    if use_schema:
        for name, schema in fields:
            _register_field(app, name, schema=schema)
        for opt in config.cr_extra_options:
            _register_field(app, opt, schema={"type": "string"})
    else:
        for name, _ in fields:
            _register_field(app, name)
        for opt in config.cr_extra_options:
            _register_field(app, opt)

    add_dynamic_function(app, cr_link)
    add_need_type(app, *config.cr_report[1:])
    add_need_type(app, *config.cr_package[1:])
    add_need_type(app, *config.cr_module[1:])
    add_need_type(app, *config.cr_function[1:])


def _register_directives(app: Sphinx) -> None:
    """Register all coverage directives with Sphinx. Called on builder-inited."""
    # Directives are imported here to avoid circular imports at module load time.
    from sphinxcontrib.coverage_report.directives.coverage_results import CoverageResultsDirective
    app.add_directive("coverage-results", CoverageResultsDirective)
    # coverage-module, coverage-package, coverage-function, coverage-report added in Tasks 9 & 10
