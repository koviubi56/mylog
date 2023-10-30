# Documentation for mylog

For an introduction to mylog, see the [readme](README.md).

## API Reference

For more information, see the docstrings and the source code.

Only things in the public API are documented here.

### _constant_ `__version__`

The current version of mylog as a string. Compliant with [Semantic Versioning](https://semver.org/). Between releases, it has the latest release's version.

### _constant_ `DEFAULT_FORMAT`

The default message format used by `Logger.format_message`. Do not modify this, instead change `logger.format`.

### _enum_ `Level`

The predefined levels for log events.

- `debug` = `10`
- `info` = `20`
- `warning` = `warn` = `30`
- `error` = `40`
- `critical` = `fatal` = `50`

### _constant_ `DEFAULT_THRESHOLD`

The default threshold used by `Logger.is_enabled_for`. Do not modify this, instead change `logger.threshold`.

### _function_ `to_level`

`to_level(level: Levelable, int_ok: bool = False) -> (Level | int)`

Turns a Levelable (`Level | Stringable | int`) into a level, or int.

If the level doesn't match any predefined levels (`Level`), then it will

- if `int_ok` is True: return an int,
- if `int_ok` is False: raise a `ValueError`.

### _dataclass_ `LogEvent`

A single log event.

#### _attribute_ `message`

The message for the log event.

#### _attribute_ `level`

The level for the log event. May be `Level` or `int`.

#### _attribute_ `time`

The time when the log event was created. It's in UNIX seconds (see `time.time()`).

#### _attribute_ `indent`

Indentation for the log message.

#### _attribute_ `frame_depth`

The depth of the frame. Used to obtain the line number where the log event was issued.

#### _attribute_ `traceback`

Whether to include the traceback when printing the log event.

### _abc_ `Handler`

An ABC for a class that handles log events.

#### _abstract method_ `handle`

`handle(self: Self@Handler, logger: Logger, event: LogEvent) -> None`

Handle the log event. For example: print it to stderr (see `StreamWriterHandler`).

### _dataclass_ `NoHandler`

Subclass and implementation of abc `Handler`, which does nothing.

#### _method_ `handle`

`handle(self: Self@NoHandler, logger: Logger, event: LogEvent) -> None`

Does nothing.

### _dataclass_ `StreamWriterHandler`

Subclass and implementation of abc `Handler`, which writes to a stream.

#### _attribute_ `stream`

The stream to write to. Must support `.write(str)` and (if `flush` is True) `.flush()`.

#### _attribute_ `flush`

Whether to flush the stream after every write.

#### _attribute_ `use_colors`

Whether to use colors.

#### _attribute_ `format_message`

Whether to format the message using `logger.format_message(event)`, or just use the log event's message.

#### _method_ `handle`

`handle(self: Self@StreamWriterHandler, logger: Logger, event: LogEvent) -> None`

Write to the stream. See the above attributes for configuration.

### _dataclass_ `AttributesToInherit`

What attributes should be inherited when that logger is inherited.

Please note, that changes done to a parent logger **will not be made** to already existing child loggers!

#### Attributes

- `propagate` (defaults to `False`)
- `_id` (defaults to `False`)
- `list` (defaults to `False`)
- `indent` (defaults to `False`)
- `enabled` (defaults to `False`)
- `ctxmgr` (defaults to `False`)
- `format` (defaults to `True`)
- `threshold` (defaults to `True`)
- `handlers` (defaults to `True`)

### _class_ `Logger`

_THE_ logger class.

You shouldn't really call `__init__`; use the root logger, or the root logger's `.get_child()`.

#### _class variable_ `colors`

Whether `.level_to_str` should use colors.

#### _class variable_ `compare_using_name`

Whether comparison (`__eq__`, `__ne__`; ==, !=) should be done with names or unique IDs.

#### _class variable_ `attributes_to_inherit`

See `AttributesToInherit`.

#### _class variable_ `color_config`

A dictionary mapping levels' names to `termcolor.colored` arguments.

#### _class variable_ `level_name_width`

Should be the width of the longest level's name. Used for `.ljust()`. Set to `0` to disable this behavior.

#### _instance attribute_ `name`

The name of the logger.

#### _instance attribute_ `higher`

The parent logger or (for root) `None`.

#### _instance attribute_ `propagate`

If `True`, the parent logger (`.higher`) will log all messages.

The root logger should not propagate!

If `.enabled` is `False` then `propagate` is ignored!

#### _instance attribute_ `list`

List of all log events. New events are appended to the end.

#### _instance attribute_ `indent`

Indentation used by `.format_message`. See `IndentLogger` and `.ctxmgr`.

#### _instance attribute_ `format`

Message format used by `.format_message`.

Values that will be replaced:

- `{indent}` (`"  " * event.indent`)
- `{level}` (`self.level_to_str(event.level)`)
- `{time}` (`str(datetime.datetime.fromtimestamp(event.time, datetime.timezone.utc))`)
- `{line}` (`str(sys._getframe(event.frame_depth).f_lineno).zfill(5)`)
- `{message}` (`str(event.message)`)
- `{name}` (`str(self.name)`)

#### _instance attribute_ `threshold`

Log events below this level will not be logged. See `is_enabled_for`.

#### _instance attribute_ `enabled`

Whether this logger is enabled. If this is `False` then `.log` will do nothing (not even propagate!).

#### _instance attribute_ `_id`

Unique UUID4 for the logger.

#### _instance attribute_ `handlers`

List of handlers. Generated using `.get_default_handlers` (or inherited; see `.attributes_to_inherit`).

#### _instance attribute_ `ctxmgr`

Instance of `IndentLogger`.

#### _static method_ `get_default_handlers`

`get_default_handlers() -> List[Handler]`

Get the list of default handlers. Called once from `__init__` (for `root`) or from `_inherit` (for children).

To change the already existing handlers, modify `logger.handlers` instead.

#### _method_ `__init__`

`__init__(self: Self@Logger, name: str, higher: Logger | None = None) -> None`

Create a new logger.

If `higher` is None the new logger will be treated as the root one. Only one root logger may exist, and it is automatically created as `root`. Any attempts to create it after that will raise a `ValueError`.

If `higher` is a Logger instance, it will be treated as the parent logger, and `._inherit()` will inherit the stuff it needs (see `Logger.attributes_to_inherit`).

#### _class method_ `color`

`color(cls: type[Self@Logger], rv: str) -> str`

Colorize a level's name if possible and requested (see `Logger.colors`).

#### _class method_ `level_to_str`

`level_to_str(cls: type[Self@Logger], level: Levelable) -> str`

Convert a Levelable to a string with optionally colorizing it (see `Logger.color`).

#### _method_ `format_message`

`format_message(self: Self@Logger, event: LogEvent) -> str`

Format the message using `.format`.

#### _method_ `_actually_log`

`_actually_log(self: Self@Logger, event: LogEvent) -> LogEvent`

**This method is _not_ in the public API! Do not call it!**

Actually log the message. This method will call the handlers.

#### _method_ `create_log_event`

`create_log_event(self: Self@Logger, *, message: Stringable, level: Levelable, frame_depth: int, traceback: bool) -> LogEvent`

Create a log event using the arguments provided.

#### _method_ `log`

`log(self: Self@Logger, level: Levelable, message: Stringable, traceback: bool = False, frame_depth: int = 4) -> (LogEvent | None)`

Log a message. Checks if the logger is enabled, propagate if needed, check if event should be logged, ...

This _is_ in the public API, but only use it if your level is not predefined in `Level`. Otherwise, use the `.debug`, `.info`, ... methods.

#### _method_ `debug`

`debug(self: Self@Logger, message: Stringable, traceback: bool = False) -> (LogEvent | None)`

Log a message with debug level. Calls `.log`.

#### _method_ `info`

`info(self: Self@Logger, message: Stringable, traceback: bool = False) -> (LogEvent | None)`

Log a message with info level. Calls `.log`.

#### _method_ `warning`

`warning(self: Self@Logger, message: Stringable, traceback: bool = False) -> (LogEvent | None)`

Log a message with warning level. Calls `.log`.

#### _method_ `error`

`error(self: Self@Logger, message: Stringable, traceback: bool = False) -> (LogEvent | None)`

Log a message with error level. Calls `.log`.

#### _method_ `critical`

`critical(self: Self@Logger, message: Stringable, traceback: bool = False) -> (LogEvent | None)`

Log a message with critical level. Calls `.log`.

#### _method_ `get_child`

`get_child(self: Self@Logger, name: str) -> Logger`

Create a child logger. Multiple may exist with the same name; calling this function will always create a new logger.

#### _method_ `is_enabled_for`

`is_enabled_for(self: Self@Logger, level: Levelable) -> bool`

Returns whether the level is greater than or equals to `.threshold`.

#### _method_ `should_be_logged`

`should_be_logged(self: Self@Logger, event: LogEvent) -> bool`

Returns whether the event should be logged.

This method **does not check** `.enabled` nor `.propagate`!

By defaults, this only calls `.is_enabled_for(event.level)`.

### _context manager_ `IndentLogger`

Indent the logger at `__enter__` and de-indent at `__exit__`.

#### _attribute_ `logger`

The logger to indent.

### _context manager_ `ChangeThreshold`

Change the threshold at `__enter__` and restore at `__exit__`

#### _attribute_ `logger`

The logger to modify.

### _variable_ `_allow_root`

**This variable is _not_ in the public API! Do not modify it!**

Whether creating a root logger (logger with no parent) is allowed.

It is `True` right before creating `root`, and is set to `False` after that.
