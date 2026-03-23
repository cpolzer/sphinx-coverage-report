# sphinxcontrib/coverage_report/config.py
"""Default option list and threshold computation helper."""

DEFAULT_OPTIONS = [
    "line_rate", "branch_rate", "lines_valid", "lines_covered",
    "branches_valid", "branches_covered", "missed_lines",
    "filename", "package", "complexity", "hits", "line_start",
]


def compute_status(data, app_config, level="module"):
    """Return 'passing' or 'failing' based on threshold config.

    Args:
        data: Parsed coverage dict for the node (must have line_rate, branch_rate,
              branches_valid).
        app_config: Sphinx app.config object with cr_threshold_* values.
        level: One of 'report', 'package', 'module' — selects per-level override dict.

    Returns:
        'passing' or 'failing'
    """
    per_level = getattr(app_config, f"cr_threshold_{level}", {})
    line_threshold = per_level.get("line_rate", app_config.cr_threshold_line_rate)
    branch_threshold = per_level.get("branch_rate", app_config.cr_threshold_branch_rate)
    if data.get("line_rate", 1.0) < line_threshold:
        return "failing"
    bv = data.get("branches_valid", 0)
    if bv > 0 and data.get("branch_rate", 1.0) < branch_threshold:
        return "failing"
    return "passing"
