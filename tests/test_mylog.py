"""
Copyright (C) 2023  Koviubi56

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
import base64
import secrets
from time import time as get_unix_time
from types import SimpleNamespace
from typing import Any, Callable, Iterable, Sequence, Tuple, TypeVar, Union

import pytest
import termcolor

import mylog

T = TypeVar("T")

mylog.root.handlers = [mylog.NoHandler()]


class Stream:
    """A stream that can be used for testing. No output to stdout."""

    def __init__(self) -> None:
        self.wrote = ""
        self.flushed = False

    def write(self, __s: str, /) -> int:
        self.wrote += __s
        return len(__s)

    def flush(self) -> None:
        self.flushed = True


def iterable_isinstance(iterable: Iterable[Any], cls: type) -> bool:
    return all(isinstance(x, cls) for x in iterable)


def _randint(__a: int, __b: int, /) -> int:
    # random.randint is used only here,
    # so we have to use "nosec" only once
    return secrets.SystemRandom().randint(__a, __b)  # nosec B311


def _randbytes(length: int) -> bytes:
    # random.randbytes is used only here,
    # so we have to use "nosec" only once
    return secrets.token_bytes(length)  # nosec B311


def _randchoice(seq: Sequence[T]) -> T:
    # random.choice is used only here,
    # so we have to use "nosec" only once
    return secrets.SystemRandom().choice(seq)  # nosec B311


def _random_int(
    neg_ok: bool, *, only_if: Callable[[int], bool] = lambda _: True
) -> int:
    # sourcery skip: assign-if-exp, reintroduce-else
    if neg_ok:
        rv = _randint(-50, 50)
    rv = _randint(0, 100)
    if only_if(rv):
        return rv
    return _random_int(neg_ok, only_if=only_if)  # pragma: no cover


def _random_bytes(
    *, only_if: Callable[[bytes], bool] = lambda _: True
) -> bytes:
    rv = _randbytes(_random_int(False))
    if only_if(rv):
        return rv
    return _random_bytes(only_if=only_if)  # pragma: no cover


def _random_urlsafe(*, only_if: Callable[[str], bool] = lambda _: True) -> str:
    tok = _random_bytes()
    rv = base64.urlsafe_b64encode(tok).rstrip(b"=").decode("ascii")
    if only_if(rv):
        return rv
    return _random_urlsafe(only_if=only_if)  # pragma: no cover


def _random_nonlevel_int(
    *, only_if: Callable[[int], bool] = lambda _: True
) -> int:
    rv = _random_int(
        True,
        only_if=lambda num: num not in {10, 20, 30, 40, 50},
    )
    if only_if(rv):
        return rv
    return _random_nonlevel_int(only_if=only_if)  # pragma: no cover


def _random_level() -> Tuple[Union[mylog.Level, int, str], mylog.Level]:
    lvl = _randchoice(tuple(mylog.Level))
    _to = _randchoice(("lvl", "int", "str"))
    return {
        "lvl": (lvl, lvl),
        "int": (lvl.value, lvl),
        "str": (lvl.name, lvl),
    }[_to]


def random_anything(
    *,
    only_if: Callable[[Union[bytes, int, str]], bool] = lambda _: True,
) -> Union[str, bytes, int]:
    rt = _randchoice(("hex", "bytes", "urlsafe", "int"))
    if rt == "hex":
        rv = _random_bytes().hex()
    elif rt == "bytes":
        rv = _random_bytes()
    elif rt == "urlsafe":
        rv = _random_urlsafe()
    elif rt == "int":
        rv = _random_int(True)
    else:  # pragma: no cover
        raise ValueError(rt)
    if only_if(rv):
        return rv
    return random_anything(only_if=only_if)  # pragma: no cover


def x_is_y(__x: object, __y: object, /) -> bool:
    # So we don't get "do not compare types, use 'isinstance()' flake8(E721)"
    return __x is __y


def x_equals_y(__x: object, __y: object, /) -> bool:
    # So we test "==" AND "__eq__"
    return (__x == __y) and (__x.__eq__(__y))


def x_not_equals_y(__x: object, __y: object, /) -> bool:
    # So we test "!=" AND "__ne__"
    return (__x != __y) and (__x.__ne__(__y))


def test_to_level():
    assert mylog.to_level(mylog.Level.debug) == mylog.Level.debug
    assert mylog.to_level(mylog.Level.info) == mylog.Level.info
    assert mylog.to_level(mylog.Level.warning) == mylog.Level.warning
    assert mylog.to_level(mylog.Level.warn) == mylog.Level.warning
    assert mylog.to_level(mylog.Level.error) == mylog.Level.error
    assert mylog.to_level(mylog.Level.critical) == mylog.Level.critical
    assert mylog.to_level(mylog.Level.fatal) == mylog.Level.critical

    assert mylog.to_level(mylog.Level.debug.numerator) == mylog.Level.debug
    assert mylog.to_level(mylog.Level.info.numerator) == mylog.Level.info
    assert mylog.to_level(mylog.Level.warning.numerator) == mylog.Level.warning
    assert mylog.to_level(mylog.Level.warn.numerator) == mylog.Level.warning
    assert mylog.to_level(mylog.Level.error.numerator) == mylog.Level.error
    assert (
        mylog.to_level(mylog.Level.critical.numerator) == mylog.Level.critical
    )
    assert mylog.to_level(mylog.Level.fatal.numerator) == mylog.Level.critical

    assert mylog.to_level(mylog.Level.debug.value) == mylog.Level.debug
    assert mylog.to_level(mylog.Level.info.value) == mylog.Level.info
    assert mylog.to_level(mylog.Level.warning.value) == mylog.Level.warning
    assert mylog.to_level(mylog.Level.warn.value) == mylog.Level.warning
    assert mylog.to_level(mylog.Level.error.value) == mylog.Level.error
    assert mylog.to_level(mylog.Level.critical.value) == mylog.Level.critical
    assert mylog.to_level(mylog.Level.fatal.value) == mylog.Level.critical

    assert (
        mylog.to_level(str(mylog.Level.debug.numerator)) == mylog.Level.debug
    )
    assert mylog.to_level(str(mylog.Level.info.numerator)) == mylog.Level.info
    assert (
        mylog.to_level(str(mylog.Level.warning.numerator))
        == mylog.Level.warning
    )
    assert (
        mylog.to_level(str(mylog.Level.warn.numerator)) == mylog.Level.warning
    )
    assert (
        mylog.to_level(str(mylog.Level.error.numerator)) == mylog.Level.error
    )
    assert (
        mylog.to_level(str(mylog.Level.critical.numerator))
        == mylog.Level.critical
    )
    assert (
        mylog.to_level(str(mylog.Level.fatal.numerator))
        == mylog.Level.critical
    )

    assert mylog.to_level(str(mylog.Level.debug.value)) == mylog.Level.debug
    assert mylog.to_level(str(mylog.Level.info.value)) == mylog.Level.info
    assert (
        mylog.to_level(str(mylog.Level.warning.value)) == mylog.Level.warning
    )
    assert mylog.to_level(str(mylog.Level.warn.value)) == mylog.Level.warning
    assert mylog.to_level(str(mylog.Level.error.value)) == mylog.Level.error
    assert (
        mylog.to_level(str(mylog.Level.critical.value)) == mylog.Level.critical
    )
    assert mylog.to_level(str(mylog.Level.fatal.value)) == mylog.Level.critical

    assert mylog.to_level(mylog.Level.debug.name) == mylog.Level.debug
    assert mylog.to_level(mylog.Level.info.name) == mylog.Level.info
    assert mylog.to_level(mylog.Level.warning.name) == mylog.Level.warning
    assert mylog.to_level(mylog.Level.warn.name) == mylog.Level.warning
    assert mylog.to_level(mylog.Level.error.name) == mylog.Level.error
    assert mylog.to_level(mylog.Level.critical.name) == mylog.Level.critical
    assert mylog.to_level(mylog.Level.fatal.name) == mylog.Level.critical

    with pytest.raises(ValueError, match="Invalid level"):
        mylog.to_level(_random_nonlevel_int())

    with pytest.raises(ValueError, match="Invalid level"):
        mylog.to_level(
            _random_urlsafe(
                # Relatively unlikely
                only_if=lambda x: x
                not in {
                    "debug",
                    "info",
                    "warn",
                    "warning",
                    "error",
                    "critical",
                    "fatal",
                }
            )
        )

    with pytest.raises(ValueError, match="Invalid level"):
        mylog.to_level(_random_bytes())

    nli = _random_nonlevel_int()
    # ↪ Non-level int
    assert mylog.to_level(nli, True) == nli


def test_nonetype():
    assert x_is_y(mylog.NoneType, type(None))


def test_setattr():
    original = random_anything()
    new = random_anything()
    obj = SimpleNamespace(exampleattr=original)

    with mylog.SetAttr(obj, "exampleattr", new):
        assert obj.exampleattr == new

    assert obj.exampleattr == original


def test_stream_writer_handler():
    stream = Stream()
    handler = mylog.StreamWriterHandler(stream, flush=True)
    logger = mylog.root.get_child()
    logger.handlers = [handler]
    event = mylog.LogEvent(
        str(random_anything()),
        _random_level()[0],
        _random_int(False),
        _random_int(False),
        1,
        False,
    )

    handler.handle(logger, event)
    assert stream.wrote
    assert stream.flushed

    stream = Stream()
    handler = mylog.StreamWriterHandler(stream, flush=False)
    logger = mylog.root.get_child()
    logger.handlers = [handler]
    event = mylog.LogEvent(
        str(random_anything()),
        _random_level()[0],
        _random_int(False),
        _random_int(False),
        1,
        False,
    )

    handler.handle(logger, event)
    assert stream.wrote
    assert not stream.flushed


class TestLogger:
    @staticmethod
    def test_eq():
        l1 = l2 = mylog.root.get_child()
        assert x_equals_y(l1, l2)
        assert x_equals_y(l2, l1)
        assert x_equals_y(mylog.root, mylog.root)
        assert l1.__eq__(object()) == NotImplemented

    @staticmethod
    def test_ne():
        l1 = mylog.root.get_child()
        l2 = mylog.root.get_child()
        assert x_not_equals_y(l1, l2)
        assert x_not_equals_y(l2, l1)
        assert l1.__ne__(object()) == NotImplemented

    @staticmethod
    def test_get_default_handlers():
        _handlers = mylog.root.get_default_handlers()
        assert isinstance(_handlers, list)
        assert iterable_isinstance(_handlers, mylog.Handler)

    @staticmethod
    def test_init():
        with pytest.raises(
            ValueError,
            match="Cannot create a new logger: Root logger already exists",
        ):
            mylog.Logger(higher=None)

        # Don't set `_allow_root` in production code
        mylog._allow_root = True
        logger = mylog.Logger(None)
        mylog._allow_root = False

        assert logger.higher is None
        assert logger.propagate is False
        assert logger.list == []

        assert logger.format == mylog.DEFAULT_FORMAT
        assert logger.threshold == mylog.DEFAULT_THRESHOLD
        assert logger.enabled is True
        assert logger.indent == 0

        with pytest.raises(
            ValueError, match=r"Cannot inherit if higher is None\."
        ):
            logger._inherit()

    @staticmethod
    def test_color():
        logger = mylog.root
        assert logger.color("quick brown fox") == "quick brown fox"
        assert logger.color("DEBUG") == termcolor.colored(
            "DEBUG".ljust(8), "blue"
        )
        assert logger.color("INFO") == termcolor.colored(
            "INFO".ljust(8), "cyan"
        )
        assert logger.color("WARNING") == termcolor.colored(
            "WARNING".ljust(8), "yellow"
        )
        assert logger.color("ERROR") == termcolor.colored(
            "ERROR".ljust(8), "red"
        )
        assert logger.color("CRITICAL") == termcolor.colored(
            "CRITICAL".ljust(8),
            "red",
            "on_yellow",
            ["bold", "underline", "blink"],
        )

    @staticmethod
    def test_level_to_string():
        logger = mylog.root
        assert logger.level_to_str(mylog.Level.debug) == termcolor.colored(
            "DEBUG".ljust(8), "blue"
        )
        assert logger.level_to_str(mylog.Level.info) == termcolor.colored(
            "INFO".ljust(8), "cyan"
        )
        assert logger.level_to_str(mylog.Level.warning) == termcolor.colored(
            "WARNING".ljust(8), "yellow"
        )
        assert logger.level_to_str(mylog.Level.warn) == termcolor.colored(
            "WARNING".ljust(8), "yellow"
        )
        assert logger.level_to_str(mylog.Level.error) == termcolor.colored(
            "ERROR".ljust(8), "red"
        )
        assert logger.level_to_str(mylog.Level.critical) == termcolor.colored(
            "CRITICAL".ljust(8),
            "red",
            "on_yellow",
            ["bold", "underline", "blink"],
        )
        assert logger.level_to_str(mylog.Level.fatal) == termcolor.colored(
            "CRITICAL".ljust(8),
            "red",
            "on_yellow",
            ["bold", "underline", "blink"],
        )
        nli = _random_nonlevel_int()
        assert logger.level_to_str(nli) == str(nli).ljust(8)

    @staticmethod
    def test_format_msg():
        logger = mylog.root
        lvl = _random_level()
        event = mylog.LogEvent(str(random_anything()), lvl[0], 0, 0, 0, False)

        # Check if it runs
        for _ in range(10):
            logger.format_msg(event)

        event.tb = True
        with pytest.warns(
            UserWarning, match="No traceback available, but tb=True"
        ):
            logger.format_msg(event)

    @staticmethod
    def test_actually_log():
        logger = mylog.root.get_child()
        logger.list = []
        logger.indent = _randint(0, 10)
        stream = Stream()
        handler = mylog.StreamWriterHandler(
            stream, flush=False, use_colors=False, format_msg=False
        )
        logger.handlers = [handler]
        lvl = _random_level()
        msg = random_anything()
        frame_depth = _randint(0, 3)

        time = get_unix_time()
        logger._actually_log(lvl[0], msg, frame_depth, False)

        assert len(logger.list) == 1
        event = logger.list[0]
        assert event.msg == str(msg)
        assert event.level == lvl[1]
        assert time - 1 < event.time < time + 1
        assert event.indent == logger.indent
        assert event.frame_depth == frame_depth
        assert stream.wrote == str(msg)

    @staticmethod
    def test_log_propagate():
        logger = mylog.root.get_child()
        if not logger.higher:  # pragma: no cover
            raise TypeError(f"{logger.higher = !r}")
        logger.list = []
        logger.indent = _randint(0, 10)
        logger.propagate = True
        logger.handlers = []
        logger.threshold = mylog.Level.debug
        logger.higher.handlers = []
        logger.higher.threshold = mylog.Level.debug
        lvl = _random_level()
        msg = random_anything()
        frame_depth = _randint(0, 3)

        time = get_unix_time()
        logger._log(lvl[0], msg, False, frame_depth)

        assert not logger.list
        event = logger.higher.list[-1]
        assert event.msg == str(msg)
        assert event.level == lvl[1]
        assert time - 1 < event.time < time + 1
        assert event.indent == logger.higher.indent
        assert event.frame_depth == frame_depth + 1
        #                                       ~~~
        # Since propagate is True, Logger._log() will automatically add one to
        # the frame_depth, if logging is done by the parent.

        with pytest.warns(
            UserWarning, match="Root logger should not propagate"
        ):
            mylog.root.propagate = True
            mylog.root._log(_random_level()[0], random_anything(), False, 2)
            mylog.root.propagate = False

    @staticmethod
    def test_log_no_propagate():
        logger = mylog.root
        logger.list = []
        logger.indent = _randint(0, 10)
        logger.threshold = mylog.Level.debug
        logger.handlers = []
        lvl = _random_level()
        msg = random_anything()
        frame_depth = _randint(0, 3)

        time = get_unix_time()
        logger._log(lvl[0], msg, False, frame_depth)

        assert len(logger.list) == 1
        event = logger.list[-1]
        assert event.msg == str(msg)
        assert event.level == lvl[1]
        assert time - 1 < event.time < time + 1
        assert event.indent == logger.indent
        assert event.frame_depth == frame_depth

    @staticmethod
    @pytest.mark.parametrize(  # noqa: PT006
        "method_name,lvl",
        [
            ("debug", mylog.Level.debug),
            ("info", mylog.Level.info),
            ("warning", mylog.Level.warning),
            ("error", mylog.Level.error),
            ("critical", mylog.Level.critical),
        ],
    )
    def test_log_methods(method_name: str, lvl: mylog.Level):
        logger = mylog.root
        logger.list = []
        logger.indent = _randint(0, 10)
        logger.threshold = mylog.Level.debug
        logger.handlers = []
        msg = random_anything()

        time = get_unix_time()
        getattr(logger, method_name)(msg, False)

        assert len(logger.list) == 1
        event = logger.list[-1]
        assert event.msg == str(msg)
        assert event.level == lvl
        assert time - 1 < event.time < time + 1
        assert event.indent == logger.indent

    @staticmethod
    def test_get_child():
        parent = mylog.root
        child = parent.get_child()

        assert isinstance(child, type(parent))
        assert child.propagate is False
        assert child.list == []
        assert child.indent == 0
        assert child.enabled is True

        assert child.format == parent.format
        assert child.threshold == parent.threshold

    @staticmethod
    def test_is_enabled_for():
        logger = mylog.root

        logger.threshold = mylog.Level.debug
        assert logger.is_enabled_for(mylog.Level.debug)
        assert logger.is_enabled_for(mylog.Level.info)
        assert logger.is_enabled_for(mylog.Level.warning)
        assert logger.is_enabled_for(mylog.Level.error)
        assert logger.is_enabled_for(mylog.Level.critical)

        logger.threshold = mylog.Level.info
        assert not logger.is_enabled_for(mylog.Level.debug)
        assert logger.is_enabled_for(mylog.Level.info)
        assert logger.is_enabled_for(mylog.Level.warning)
        assert logger.is_enabled_for(mylog.Level.error)
        assert logger.is_enabled_for(mylog.Level.critical)

        logger.threshold = mylog.Level.warning
        assert not logger.is_enabled_for(mylog.Level.debug)
        assert not logger.is_enabled_for(mylog.Level.info)
        assert logger.is_enabled_for(mylog.Level.warning)
        assert logger.is_enabled_for(mylog.Level.error)
        assert logger.is_enabled_for(mylog.Level.critical)

        logger.threshold = mylog.Level.error
        assert not logger.is_enabled_for(mylog.Level.debug)
        assert not logger.is_enabled_for(mylog.Level.info)
        assert not logger.is_enabled_for(mylog.Level.warning)
        assert logger.is_enabled_for(mylog.Level.error)
        assert logger.is_enabled_for(mylog.Level.critical)

        logger.threshold = mylog.Level.critical
        # -
        logger.list = []
        logger.debug(random_anything())
        assert not logger.list
        # -
        assert not logger.is_enabled_for(mylog.Level.debug)
        assert not logger.is_enabled_for(mylog.Level.info)
        assert not logger.is_enabled_for(mylog.Level.warning)
        assert not logger.is_enabled_for(mylog.Level.error)
        assert logger.is_enabled_for(mylog.Level.critical)

        logger.threshold = "fatal"  # type: ignore
        with pytest.warns(
            UserWarning, match="Logger threshold should be a Level"
        ):
            logger.is_enabled_for(mylog.Level.critical)

    @staticmethod
    def test_enabled():
        logger = mylog.root.get_child()
        logger.critical(random_anything())
        assert logger.list
        logger.list = []

        logger.enabled = False
        logger.critical(random_anything())
        assert not logger.list

        logger.enabled = True
        logger.critical(random_anything())
        assert logger.list


def test_indent_logger():
    logger = mylog.root
    start = _randint(0, 6)
    logger.indent = start

    with logger.ctxmgr:
        assert logger.indent == start + 1

    assert logger.indent == start


def test_change_threshold():
    logger = mylog.root
    start = _random_level()
    new = _random_level()
    logger.threshold = start[1]

    with mylog.ChangeThreshold(logger, new[0]):
        assert logger.threshold == new[1]

    assert logger.threshold == start[1]
