"""
Copyright (C) 2022-2024  Koviubi56

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

__version__ = "0.10.0"
__author__ = "Koviubi56"
__email__ = "koviubi56@duck.com"
__license__ = "GPL-3.0-or-later"
__copyright__ = "Copyright (C) 2022-2024 Koviubi56"
__description__ = "My logging library."
__url__ = "https://github.com/koviubi56/mylog"

import abc
import contextlib
import dataclasses
import datetime
import enum
import sys
import time as timelib
import traceback as tracebacklib
from collections.abc import Generator, Iterable, Mapping
from typing import Protocol

import termcolor
from typing_extensions import Self

DEFAULT_FORMAT = "[{name} {level} {time} line: {line}] {indentation}{message}"


class StreamProtocol(Protocol):
    """Protocol for streams."""

    def write(self, __s: str, /) -> int:  # pragma: no cover
        """
        Writes `__s` to the stream.

        Args:
            __s (str): The string to write.

        Returns:
            int: The number of bytes written.
        """
        return 0

    def flush(self) -> None:
        """Flushes the streams."""


def optional_string_format(__string: str, /, **kwargs: str) -> str:
    """
    Same as `str.format()` but optional.

    >>> optional_string_format("{hello} {world}", hello="hi", bye="goodbye")
    'hi {world}'

    Args:
        __string (str): The string to format.
        **kwargs (str): Values.

    Returns:
        str: The formatted string.
    """
    for key, value in kwargs.items():
        __string = __string.replace("{" + key + "}", value)
    return __string


class Level(enum.IntEnum):
    """Level for the log message."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    @classmethod
    def new(cls, level: object) -> Self:
        """
        Create a new level from `level`.

        >>> Level.new("DEBUG")
        <Level.DEBUG: 10>
        >>> Level.new(40)
        <Level.ERROR: 40>
        >>> Level.new("50")
        <Level.CRITICAL: 50>
        >>> Level.new("foo")
        Traceback (most recent call last):
        ValueError: invalid level: 'foo'

        Args:
            level (object): The object to create the level from.

        Raises:
            ValueError: If the object cannot be converted into a level.

        Returns:
            Self: The level created from `level`.
        """
        with contextlib.suppress(ValueError):
            return cls(level)
        with contextlib.suppress(ValueError):
            return cls(int(level))
        with contextlib.suppress(AttributeError, ValueError):
            return getattr(Level, str(level).upper())
        raise ValueError(f"invalid level: {level!r}")

    @classmethod
    def new_or_int(cls, level: object) -> Self | int:
        """
        Create a new level from `level` or return an int.

        >>> Level.new_or_int("WARNING")
        <Level.WARNING: 30>
        >>> Level.new_or_int("25")
        25
        >>> Level.new_or_int("foo")
        Traceback (most recent call last):
        ValueError: invalid level: 'foo'

        Args:
            level (object): The object to create the level or int from.

        Raises:
            ValueError: If the object cannot be converted into a level or int.

        Returns:
            Self | int: The level or int created from `level`.
        """
        with contextlib.suppress(ValueError):
            return cls.new(level)
        with contextlib.suppress(ValueError):
            return int(level)
        raise ValueError(f"invalid level: {level!r}")


DEFAULT_THRESHOLD = Level.WARNING
DEFAULT_COLOR_CONFIG = {
    Level.DEBUG: ("blue",),
    Level.INFO: ("cyan",),
    Level.WARNING: ("yellow",),
    Level.ERROR: ("red",),
    Level.CRITICAL: ("red", "on_yellow", ["bold", "underline", "blink"]),
}


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class LogEvent:
    """
    A log event.

    Args:
        message (str): The message.
        level (int): The level.
        time (float): The time in UNIX seconds (see `time.time()`).
        indentation (int): The indentation before the message.
        line_number (int): The line number where this event was created.
        exception (BaseException | None): An exception that is related to this
            log event or None.
    """

    message: str
    level: int
    time: float
    indentation: int
    line_number: int
    exception: BaseException | None


class Handler(abc.ABC):
    """An ABC class for handlers."""

    @abc.abstractmethod
    def handle(self, logger: "Logger", event: LogEvent) -> None:
        """
        Handle the event.

        Args:
            logger (Logger): The logger that created the event.
            event (LogEvent): The event.
        """


@dataclasses.dataclass(frozen=True, slots=True)
class NoHandler(Handler):
    """A handler that does nothing."""

    def handle(self, logger: "Logger", event: LogEvent) -> None:
        """
        Handle the event.

        Args:
            logger (Logger): The logger that created the event.
            event (LogEvent): The event.
        """


