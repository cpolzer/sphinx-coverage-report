# sphinxcontrib/coverage_report/directives/coverage_results.py
from docutils import nodes
from docutils.parsers.rst import directives
from sphinxcontrib.coverage_report.directives.coverage_common import (
    CoverageCommonDirective, _load_coverage_file,
)


class CoverageResultsDirective(CoverageCommonDirective):
    """
    Standalone coverage table. No sphinx-needs dependency.

    Usage::

        .. coverage-results:: path/to/coverage.xml
    """
    required_arguments = 1
    optional_arguments = 0
    has_content = False
    option_spec = {
        "package": directives.unchanged,
    }

    def run(self):
        filepath = self._resolve_path(self.arguments[0])
        data = _load_coverage_file(filepath, self.env)

        if data is None or not data.get("packages"):
            self._warn_if_no_data(filepath, data)
            return [nodes.warning(
                "",
                nodes.paragraph(text=f"No coverage data available from: {filepath}"),
            )]

        pkg_filter = self.options.get("package")
        modules = []
        for pkg in data["packages"]:
            if pkg_filter and pkg["name"] != pkg_filter:
                continue
            modules.extend(pkg["modules"])

        return [self._build_table(modules)]

    def _build_table(self, modules):
        table = nodes.table()
        tgroup = nodes.tgroup(cols=4)
        table += tgroup
        for width in [40, 20, 20, 20]:
            tgroup += nodes.colspec(colwidth=width)

        thead = nodes.thead()
        tgroup += thead
        header_row = nodes.row()
        for title in ["Module", "Line Rate", "Branch Rate", "Missed Lines"]:
            entry = nodes.entry()
            entry += nodes.paragraph(text=title)
            header_row += entry
        thead += header_row

        tbody = nodes.tbody()
        tgroup += tbody
        for mod in modules:
            row = nodes.row()
            for val in [
                mod["filename"],
                f"{mod['line_rate']:.0%}",
                f"{mod['branch_rate']:.0%}" if mod["branches_valid"] else "n/a",
                ", ".join(str(ln) for ln in mod["missed_lines"]) or "—",
            ]:
                entry = nodes.entry()
                entry += nodes.paragraph(text=val)
                row += entry
            tbody += row
        return table
