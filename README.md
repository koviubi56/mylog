# mylog

A simple logging library for Python.

## Example/Getting started

First, install it with `pip install git+https://github.com/koviubi56/mylog.git`. [*Need more help?*](https://packaging.python.org/en/latest/tutorials/installing-packages/)

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

### _function_ `to_level`(lvl: _Levelable_) -> _Level_

Converts an int/str/something to a Level.

### _class_ `NoLock`(blocking: _bool_ = True, timeout: _float_ = -1)

A "Lock" that does nothing.

### _class_ `LogEvent`(msg: _str_, level: _Level_, time: _int_, indent: _int_, frame-depth: _int_)

A log event.
Time is in UNIX seconds.

### _class_ `Logger`(higher: _Optional[Logger]_, \*, lock: _Optional[Lock]_ = None)

The logger class.

#### Class variables

##### _bool_ `colors`

Should level_to_str use colors? Defaults to `True`.

#### Methods

##### `level_to_str`(lvl: _Levelable_) -> _str_

Convert a level to a string.

##### `format_msg`(lvl: _Levelable_, msg: _Stringable_, tb: _bool_, frame-depth: _int_) -> _str_

Format the message.

##### `debug`/`info`/`warning`/`error`/`critical`(msg: _Stringable_, traceback: _bool_ = False) -> _int_

Log a message.

##### `get_child`() -> _Logger_

Get a child logger.

##### `is_enabled_for`(lvl: _Levelable_) -> _bool_

Check if the logger is enabled for the given level.

##### `get_effective_level`/`get_format`/`get_enabled`/`get_stream`/`get_indent`()

Get one of the logger's attribute.
It returns (respectively) `Level`, `str`, `bool`, `IO[str]`, `int`.

### _context manager_ `IndentLogger`(logger: _Logger_)

Indent the logger by one when entered, then unindent by one when exited.

### _variable_ `root`

The root logger.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[GNU LGPLv3.0+](https://www.gnu.org/licenses/lgpl-3.0.en.html)
