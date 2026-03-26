# sphinxcontrib/coverage_report/directives/coverage_report_directive.py
from docutils.parsers.rst import directives

from sphinxcontrib.coverage_report.directives.coverage_common import CoverageCommonDirective


class CoverageReportDirective(CoverageCommonDirective):
    """
    Template-based full coverage report.

    Reads the template file, substitutes variables, and inserts the
    expanded RST back into the document via state_machine.insert_input().

    Usage::

        .. coverage-report:: path/to/coverage.xml
           :id: CR_001
           :title: My Coverage Report
           :tags: backend
    """
    required_arguments = 1
    optional_arguments = 0
    option_spec = {
        "id": directives.unchanged,
        "tags": directives.unchanged,
        "title": directives.unchanged,
    }
    has_content = False

    def run(self):
        filepath = self._resolve_path(self.arguments[0])
        cfg = self.config
        template_path = cfg.cr_report_template

        with open(template_path, encoding="utf-8") as fh:
            template = fh.read()

        report_id = self.options.get("id", "CR_REPORT")
        title = self.options.get("title", f"Coverage Report: {filepath}")
        rst = template.format(
            file=self.arguments[0],
            id=report_id,
            tags=self.options.get("tags", report_id),
            title=title,
            title_underline="=" * len(title),
            module_need=cfg.cr_module[1],
            package_need=cfg.cr_package[1],
        )
        self.state_machine.insert_input(rst.splitlines(), self.arguments[0])
        return []
