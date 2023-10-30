"""
Copyright (C) 2022-2023  Koviubi56

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
# SPDX-License-Identifier: GPL-3.0-or-later

__version__ = "0.8.0"

import abc
import contextlib
import dataclasses
import datetime
import sys
import time
import traceback as tracebacklib
import uuid
import warnings
from enum import IntEnum
from types import TracebackType
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Literal,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
    runtime_checkable,
)

import termcolor

with contextlib.suppress(Exception):
    import colorama

    colorama.init()

UnionType = type(Union[int, str])
T = TypeVar("T")
DEFAULT_FORMAT = "[{name} {level} {time} line: {line}] {indent}{message}"
# dataclass' kw_only argument was introduced in python 3.10
# i don't want to make the requirement 3.10 from 3.8, so instead we check
# whether or not kw_only is a thing. if it is we'll use it, if it's not, we'll
# ignore it
DATACLASS_HAS_KW_ONLY = "kw_only" in dataclasses.dataclass.__kwdefaults__
DATACLASS_KW_ONLY = {"kw_only": True} if DATACLASS_HAS_KW_ONLY else {}


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

    def __str__(self) -> str:  # pragma: no cover
        """Return the string representation of the object."""
        return ""


Levelable = Union[Level, Stringable, int]


@overload
def to_level(
    level: Levelable, int_ok: Literal[True] = False
) -> Union[Level, int]:  # pragma: no cover
    ...


@overload
def to_level(
    level: Levelable, int_ok: Literal[False] = False
) -> Level:  # pragma: no cover
    ...


def to_level(level: Levelable, int_ok: bool = False) -> Union[Level, int]:
    """
    Convert a Levelable to a Level (or int).

    Args:
        level (Levelable): The levelable object to convert.
        int_ok (bool, optional): If there's no level, can this function return\
 an int? Defaults to False.

    Raises:
        ValueError: If there's no level, and int_ok is False.

    Returns:
        Union[Level, int]: The level or int.
    """
    try:
        return Level(level)
    except ValueError:
        try:
            return Level(int(level))
        except ValueError:
            try:
                return getattr(Level, str(level))
            except (AttributeError, ValueError):
                with contextlib.suppress(ValueError):
                    if int_ok:
                        return int(level)
                raise ValueError(
                    f"Invalid level: {level!r}. Must be a Level, int, or str."
                ) from None


NoneType = type(None)


@dataclasses.dataclass(order=True)
class SetAttr:
    """A context manager for setting and then resetting an attribute."""

    obj: object
    name: str
    new_value: Any

    def __enter__(self) -> "SetAttr":
        """
        Enter the context manager.

        Returns:
            SetAttr: The SetAttr instance.
        """
        self.old_value = getattr(self.obj, self.name)
        setattr(self.obj, self.name, self.new_value)
        return self

    def __exit__(
        self,
        typ: Optional[Type[BaseException]],
        value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Exit the context manager."""
        setattr(self.obj, self.name, self.old_value)


@dataclasses.dataclass(order=True, frozen=True)
class LogEvent:
    """A log event."""

    message: str
    level: Levelable
    time: float  # ! UNIX seconds (see time.time())
    indent: int
    frame_depth: int
    traceback: bool


@runtime_checkable
class StreamProtocol(Protocol):
    """Protocol for streams."""

    def write(self, __s: str, /) -> int:  # pragma: no cover
        """
        Writes `__s` to the stream.

        Args:
            __s (str): The string to write.

        Returns:
            int: `len(__s)`
        """
        return 0

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


@dataclasses.dataclass
class NoHandler(Handler):
    """A handler that does nothing."""

    def handle(self, logger: "Logger", event: LogEvent) -> None:
        """
        Handle the event.

        Args:
            logger (Logger): The logger that created the event.
            event (LogEvent): The event.
        """


@dataclasses.dataclass(order=True, frozen=True)
class StreamWriterHandler(Handler):
    """A handler to write to a stream."""

    stream: StreamProtocol
    flush: bool = True
    use_colors: bool = True
    format_message: bool = True

    def handle(self, logger: "Logger", event: LogEvent) -> None:
        """
        Handle the event.

        Args:
            logger (Logger): The logger that created the event.
            event (LogEvent): The event.
        """
        with SetAttr(logger, "colors", self.use_colors):
            message = (
                (logger.format_message(event))
                if (self.format_message)
                else (event.message)
            )
        self.stream.write(message)
        if self.flush:
            self.stream.flush()


