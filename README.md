# mylog

[![Hits-of-Code](https://hitsofcode.com/github/koviubi56/mylog?branch=main)](https://hitsofcode.com/github/koviubi56/mylog/view?branch=main)
![Codecov](https://img.shields.io/codecov/c/github/koviubi56/mylog)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![semantic-release](https://img.shields.io/badge/%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)
![PyPI - License](https://img.shields.io/pypi/l/python-mylog)
![PyPI](https://img.shields.io/pypi/v/python-mylog)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/python-mylog)
![PyPI - Format](https://img.shields.io/pypi/format/python-mylog)
![PyPI - Implementation](https://img.shields.io/pypi/implementation/python-mylog)
![GitHub Workflow Status Tests](https://img.shields.io/github/actions/workflow/status/koviubi56/mylog/tests.yml?label=tests)

A simple logging library for Python.

## Example/Getting started

First, install it with `pip install python-mylog`. [_Need more help?_](https://packaging.python.org/en/latest/tutorials/installing-packages/)

```py
import mylog

mylog.root.info("Hello, world!")
# Output: <nothing>
# Why? Because the threshold is set to WARNING.

# Try this:
mylog.root.warning("Hello, world!")
# Output: [root WARNING 2023-12-23 13:39:16.127495+00:00 line: 00001] Hello, world!

# Or
mylog.root.threshold = mylog.Level.DEBUG
mylog.root.info("Hello, world!")
# Output: [root INFO 2023-12-23 13:39:34.231029+00:00 line: 00001] Hello, world!
```

## API reference

For the API reference see the docstrings.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[GNU GPLv3.0+](LICENSE)

**Please note, that by contributing to mylog, you accept the DCO. [More info](CONTRIBUTING.md#dco)**
