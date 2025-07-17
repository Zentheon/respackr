
# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).
 
## [Unreleased] - yyyy-mm-dd
 
### Added
 
### Changed
 
### Fixed
 
## [2.0.0] - 2025-07-16
 
### Added

- Modularity. The script now loads from easier-to-maintain modules instead of one long .py file.
- New arguments:
  - `--config-file` allows specifying a different config location.
  - `--debug` enables extra log formatting.
  - `-e`, `--exit-error` Makes the script exit with a code if an error is thrown.

### Changed

- A bunch of code. Notably configuration loading and logging are much different.
- Logging: Use python `logging` module. Error messages are now shown by default.
- `--verbose` uses `count` argparse type. There are now three different verbosity options.
- Error handling: Improvements were made to error handling functions. "warning" and "critical" types are supported.
 
### Fixed
 
## [1.0.1] - 2017-03-14
 
### Added
   
### Changed

- Improved `apply_inclusions` logic. Now checks if there are files to include first.
- Slightly improved various log messages.
 
### Fixed

