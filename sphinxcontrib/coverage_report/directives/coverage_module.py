# sphinxcontrib/coverage_report/directives/coverage_module.py
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


class CoverageModuleDirective(CoverageCommonDirective):
    """
    Creates a sphinx-needs node for a single source file.

    Usage::

        .. coverage-module:: path/to/coverage.xml
           :package: mypackage
           :module: module.py
           :id: CM_001
    """
    required_arguments = 1
    optional_arguments = 0
    option_spec = {
        "id": directives.unchanged,
        "status": directives.unchanged,
        "tags": directives.unchanged,
        "links": directives.unchanged,
        "package": directives.unchanged,
        "module": directives.unchanged,
    }
    has_content = False

    def run(self):
        filepath = self._resolve_path(self.arguments[0])
        data = _load_coverage_file(filepath, self.env)
        pkg_name = self.options.get("package", "")
        mod_name = self.options.get("module", "")

        mod_data = self._find_module(data, pkg_name, mod_name)
        if mod_data is None:
            identifier = f"{pkg_name}/{mod_name}" if pkg_name else mod_name
            self._warn_if_no_data(filepath, data, identifier=identifier or None)
            return []

        app = self.env.app
        cfg = self.config
        need_type = cfg.cr_module[1]
        sn_cfg = NeedsSphinxConfig(cfg)
        need_id = self.options.get("id") or _make_hashed_id(
            need_type, f"{filepath}{pkg_name}{mod_name}", "", sn_cfg
        )

        status = self.options.get("status") or compute_status(mod_data, cfg, "module")
        title = f"{cfg.cr_module[2]}: {mod_data['filename']}"
        options = dict(
            line_rate=str(mod_data["line_rate"]),
            branch_rate=str(mod_data["branch_rate"]),
            lines_valid=str(mod_data["lines_valid"]),
            lines_covered=str(mod_data["lines_covered"]),
            branches_valid=str(mod_data["branches_valid"]),
            branches_covered=str(mod_data["branches_covered"]),
            missed_lines=", ".join(str(ln) for ln in mod_data["missed_lines"]),
            filename=mod_data["filename"],
            package=pkg_name,
            complexity=str(mod_data.get("complexity", 0)),
        )
        result = add_need(
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
        return result

    @staticmethod
    def _find_module(data, pkg_name, mod_name):
        if data is None:
            return None
        for pkg in data.get("packages", []):
            if pkg_name and pkg["name"] != pkg_name:
                continue
            for mod in pkg.get("modules", []):
                if not mod_name or mod["name"] == mod_name or mod["filename"] == mod_name:
                    return mod
        return None
