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
import sys
from unittest.mock import Mock

import mylog
import pytest
import termcolor

try:
    0 / 0  # noqa: B018
except ZeroDivisionError as err:
    exception = err

TEST_LOG_EVENT = mylog.LogEvent(
    message="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do.",
    level=69,
    time=0,
    indentation=6,
    line_number=1024,
    exception=exception,
)


class NeverHandler(mylog.Handler):
    def handle(*_: object, **__: object) -> object:
        raise AssertionError("call not expected")


def test_optional_string_format() -> None:
    assert mylog.optional_string_format("Hello, world!") == "Hello, world!"
    assert (
        mylog.optional_string_format("Hello, world!", foo="hi")
        == "Hello, world!"
    )
    assert (
        mylog.optional_string_format("Hello, world!", bar="bye")
        == "Hello, world!"
    )
    assert (
        mylog.optional_string_format("Hello, world!", foo="hi", bar="bye")
        == "Hello, world!"
    )
    assert (
        mylog.optional_string_format("Hello, {foo} world!")
        == "Hello, {foo} world!"
    )
    assert (
        mylog.optional_string_format("Hello, {foo} world!", foo="hi")
        == "Hello, hi world!"
    )
    assert (
        mylog.optional_string_format("Hello, {foo} world! {bar}", foo="hi")
        == "Hello, hi world! {bar}"
    )
    assert (
        mylog.optional_string_format("Hello, {foo} world! {bar}", bar="bye")
        == "Hello, {foo} world! bye"
    )
    assert (
        mylog.optional_string_format(
            "Hello, {foo} world! {bar}", foo="hi", bar="bye"
        )
        == "Hello, hi world! bye"
    )


class TestLevel:
    @staticmethod
    def test_new() -> None:
        assert mylog.Level.new(20) == mylog.Level.INFO
        assert mylog.Level.new(50) == mylog.Level.CRITICAL
        with pytest.raises(ValueError, match=r"invalid level: 0"):
            mylog.Level.new(0)
        with pytest.raises(ValueError, match=r"invalid level: 51"):
            mylog.Level.new(51)

        assert mylog.Level.new("40") == mylog.Level.ERROR
        assert mylog.Level.new("10") == mylog.Level.DEBUG
        with pytest.raises(ValueError, match=r"invalid level: '0'"):
            mylog.Level.new("0")
        with pytest.raises(ValueError, match=r"invalid level: '35'"):
            mylog.Level.new("35")

        assert mylog.Level.new("wArNIng") == mylog.Level.WARNING
        assert mylog.Level.new("eRROR") == mylog.Level.ERROR
        with pytest.raises(ValueError, match=r"invalid level: 'foobar'"):
            mylog.Level.new("foobar")
        with pytest.raises(ValueError, match=r"invalid level: 'FATAL'"):
            mylog.Level.new("FATAL")

    @staticmethod
    def test_new_or_int() -> None:
        assert mylog.Level.new_or_int(20) == mylog.Level.INFO
        assert mylog.Level.new_or_int(50) == mylog.Level.CRITICAL
        assert mylog.Level.new_or_int(0) == 0
        assert mylog.Level.new_or_int(51) == 51

        assert mylog.Level.new_or_int("40") == mylog.Level.ERROR
        assert mylog.Level.new_or_int("10") == mylog.Level.DEBUG
        assert mylog.Level.new_or_int("0") == 0
        assert mylog.Level.new_or_int("35") == 35

        assert mylog.Level.new_or_int("wArNIng") == mylog.Level.WARNING
        assert mylog.Level.new_or_int("eRROR") == mylog.Level.ERROR
        with pytest.raises(ValueError, match=r"invalid level: 'foobar'"):
            mylog.Level.new_or_int("foobar")
        with pytest.raises(ValueError, match=r"invalid level: 'FATAL'"):
            mylog.Level.new_or_int("FATAL")


def test_no_handler() -> None:
    mylog.NoHandler().handle(mylog.root, TEST_LOG_EVENT)


