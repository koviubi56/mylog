import secrets

import pytest

import mylog

mylog.root.get_child().threshold


def test_nolock_enter():
    nl = mylog.NoLock()

    enter_rv = nl.__enter__()

    assert isinstance(enter_rv, bool) or enter_rv == 1


def test_nolock_exit():
    nl = mylog.NoLock()

    exit_rv = nl.__exit__(None, None, None)

    assert exit_rv is None


def test_check_types():
    assert mylog.check_types(a=(int, 1), b=(str, "2"))
    assert mylog.check_types(
        arg_1=((int, float), 1), b_8=(str, "Hello world")
    )
    assert mylog.check_types(do=(bool, True))
    with pytest.raises(
        TypeError,
        match="'do' must be type <class 'bool'>, got <class 'NoneType'>"
        r" \(None\)",
    ):
        mylog.check_types(do=(bool, None))  # !
    with pytest.raises(
        TypeError,
        match=r"'sure' must be type \(<class 'bool'>, <class 'int'>\), got"
        r" <class 'float'> \(6.9\)",
    ):
        mylog.check_types(
            do=(bool, False), sure=((bool, int), 6.9)
        )  # !


def test_logger_does_not_allow_root():
    with pytest.raises(
        ValueError,
        match="Cannot create a new logger: Root logger already"
        " exists. Use that, or make a child logger from the root"
        " one.",
    ):
        mylog.Logger()


def anyting_except(exc: type) -> object:
    while True:
        r = secrets.choice(
            (
                "str",
                "int",
                "float",
                "bool",
                "None",
                "list",
                "tuple",
                "dict",
                "set",
                "frozenset",
                "bytes",
                "bytearray",
            )
        )
        if r == exc:
            continue
        if r == "str":
            return secrets.token_urlsafe()
        if r == "int":
            return secrets.randbelow(int(1e6))
        if r == "float":
            return secrets.SystemRandom().uniform(0, int(1e6))
        if r == "bool":
            return secrets.choice((True, False))
        if r == "None":
            return None
        if r == "list":
            return [
                anyting_except("{NULL}")
                for _ in range(secrets.randbelow(5))
            ]
        if r == "tuple":
            return tuple(
                anyting_except("{NULL}")
                for _ in range(secrets.randbelow(5))
            )
        if r == "dict":
            return {
                secrets.token_urlsafe(): anyting_except("{NULL}")
                for _ in range(secrets.randbelow(5))
            }
        if r == "set":
            return {
                secrets.token_urlsafe()
                for _ in range(secrets.randbelow(5))
            }
        if r == "frozenset":
            return frozenset(
                secrets.token_urlsafe()
                for _ in range(secrets.randbelow(5))
            )
        if r == "bytes":
            return secrets.token_bytes()
        if r == "bytearray":
            return bytearray(secrets.token_bytes())


def test_logger_root_propagate():
    mylog.root.propagate = True
    with pytest.warns(
        UserWarning,
        match="Root logger should not propagate! Set enabled to"
        " False if you want to disable it.",
    ):
        mylog.root.debug("Test")
    mylog.root.propagate = False


def test_logger_get_child():
    root = mylog.root
    child = root.get_child()
    assert child.higher == root
    assert child.colors == root.colors
    assert child.enabled is None
    assert child.format is None
    assert child.indent is None
    assert child.propagate is False
    assert child.stream is None
    assert child.threshold is None


# self is not needed
def no_format_msg(lvl, msg, tb, frame_depth):
    return ""


