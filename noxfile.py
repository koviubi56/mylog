import os

import nox

# By default (unless explicit set otherwise) running nox should only
# run `test`, because `test_coverage` also uploads to CodeCov
nox.options.sessions = ["test"]

PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]


@nox.session(python=PYTHON_VERSIONS)
def test_coverage(session: nox.Session) -> None:
    session.install("-U", "pip", "setuptools", "wheel")
    try:
        session.install(
            "-U", "-e", ".", "pytest-randomly", "pytest-codecov[git]"
        )
    except BaseException:
        session.warn(session.env)
        session.warn(session.name)
        session.warn(session.python)
        raise
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
    session.run(
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