@dataclasses.dataclass(slots=True)
class StreamWriterHandler(Handler):
    """
    A handler to write to a stream.

    Args:
        stream (StreamProtocol): The stream to write to.
        flush (bool, optional): Whether to flush the stream after writing to
            it. Defaults to True.
        use_colors (bool, optional): Whether to use colors. Defaults to True.
        should_format_message (bool, optional): Whether to write the formatted
            message or just write the log event's message. Defaults to True.
        level_name_width (int, optional): The width to ljust the level.
            Defaults to 8.
        color_config (Mapping[int, tuple[object, ...]], optional): A dictionary
            where the keys are the levels, and the values are the `args`
            to `termcolor.colored(level, *args)`. Defaults to
            DEFAULT_COLOR_CONFIG.
    """

    stream: StreamProtocol
    flush: bool = True
    format_: str = DEFAULT_FORMAT
    use_colors: bool = True
    should_format_message: bool = True
    level_name_width: int = 8
    color_config: Mapping[int, tuple[object, ...]] = dataclasses.field(
        default_factory=lambda: DEFAULT_COLOR_CONFIG.copy()
    )

    def level_to_str(self, level: int) -> str:
        """
        Convert a level to a string.

        Args:
            level (int): The level.

        Returns:
            str: The string.
        """
        try:
            string = Level.new(level).name.upper().ljust(self.level_name_width)
        except (ValueError, AttributeError):
            string = str(level).ljust(self.level_name_width)

        if self.use_colors and (level in self.color_config):
            string = termcolor.colored(string, *self.color_config[level])

        return string

    def format_message(self, logger: "Logger", event: LogEvent) -> str:
        """
        Format the message.

        Args:
            logger (Logger): The logger that created the event.
            event (LogEvent): The event.

        Returns:
            str: The formatted message.
        """
        indentation = "  " * event.indentation
        level = self.level_to_str(event.level)
        time = str(
            datetime.datetime.fromtimestamp(event.time, datetime.timezone.utc)
        )
        line = str(event.line_number).zfill(5)
        message = str(event.message)
        name = str(logger.name)
        traceback = (
            ("\n" + "\n".join(tracebacklib.format_exception(event.exception)))
            if event.exception
            else ""
        )
        return (
            optional_string_format(
                self.format_,
                indentation=indentation,
                level=level,
                time=time,
                line=line,
                message=message,
                name=name,
            )
            + traceback
            + "\n"
        )

    def handle(self, logger: "Logger", event: LogEvent) -> None:
        """
        Handle the event.

        Args:
            logger (Logger): The logger that created the event.
            event (LogEvent): The event.
        """
        message = (
            self.format_message(logger, event)
            if self.should_format_message
            else event.message
        )
        self.stream.write(message)
        if self.flush:
            self.stream.flush()


@dataclasses.dataclass(slots=True, kw_only=True)
class AttributesToInherit:
    """
    What attributes to inherit.

    Note: Changes made to the parent logger won't be made to the children
    automatically. They will only be made if `.inherit()` is called and
    inheriting that attribute is turned on.
    """

    name: bool = False
    propagate: bool = False
    list_: bool = False
    indentation: bool = False
    enabled: bool = False
    threshold: bool = True
    handlers: bool = True