class TestStreamWriterHandler:
    @staticmethod
    def test_level_to_str() -> None:
        handler = mylog.StreamWriterHandler(sys.stderr)
        assert handler.level_to_str(mylog.Level.DEBUG) == termcolor.colored(
            "DEBUG", "blue"
        ).ljust(8)
        assert handler.level_to_str(mylog.Level.CRITICAL) == termcolor.colored(
            "CRITICAL", "red", "on_yellow", ["bold", "underline", "blink"]
        ).ljust(8)
        handler.use_colors = False
        assert handler.level_to_str(mylog.Level.DEBUG) == "DEBUG   "
        assert handler.level_to_str(mylog.Level.CRITICAL) == "CRITICAL"

    @staticmethod
    def test_format_message() -> None:
        handler = mylog.StreamWriterHandler(sys.stderr)
        message = handler.format_message(mylog.root, TEST_LOG_EVENT)
        assert message.startswith(
            "[root 69       1970-01-01 00:00:00+00:00 line: 01024]"
            "             Lorem ipsum dolor sit amet, consectetur adipiscing"
            " elit, sed do.\nTraceback (most recent call last):\n\n  File "
        )
        assert message.endswith("\n\nZeroDivisionError: division by zero\n\n")

    @staticmethod
    def test_handle_flush() -> None:
        mock = Mock()
        handler = mylog.StreamWriterHandler(mock)
        handler.handle(mylog.root, TEST_LOG_EVENT)
        mock.write.assert_called_once()
        assert mock.write.call_args.args[0].startswith(
            "[root 69       1970-01-01 00:00:00+00:00 line: 01024]"
            "             Lorem ipsum dolor sit amet, consectetur adipiscing"
            " elit, sed do.\nTraceback (most recent call last):\n\n  File "
        )
        assert mock.write.call_args.args[0].endswith(
            "\n\nZeroDivisionError: division by zero\n\n"
        )
        mock.flush.assert_called_once_with()

    @staticmethod
    def test_handle_no_flush() -> None:
        mock = Mock()
        handler = mylog.StreamWriterHandler(mock)
        handler.flush = False
        handler.handle(mylog.root, TEST_LOG_EVENT)
        mock.write.assert_called_once()
        assert mock.write.call_args.args[0].startswith(
            "[root 69       1970-01-01 00:00:00+00:00 line: 01024]"
            "             Lorem ipsum dolor sit amet, consectetur adipiscing"
            " elit, sed do.\nTraceback (most recent call last):\n\n  File "
        )
        assert mock.write.call_args.args[0].endswith(
            "\n\nZeroDivisionError: division by zero\n\n"
        )
        mock.flush.assert_not_called()


