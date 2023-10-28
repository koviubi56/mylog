import os
from typing import Literal

import nox

# By default (unless explicit set otherwise) running nox should only
# run `test`, because `test_coverage` also uploads to CodeCov
nox.options.sessions = ["test"]

PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]


def never_contains(_: object) -> Literal[False]:
    return False


def optional_contains(this: object, that: object) -> bool:
    return getattr(this, "__contains__", never_contains)(that)


def is_session_version(session: nox.Session, version: str) -> bool:
    return (
        (optional_contains(session.python, version))
        or (version in session.name)
        or (version in session.env.get("NOX_CURRENT_SESSION", ""))
    )


NORMAL_PYTEST_COMMAND = (
    "pytest",
    "--ff",
    "-vv",
    "-r",
    "A",
    "-l",
    "--color=yes",
    "--code-highlight=yes",
    "--continue-on-collection-errors",
)


@nox.session(python=PYTHON_VERSIONS)
def test_coverage(session: nox.Session) -> None:
    session.install("-U", "pip", "setuptools", "wheel")
    session.install("-U", "-e", ".", "pytest-randomly")
    try:
        session.install("pytest-codecov[git]")
    except BaseException:  # noqa: BLE001
        session.warn(
            "Failed to install pytest-codecov, continuing without coverage..."
        )
        session.run(*NORMAL_PYTEST_COMMAND)
        return
    try:
        env = {"CODECOV_TOKEN": os.environ["CODECOV_TOKEN"]}
    except KeyError:
        env = None
    session.run(
        "pytest",
        "--codecov",
        "--ff",
        "-vv",
        "-r",
        "A",
        "-l",
        "--color=yes",
        "--code-highlight=yes",
        "--continue-on-collection-errors",
        env=env,
    )


@nox.session(python=PYTHON_VERSIONS)
def test(session: nox.Session) -> None:
    session.install("-U", "pip", "setuptools", "wheel")
    session.install("-U", "-e", ".", "pytest-randomly")
    session.run(*NORMAL_PYTEST_COMMAND)
