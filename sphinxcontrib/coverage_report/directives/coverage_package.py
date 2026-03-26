# sphinxcontrib/coverage_report/directives/coverage_package.py
from importlib.metadata import version as _pkg_version

from docutils.parsers.rst import directives
from sphinx_needs.api import add_need
from sphinx_needs.config import NeedsSphinxConfig
from sphinx_needs.utils import add_doc

from sphinxcontrib.coverage_report.config import compute_status
from sphinxcontrib.coverage_report.directives.coverage_common import (
    CoverageCommonDirective,
    _load_coverage_file,
)

_sn_major = int(_pkg_version("sphinx-needs").split(".")[0])
if _sn_major >= 4:
    from sphinx_needs.api.need import _make_hashed_id
else:
    from sphinx_needs.api import make_hashed_id as _make_hashed_id


class CoveragePackageDirective(CoverageCommonDirective):
    required_arguments = 1
    optional_arguments = 0
    option_spec = {
        "id": directives.unchanged,
        "status": directives.unchanged,
        "tags": directives.unchanged,
        "links": directives.unchanged,
        "package": directives.unchanged,
        "expand": directives.flag,
    }
    has_content = False

    def run(self):
        filepath = self._resolve_path(self.arguments[0])
        data = _load_coverage_file(filepath, self.env)
        pkg_name = self.options.get("package", "")
        pkg_data = self._find_package(data, pkg_name)

        if pkg_data is None:
            self._warn_if_no_data(filepath, data, identifier=pkg_name or None)
            return []

        app = self.env.app
        cfg = self.config
        need_type = cfg.cr_package[1]
        sn_cfg = NeedsSphinxConfig(cfg)
        need_id = self.options.get("id") or _make_hashed_id(
            need_type, f"{filepath}{pkg_name}", "", sn_cfg
        )
        status = self.options.get("status") or compute_status(pkg_data, cfg, "package")
        title = f"{cfg.cr_package[2]}: {pkg_data['name']}"
        options = dict(
            line_rate=str(pkg_data["line_rate"]),
            branch_rate=str(pkg_data["branch_rate"]),
            lines_valid=str(pkg_data["lines_valid"]),
            lines_covered=str(pkg_data["lines_covered"]),
            branches_valid=str(pkg_data["branches_valid"]),
            branches_covered=str(pkg_data["branches_covered"]),
            package=pkg_data["name"],
        )
        result_nodes = add_need(
            app, self.state, self.env.docname, self.lineno,
            need_type=need_type,
            title=title,
            id=need_id,
            status=status,
            tags=self.options.get("tags", ""),
            links=self.options.get("links", ""),
            **options,
        )
        add_doc(self.env, self.env.docname)

        if "expand" in self.options:
            from sphinxcontrib.coverage_report.directives.coverage_module import CoverageModuleDirective
            for mod in pkg_data["modules"]:
                child_opts = {
                    "package": pkg_data["name"],
                    "module": mod["name"],
                    "links": need_id,
                }
                child = CoverageModuleDirective(
                    self.name, [self.arguments[0]], child_opts,
                    self.content, self.lineno, self.content_offset,
                    self.block_text, self.state, self.state_machine,
                )
                result_nodes.extend(child.run())

        return result_nodes

    @staticmethod
    def _find_package(data, pkg_name):
        if data is None:
            return None
        for pkg in data.get("packages", []):
            if not pkg_name or pkg["name"] == pkg_name:
                return pkg
        return None