class TestLoggerList:
    @staticmethod
    def logger_factory():
        return mylog.root.get_child()

    def test_new(self):
        mylogger = self.logger_factory()

        assert mylogger.get_enabled() is True
        assert mylogger.list == []

    def test_success(self):
        mylogger = self.logger_factory()
        mylogger.format_msg = no_format_msg

        stuff = str(anyting_except("{NULL}"))
        mylogger.critical(stuff)

        assert len(mylogger.list) == 1

        logevent = mylogger.list[0]
        self.check_log_event(logevent, stuff)

    def test_enabled(self):
        mylogger = self.logger_factory()
        mylogger.enabled = False

        stuff = str(anyting_except("{NULL}"))
        mylogger.critical(stuff)

        assert mylogger.list == []

    def test_propagate(self):
        mylogger = self.logger_factory()
        mylogger.propagate = True
        mylog.root.format_msg = no_format_msg

        stuff = str(anyting_except("{NULL}"))
        mylogger.critical(stuff)

        assert mylogger.list == []
        assert len(mylogger.higher.list) == 1
        logevent = mylogger.higher.list[0]
        self.check_log_event(logevent, stuff)

    def test_enabled_for(self):
        mylogger = self.logger_factory()
        mylogger.threshold = mylog.Level.critical

        mylogger.debug(str(anyting_except("{NULL}")))

        assert mylogger.list == []

    def test_is_enabled_for(self):
        mylogger = self.logger_factory()
        mylogger.threshold = mylog.Level.critical
        assert mylogger.is_enabled_for(mylog.Level.critical) is True
        assert mylogger.is_enabled_for(mylog.Level.error) is False
        assert mylogger.is_enabled_for(mylog.Level.warning) is False
        assert mylogger.is_enabled_for(mylog.Level.info) is False
        assert mylogger.is_enabled_for(mylog.Level.debug) is False

        mylogger.threshold = mylog.Level.error
        assert mylogger.is_enabled_for(mylog.Level.critical) is True
        assert mylogger.is_enabled_for(mylog.Level.error) is True
        assert mylogger.is_enabled_for(mylog.Level.warning) is False
        assert mylogger.is_enabled_for(mylog.Level.info) is False
        assert mylogger.is_enabled_for(mylog.Level.debug) is False

        mylogger.threshold = mylog.Level.warning
        assert mylogger.is_enabled_for(mylog.Level.critical) is True
        assert mylogger.is_enabled_for(mylog.Level.error) is True
        assert mylogger.is_enabled_for(mylog.Level.warning) is True
        assert mylogger.is_enabled_for(mylog.Level.info) is False
        assert mylogger.is_enabled_for(mylog.Level.debug) is False

        mylogger.threshold = mylog.Level.info
        assert mylogger.is_enabled_for(mylog.Level.critical) is True
        assert mylogger.is_enabled_for(mylog.Level.error) is True
        assert mylogger.is_enabled_for(mylog.Level.warning) is True
        assert mylogger.is_enabled_for(mylog.Level.info) is True
        assert mylogger.is_enabled_for(mylog.Level.debug) is False

        mylogger.threshold = mylog.Level.debug
        assert mylogger.is_enabled_for(mylog.Level.critical) is True
        assert mylogger.is_enabled_for(mylog.Level.error) is True
        assert mylogger.is_enabled_for(mylog.Level.warning) is True
        assert mylogger.is_enabled_for(mylog.Level.info) is True
        assert mylogger.is_enabled_for(mylog.Level.debug) is True

    def check_log_event(self, logevent, stuff):
        assert logevent.msg == stuff
        assert logevent.level == mylog.Level.critical
        assert logevent.indent == 0


def test_indent():
    mylogger = mylog.root.get_child()
    assert mylogger.get_indent() == 0
    with mylogger.ctxmgr:
        assert mylogger.get_indent() == 1
    assert mylogger.get_indent() == 0


def test_change_threshold():
    mylogger = mylog.root.get_child()
    assert mylogger.get_effective_level() == mylog.DEFAULT_THRESHOLD
    with mylog.ChangeThreshold(mylogger, 30):
        assert mylogger.get_effective_level() == mylog.Level.warning
    assert mylogger.get_effective_level() == mylog.DEFAULT_THRESHOLD
