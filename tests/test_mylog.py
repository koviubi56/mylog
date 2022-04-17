import base64
import os
import secrets
import sys
from time import time as get_unix_time
from typing import Callable, Sequence, Tuple, TypeVar, Union

import pytest
import termcolor

import mylog

T = TypeVar("T")


def _randint(a: int, b: int) -> int:
    # random.randint is used only here,
    # so we have to use "nosec" (vvvvvvvvvvvv) only once
    return secrets.SystemRandom().randint(a, b)  # nosec B311


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
    return _random_int(neg_ok, only_if=only_if)


def _random_bytes(
    *, only_if: Callable[[int], bool] = lambda _: True
) -> bytes:
    rv = _randbytes(_random_int(False))
    if only_if(rv):
        return rv
    return _random_bytes(only_if=only_if)


def _random_urlsafe(
    *, only_if: Callable[[int], bool] = lambda _: True
) -> str:
    tok = _random_bytes()
    rv = base64.urlsafe_b64encode(tok).rstrip(b"=").decode("ascii")
    if only_if(rv):
        return rv
    return _random_urlsafe(only_if=only_if)


def _random_nonlevel_int(
    *, only_if: Callable[[int], bool] = lambda _: True
) -> int:
    rv = _random_int(
        True,
        only_if=lambda num: num not in {10, 20, 30, 40, 50},
    )
    if only_if(rv):
        return rv
    return _random_nonlevel_int(only_if=only_if)


def _random_level() -> Tuple[
    Union[mylog.Level, int, str], mylog.Level
]:
    lvl = _randchoice(tuple(mylog.Level))
    _to = _randchoice(("lvl", "int", "str"))
    if _to == "lvl":
        return lvl, lvl
    elif _to == "int":
        return lvl.value, lvl
    elif _to == "str":
        return lvl.name, lvl
    # else is not needed


def _random_bool() -> bool:
    return _randchoice((True, False))


