import os

import dotenv
import nox

# By default (unless explicit set otherwise) running now should only
# run `test`, because `test_coverage` also uploads to CodeCov
nox.options.sessions = ["test"]


@nox.session(python=["3.8", "3.9", "3.10", "3.11", "3.12"])
def test_coverage(session: nox.Session) -> None:
    dotenv.load_dotenv()
    session.install("-U", "pip", "setuptools", "wheel")
    session.install("-U", "-e", ".", "pytest-randomly", "pytest-codecov[git]")
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


@nox.session(python=["3.8", "3.9", "3.10", "3.11", "3.12"])
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
