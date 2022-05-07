# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
