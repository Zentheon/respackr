
# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).
 
## [Unreleased] - yyyy-mm-dd
 
### Added

- `--debug` flag will now print out error stacktraces. 

### Changed

- `mcmeta.py 2.0.0`: Rewritten to instead read and process an input template.
- `error.py 1.1.0`: Generally improved logic and log handling.
- `config.py 1.1.0` Moved over some config/args validation from genscript.py and added type checking for entries.
- `arguments.py 1.0.1`: Remove unnecessary `get_args` helper function.
- `arguments 1.1.0`: Improve help message.
 
### Fixed

- `--debug` didn't work because of a tiny error with `modules/log.py` (1.0.0 -> 1.0.1)
- `genscript.py`: Some cleanup
- `src.py 1.0.1`: Various cleanup and fixes.
- `config.py 1.0.1`: Various cleanup and fixes.
- `config.py 1.1.0`: Optional config values are handled properly now.
- `makezip.py 1.0.2`: Various cleanup and fixes.
- `svg2png.py 1.0.1`: Various cleanup and fixes.
- `theme.py 1.0.1`: Various cleanup. More error handling.
- `exclusion.py 1.0.1`: Various cleanup. More error handling.
- `inclusion.py 1.0.1`: Various cleanup. More error handling.

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
 
## [1.0.1] - 2025-07-14
 
### Added
   
### Changed

- Improved `apply_inclusions` logic. Now checks if there are files to include first.
- Slightly improved various log messages.
 
### Fixed

