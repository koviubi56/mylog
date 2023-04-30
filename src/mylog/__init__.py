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
# ruff: noqa: SLF001

__version__ = "0.8.0-beta.1"

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
from types import TracebackType  # noqa: TCH003
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
DEFAULT_FORMAT = (
    "[{name} {lvl} {time} line: {line}] {indent}{msg}"  # noqa: FS003
)
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
    lvl: Levelable, int_ok: Literal[True] = False
) -> Union[Level, int]:  # pragma: no cover
    ...


@overload
def to_level(
    lvl: Levelable, int_ok: Literal[False] = False
) -> Level:  # pragma: no cover
    ...


def to_level(lvl: Levelable, int_ok=False):
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
        typ: Type[BaseException],
        value: BaseException,
        tb: TracebackType,
    ) -> None:
        """Exit the context manager."""
        setattr(self.obj, self.name, self.old_value)


@dataclasses.dataclass(order=True, frozen=True)
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
    format_msg: bool = True

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


@dataclasses.dataclass(order=True, frozen=True, **DATACLASS_KW_ONLY)
class AttributesToInherit:
    """
    What attributes to inherit.
    Changes made to the parent logger won't be made to the children.
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
    """THE logger class. You shouldn't really call __init__; use the root\
 logger, or the root logger's get_child"""

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
        if cls.compare_using_name:
            return obj.name
        return obj._id

    def __eq__(self, __o: object) -> bool:
        # sourcery skip: assign-if-exp, reintroduce-else
        if isinstance(
            __o, Logger  # Hardcoded, because class can be subclassed
        ):
            return self._thing_to_compare(self) == self._thing_to_compare(__o)
        return NotImplemented

    def __ne__(self, __o: object) -> bool:
        # sourcery skip: assign-if-exp, reintroduce-else
        if isinstance(
            __o, Logger  # Hardcoded, because class can be subclassed
        ):
            return self._thing_to_compare(self) != self._thing_to_compare(__o)

        return NotImplemented

    def __repr__(self) -> str:  # pragma: no cover
        return f"<{self.__class__.__qualname__} {self.name}>"

    def _inherit(self) -> None:  # noqa: PLR0912,C901  # pragma: no cover
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
            self.enabled: bool = True
        if self.attributes_to_inherit.ctxmgr:
            self.ctxmgr = self.higher.ctxmgr
        else:
            self.ctxmgr = IndentLogger(self)
        if self.attributes_to_inherit.format:
            self.format: str = self.higher.format
        else:
            self.format = DEFAULT_FORMAT
        if self.attributes_to_inherit.threshold:
            self.threshold: Union[Level, int] = self.higher.threshold
        else:
            self.threshold = DEFAULT_THRESHOLD
        if self.attributes_to_inherit.handlers:
            self.handlers: List[Handler] = self.higher.handlers
        else:
            self.handlers = self.get_default_handlers()

    @staticmethod
    def get_default_handlers() -> List[Handler]:
        """
        Get the default handlers. Please note, that overwriting this function\
 will not change the handlers.

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
    def level_to_str(cls, lvl: Levelable) -> str:
        """
        Convert a level to a string.

        Args:
            lvl (Levelable): The level.

        Returns:
            str: The string.
        """
        try:
            rv = to_level(lvl, False).name.upper()  # type: ignore
        except (ValueError, AttributeError):
            rv = str(lvl).ljust(cls.level_name_width)

        if rv == "WARN":  # pragma: no cover
            rv = "WARNING"
        if rv == "FATAL":  # pragma: no cover
            rv = "CRITICAL"

        if cls.colors:
            rv = cls.color(rv)

        return rv  # noqa: R504

    def format_msg(self, event: LogEvent) -> str:
        """
        Format the message.

        Args:
            event (LogEvent): The event.

        Returns:
            str: The formatted message.
        """
        _indent = "  " * self.indent
        _lvl = self.level_to_str(event.level)
        _time = str(
            datetime.datetime.fromtimestamp(event.time)  # noqa: DTZ006
        )
        _line = str(sys._getframe(event.frame_depth).f_lineno).zfill(5)
        _msg = str(event.msg)
        _name = str(self.name)
        if (event.tb) and (sys.exc_info() == (None, None, None)):
            warnings.warn(
                "No traceback available, but tb=True",
                UserWarning,
                stacklevel=event.frame_depth - 1,
            )
        _tb = ("\n" + tracebacklib.format_exc()) if event.tb else ""
        return (
            self.format.format(
                indent=_indent,
                lvl=_lvl,
                time=_time,
                line=_line,
                msg=_msg,
                name=_name,
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

    def log(
        self,
        lvl: Levelable,
        msg: Stringable,
        traceback: bool = False,
        frame_depth: int = 4,
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
            return self.higher.log(lvl, msg, traceback, frame_depth + 1)
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
        return self.log(Level.debug, msg, traceback, 5)

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
        return self.log(Level.info, msg, traceback, 5)

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
        return self.log(Level.warning, msg, traceback, 5)

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
        return self.log(Level.error, msg, traceback, 5)

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
        return self.log(Level.critical, msg, traceback, 5)

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

    def is_enabled_for(self, lvl: Levelable) -> bool:
        """
        Check if the logger is enabled for the given level.

        Args:
            lvl (Levelable): The level to check.

        Returns:
            bool: Whether the logger is enabled for the given level.
        """
        lvl = to_level(lvl, True)
        return lvl >= self.threshold


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
root = Logger("root")
_allow_root = False