class TestLogger:
    @staticmethod
    def test_get_default_handlers() -> None:
        assert mylog.Logger.get_default_handlers() == [
            mylog.StreamWriterHandler(sys.stderr)
        ]

    @staticmethod
    def test_create_root() -> None:
        root = mylog.Logger._create_root()
        assert root.name == "root"
        assert root.parent is None

    @staticmethod
    def test_new() -> None:
        new = mylog.Logger.new(
            name="foobar",
            parent=mylog.root,
            handlers=[mylog.NoHandler()],
            propagate=True,
            indentation=10,
            enabled=False,
            threshold=12,
        )
        assert new.name == "foobar"
        assert new.parent == mylog.root
        # to also test __ne__  vv
        assert not (new.parent != mylog.root)  # noqa: SIM202
        assert new.handlers == [mylog.NoHandler()]
        assert new.propagate is True
        assert new.indentation == 10
        assert new.enabled is False
        assert new.threshold == 12

    @staticmethod
    def test_repr() -> None:
        assert repr(mylog.root) == "<Logger root>"

    @staticmethod
    def test_inherit() -> None:
        with pytest.raises(
            TypeError, match=r"cannot inherit if parent is None"
        ):
            mylog.root.inherit()

        logger = mylog.Logger.new(name="logger", parent=mylog.root)
        logger.name = (
            logger.propagate
        ) = logger.list_ = logger.indentation = logger.enabled = 1
        logger.inherit(
            mylog.AttributesToInherit(
                name=True,
                propagate=True,
                list_=True,
                indentation=True,
                enabled=True,
            )
        )
        assert logger.name == "root"
        assert logger.propagate is False
        assert logger.list_ == mylog.root.list_
        assert logger.indentation == 0
        assert logger.enabled is True
        assert logger.threshold == mylog.DEFAULT_THRESHOLD
        assert logger.handlers == [mylog.StreamWriterHandler(sys.stderr)]

    @staticmethod
    def test_create_child() -> None:
        logger = mylog.root.create_child(
            "logger",
            mylog.AttributesToInherit(
                name=True,
                propagate=True,
                list_=True,
                indentation=True,
                enabled=True,
            ),
        )
        assert logger.name == "root"
        assert logger.propagate is False
        assert logger.list_ == mylog.root.list_
        assert logger.indentation == 0
        assert logger.enabled is True
        assert logger.threshold == mylog.DEFAULT_THRESHOLD
        assert logger.handlers == [mylog.StreamWriterHandler(sys.stderr)]

    @staticmethod
    def test_create_log_event() -> None:
        event = mylog.root.create_log_event(
            message="foo, bar?",
            level=10,
            indentation=2,
            line_number=63,
            exception=None,
        )
        assert event.message == "foo, bar?"
        assert event.level == 10
        assert event.indentation == 2
        assert event.line_number == 63
        assert event.exception is None

    @staticmethod
    def test_add_to_list() -> None:
        logger = mylog.root.create_child("logger")
        logger.list_ = Mock()
        logger._add_to_list(TEST_LOG_EVENT)
        logger.list_.append.assert_called_once_with(TEST_LOG_EVENT)

    @staticmethod
    def test_handle() -> None:
        logger = mylog.root.create_child("logger")
        handler = Mock()
        logger._handle(TEST_LOG_EVENT, handler)
        handler.handle.assert_called_once_with(logger, TEST_LOG_EVENT)

    @staticmethod
    def test_call_handlers() -> None:
        logger = mylog.root.create_child("logger")
        handler1 = Mock()
        handler2 = Mock()
        logger.handlers = [handler1, handler2]
        logger._call_handlers(TEST_LOG_EVENT)
        handler1.handle.assert_called_once_with(logger, TEST_LOG_EVENT)
        handler2.handle.assert_called_once_with(logger, TEST_LOG_EVENT)

    @staticmethod
    def test_log() -> None:
        logger = mylog.root.create_child("logger")
        handler1 = Mock()
        handler2 = Mock()
        logger.handlers = [handler1, handler2]
        logger.list_ = Mock()

        logger._log(TEST_LOG_EVENT)

        handler1.handle.assert_called_once_with(logger, TEST_LOG_EVENT)
        handler2.handle.assert_called_once_with(logger, TEST_LOG_EVENT)
        logger.list_.append.assert_called_once_with(TEST_LOG_EVENT)

    @staticmethod
    def test_is_disabled() -> None:
        assert mylog.root.is_disabled(TEST_LOG_EVENT) is False
        mylog.root.enabled = False
        assert mylog.root.is_disabled(TEST_LOG_EVENT) is True
        mylog.root.enabled = True
        assert mylog.root.is_disabled(TEST_LOG_EVENT) is False

    @staticmethod
    def test_should_propagate() -> None:
        assert mylog.root.should_propagate(TEST_LOG_EVENT) is False
        mylog.root.propagate = True
        assert mylog.root.should_propagate(TEST_LOG_EVENT) is True
        mylog.root.propagate = False
        assert mylog.root.should_propagate(TEST_LOG_EVENT) is False

    @staticmethod
    def test_actually_propagate() -> None:
        with pytest.raises(
            RuntimeError, match=r"cannot propagate without a parent"
        ):
            mylog.root.actually_propagate(TEST_LOG_EVENT)
        parent = Mock()
        logger = mylog.Logger.new(name="logger", parent=parent)
        logger.actually_propagate(TEST_LOG_EVENT)
        parent.log.assert_called_once_with(TEST_LOG_EVENT)

    @staticmethod
    def test_is_enabled_for() -> None:
        assert mylog.root.is_enabled_for(29) is False
        assert mylog.root.is_enabled_for(30) is True
        assert mylog.root.is_enabled_for(31) is True

    @staticmethod
    def test_should_be_logged() -> None:
        assert mylog.root.should_be_logged(TEST_LOG_EVENT) is True
        assert (
            mylog.root.should_be_logged(
                mylog.root.create_log_event("hi", 1, 0, 0, None)
            )
        ) is False

    @staticmethod
    def test_log_disabled() -> None:
        logger = mylog.root.create_child("logger")
        logger.enabled = False
        logger.should_propagate = Mock()
        logger.handlers = [NeverHandler()]

        logger.log(TEST_LOG_EVENT)

        logger.should_propagate.assert_not_called()

    @staticmethod
    def test_log_propagate() -> None:
        parent_logger = mylog.root.create_child("parent")
        parent_logger._call_handlers = Mock()
        child_logger = parent_logger.create_child("child")
        child_logger.propagate = True
        handler = Mock()
        child_logger.handlers = [handler]

        child_logger.log(TEST_LOG_EVENT)

        handler.handle.assert_called_once_with(child_logger, TEST_LOG_EVENT)
        parent_logger._call_handlers.assert_called_once_with(TEST_LOG_EVENT)

    @staticmethod
    def test_log_should_not_be_logged() -> None:
        logger = mylog.root.create_child("logger")
        logger.should_be_logged = lambda _: False
        logger._log = Mock()

        logger.log(TEST_LOG_EVENT)

        logger._log.assert_not_called()

    @staticmethod
    def test_log_should_be_logged() -> None:
        logger = mylog.root.create_child("logger")
        logger.should_be_logged = lambda _: True
        logger._log = Mock()

        logger.log(TEST_LOG_EVENT)

        logger._log.assert_called_once_with(TEST_LOG_EVENT)

    @staticmethod
    def test_predefined_log() -> None:
        logger = mylog.root.create_child("logger")
        logger.log = Mock()

        logger._predefined_log(10, "hi", False)

        logger.log.assert_called_once()
        assert logger.log.call_args.args[0].message == "hi"
        assert logger.log.call_args.args[0].level == 10
        assert logger.log.call_args.args[0].exception is None

    @staticmethod
    def test_predefined_logs() -> None:
        logger = mylog.root.create_child("logger")
        logger._predefined_log = Mock()

        logger.debug("hello", True)
        logger._predefined_log.assert_called_once_with(
            mylog.Level.DEBUG, "hello", True
        )
        logger._predefined_log.reset_mock()

        logger.info("hello", False)
        logger._predefined_log.assert_called_once_with(
            mylog.Level.INFO, "hello", False
        )
        logger._predefined_log.reset_mock()

        logger.warning("hello", False)
        logger._predefined_log.assert_called_once_with(
            mylog.Level.WARNING, "hello", False
        )
        logger._predefined_log.reset_mock()

        logger.error("hello", True)
        logger._predefined_log.assert_called_once_with(
            mylog.Level.ERROR, "hello", True
        )
        logger._predefined_log.reset_mock()

        logger.critical("hello", True)
        logger._predefined_log.assert_called_once_with(
            mylog.Level.CRITICAL, "hello", True
        )
        logger._predefined_log.reset_mock()

    @staticmethod
    def test_indent() -> None:
        assert mylog.root.indentation == 0
        with mylog.root.indent:
            assert mylog.root.indentation == 1
        assert mylog.root.indentation == 0

    @staticmethod
    def test_threshold() -> None:
        assert mylog.root.threshold == mylog.Level.WARNING
        with mylog.root.change_threshold(mylog.Level.INFO):
            assert mylog.root.threshold == mylog.Level.INFO
        assert mylog.root.threshold == mylog.Level.WARNING
