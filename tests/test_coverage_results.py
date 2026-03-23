import pytest
from sphinx.application import Sphinx
import os

@pytest.fixture
def build_app(tmp_path):
    src = os.path.join(os.path.dirname(__file__), "doc_test", "basic_results")
    out = str(tmp_path / "output")
    app = Sphinx(src, src, out, out, "html")
    app.build()
    return tmp_path

def test_build_succeeds(build_app):
    index_html = (build_app / "output" / "index.html").read_text()
    assert "module.py" in index_html
    assert "mypackage/module.py" in index_html

def test_line_rate_shown(build_app):
    html = (build_app / "output" / "index.html").read_text()
    assert "92%" in html or "80%" in html  # at least one module rate
