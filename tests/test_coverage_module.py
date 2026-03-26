import os
import pytest
from sphinx.application import Sphinx


@pytest.fixture
def build_app(tmp_path):
    src = os.path.join(os.path.dirname(__file__), "doc_test", "module_needs")
    out = str(tmp_path / "output")
    app = Sphinx(src, src, out, out, "html")
    app.build()
    return tmp_path


def test_build_succeeds(build_app):
    html = (build_app / "output" / "index.html").read_text()
    assert "mypackage/module.py" in html


def test_coverage_module_need_rendered(build_app):
    html = (build_app / "output" / "index.html").read_text()
    assert "Coverage Module" in html