def random_anything(
    *, only_if: Callable[[int], bool] = lambda _: True
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
    # else is not needed
    if only_if(rv):
        return rv
    return random_anything(only_if=only_if)


def x_is_y(x: object, y: object) -> bool:
    # So we don't get "do not compare types, use 'isinstance()' flake8(E721)"
    return x is y


def x_equals_y(x: object, y: object) -> bool:
    # So we test "==" AND "__eq__"
    return (x == y) and (x.__eq__(y))


def x_not_equals_y(x: object, y: object) -> bool:
    # So we test "!=" AND "__ne__"
    return (x != y) and (x.__ne__(y))


def speed() -> float:
    start = get_unix_time()
    logger = mylog.root.get_child()
    logger.threshold = mylog.Level(10)
    logger.stream = open(os.devnull, "w")
    logger.critical(
        "The quick brown fox jumps over the lazy dog.", False
    )
    end = get_unix_time()
    return end - start


def skip_if_slow():
    if (spd := speed()) >= 1:
        pytest.skip(
            f"This computer is too slow. A few simple stuff took {spd}"
            " seconds, while it should be less then one second."
        )


def test_to_level():
    assert mylog.to_level(mylog.Level.debug) == mylog.Level.debug
    assert mylog.to_level(mylog.Level.info) == mylog.Level.info
    assert mylog.to_level(mylog.Level.warning) == mylog.Level.warning
    assert mylog.to_level(mylog.Level.warn) == mylog.Level.warning
    assert mylog.to_level(mylog.Level.error) == mylog.Level.error
    assert (
        mylog.to_level(mylog.Level.critical) == mylog.Level.critical
    )
    assert mylog.to_level(mylog.Level.fatal) == mylog.Level.critical

    assert (
        mylog.to_level(mylog.Level.debug.numerator)
        == mylog.Level.debug
    )
    assert (
        mylog.to_level(mylog.Level.info.numerator) == mylog.Level.info
    )
    assert (
        mylog.to_level(mylog.Level.warning.numerator)
        == mylog.Level.warning
    )
    assert (
        mylog.to_level(mylog.Level.warn.numerator)
        == mylog.Level.warning
    )
    assert (
        mylog.to_level(mylog.Level.error.numerator)
        == mylog.Level.error
    )
    assert (
        mylog.to_level(mylog.Level.critical.numerator)
        == mylog.Level.critical
    )
    assert (
        mylog.to_level(mylog.Level.fatal.numerator)
        == mylog.Level.critical
    )

    assert (
        mylog.to_level(mylog.Level.debug.value) == mylog.Level.debug
    )
    assert mylog.to_level(mylog.Level.info.value) == mylog.Level.info
    assert (
        mylog.to_level(mylog.Level.warning.value)
        == mylog.Level.warning
    )
    assert (
        mylog.to_level(mylog.Level.warn.value) == mylog.Level.warning
    )
    assert (
        mylog.to_level(mylog.Level.error.value) == mylog.Level.error
    )
    assert (
        mylog.to_level(mylog.Level.critical.value)
        == mylog.Level.critical
    )
    assert (
        mylog.to_level(mylog.Level.fatal.value)
        == mylog.Level.critical
    )

    assert (
        mylog.to_level(str(mylog.Level.debug.numerator))
        == mylog.Level.debug
    )
    assert (
        mylog.to_level(str(mylog.Level.info.numerator))
        == mylog.Level.info
    )
    assert (
        mylog.to_level(str(mylog.Level.warning.numerator))
        == mylog.Level.warning
    )
    assert (
        mylog.to_level(str(mylog.Level.warn.numerator))
        == mylog.Level.warning
    )
    assert (
        mylog.to_level(str(mylog.Level.error.numerator))
        == mylog.Level.error
    )
    assert (
        mylog.to_level(str(mylog.Level.critical.numerator))
        == mylog.Level.critical
    )
    assert (
        mylog.to_level(str(mylog.Level.fatal.numerator))
        == mylog.Level.critical
    )

    assert (
        mylog.to_level(str(mylog.Level.debug.value))
        == mylog.Level.debug
    )
    assert (
        mylog.to_level(str(mylog.Level.info.value))
        == mylog.Level.info
    )
    assert (
        mylog.to_level(str(mylog.Level.warning.value))
        == mylog.Level.warning
    )
    assert (
        mylog.to_level(str(mylog.Level.warn.value))
        == mylog.Level.warning
    )
    assert (
        mylog.to_level(str(mylog.Level.error.value))
        == mylog.Level.error
    )
    assert (
        mylog.to_level(str(mylog.Level.critical.value))
        == mylog.Level.critical
    )
    assert (
        mylog.to_level(str(mylog.Level.fatal.value))
        == mylog.Level.critical
    )

    assert mylog.to_level(mylog.Level.debug.name) == mylog.Level.debug
    assert mylog.to_level(mylog.Level.info.name) == mylog.Level.info
    assert (
        mylog.to_level(mylog.Level.warning.name)
        == mylog.Level.warning
    )
    assert (
        mylog.to_level(mylog.Level.warn.name) == mylog.Level.warning
    )
    assert mylog.to_level(mylog.Level.error.name) == mylog.Level.error
    assert (
        mylog.to_level(mylog.Level.critical.name)
        == mylog.Level.critical
    )
    assert (
        mylog.to_level(mylog.Level.fatal.name) == mylog.Level.critical
    )

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


def tets_nolock():
    nolock = mylog.NoLock()

    assert nolock.__enter__() in {True, False, 1}
    assert nolock.__exit__() is None


def test_nonetype():
    assert x_is_y(mylog.NoneType, type(None))


def test_check_types():
    assert mylog.check_types(a=(int, 1), b=(str, "2")) is True
    assert (
        mylog.check_types(
            arg_1=((int, float), 1), b_8=(str, "Hello world")
        )
        is True
    )
    assert mylog.check_types(do=(bool, True)) is True
    with pytest.raises(
        TypeError,
        match=r"'do' must be type <class 'bool'>, got <class 'NoneType'>"
        r" \(None\)",
    ):
        mylog.check_types(do=(bool, None))
    with pytest.raises(
        TypeError,
        match=r"'sure' must be type \(<class 'bool'>, <class 'int'>\), got"
        r" <class 'float'> \(6.9\)",
    ):
        mylog.check_types(do=(bool, False), sure=((bool, int), 6.9))


class TestLogger:
    @staticmethod
    def test_eq():
        l1 = l2 = mylog.root.get_child()
        assert x_equals_y(l1, l2)
        assert x_equals_y(l2, l1)
        assert x_equals_y(mylog.root, mylog.root)

    @staticmethod
    def test_ne():
        l1 = mylog.root.get_child()
        l2 = mylog.root.get_child()
        assert x_not_equals_y(l1, l2)
        assert x_not_equals_y(l2, l1)

    @staticmethod
    def test_init():
        lock = mylog.NoLock()
        # Don't set `_allow_root` in production code
        mylog._allow_root = True
        logger = mylog.Logger(None, lock=lock)
        mylog._allow_root = False

        assert logger.higher is None
        assert logger.propagate is False
        assert logger.lock == lock
        assert logger.list == []

        assert logger.format == mylog.DEFAULT_FORMAT
        assert logger.threshold == mylog.DEFAULT_THRESHOLD
        assert logger.enabled is True
        assert logger.stream == sys.stdout
        assert logger.indent == 0

    @staticmethod
    def test_color():
        logger = mylog.root
        assert logger._color("quick brown fox") == "quick brown fox"
        assert logger._color("DEBUG") == termcolor.colored(
            "DEBUG".ljust(8), "blue"
        )
        assert logger._color("INFO") == termcolor.colored(
            "INFO".ljust(8), "cyan"
        )
        assert logger._color("WARNING") == termcolor.colored(
            "WARNING".ljust(8), "yellow"
        )
        assert logger._color("ERROR") == termcolor.colored(
            "ERROR".ljust(8), "red"
        )
        assert logger._color("CRITICAL") == termcolor.colored(
            "CRITICAL".ljust(8),
            "red",
            "on_yellow",
            ["bold", "underline", "blink"],
        )

    @staticmethod
    def test_level_to_string():
        logger = mylog.root
        assert logger.level_to_str(
            mylog.Level.debug
        ) == termcolor.colored("DEBUG".ljust(8), "blue")
        assert logger.level_to_str(
            mylog.Level.info
        ) == termcolor.colored("INFO".ljust(8), "cyan")
        assert logger.level_to_str(
            mylog.Level.warning
        ) == termcolor.colored("WARNING".ljust(8), "yellow")
        assert logger.level_to_str(
            mylog.Level.warn
        ) == termcolor.colored("WARNING".ljust(8), "yellow")
        assert logger.level_to_str(
            mylog.Level.error
        ) == termcolor.colored("ERROR".ljust(8), "red")
        assert logger.level_to_str(
            mylog.Level.critical
        ) == termcolor.colored(
            "CRITICAL".ljust(8),
            "red",
            "on_yellow",
            ["bold", "underline", "blink"],
        )
        assert logger.level_to_str(
            mylog.Level.fatal
        ) == termcolor.colored(
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
        # Check if it runs
        for _ in range(10):
            logger.format_msg(
                lvl[0],
                random_anything(),
                False,
                _randint(0, 3),
            )
        with pytest.warns(
            UserWarning, match="No traceback available, but tb=True"
        ):
            logger.format_msg(
                lvl[0],
                random_anything(),
                True,
                _randint(0, 3),
            )

    @staticmethod
    def test_actually_log():
        skip_if_slow()

        logger = mylog.root
        logger.list = []
        logger.indent = _randint(0, 10)
        logger.stream = open(os.devnull, "w")
        lvl = _random_level()
        msg = random_anything()
        frame_depth = _randint(0, 3)

        time = get_unix_time()
        logger._actually_log(lvl[0], msg, frame_depth, False)

        assert len(logger.list) == 1
        event = logger.list[0]
        assert event.msg == str(msg)
        assert event.level == lvl[1]
        assert event.time == pytest.approx(time, rel=1)
        assert event.indent == logger.indent
        assert event.frame_depth == frame_depth

    @staticmethod
    def test_log_propagate():
        skip_if_slow()

        logger = mylog.root.get_child()
        logger.list = []
        logger.indent = _randint(0, 10)
        logger.propagate = True
        logger.stream = open(os.devnull, "w")
        logger.threshold = mylog.Level.debug
        logger.higher.stream = open(os.devnull, "w")
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
        assert event.time == pytest.approx(time, rel=1)
        assert event.indent == logger.higher.indent
        assert event.frame_depth == frame_depth + 1
        #                                       ~~~
        # Since propagate is True, Logger._log() will automatically add one to
        # the frame_depth, if logging is done by the parent.

    @staticmethod
    def test_log_no_propagate():
        logger = mylog.root
        logger.list = []
        logger.indent = _randint(0, 10)
        logger.threshold = mylog.Level.debug
        logger.stream = open(os.devnull, "w")
        lvl = _random_level()
        msg = random_anything()
        frame_depth = _randint(0, 3)

        time = get_unix_time()
        logger._log(lvl[0], msg, False, frame_depth)

        assert len(logger.list) == 1
        event = logger.list[-1]
        assert event.msg == str(msg)
        assert event.level == lvl[1]
        assert event.time == pytest.approx(time, rel=1)
        assert event.indent == logger.indent
        assert event.frame_depth == frame_depth

    @staticmethod
    @pytest.mark.parametrize(
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
        logger.stream = open(os.devnull, "w")
        msg = random_anything()

        time = get_unix_time()
        getattr(logger, method_name)(msg, False)

        assert len(logger.list) == 1
        event = logger.list[-1]
        assert event.msg == str(msg)
        assert event.level == lvl
        assert event.time == pytest.approx(time, rel=1)
        assert event.indent == logger.indent

    @staticmethod
    def test_get_child():
        parent = mylog.root
        child = parent.get_child()

        assert isinstance(child, type(parent))
        assert child.propagate is False
        assert isinstance(child.lock, mylog.Lock)
        assert child.list == []
        assert child.indent == 0
        assert child.enabled is True

        assert child.format == parent.format
        assert child.threshold == parent.threshold
        assert child.stream == parent.stream

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
        assert not logger.is_enabled_for(mylog.Level.debug)
        assert not logger.is_enabled_for(mylog.Level.info)
        assert not logger.is_enabled_for(mylog.Level.warning)
        assert not logger.is_enabled_for(mylog.Level.error)
        assert logger.is_enabled_for(mylog.Level.critical)


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