@dataclasses.dataclass(order=True, frozen=True, **DATACLASS_KW_ONLY)
class AttributesToInherit:
    """
    What attributes to inherit.

    Note: Changes made to the parent logger won't be made to the children.
    """

    propagate: bool = False
    _id: bool = False
    list: bool = False  # noqa: A003
    indent: bool = False
    enabled: bool = False
    ctxmgr: bool = False
    # IndentLogger (used by ctxmgr) takes the logger as an argument.
    # If it's inherited the PARENT LOGGER will be indented
    format: bool = True  # noqa: A003
    threshold: bool = True
    handlers: bool = True


class Logger:
    """
    THE logger class.

    You shouldn't really call `__init__`; use the root logger, or the root
    logger's `get_child`.
    """

    colors: ClassVar[bool] = True
    # ↪ Should level_to_str use colors? Should be set manually.
    compare_using_name: ClassVar[bool] = False
    # ↪ Compare (__eq__, __ne__) using self.name? If False, use self._id
    attributes_to_inherit: ClassVar[
        AttributesToInherit
    ] = AttributesToInherit()
    # ↪ What attributes should get inherited in ._inherit()
    color_config: ClassVar[Dict[str, Tuple[Any, ...]]] = {
        "DEBUG": ("blue",),
        "INFO": ("cyan",),
        "WARNING": ("yellow",),
        "ERROR": ("red",),
        "CRITICAL": ("red", "on_yellow", ["bold", "underline", "blink"]),
    }
    level_name_width: ClassVar[int] = 8

    @classmethod
    def _thing_to_compare(cls, obj: "Logger") -> str:
        return obj.name if cls.compare_using_name else str(obj._id)

    def __eq__(self, __o: object) -> bool:
        if isinstance(
            __o,
            Logger,  # Hardcoded, because class can be subclassed
        ):
            return self._thing_to_compare(self) == self._thing_to_compare(__o)
        return NotImplemented

    def __ne__(self, __o: object) -> bool:
        if isinstance(
            __o,
            Logger,  # Hardcoded, because class can be subclassed
        ):
            return self._thing_to_compare(self) != self._thing_to_compare(__o)

        return NotImplemented

    def __repr__(self) -> str:  # pragma: no cover
        return f"<{self.__class__.__qualname__} {self.name}>"

    def _inherit(self) -> None:  # noqa: C901, PLR0912  # pragma: no cover
        if self.higher is None:
            raise ValueError("Cannot inherit if higher is None.")

        if self.attributes_to_inherit.propagate:
            self.propagate = self.higher.propagate
        else:
            self.propagate = False
        if self.attributes_to_inherit._id:
            self._id = self.higher._id
        else:
            self._id = uuid.uuid4()
        if self.attributes_to_inherit.list:
            self.list = self.higher.list
        else:
            self.list: List[LogEvent] = []
        if self.attributes_to_inherit.indent:
            self.indent = self.higher.indent
        else:
            self.indent = 0
        if self.attributes_to_inherit.enabled:
            self.enabled = self.higher.enabled
        else:
            self.enabled = True
        if self.attributes_to_inherit.ctxmgr:
            self.ctxmgr = self.higher.ctxmgr
        else:
            self.ctxmgr = IndentLogger(self)
        if self.attributes_to_inherit.format:
            self.format = self.higher.format
        else:
            self.format = DEFAULT_FORMAT
        if self.attributes_to_inherit.threshold:
            self.threshold: Union[Level, int] = self.higher.threshold
        else:
            self.threshold = DEFAULT_THRESHOLD
        if self.attributes_to_inherit.handlers:
            self.handlers = self.higher.handlers
        else:
            self.handlers = self.get_default_handlers()

    @staticmethod
    def get_default_handlers() -> List[Handler]:
        """
        Get the default handlers.

        This is called once in `__init__` and `_inherit`.

        Returns:
            List[Handler]: The default handlers.
        """
        return [StreamWriterHandler(sys.stderr)]

    def __init__(self, name: str, higher: Optional["Logger"] = None) -> None:
        """
        Initialize the logger.

        Args:
            name (str): The name of the logger.
            higher (Optional[Logger], optional): The higher logger. If it's\
 None or omitted then the logger will be the root. Defaults to None.

        Raises:
            ValueError: If the higher logger is None, but root is already\
 created (internally)
        """
        if (higher is None) and (not _allow_root):
            raise ValueError(
                "Cannot create a new logger: Root logger already"
                " exists. Use that, or make a child logger from the root"
                " one."
            )
        self.name = name
        self.higher = higher
        if higher is not None:
            # Made a separate function so it can be overwritten
            self._inherit()
            return
        self.propagate = False  # ! Root logger should not propagate!
        self.list: List[LogEvent] = []
        self.indent = 0  # Should be set manually
        self.format: str = DEFAULT_FORMAT
        self.threshold: Union[Level, int] = DEFAULT_THRESHOLD
        self.enabled: bool = True
        self._id = uuid.uuid4()  # Only used for ==, !=
        self.handlers: List[Handler] = self.get_default_handlers()

        self.ctxmgr = IndentLogger(self)

    @classmethod
    def color(cls, rv: str) -> str:
        """
        Colorize the string. This function is only recommended internally.

        Args:
            rv (str): The string to colorize.

        Returns:
            str: The colorized string.
        """
        if rv in cls.color_config:
            return termcolor.colored(
                rv.ljust(cls.level_name_width), *cls.color_config[rv]
            )
        return rv

    @classmethod
    def level_to_str(cls, level: Levelable) -> str:
        """
        Convert a level to a string.

        Args:
            level (Levelable): The level.

        Returns:
            str: The string.
        """
        try:
            rv = to_level(level, False).name.upper()
        except (ValueError, AttributeError):
            rv = str(level).ljust(cls.level_name_width)

        if cls.colors:
            rv = cls.color(rv)

        return rv

    def format_message(self, event: LogEvent) -> str:
        """
        Format the message.

        Args:
            event (LogEvent): The event.

        Returns:
            str: The formatted message.
        """
        _indent = "  " * self.indent
        _level = self.level_to_str(event.level)
        _time = str(
            datetime.datetime.fromtimestamp(event.time, datetime.timezone.utc)
        )
        _line = str(sys._getframe(event.frame_depth).f_lineno).zfill(5)
        _message = str(event.message)
        _name = str(self.name)
        if (event.traceback) and (sys.exc_info() == (None, None, None)):
            warnings.warn(
                "No traceback available, but traceback=True",
                UserWarning,
                stacklevel=event.frame_depth - 1,
            )
        _traceback = (
            ("\n" + tracebacklib.format_exc()) if event.traceback else ""
        )
        return (
            self.format.format(
                indent=_indent,
                level=_level,
                time=_time,
                line=_line,
                message=_message,
                name=_name,
            )
            + _traceback
            + "\n"
        )

    def _actually_log(
        self,
        event: LogEvent,
    ) -> LogEvent:
        """
        Actually log the message. ONLY USE THIS INTERNALLY!

        ! THIS DOES *NOT* CHECK IF IT SHOULD BE LOGGED! THIS IS *NOT* IN THE
        ! PUBLIC API, AND IT MUST NOT BE CALLED EXCEPT INTERNALLY!

        Args:
            event (LogEvent): The event to log.

        Returns:
            LogEvent: The log event.
        """
        self.list.append(event)
        for handler in self.handlers:
            handler.handle(self, event)
        return event

    def create_log_event(
        self,
        *,
        message: Stringable,
        level: Levelable,
        frame_depth: int,
        traceback: bool,
    ) -> LogEvent:
        """
        Create a log event.

        Args:
            message (str): The message for the event.
            level (Levelable): The log level.
            frame_depth (int): The depth of the frame.
            traceback (bool): Whether to include the traceback.

        Returns:
            LogEvent: The newly created log event.
        """
        return LogEvent(
            message=str(message),
            level=to_level(level, True),
            time=time.time(),
            indent=self.indent,
            frame_depth=frame_depth,
            traceback=traceback,
        )

    def log(
        self,
        level: Levelable,
        message: Stringable,
        traceback: bool = False,
        frame_depth: int = 4,
    ) -> Optional[LogEvent]:
        """
        Log the message. Checks if the logger is enabled, propagate, and stuff.

        This IS in the public api, but (unless you need it) use the methods
        debug, info, warning, error, critical.

        Args:
            level (Levelable): The level of the message.
            message (Stringable): The message.
            traceback (bool): Whether to include the traceback.
            frame_depth (int): The depth of the frame. If you call this from\
 your code, this (probably) should be 4.

        Returns:
            Optional[LogEvent]: The log event if created.
        """
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
            return self.higher.log(level, message, traceback, frame_depth + 1)
        event = self.create_log_event(
            message=message,
            level=level,
            frame_depth=frame_depth,
            traceback=traceback,
        )
        # Check if it should be logged
        if not self.should_be_logged(event):
            return None
        # Log
        return self._actually_log(event)

    def debug(
        self, message: Stringable, traceback: bool = False
    ) -> Optional[LogEvent]:
        """
        Log a debug message.

        Args:
            message (Stringable): The message.
            traceback (bool, optional): Whether to include the traceback.\
 Defaults to False.

        Returns:
            int: The number of characters written.
        """
        return self.log(Level.debug, message, traceback, 5)

    def info(
        self, message: Stringable, traceback: bool = False
    ) -> Optional[LogEvent]:
        """
        Log an info message.

        Args:
            message (Stringable): The message.
            traceback (bool, optional): Whether to include the traceback.\
 Defaults to False.

        Returns:
            int: The number of characters written.
        """
        return self.log(Level.info, message, traceback, 5)

    def warning(
        self, message: Stringable, traceback: bool = False
    ) -> Optional[LogEvent]:
        """
        Log a warning message.

        Args:
            message (Stringable): The message.
            traceback (bool, optional): Whether to include the traceback.\
 Defaults to False.

        Returns:
            int: The number of characters written.
        """
        return self.log(Level.warning, message, traceback, 5)

    def error(
        self, message: Stringable, traceback: bool = False
    ) -> Optional[LogEvent]:
        """
        Log an error message.

        Args:
            message (Stringable): The message.
            traceback (bool, optional): Whether to include the traceback.\
 Defaults to False.

        Returns:
            int: The number of characters written.
        """
        return self.log(Level.error, message, traceback, 5)

    def critical(
        self, message: Stringable, traceback: bool = False
    ) -> Optional[LogEvent]:
        """
        Log a critical/fatal message.

        Args:
            message (Stringable): The message.
            traceback (bool, optional): Whether to include the traceback.\
 Defaults to False.

        Returns:
            int: The number of characters written.
        """
        return self.log(Level.critical, message, traceback, 5)

    def get_child(self, name: str) -> "Logger":
        """
        Get a child logger.

        Returns:
            Logger: The child logger.
        """
        # This function should be short, so if the user doesn't like it, it
        # can be copy-pasted, and the user can change it.
        # (That's why we have `._inherit`)
        return type(self)(name, self)

    def is_enabled_for(self, level: Levelable) -> bool:
        """
        Check if the logger is enabled for the given level.

        Args:
            level (Levelable): The level to check.

        Returns:
            bool: Whether the logger is enabled for the given level.
        """
        level = to_level(level, True)
        return level >= self.threshold

    def should_be_logged(self, event: LogEvent) -> bool:
        """
        Returns whether or not `event` should be logged.

        Args:
            event (LogEvent): The log event in question.

        Returns:
            bool: True if it should be logged, False otherwise.
        """
        return self.is_enabled_for(event.level)