@dataclasses.dataclass
class Logger:
    """
    The logger class.

    Args:
        (for the args not mentioned, see `.new()`)
        id_ (str): A unique ID for this logger instance.
        list_ (list[LogEvent]): A list of log events handled by this logger.
        handlers (Iterable[Handler]): An iterable of the handlers to use.
    """

    name: str
    id_: str
    parent: "Logger | None"
    propagate: bool
    list_: list[LogEvent]
    indentation: int
    enabled: bool
    threshold: int
    handlers: Iterable[Handler]

    @classmethod
    def get_default_handlers(cls) -> list[Handler]:
        """
        Get the default handlers.

        Returns:
            List[Handler]: The default handlers.
        """
        return [StreamWriterHandler(sys.stderr)]

    @classmethod
    def _create_root(cls) -> Self:
        # Should only be called exactly once by us!
        return cls.new(name="root", parent=None)

    @classmethod
    def new(  # noqa: PLR0913
        cls,
        *,
        name: str,
        parent: "Logger | None",
        handlers: Iterable[Handler] | None = None,
        propagate: bool = False,
        indentation: int = 0,
        enabled: bool = True,
        threshold: int = DEFAULT_THRESHOLD,
    ) -> Self:
        """
        Create a new logger instance.

        >>> Logger.new(name="foo", parent=root)
        <Logger foo>

        Args:
            name (str): The name of the logger. Multiple loggers may have the
                same name.
            parent (Logger | None): The parent logger.
            handlers (Iterable[Handler] | None, optional): The handlers. If
                None, it will use `cls.get_default_handlers()`. Defaults to
                None.
            propagate (bool, optional): Whether to propagate log events to the
                parent. Defaults to False.
            indentation (int, optional): The current indentation. Defaults to
                0.
            enabled (bool, optional): Whether the logger is enabled. Defaults
                to True.
            threshold (int, optional): The minimum level that a log event has
                to reach in order to be handled. Defaults to DEFAULT_THRESHOLD.

        Returns:
            Self: Always a new logger instance.
        """
        return cls(
            name=name,
            id_=str(timelib.time_ns()),
            parent=parent,
            propagate=propagate,
            list_=[],
            indentation=indentation,
            enabled=enabled,
            threshold=threshold,
            handlers=handlers
            if handlers is not None
            else cls.get_default_handlers(),
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Logger):
            return self.id_ == self.id_
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Logger):
            return self.id_ != self.id_
        return NotImplemented

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__} {self.name}>"

    def inherit(
        self, attributes_to_inherit: AttributesToInherit | None = None
    ) -> None:
        """
        Inherit some attributes from the parent logger (`self.parent`).

        Args:
            attributes_to_inherit (AttributesToInherit | None, optional): What
                attributes to inherit from the parent. If None, it uses
                AttributesToInherit's defaults. Defaults to None.

        Raises:
            TypeError: If `self.parent` is None
        """
        if not self.parent:
            raise TypeError("cannot inherit if parent is None")

        attributes_to_inherit = attributes_to_inherit or AttributesToInherit()
        if attributes_to_inherit.name:
            self.name = self.parent.name
        if attributes_to_inherit.propagate:
            self.propagate = self.parent.propagate
        if attributes_to_inherit.list_:
            self.list_ = self.parent.list_
        if attributes_to_inherit.indentation:
            self.indentation = self.parent.indentation
        if attributes_to_inherit.enabled:
            self.enabled = self.parent.enabled
        if attributes_to_inherit.threshold:
            self.threshold = self.parent.threshold
        if attributes_to_inherit.handlers:
            self.handlers = self.parent.handlers

    def create_child(
        self,
        name: str,
        attributes_to_inherit: AttributesToInherit | None = None,
    ) -> Self:
        """
        Create child and inherit.

        >>> foo = root.create_child("foo", AttributesToInherit())
        >>> foo.name
        'foo'
        >>> foo.threshold == root.threshold
        True

        Args:
            name (str): The name of the child logger.
            attributes_to_inherit (AttributesToInherit | None, optional): What
                attributes to inherit from the parent (`self`). If None, it
                uses AttributesToInherit's defaults. Defaults to None.

        Returns:
            Self: The new child logger instance.
        """
        child = self.new(name=name, parent=self)
        child.inherit(attributes_to_inherit or AttributesToInherit())
        return child

    def create_log_event(  # noqa: PLR0913
        self,
        message: str,
        level: int,
        indentation: int,
        line_number: int,
        exception: BaseException | None,
    ) -> LogEvent:
        """
        Create a log event.

        Args:
            message (str): The message.
            level (int): The level.
            indentation (int): The indentation before the message.
            line_number (int): The line number where the event was created.
            exception (BaseException | None): An exception that is related to
                this log event or None.

        Returns:
            LogEvent: The new log event.
        """
        return LogEvent(
            message=message,
            level=level,
            time=timelib.time(),
            indentation=indentation,
            line_number=line_number,
            exception=exception,
        )

    def _add_to_list(self, event: LogEvent) -> None:
        # Add the event to the list `self.list_`
        self.list_.append(event)

    def _handle(self, event: LogEvent, handler: Handler) -> None:
        # Handle `event` with `handler`
        return handler.handle(self, event)

    def _call_handlers(self, event: LogEvent) -> None:
        # Call handlers for `event`
        for handler in self.handlers:
            self._handle(event, handler)

    def _log(self, event: LogEvent) -> None:
        # Actually log `event` using *this* logger
        self._add_to_list(event)
        self._call_handlers(event)

    def is_disabled(self, event: LogEvent) -> bool:  # noqa: ARG002
        """
        Returns whether this logger is disabled (for this event).

        Args:
            event (LogEvent): The log event whose handling made running this
                function. (Not used by default, may be useful for subclasses)

        Returns:
            bool: Whether this logger is disabled (for this event).
        """
        return not self.enabled

    def should_propagate(self, event: LogEvent) -> bool:  # noqa: ARG002
        """
        Returns whether this logger should propagate (for this event).

        Args:
            event (LogEvent): The log event whose handling made running this
                function. (Not used by default, may be useful for subclasses)

        Returns:
            bool: Whether this logger should propagate (for this event).
        """
        return self.propagate

    def actually_propagate(self, event: LogEvent) -> None:
        """
        Actually propagate this event to the parent.

        Args:
            event (LogEvent): The event to propagate.

        Raises:
            RuntimeError: If this logger doesn't have a parent.
        """
        if self.parent is None:
            raise RuntimeError("cannot propagate without a parent")
        return self.parent.log(event)

    def is_enabled_for(self, level: int) -> bool:
        """
        Returns whether `level` is over the threshold.

        >>> root.threshold
        <Level.WARNING: 30>
        >>> root.is_enabled_for(Level.INFO)
        False
        >>> root.is_enabled_for(Level.WARNING)
        True

        Args:
            level (int): The level to check.

        Returns:
            bool: `level >= self.threshold`
        """
        return level >= self.threshold

    def should_be_logged(self, event: LogEvent) -> bool:
        """
        Returns whether this event should be actually logged.

        By defaults, it checks the event's level.

        Args:
            event (LogEvent): The event in question.

        Returns:
            bool: Whether it should actually be logger by this logger.
        """
        return self.is_enabled_for(event.level)

    def log(self, event: LogEvent) -> None:
        """
        Correctly log the event.

        This function checks if this logger is disabled, if the event should be
        logged, and it propagates if necessary.

        Args:
            event (LogEvent): The event to log.
        """
        if self.is_disabled(event):
            return
        if self.should_be_logged(event):
            self._log(event)
        if self.should_propagate(event):
            self.actually_propagate(event)

    def _predefined_log(
        self,
        level: int,
        message: str,
        exception: bool,  # noqa: FBT001
    ) -> None:
        # Used by .debug(), .info(), ...
        event = self.create_log_event(
            message=message,
            level=level,
            indentation=self.indentation,
            line_number=sys._getframe(2).f_lineno,  # noqa: SLF001
            exception=sys.last_value if exception else None,
        )
        self.log(event)

    def debug(self, message: str, exception: bool = False) -> None:  # noqa: FBT001, FBT002
        """
        Log an event with debug level.

        Args:
            message (str): The message.
            exception (bool, optional): Whether to associate the latest
                exception with this event. Defaults to False.
        """
        self._predefined_log(Level.DEBUG, message, exception)

    def info(self, message: str, exception: bool = False) -> None:  # noqa: FBT001, FBT002
        """
        Log an event with info level.

        Args:
            message (str): The message.
            exception (bool, optional): Whether to associate the latest
                exception with this event. Defaults to False.
        """
        self._predefined_log(Level.INFO, message, exception)

    def warning(self, message: str, exception: bool = False) -> None:  # noqa: FBT001, FBT002
        """
        Log an event with warning level.

        Args:
            message (str): The message.
            exception (bool, optional): Whether to associate the latest
                exception with this event. Defaults to False.
        """
        self._predefined_log(Level.WARNING, message, exception)

    def error(self, message: str, exception: bool = False) -> None:  # noqa: FBT001, FBT002
        """
        Log an event with error level.

        Args:
            message (str): The message.
            exception (bool, optional): Whether to associate the latest
                exception with this event. Defaults to False.
        """
        self._predefined_log(Level.ERROR, message, exception)

    def critical(self, message: str, exception: bool = False) -> None:  # noqa: FBT001, FBT002
        """
        Log an event with critical level.

        Args:
            message (str): The message.
            exception (bool, optional): Whether to associate the latest
                exception with this event. Defaults to False.
        """
        self._predefined_log(Level.CRITICAL, message, exception)

    @property
    @contextlib.contextmanager
    def indent(self) -> Generator[None, None, None]:
        """A context manager to indent and then de-indent the logger."""
        self.indentation += 1
        try:
            yield
        finally:
            self.indentation -= 1

    @contextlib.contextmanager
    def change_threshold(
        self, new_threshold: int
    ) -> Generator[None, None, None]:
        """
        Context manage to modify and then restore the logger's threshold.

        >>> root.threshold
        <Level.WARNING: 30>
        >>> with root.change_threshold(15):
        ...     root.threshold
        15
        >>> root.threshold
        <Level.WARNING: 30>

        Args:
            new_threshold (int): The new threshold.
        """
        old_threshold = self.threshold
        self.threshold = new_threshold
        try:
            yield
        finally:
            self.threshold = old_threshold


root = Logger._create_root()  # noqa: SLF001
