from app.core.dependency import DependencyChecker


def test_dependency_checker_reports_missing_binary() -> None:
    checker = DependencyChecker()

    status = checker.check("definitely-not-installed-trex-binary")

    assert status.available is False
    assert status.path is None


def test_dependency_checker_reports_python_module() -> None:
    checker = DependencyChecker()

    status = checker.check("python:sys")

    assert status.available is True
    assert status.path == "sys"
