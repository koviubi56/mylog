# mylog

![Codacy grade](https://img.shields.io/codacy/grade/60939547f7b344bea1094f4c90ee69bb)
![CodeFactor Grade](https://img.shields.io/codefactor/grade/github/koviubi56/mylog/main)
![Codecov](https://img.shields.io/codecov/c/github/koviubi56/mylog)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![semantic-release](https://img.shields.io/badge/%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)
![PyPI - License](https://img.shields.io/pypi/l/python-mylog)
![PyPI](https://img.shields.io/pypi/v/python-mylog)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/python-mylog)
![PyPI - Format](https://img.shields.io/pypi/format/python-mylog)

A simple logging library for Python.

## Example/Getting started

First, install it with `pip install python-mylog`. [_Need more help?_](https://packaging.python.org/en/latest/tutorials/installing-packages/)

_For demonstration purposes only! Output may not be the same as shown here!_

```py
import mylog

logger = mylog.root.get_child()

logger.info("Hello, world!")
# Returns: 0
# Output: <nothing>
# Why? Because the threshold is set to WARNING.

# Try this:
logger.warning("Hello, world!")
# Returns: 70
# Output: [WARNING Sun Mar 27 18:56:57 2022 line: 00001] Hello, world!

# Or
logger.threshold = mylog.Level.debug
logger.info("Hello, world!")
# Returns: 67
# Output: [INFO Sun Mar 27 18:58:40 2022 line: 00001] Hello, world!
```

## API reference

For the API reference see the docstrings.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[GNU GPLv3.0+](LICENSE)

**Please note, that by contributing to mylog, you accept the DCO. [More info](CONTRIBUTING.md#dco)**
