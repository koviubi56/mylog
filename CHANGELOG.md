# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changes

- **! Renamed `Logger._log` to `Logger.log`, and its new signature is `Logger.log(self: Self@Logger, lvl: Levelable, msg: Stringable, traceback: bool = False, frame_depth: int = 3) -> (LogEvent | None)`**

## [0.7.0] - 2023-03-19

### Added

- **! Added names for loggers! => `Logger.__init__(self: Self@Logger, name: str, higher: Logger | None = None) -> None`, new format substitution: `{name}`, `Logger.get_child(self: Self@Logger, name: str) -> Logger`** #51
- **Added `AttributesToInherit`, `Logger.compare_using_name` (=> `Logger._thing_to_compare`), `Logger.attributes_to_inherit`, `Logger.color_config` (=> `Logger.color(cls: Type[Self@Logger], rv: str) -> str`), and `Logger.level_name_width` to make making changes to loggers easier.**

### Changed

- **Renamed `Logger._color` to `Logger.color`** ([`26ee19f`](https://github.com/koviubi56/mylog/commit/26ee19f7255397d774d2e2439e927318a8bb3dac#diff-134a3f0dfece1d8aef44db6e6c1f05dbb0c904328960638685919788921d38d3L362-R382))
- Made the following classes dataclasses:
  - `SetAttr`,
  - `NoHandler`,
  - `StreamWriterHandler`,
  - `IndentLogger`,
  - `ChangeThreshold`,
- Made some methods class/staticmethods:
  - `Logger.get_default_handlers`,
  - `Logger.level_to_str`
- `Logger.threshold` is a `Union[Level, int]` ([`26ee19f`](https://github.com/koviubi56/mylog/commit/26ee19f7255397d774d2e2439e927318a8bb3dac#diff-134a3f0dfece1d8aef44db6e6c1f05dbb0c904328960638685919788921d38d3L354-R374))

### Removed

- Removed `check_typed` and related (`check_union`, `is_union`, `_check_types_error`) ([`ef85a86`](https://github.com/koviubi56/mylog/commit/ef85a86b2d5cd165190d25e3098296f700a32ea9#diff-134a3f0dfece1d8aef44db6e6c1f05dbb0c904328960638685919788921d38d3L119-L212))

## [0.6.0] - 2022-07-13

_Changed from pre-releases are listed here._

### Added

- **Added an "optional" `colorama.init()` call. mylog tries to import colorama, and call `colorama.init()`, but if there's an exception, it will be ignored.**

### Removed

- **`typing-extensions` is not being used; it is not a dependency**

### Fixed

- **Fixed frame depth with debug, info, warning, error, and critical. Changed from 4 to 5.**

## [0.6.0-beta.1] - 2022-07-10

### Added

- **Added an "optional" `colorama.init()` call. mylog tries to import colorama, and call `colorama.init()`, but if there's an exception, it will be ignored.**

### Fixed

- **Fixed frame depth with debug, info, warning, error, and critical. Changed from 4 to 5.**

## [0.5.0] - 2022-06-11

### Added

- Added `__repr__` to `SetAttr`, `NoHandler`, `StreamWriterHandler`, `Logger`, `IndentLogger`, and `ChangeThreshold`

## [0.4.0] - 2022-06-06

### Added

- **! Added handlers! Added `Handler` ABC, `StreamWriterHandler`, `Logger.handlers`, `Logger.get_default_handlers`**
- **Added `tb` to `LogEvent`**
- Added `SetAttr`

### Changed

- **`Logger._inherit` does not have a parameter `lock`**
- **`Logger.format_msg`'s signature looks like this: `format_msg(self, event: LogEvent) -> str`**
- `Logger._actually_log`, `Logger._log`, and the log methods (debug, info, ...) now return `Optional[LogEvent]`

### Removed

- **! Removed `Logger.lock`, `Logger.flush`, `Logger.stream`**
- **Removed `TeeStream`**
- Removed `Lock`, `NoLock`

## [0.3.0] - 2022-05-07

### Added

- **! Added `TeeStream`.**
- **Added `Logger.flush`. Defaults to `True`. _Not_ inherited. Must be set manually.**
- Added `StreamProtocol`

## [0.2.0] - 2022-05-06

_Changed from pre-releases are listed here._

### Added

- **A `UserWarning` is issued, if a log function is called with `traceback=True` (or `tb=True`) but there's _no_ exception.**
- **`Logger.is_enabled_for` issues a `UserWarning`, if `Logger.threshold` is not a `Level`, and it tries to convert it.**

### Changed

- **Changed how inheritance works**
- Protocols are now runtime checkable.
- Specified requirements/dependencies in `setup.cfg` too.

### Removed

- **! Because inheritance changed, most of the `get_*` methods were _removed_.**

## [0.2.0-beta.1] - 2022-04-22

### Added

- **A `UserWarning` is issued, if a log function is called with `traceback=True` (or `tb=True`) but there's _no_ exception.**
- **`Logger.is_enabled_for` issues a `UserWarning`, if `Logger.threshold` is not a `Level`, and it tries to convert it.**

### Changed

- **Changed how inheritance works**
- Protocols are now runtime checkable.

### Removed

- **! Because inheritance changed, most of the `get_*` methods were _removed_.**

## [0.1.1] - 2022-03-27

### Changed

- Uncommented lots of stuff in `setup.cfg`
- Added `.vscode` into `.gitignore`

## [0.1.0] - 2022-03-27
