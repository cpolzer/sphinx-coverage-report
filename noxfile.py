import nox

PYTHON_VERSIONS = ["3.10", "3.11", "3.12"]
SPHINX_NEEDS_VERSIONS = ["6.3.0", "7.0.0", "8.0.0"]


@nox.session(python=PYTHON_VERSIONS)
@nox.parametrize("sphinx_needs", SPHINX_NEEDS_VERSIONS)
def tests(session, sphinx_needs):
    session.install("-e", ".[test]")
    session.install(f"sphinx-needs=={sphinx_needs}")
    session.run("pytest", "tests/", "-v", "--tb=short")


@nox.session
def lint(session):
    session.install("ruff")
    session.run("ruff", "check", "sphinxcontrib/", "tests/")


@nox.session
def coverage(session):
    session.install("-e", ".[test]")
    session.run(
        "pytest", "tests/", "--cov=sphinxcontrib/coverage_report",
        "--cov-report=xml", "--cov-report=term-missing",
    )


@nox.session
def docs(session):
    session.install("-e", ".[docs,test]")
    session.run(
        "pytest",
        "--cov=sphinxcontrib/coverage_report",
        "--cov-report=xml:docs/_coverage/coverage.xml",
        "-q",
    )
    session.run("sphinx-build", "-W", "docs", "docs/_build/html")
