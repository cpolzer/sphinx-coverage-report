# sphinxcontrib/coverage_report/directives/coverage_function.py
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


class CoverageFunctionDirective(CoverageCommonDirective):
    required_arguments = 1
    optional_arguments = 0
    option_spec = {
        "id": directives.unchanged,
        "status": directives.unchanged,
        "tags": directives.unchanged,
        "links": directives.unchanged,
        "package": directives.unchanged,
        "module": directives.unchanged,
        "function": directives.unchanged,
    }
    has_content = False

    def run(self):
        filepath = self._resolve_path(self.arguments[0])
        data = _load_coverage_file(filepath, self.env)
        pkg_name = self.options.get("package", "")
        mod_name = self.options.get("module", "")
        fn_name = self.options.get("function", "")

        fn_data = self._find_function(data, pkg_name, mod_name, fn_name)
        if fn_data is None:
            self._warn_if_no_data(filepath, data, identifier=fn_name or None)
            return []

        app = self.env.app
        cfg = self.config
        need_type = cfg.cr_function[1]
        sn_cfg = NeedsSphinxConfig(cfg)
        need_id = self.options.get("id") or _make_hashed_id(
            need_type, f"{filepath}{pkg_name}{mod_name}{fn_name}", "", sn_cfg
        )
        # Functions have no branch data; pass branches_valid=0 to skip branch threshold
        fn_data_with_bv = {**fn_data, "branches_valid": 0}
        status = self.options.get("status") or compute_status(fn_data_with_bv, cfg, "module")
        title = f"{cfg.cr_function[2]}: {fn_data['name']}"
        result = add_need(
            app, self.state, self.env.docname, self.lineno,
            need_type=need_type,
            title=title,
            id=need_id,
            status=status,
            tags=self.options.get("tags", ""),
            links=self.options.get("links", ""),
            hits=str(fn_data["hits"]),
            line_start=str(fn_data["line_start"]),
            filename=mod_name,
            package=pkg_name,
        )
        add_doc(self.env, self.env.docname)
        return result

    @staticmethod
    def _find_function(data, pkg_name, mod_name, fn_name):
        if data is None:
            return None
        for pkg in data.get("packages", []):
            if pkg_name and pkg["name"] != pkg_name:
                continue
            for mod in pkg.get("modules", []):
                if mod_name and mod["name"] != mod_name and mod["filename"] != mod_name:
                    continue
                for fn in mod.get("functions", []):
                    if not fn_name or fn["name"] == fn_name:
                        return fn
        return None