@dataclasses.dataclass(order=True)
class IndentLogger:
    """Indent the logger."""

    logger: Logger

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
        typ: Optional[Type[BaseException]],
        value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """
        Unindent the logger by one.

        Args:
            typ (Type[BaseException]): The exception type.
            value (BaseException): The exception.
            traceback (TracebackType): The traceback.
        """
        self.logger.indent -= 1


@dataclasses.dataclass(order=True)
class ChangeThreshold:
    """Change the threshold for a logger."""

    def __init__(self, logger: Logger, level: Levelable) -> None:
        """
        Initialize the threshold changer.

        Args:
            logger (Logger): The logger.
            level (Levelable): The new threshold.
        """
        self.logger = logger
        self.level = to_level(level, True)

    def __enter__(self) -> Union[Level, int]:
        """
        Change the threshold.

        Returns:
            Union[Level, int]: The old threshold.
        """
        self.old_level = self.logger.threshold
        self.logger.threshold = self.level
        return self.old_level

    def __exit__(
        self,
        typ: Optional[Type[BaseException]],
        value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """
        Restore the threshold.

        Args:
            typ (Optional[Type[BaseException]]): The exception type.
            value (Optional[BaseException]): The exception.
            traceback (Optional[TracebackType]): The traceback.
        """
        self.logger.threshold = self.old_level


_allow_root = True
root = Logger("root")
_allow_root = False
