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

import contextlib
import dataclasses
import threading
import time
import traceback
import uuid
from enum import IntEnum
from sys import _getframe, stdout
from time import asctime
from types import TracebackType
from typing import (
    IO,
    Any,
    List,
    Literal,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from warnings import warn

import termcolor  # type: ignore

__version__ = "0.1.1"

T = TypeVar("T")
DEFAULT_FORMAT = "[{lvl} {time} line: {line}] {indent}{msg}"


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


class Stringable(Protocol):
    """Protocol for stringable objects."""

    def __str__(self) -> str:
        """
        Return the string representation of the object.

        Returns:
            str: The string representation of the object.
        """
        ...


Levelable = Union[Level, Stringable, int]


def to_level(
    lvl: Levelable, int_ok: bool = False
) -> Union[Level, int]:
    try:
        return Level(lvl)  # type: ignore
    except ValueError:
        try:
            return Level(int(lvl))  # type: ignore
        except ValueError:
            try:
                return getattr(Level, str(lvl).lower())  # type: ignore
            except (AttributeError, ValueError):
                with contextlib.suppress(ValueError):
                    if int_ok:
                        return int(lvl)  # type: ignore
                raise ValueError(
                    f"Invalid level: {lvl!r}. Must be a Level, int, or str."
                ) from None


class Lock(Protocol):
    """Protocol for locks that are needed by the logger."""

    def __enter__(
        self, blocking: bool = True, timeout: float = -1
    ) -> Union[bool, Literal[1]]:
        """
        Enter the lock.

        Args:
            blocking (bool, optional): Defaults to True.
            timeout (float, optional): Defaults to -1.

        Returns:
            Union[bool, Literal[1]]
        """
        ...

    def __exit__(
        self,
        typ: Type[BaseException],
        value: BaseException,
        tb: TracebackType,
    ) -> None:
        """
        Exit the lock.

        Args:
            t (Type[BaseException]): The type of the exception.
            v (BaseException): The exception.
            tb (TracebackType): The traceback.
        """
        ...


class NoLock:
    """No lock, if you don't want a lock"""

    def __enter__(
        self, blocking: bool = True, timeout: float = -1
    ) -> Union[bool, Literal[1]]:
        """
        Enter the lock.

        Args:
            blocking (bool, optional): Defaults to True.
            timeout (float, optional): Defaults to -1.

        Returns:
            Union[bool, Literal[1]]
        """
        return True

    def __exit__(
        self,
        typ: Type[BaseException],
        value: BaseException,
        tb: TracebackType,
    ) -> None:
        """
        Exit the lock.

        Args:
            t (Type[BaseException]): The type of the exception.
            v (BaseException): The exception.
            tb (TracebackType): The traceback.
        """
        return


NoneType = type(None)


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
    """
    for arg, (expected, got) in kwargs.items():
        if not isinstance(got, expected):
            raise TypeError(
                f"{arg!r} must be type {expected!r}, got {type(got)!r}"
                f" ({got!r})"
            )
    return True


@dataclasses.dataclass
class LogEvent:
    msg: str
    level: Levelable
    time: float  # ! UNIX seconds
    indent: int
    # // tb: bool
    frame_depth: int


class Logger:
    """THE logger class. You shouldn't really call __init__; use the root\
 logger, or the root logger's get_child"""

    colors: bool = True
    # ↳ Should level_to_str use colors? Should be set manually.

    def __eq__(self, __o: object) -> bool:
        # sourcery skip: assign-if-exp, reintroduce-else
        if isinstance(
            __o, Logger  # Hardcoded, because class can be subclassed
        ):
            return self._id == __o._id  # type: ignore
        return NotImplemented

    def __ne__(self, __o: object) -> bool:
        # sourcery skip: assign-if-exp, reintroduce-else
        if isinstance(
            __o, Logger  # Hardcoded, because class can be subclassed
        ):
            return self._id != __o._id  # type: ignore
        return NotImplemented

    def __init__(
        self,
        higher: Optional["Logger"] = None,
        *,
        lock: Optional[Lock] = None,  # You can use NoLock
    ) -> None:
        """
        Initialize the logger.

        Args:
            higher (Optional[Logger], optional): The higher logger. If it's\
 None or omitted then the logger will be the root. Defaults to None.
            lock (Optional[Lock], optional): The lock to use. If you don't\
 want a lock use NoLock. Defaults to None.

        Raises:
            ValueError: If the higher logger is None, but root is already\
 created (internally)
        """
        check_types(
            higher=((Logger, NoneType), higher),  # type: ignore
            lock=(  # type: ignore
                (NoneType, object),
                lock,
            ),  # ? Always passes?
        )
        if (higher is None) and (not _allow_root):
            raise ValueError(
                "Cannot create a new logger: Root logger already"
                " exists. Use that, or make a child logger from the root"
                " one."
            )
        # ! Note that these (with the exception of propagate, higher and
        # ! lock) should be accessed with their method (get_*)!
        # * If you think that we should make these (with the exceptions)
        # * properties, then you're wrong. Only make an issue/send a pr if you
        # * have a good reason.
        self.higher = higher
        self.propagate = False  # ! Root logger should not propagate!
        self.lock = lock or threading.Lock()
        self.list: List[LogEvent] = []
        self._id = uuid.uuid4()  # Only used for ==, !=

        if higher is None:
            self.format: Optional[str] = DEFAULT_FORMAT
            self.threshold: Optional[Level] = DEFAULT_THRESHOLD
            self.enabled: Optional[bool] = True
            self.stream: Optional[IO[str]] = stdout
            self.indent = 0  # Should be set manually
        else:
            self.format: Optional[str] = None  # type: ignore
            self.threshold: Optional[Level] = None  # type: ignore
            self.enabled: Optional[bool] = None  # type: ignore
            self.stream: Optional[IO[str]] = None  # type: ignore
            self.indent = None  # type: ignore

        self.ctxmgr = IndentLogger(
            self
        )  # None of the above rules apply to this; use this directly

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
        rv = rv.strip()
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
        return rv

    def level_to_str(self, lvl: Levelable) -> str:
        """
        Convert a level to a string.

        Args:
            lvl (Union[Level, Stringable]): The level.

        Returns:
            str: The string.
        """
        check_types(lvl=((Level, object), lvl))  # ? Always passes?
        try:
            rv = to_level(lvl, False).name.upper()  # type: ignore
        except (ValueError, AttributeError):
            rv = str(lvl)

        if rv == "WARN":
            rv = "WARNING"
        if rv == "FATAL":
            rv = "CRITICAL"

        if self.colors:
            rv = self._color(rv)

        return rv

    def format_msg(
        self,
        lvl: Levelable,
        msg: Stringable,
        tb: bool,
        frame_depth: int,
    ) -> str:
        """
        Format the message.

        Args:
            lvl (Union[Level, Stringable]): The level of the message.
            msg (Stringable): The message.
            tb (bool): Whether to include the traceback.
            frame_depth (int): The depth of the frame.

        Returns:
            str: The formatted message.
        """
        check_types(
            lvl=((Level, object), lvl),  # ? Always passes?
            msg=(str, msg),
            tb=(bool, tb),
            frame_depth=(int, frame_depth),
        )
        return (
            self.get_format().format(
                indent="  " * self.get_indent(),
                lvl=self.level_to_str(lvl),
                time=str(asctime()),
                line=str(_getframe(frame_depth).f_lineno).zfill(5),
                msg=str(msg),
            )
            + (("\n" + traceback.format_exc()) if tb else "")
            + "\n"
        )

    def _actually_log(
        self,
        lvl: Levelable,
        msg: Stringable,
        frame_depth: int,
        tb: bool,
    ) -> int:
        """
        Actually log the message. ONLY USE THIS INTERNALLY!
        ! THIS DOES *NOT* CHECK IF IT SHOULD BE LOGGED! THIS IS *NOT* IN THE
        ! PUBLIC API, AND IT MUST NOT BE CALLED EXCEPT INTERNALLY!

        Args:
            lvl (Union[Level, Stringable]): The level of the message.
            msg (Stringable): The message.
            frame_depth (int): The depth of the frame.
            tb (bool): Whether to include the traceback.

        Returns:
            int: The number of characters written.
        """
        check_types(
            lvl=((Level, object), lvl),  # ? Always passes?
            msg=(str, msg),
            frame_depth=(int, frame_depth),
        )
        self.list.append(
            LogEvent(
                msg=str(msg),
                level=to_level(lvl, True),
                time=time.time(),
                indent=self.get_indent(),
                frame_depth=frame_depth,
            )
        )
        with self.lock:
            rv = self.get_stream().write(
                self.format_msg(lvl, msg, tb, frame_depth)
            )
        self.get_stream().flush()
        return rv

    def _log(
        self,
        lvl: Levelable,
        msg: Stringable,
        traceback: bool,
        frame_depth: int,
    ) -> int:
        """
        Log the message. Checks if the logger is enabled, propagate, and stuff.
        This IS in the public api, but (unless you need it) use the methods
        debug, info, warning, error, critical.

        Args:
            lvl (Union[Level, Stringable]): The level of the message.
            msg (Stringable): The message.
            traceback (bool): Whether to include the traceback.
            frame_depth (int): The depth of the frame. If you call this from\
 your code, this (probably) should be 3.

        Returns:
            int: The number of characters written.
        """
        check_types(
            lvl=((Level, object), lvl),  # ? Always passes?
            msg=(str, msg),
            traceback=(bool, traceback),
            frame_depth=(int, frame_depth),
        )
        # Check if enabled
        if self.get_enabled():
            # Check if we should log it
            if self.propagate:
                # Check if we are root
                if self.higher is None:  # Should not happen
                    warn(
                        "Root logger should not propagate! Set enabled to"
                        " False if you want to disable it.",
                        UserWarning,
                        stacklevel=frame_depth - 1,
                    )
                    return 0
                # Log with parent
                return self.higher._log(
                    lvl, msg, traceback, frame_depth + 1
                )
            # Check if it's enabled
            if not self.is_enabled_for(lvl):
                return 0
            # Log
            return self._actually_log(
                lvl, msg, frame_depth, traceback
            )
        return 0

    def debug(self, msg: Stringable, traceback: bool = False) -> int:
        """
        Log a debug message.

        Args:
            msg (Stringable): The message.
            traceback (bool, optional): Whether to include the traceback.\
 Defaults to False.

        Returns:
            int: The number of characters written.
        """
        check_types(msg=(str, msg), traceback=(bool, traceback))
        return self._log(Level.debug, msg, traceback, 4)

    def info(self, msg: Stringable, traceback: bool = False) -> int:
        """
        Log an info message.

        Args:
            msg (Stringable): The message.
            traceback (bool, optional): Whether to include the traceback.\
 Defaults to False.

        Returns:
            int: The number of characters written.
        """
        check_types(msg=(str, msg), traceback=(bool, traceback))
        return self._log(Level.info, msg, traceback, 4)

    def warning(
        self, msg: Stringable, traceback: bool = False
    ) -> int:
        """
        Log a warning message.

        Args:
            msg (Stringable): The message.
            traceback (bool, optional): Whether to include the traceback.\
 Defaults to False.

        Returns:
            int: The number of characters written.
        """
        check_types(msg=(str, msg), traceback=(bool, traceback))
        return self._log(Level.warning, msg, traceback, 4)

    def error(self, msg: Stringable, traceback: bool = False) -> int:
        """
        Log an error message.

        Args:
            msg (Stringable): The message.
            traceback (bool, optional): Whether to include the traceback.\
 Defaults to False.

        Returns:
            int: The number of characters written.
        """
        check_types(msg=(str, msg), traceback=(bool, traceback))
        return self._log(Level.error, msg, traceback, 4)

    def critical(
        self, msg: Stringable, traceback: bool = False
    ) -> int:
        """
        Log a critical/fatal message.

        Args:
            msg (Stringable): The message.
            traceback (bool, optional): Whether to include the traceback.\
 Defaults to False.

        Returns:
            int: The number of characters written.
        """
        check_types(msg=(str, msg), traceback=(bool, traceback))
        return self._log(Level.critical, msg, traceback, 4)

    def get_child(self) -> "Logger":
        """
        Get a child logger.

        Returns:
            Logger: The child logger.
        """
        cls: Type[Logger] = type(self)
        return cls(self)

    def is_enabled_for(self, lvl: Levelable) -> bool:
        """
        Check if the logger is enabled for the given level.

        Args:
            lvl (Union[Level, Stringable]): The level to check.

        Returns:
            bool: Whether the logger is enabled for the given level.
        """
        check_types(lvl=((Level, object), lvl))  # ? Always passes?
        lvl = to_level(lvl, True)
        return lvl >= self.get_effective_level()

    def _get_x(self, attr: str, default: T) -> Union[T, Any]:
        """
        Get an attribute.

        Args:
            attr (str): The attribute to get.
            default (T): The default value.

        Returns:
            Union[T, Any]: The attribute.
        """
        check_types(
            attr=(str, attr),
            default=(object, default),
        )
        if getattr(self, attr, None) is None:
            if self.higher is None:
                return default
            return self.higher._get_x(attr, default)
        rv = getattr(self, attr)
        return rv

    def get_effective_level(self) -> Level:
        """
        Get the effective level (threshold).

        Returns:
            Level: The effective level.
        """
        return self._get_x("threshold", DEFAULT_THRESHOLD)

    get_threshold = get_effective_level

    def get_format(self) -> str:
        """
        Get the format.

        Returns:
            str: The format.
        """
        return self._get_x("format", DEFAULT_FORMAT)

    def get_enabled(self) -> bool:
        """
        Get the enabled state.

        Returns:
            bool: Whether the logger is enabled.
        """
        return self._get_x("enabled", True)

    def get_stream(self) -> IO[str]:
        """
        Get the stream.

        Returns:
            IO[str]: The stream.
        """
        return self._get_x("stream", stdout)

    def get_indent(self) -> int:
        """
        Get the indent.

        Returns:
            int: The indent.
        """
        return self._get_x("indent", 0)


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
        if self.logger.indent is None:
            self.logger.indent = self.logger.get_indent()
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
            t (Type[BaseException]): The exception type.
            v (BaseException): The exception.
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
        check_types(logger=(Logger, logger))
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
        return self.old_level  # type: ignore

    def __exit__(
        self,
        typ: Type[BaseException],
        value: BaseException,
        tb: TracebackType,
    ) -> None:
        """
        Restore the threshold.

        Args:
            t (Type[BaseException]): The exception type.
            v (BaseException): The exception.
            tb (TracebackType): The traceback.
        """
        self.logger.threshold = self.old_level


_allow_root = True
root = Logger()
_allow_root = False
