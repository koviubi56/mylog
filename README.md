# mylog

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/60939547f7b344bea1094f4c90ee69bb)](https://www.codacy.com/gh/koviubi56/mylog/dashboard?utm_source=github.com&utm_medium=referral&utm_content=koviubi56/mylog&utm_campaign=Badge_Grade)
[![CodeFactor](https://www.codefactor.io/repository/github/koviubi56/mylog/badge)](https://www.codefactor.io/repository/github/koviubi56/mylog)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/koviubi56/mylog/main.svg)](https://results.pre-commit.ci/latest/github/koviubi56/mylog/main)
[![Build Status](https://app.travis-ci.com/koviubi56/mylog.svg?branch=main)](https://app.travis-ci.com/koviubi56/mylog)
[![codecov](https://codecov.io/gh/koviubi56/mylog/branch/main/graph/badge.svg?token=PFHDLZJMVL)](https://codecov.io/gh/koviubi56/mylog)

A simple logging library for Python.

## Example/Getting started

First, install it with `pip install git+https://github.com/koviubi56/mylog.git`. [_Need more help?_](https://packaging.python.org/en/latest/tutorials/installing-packages/)

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

**Warning!** This is only the public API!

**WARNING!** If you see a `-` (minus/dash/hyphen) in an argument name, **it is a `_` (underscore)!**

### _variable_ `__version__`

The version string of the library.

### _constant_ `DEFAULT_FORMAT`

The default format used by MyLog.
By default it is `"[{lvl} {time} line: {line}] {indent}{msg}"`.

### _IntEnum class_ `Level`

Different levels of logging. (Note that logging levels aren't required to be one of these.)

| Name       | Value |
| ---------- | ----- |
| `debug`    | `10`  |
| `info`     | `20`  |
| `warning`  | `30`  |
| `error`    | `40`  |
| `critical` | `50`  |

Aliases:

- `warn` == `warning`
- `fatal` == `critical`

### _constant_ `DEFAULT_THRESHOLD`

The default threshold used by MyLog.
By default it is `Level.warning`.

### _protocol_ `Stringable`

A class that has a `__str__` method, that returns a string.

### _type alias_ `Levelable`

```py
Union[Level, Stringable, int]
```

### _function_ `to_level`(lvl: _Levelable_, int-ok: _bool_ = False) -> _Level_

Converts an int/str/something to a Level. If `lvl` cannot be converted, and `int_ok` is True, the int will be returned.

### _protocol_ `Lock`

A class that has a `__enter__` and `__exit__` method.

### _class_ `NoLock`(blocking: _bool_ = True, timeout: _float_ = -1)

A "Lock" that does nothing.

### _type alias_ `NoneType`

```py
type(None)
```

### _class_ `LogEvent`(msg: _str_, level: _Level_, time: _float_, indent: _int_, frame-depth: _int_)

A log event.
Time is in UNIX seconds.

### _class_ `Logger`(higher: _Optional[Logger]_, \*, lock: _Optional[Lock]_ = None)

The logger class.

#### Class variables

##### _bool_ `colors`

Should level_to_str use colors? Defaults to `True`.

#### Static methods

##### `_color`(rv: _str_) -> _str_

Colorizes a string.

#### Methods

##### `_inherit_`(lock: _Optional[Lock]_) -> _None_

Inherit from `self.higher` (_"parent"_).

##### `level_to_str`(lvl: _Levelable_) -> _str_

Convert a level to a string.

##### `format_msg`(lvl: _Levelable_, msg: _Stringable_, tb: _bool_, frame-depth: _int_) -> _str_

Format the message.

##### `_log`(lvl: _Levelable_, msg: _Stringable_, tb: _bool_, frame-depth: _int_) -> _int_

Log a message.

##### `debug`/`info`/`warning`/`error`/`critical`(msg: _Stringable_, traceback: _bool_ = False) -> _int_

Log a message.

##### `get_child`() -> _Logger_

Get a child logger.

##### `is_enabled_for`(lvl: _Levelable_) -> _bool_

Check if the logger is enabled for the given level.

### _context manager_ `IndentLogger`(logger: _Logger_)

Indent the logger by one when entered, then unindent by one when exited.

### _context manager_ `ChangeThreshold`(logger: _Logger_, level: _Levelable_)

Change the threshold of the logger to `level` when entered, then restore the threshold when exited.

### _variable_ `root`

The root logger.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[GNU LGPLv3.0+](https://www.gnu.org/licenses/lgpl-3.0.en.html)
