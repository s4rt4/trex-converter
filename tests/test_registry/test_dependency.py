from pathlib import Path

from app.core import dependency
from app.core.dependency import DependencyChecker, dependency_label


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


def test_libreoffice_component_present(tmp_path, monkeypatch) -> None:
    # writer launcher present in the program dir -> component available.
    (tmp_path / "swriter").write_text("#!/bin/sh\n")
    monkeypatch.setattr(dependency, "_libreoffice_program_dir", lambda: tmp_path)
    checker = DependencyChecker()

    status = checker.check("libreoffice:writer")

    assert status.available is True
    assert status.path == str(tmp_path / "swriter")


def test_libreoffice_component_missing_when_marker_absent(tmp_path, monkeypatch) -> None:
    # program dir exists (core installed) but calc marker is absent.
    monkeypatch.setattr(dependency, "_libreoffice_program_dir", lambda: tmp_path)
    checker = DependencyChecker()

    status = checker.check("libreoffice:calc")

    assert status.available is False
    assert status.path is None


def test_libreoffice_component_missing_when_not_installed(monkeypatch) -> None:
    # no LibreOffice at all -> every component reports missing.
    monkeypatch.setattr(dependency, "_libreoffice_program_dir", lambda: None)
    checker = DependencyChecker()

    status = checker.check("libreoffice:impress")

    assert status.available is False
    assert status.path is None


def test_libreoffice_component_lib_fallback(tmp_path, monkeypatch) -> None:
    # launcher missing but the component shared lib is present -> available.
    (tmp_path / "libsclo.so").write_text("")
    monkeypatch.setattr(dependency, "_libreoffice_program_dir", lambda: tmp_path)
    checker = DependencyChecker()

    status = checker.check("libreoffice:calc")

    assert status.available is True
    assert status.path == str(tmp_path / "libsclo.so")


def test_dependency_label_formats_tokens() -> None:
    assert dependency_label("libreoffice:calc") == "LibreOffice Calc (spreadsheets)"
    assert dependency_label("python:fitz") == "PyMuPDF (python)"
    assert dependency_label("python:lxml") == "lxml (python)"
    assert dependency_label("ffmpeg") == "ffmpeg"
