# Contributing guidelines

First off, thank you for considering contributing.

**Please note, that by contributing to our project you agree to the DCO! [More info](#dco)**

## Why do these guidelines exists?

Following these guidelines helps to communicate that you respect the time of the developers managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

## What to do

mylog is an open source project and we love to receive contributions from our community! There are many ways to contribute, from improving the documentation, submitting bug reports and feature requests or writing code.

## Rules

- Fill issue/pull request templates.
- If you are making a big pull request, create an issue first.
- Run tests. _[Need more help?](#run-tests)_
- Search open **and closed** issues **and** pull requests.
- Please, **don't** open an issue for questions. Ask it in the discussions tab!
- Make sure to put an X in the square brackets at the end of your pull requests and issues.
- Don't forget to add an entry to the changelog. Unless you know what you are doing, put it in the Unreleased section. For more information, see the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## How to file a bug report?

Click [here](https://github.com/koviubi56/mylog/issues/new?assignees=&labels=bug&template=bug_report.yml) and fill out the form.

## How to suggest a feature?

Click [here](https://github.com/koviubi56/mylog/issues/new?assignees=&labels=enhancement&template=feature_request.yml) and fill out the form.

## How to set up your environment and run tests?

### Set up environment

1. Clone the GitHub repository using `git clone`. _[Need more help?](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)_
1. Create a virtual environment using `venv .venv`. _[Need more help?](https://packaging.python.org/en/latest/tutorials/installing-packages/#creating-virtual-environments)_
1. Activate the virtual environment: _[Need more help?](https://packaging.python.org/en/latest/tutorials/installing-packages/#tab-set--5-input--1)_
    - **On PowerShell**: `.\\.venv\\Scripts\\Activate.ps1`
    - **On cmd.exe**: `.\\.venv\\Scripts\\activate.bat`
    - **On Bash**: `source ./.venv/Scripts/activate`

### Install

Run `pip install -e .`. _[Need more help?](https://packaging.python.org/en/latest/tutorials/installing-packages/#installing-from-a-local-src-tree)_

### Run tests

1. Install nox with `pip install nox` _[Need more help?](https://nox.thea.codes/en/stable/index.html#welcome-to-nox)_
1. Run `nox`. _[Need more help?](https://nox.thea.codes/en/stable/index.html#welcome-to-nox)_

## Pull requests

- **Read the [DCO](#dco).**
- Create an issue first.
- Wait until a maintainer accepts it.
- Create a fork.
- Make the changes
- Create a pull request
- Request review
- Wait...

## Security vulnerabilities

How to report them can be found in the [SECURITY.md](SECURITY.md) file.

## DCO

By contributing to our project you fully agree to the whole DCO.

By [signing off](https://git-scm.com/docs/git-commit#Documentation/git-commit.txt--s) your git commits you explicitly agree with the DCO.

A copy of the DCO can be found at <https://developercertificate.org/> or here:

> Developer Certificate of Origin
> Version 1.1
>
> Copyright (C) 2004, 2006 The Linux Foundation and its contributors.
>
> Everyone is permitted to copy and distribute verbatim copies of this
> license document, but changing it is not allowed.
>
> Developer's Certificate of Origin 1.1
>
> By making a contribution to this project, I certify that:
>
> (a) The contribution was created in whole or in part by me and I
> have the right to submit it under the open source license
> indicated in the file; or
>
> (b) The contribution is based upon previous work that, to the best
> of my knowledge, is covered under an appropriate open source
> license and I have the right under that license to submit that
> work with modifications, whether created in whole or in part
> by me, under the same open source license (unless I am
> permitted to submit under a different license), as indicated
> in the file; or
>
> (c) The contribution was provided directly to me by some other
> person who certified (a), (b) or (c) and I have not modified
> it.
>
> (d) I understand and agree that this project and the contribution
> are public and that a record of the contribution (including all
> personal information I submit with it, including my sign-off) is
> maintained indefinitely and may be redistributed consistent with
> this project or the open source license(s) involved.

Any contribution submitted for inclusion in the project by you, shall be licensed under the project's license, without any additional terms or conditions.