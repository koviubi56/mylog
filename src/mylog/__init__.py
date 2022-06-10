"""
Copyright (C) 2022  Koviubi56

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

__version__ = "0.4.0"

import abc
import contextlib
import dataclasses
import datetime
import sys
import time
import traceback
import uuid
import warnings
from enum import IntEnum
from types import TracebackType
from typing import Any, List, NoReturn, Optional, Tuple, TypeVar, Union

import termcolor
from typing_extensions import Literal, Protocol, Type, runtime_checkable

try:
    from types import UnionType
except ImportError:
    UnionType = type(Union[int, str])


T = TypeVar("T")
DEFAULT_FORMAT = "[{lvl} {time} line: {line}] {indent}{msg}"  # noqa: FS003


class Level(IntEnum):
    """Level for the log message."""

    debug = 10
    info = 20
    warning = 30
    error = 40
    critical = 50

    warn = warning
    fatal = critical


DEFAULT_THRESHOLD = Level.warning


@runtime_checkable
class Stringable(Protocol):
    """Protocol for stringable objects."""

    def __str__(self) -> str:
        """Return the string representation of the object."""


Levelable = Union[Level, Stringable, int]


def to_level(lvl: Levelable, int_ok: bool = False) -> Union[Level, int]:
    """
    Convert a Levelable to a Level (or int).

    Args:
        lvl (Levelable): The levelable object to convert.
        int_ok (bool, optional): If there's no level, can this function return\
 an int? Defaults to False.

    Raises:
        ValueError: If there's no level, and int_ok is False.

    Returns:
        Union[Level, int]: The level or int.
    """
    try:
        return Level(lvl)  # type: ignore
    except ValueError:
        try:
            return Level(int(lvl))  # type: ignore
        except ValueError:
            try:
                return getattr(Level, str(lvl))  # type: ignore
            except (AttributeError, ValueError):
                with contextlib.suppress(ValueError):
                    if int_ok:
                        return int(lvl)  # type: ignore
                raise ValueError(
                    f"Invalid level: {lvl!r}. Must be a Level, int, or str."
                ) from None


NoneType = type(None)


def _check_types_error(
    arg: str, expected: Union[type, Tuple[type, ...]], got: Any
) -> NoReturn:
    """
    Raise a TypeError with the correct message.

    Args:
        arg (str): The argument name.
        expected (Union[type, Tuple[type, ...]]): The expected type.
        got (Any): The got value.

    Raises:
        TypeError

    Returns:
        NoReturn: Never returns; raises.
    """
    raise TypeError(
        f"{arg!r} must be type {expected!r}, got {type(got)!r} ({got!r})"
    )


def is_union(union: Any) -> bool:
    """
    Is `union` a Union?

    >>> is_union(Union[int, str])
    True

    Args:
        union (Any): The object to check.

    Returns:
        bool: True if `union` is a Union, False otherwise.
    """
    try:
        return (
            (type(union) is Union)
            or (type(union) is UnionType)
            or (union.__origin__ is Union)  # type: ignore
        )
    except AttributeError:
        return False


#    Actually: Union   vvv
#                      ~~~
def check_union(union: Any, got: Any) -> bool:
    try:
        return isinstance(got, union)
    except TypeError:  # pragma: no cover
        return any(isinstance(got, typ) for typ in union.__args__)


def check_types(
    **kwargs: Tuple[Union[type, Tuple[type, ...]], Any]
) -> Literal[True]:
    """
    Check types.

    >>> check_types(a=(int, 1), b=(str, "2"))
    True
    >>> check_types(arg_1=((int, float), 1), b_8=(str, "Hello world"))
    True
    >>> check_types(do=(bool, True))
    True
    >>> check_types(do=(bool, None))  # !
    Traceback (most recent call last):
    TypeError: 'do' must be type <class 'bool'>, got <class 'NoneType'> (None)
    >>> check_types(do=(bool, False), sure=((bool, int), 6.9))  # !
    Traceback (most recent call last):
    TypeError: 'sure' must be type (<class 'bool'>, <class 'int'>), got\
 <class 'float'> (6.9)

    Args:
        **kwargs (Tuple[Union[type, Tuple[type, ...]], Any]): The args,\
 expected types and got values.

    Raises:
        TypeError: If the types are not correct.

    Returns:
        Literal[True]: Always True.
    """
    for arg, (expected, got) in kwargs.items():
        # ! This union thing is needed, because you cannot use isinstance with
        # ! unions in python 3.9 and below.
        if is_union(expected) and check_union(expected, got):
            continue
        if not isinstance(got, expected):
            _check_types_error(arg, expected, got)
    return True


class SetAttr:
    """A context manager for setting and then resetting an attribute."""

    def __init__(self, obj: object, name: str, new_value: Any) -> None:
        """
        Initialize the SetAttr.

        Args:
            obj (object): The object to set the attribute on.
            name (str): The name of the attribute.
            new_value (Any): The new value of the attribute.
        """
        self.obj = obj
        self.name = name
        self.new_value = new_value

    def __enter__(self) -> "SetAttr":
        """
        Enter the context manager.

        Returns:
            SetAttr: The SetAttr instance.
        """
        self.old_value = getattr(self.obj, self.name)
        setattr(self.obj, self.name, self.new_value)
        return self

    def __exit__(self, *args):
        """Exit the context manager."""
        setattr(self.obj, self.name, self.old_value)


@dataclasses.dataclass
class LogEvent:
    """A log event."""

    msg: str
    level: Levelable
    time: float  # ! UNIX seconds
    indent: int
    frame_depth: int
    tb: bool


@runtime_checkable
class StreamProtocol(Protocol):
    """Protocol for streams."""

    def write(self, __s: str, /) -> int:
        """
        Writes `__s` to the stream.

        Args:
            __s (str): The string to write.

        Returns:
            int: `len(__s)`
        """

    def flush(self) -> None:
        """Flushes the streams."""


class Handler(abc.ABC):
    """A handler ABC class."""

    @abc.abstractmethod
    def handle(self, logger: "Logger", event: LogEvent) -> None:
        """
        Handle the event.

        Args:
            logger (Logger): The logger that created the event.
            event (LogEvent): The event.
        """


class NoHandler(Handler):
    """A handler that does nothing."""

    def handle(self, logger: "Logger", event: LogEvent) -> None:
        """
        Handle the event.

        Args:
            logger (Logger): The logger that created the event.
            event (LogEvent): The event.
        """


class StreamWriterHandler(Handler):
    """A handler to write to a stream."""

    def __init__(
        self,
        stream: StreamProtocol,
        *,
        flush: bool = True,
        use_colors: bool = True,
        format_msg: bool = True,
    ) -> None:
        """
        Initialize the StreamWriterHandler.

        Args:
            stream (StreamProtocol): The stream to write to.
            flush (bool, optional): Flush the stream after writing to it?\
 Defaults to True.
            use_colors (bool, optional): Use colors? Defaults to True.
            format_msg (bool, optional): Format the message? Defaults to True.
        """
        check_types(
            stream=(StreamProtocol, stream),
            flush=(bool, flush),
            use_colors=(bool, use_colors),
            format_msg=(bool, format_msg),
        )
        self.stream = stream
        self.flush = flush
        self.use_colors = use_colors
        self.format_msg = format_msg

    def handle(self, logger: "Logger", event: LogEvent) -> None:
        """
        Handle the event.

        Args:
            logger (Logger): The logger that created the event.
            event (LogEvent): The event.
        """
        with SetAttr(logger, "colors", self.use_colors):
            msg = (
                (logger.format_msg(event))
                if (self.format_msg)
                else (event.msg)
            )
        self.stream.write(msg)
        if self.flush:
            self.stream.flush()


class Logger:
    """THE logger class. You shouldn't really call __init__; use the root\
 logger, or the root logger's get_child"""

    colors: bool = True
    # ↪ Should level_to_str use colors? Should be set manually.

    def __eq__(self, __o: object) -> bool:
        # sourcery skip: assign-if-exp, reintroduce-else
        if isinstance(
            __o, Logger  # Hardcoded, because class can be subclassed
        ):
            return self._id == __o._id
        return NotImplemented

    def __ne__(self, __o: object) -> bool:
        # sourcery skip: assign-if-exp, reintroduce-else
        if isinstance(
            __o, Logger  # Hardcoded, because class can be subclassed
        ):
            return self._id != __o._id
        return NotImplemented

    def _inherit(self) -> None:
        # Made a separate function so it can be overwritten

        # These (in my opinion) should not be inherited.
        self.propagate = False
        self._id = uuid.uuid4()  # Only used for ==, !=
        self.list: List[LogEvent] = []
        self.indent = 0  # Should be set manually
        self.enabled: bool = True
        self.ctxmgr = IndentLogger(self)

        # These (in my opinion) should be inherited.
        self.format: str = self.higher.format
        self.threshold: Level = self.higher.threshold
        self.handlers: List[Handler] = self.higher.handlers

    def get_default_handlers(self) -> List[Handler]:
        """
        Get the default handlers. Please note, that overwriting this function\
 will not change the handlers.

        Returns:
            List[Handler]: The default handlers.
        """
        return [StreamWriterHandler(sys.stderr)]

    def __init__(self, higher: Optional["Logger"] = None) -> None:
        """
        Initialize the logger.

        Args:
            higher (Optional[Logger], optional): The higher logger. If it's\
 None or omitted then the logger will be the root. Defaults to None.

        Raises:
            ValueError: If the higher logger is None, but root is already\
 created (internally)
        """
        check_types(higher=((Logger, NoneType), higher))
        if (higher is None) and (not _allow_root):
            raise ValueError(
                "Cannot create a new logger: Root logger already"
                " exists. Use that, or make a child logger from the root"
                " one."
            )
        if higher is not None:
            self.higher = higher
            # Made a separate function so it can be overwritten
            self._inherit()
            return
        self.higher = higher
        self.propagate = False  # ! Root logger should not propagate!
        self.list: List[LogEvent] = []
        self.indent = 0  # Should be set manually
        self.format: str = DEFAULT_FORMAT
        self.threshold: Level = DEFAULT_THRESHOLD
        self.enabled: bool = True
        self._id = uuid.uuid4()  # Only used for ==, !=
        self.handlers: List[Handler] = self.get_default_handlers()

        self.ctxmgr = IndentLogger(self)

    @staticmethod
    def _color(rv: str) -> str:
        """
        Colorize the string. This function is only recommended internally.

        Args:
            rv (str): The string to colorize.

        Returns:
            str: The colorized string.
        """
        check_types(rv=(str, rv))
        if rv == "DEBUG":
            rv = termcolor.colored("DEBUG".ljust(8), "blue")
        elif rv == "INFO":
            rv = termcolor.colored("INFO".ljust(8), "cyan")
        elif rv == "WARNING":
            rv = termcolor.colored("WARNING".ljust(8), "yellow")
        elif rv == "ERROR":
            rv = termcolor.colored("ERROR".ljust(8), "red")
        elif rv == "CRITICAL":
            rv = termcolor.colored(
                "CRITICAL".ljust(8),
                "red",
                "on_yellow",
                ["bold", "underline", "blink"],
            )
        return rv  # noqa: R504

    def level_to_str(self, lvl: Levelable) -> str:
        """
        Convert a level to a string.

        Args:
            lvl (Levelable): The level.

        Returns:
            str: The string.
        """
        check_types(lvl=(Levelable, lvl))
        try:
            rv = to_level(lvl, False).name.upper()  # type: ignore
        except (ValueError, AttributeError):
            rv = str(lvl).ljust(8)

        if rv == "WARN":  # pragma: no cover
            rv = "WARNING"
        if rv == "FATAL":  # pragma: no cover
            rv = "CRITICAL"

        if self.colors:
            rv = self._color(rv)

        return rv  # noqa: R504

    def format_msg(self, event: LogEvent) -> str:
        """
        Format the message.

        Args:
            event (LogEvent): The event.

        Returns:
            str: The formatted message.
        """
        check_types(event=(LogEvent, event))
        _indent = "  " * self.indent
        _lvl = self.level_to_str(event.level)
        _time = str(datetime.datetime.fromtimestamp(event.time))
        _line = str(sys._getframe(event.frame_depth).f_lineno).zfill(5)
        _msg = str(event.msg)
        if (event.tb) and (sys.exc_info() == (None, None, None)):
            warnings.warn(
                "No traceback available, but tb=True",
                UserWarning,
                event.frame_depth - 1,
            )
        _tb = ("\n" + traceback.format_exc()) if event.tb else ""
        return (
            self.format.format(
                indent=_indent,
                lvl=_lvl,
                time=_time,
                line=_line,
                msg=_msg,
            )
            + _tb
            + "\n"
        )

    def _actually_log(
        self,
        lvl: Levelable,
        msg: Stringable,
        frame_depth: int,
        tb: bool,
    ) -> LogEvent:  # sourcery skip: remove-unnecessary-cast
        """
        Actually log the message. ONLY USE THIS INTERNALLY!
        ! THIS DOES *NOT* CHECK IF IT SHOULD BE LOGGED! THIS IS *NOT* IN THE
        ! PUBLIC API, AND IT MUST NOT BE CALLED EXCEPT INTERNALLY!

        Args:
            lvl (Levelable): The level of the message.
            msg (Stringable): The message.
            frame_depth (int): The depth of the frame.
            tb (bool): Whether to include the traceback.

        Returns:
            LogEvent: The log event.
        """
        check_types(
            lvl=(Levelable, lvl),
            msg=(Stringable, msg),
            frame_depth=(int, frame_depth),
            tb=(bool, tb),
        )
        event = LogEvent(
            msg=str(msg),
            level=to_level(lvl, True),
            time=time.time(),
            indent=self.indent,
            frame_depth=frame_depth,
            tb=bool(tb),
        )
        self.list.append(event)
        for handler in self.handlers:
            handler.handle(self, event)
        return event

    def _log(
        self,
        lvl: Levelable,
        msg: Stringable,
        traceback: bool,
        frame_depth: int,
    ) -> Optional[LogEvent]:
        """
        Log the message. Checks if the logger is enabled, propagate, and stuff.
        This IS in the public api, but (unless you need it) use the methods
        debug, info, warning, error, critical.

        Args:
            lvl (Levelable): The level of the message.
            msg (Stringable): The message.
            traceback (bool): Whether to include the traceback.
            frame_depth (int): The depth of the frame. If you call this from\
 your code, this (probably) should be 3.

        Returns:
            Optional[LogEvent]: The log event if created.
        """
        check_types(
            lvl=(Levelable, lvl),
            msg=(Stringable, msg),
            traceback=(bool, traceback),
            frame_depth=(int, frame_depth),
        )
        # Check if disabled
        if not self.enabled:
            return None
        # Check if we should log it
        if self.propagate:
            # Check if we are root
            if self.higher is None:
                warnings.warn(
                    "Root logger should not propagate! Set enabled to"
                    " False if you want to disable it.",
                    UserWarning,
                    stacklevel=frame_depth - 1,
                )
                return None
            # Log with parent
            return self.higher._log(lvl, msg, traceback, frame_depth + 1)
        # Check if it's enabled
        if not self.is_enabled_for(lvl):
            return None
        # Log
        return self._actually_log(lvl, msg, frame_depth, traceback)

    def debug(
        self, msg: Stringable, traceback: bool = False
    ) -> Optional[LogEvent]:
        """
        Log a debug message.

        Args:
            msg (Stringable): The message.
            traceback (bool, optional): Whether to include the traceback.\
 Defaults to False.

        Returns:
            int: The number of characters written.
        """
        check_types(msg=(Stringable, msg), traceback=(bool, traceback))
        return self._log(Level.debug, msg, traceback, 4)

    def info(
        self, msg: Stringable, traceback: bool = False
    ) -> Optional[LogEvent]:
        """
        Log an info message.

        Args:
            msg (Stringable): The message.
            traceback (bool, optional): Whether to include the traceback.\
 Defaults to False.

        Returns:
            int: The number of characters written.
        """
        check_types(msg=(Stringable, msg), traceback=(bool, traceback))
        return self._log(Level.info, msg, traceback, 4)

    def warning(
        self, msg: Stringable, traceback: bool = False
    ) -> Optional[LogEvent]:
        """
        Log a warning message.

        Args:
            msg (Stringable): The message.
            traceback (bool, optional): Whether to include the traceback.\
 Defaults to False.

        Returns:
            int: The number of characters written.
        """
        check_types(msg=(Stringable, msg), traceback=(bool, traceback))
        return self._log(Level.warning, msg, traceback, 4)

    def error(
        self, msg: Stringable, traceback: bool = False
    ) -> Optional[LogEvent]:
        """
        Log an error message.

        Args:
            msg (Stringable): The message.
            traceback (bool, optional): Whether to include the traceback.\
 Defaults to False.

        Returns:
            int: The number of characters written.
        """
        check_types(msg=(Stringable, msg), traceback=(bool, traceback))
        return self._log(Level.error, msg, traceback, 4)

    def critical(
        self, msg: Stringable, traceback: bool = False
    ) -> Optional[LogEvent]:
        """
        Log a critical/fatal message.

        Args:
            msg (Stringable): The message.
            traceback (bool, optional): Whether to include the traceback.\
 Defaults to False.

        Returns:
            int: The number of characters written.
        """
        check_types(msg=(Stringable, msg), traceback=(bool, traceback))
        return self._log(Level.critical, msg, traceback, 4)

    def get_child(self) -> "Logger":
        """
        Get a child logger.

        Returns:
            Logger: The child logger.
        """
        # This function should be short, so if the user doesn't like it, it
        # can be copy-pasted, and the user can change it.
        # (That's why we have `._inherit`)
        return type(self)(self)

    def is_enabled_for(self, lvl: Levelable) -> bool:
        """
        Check if the logger is enabled for the given level.

        Args:
            lvl (Levelable): The level to check.

        Returns:
            bool: Whether the logger is enabled for the given level.
        """
        check_types(lvl=(Levelable, lvl))
        lvl = to_level(lvl, True)
        if not isinstance(self.threshold, Level):
            warnings.warn(
                "Logger threshold should be a Level, not"
                f" {type(self.threshold)!r} ({self.threshold!r})."
                " Converting threshold...",
                UserWarning,
            )
            self.threshold = to_level(self.threshold, True)
        return lvl >= self.threshold


class IndentLogger:
    """Indent the logger."""

    def __init__(self, logger: Logger) -> None:
        """
        Initialize the indent logger.

        Args:
            logger (Logger): The logger.
        """
        check_types(logger=(Logger, logger))
        self.logger = logger

    def __enter__(self) -> int:
        """
        Indent the logger by one.

        Returns:
            int: The logger's indent
        """
        self.logger.indent += 1
        return self.logger.indent

    def __exit__(
        self,
        typ: Type[BaseException],
        value: BaseException,
        tb: TracebackType,
    ) -> None:
        """
        Unindent the logger by one.

        Args:
            typ (Type[BaseException]): The exception type.
            value (BaseException): The exception.
            tb (TracebackType): The traceback.
        """
        self.logger.indent -= 1


class ChangeThreshold:
    """Change the threshold for a logger."""

    def __init__(self, logger: Logger, level: Levelable) -> None:
        """
        Initialize the threshold changer.

        Args:
            logger (Logger): The logger.
            level (Levelable): The new threshold.
        """
        check_types(logger=(Logger, logger), level=(Levelable, level))
        self.logger = logger
        self.level = to_level(level, True)

    def __enter__(self) -> Level:
        """
        Change the threshold.

        Returns:
            Level: The old threshold.
        """
        self.old_level = self.logger.threshold
        self.logger.threshold = self.level  # type: ignore
        return self.old_level

    def __exit__(
        self,
        typ: Type[BaseException],
        value: BaseException,
        tb: TracebackType,
    ) -> None:
        """
        Restore the threshold.

        Args:
            typ (Type[BaseException]): The exception type.
            value (BaseException): The exception.
            tb (TracebackType): The traceback.
        """
        self.logger.threshold = self.old_level


_allow_root = True
root = Logger()
_allow_root = False
