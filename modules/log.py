# log.py

"""
Logging configuration
"""

# Revision of this module:
__version__ = "1.0.0"

import logging

def add_logging_level(level_val, level_name, method_name=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `level_name` becomes an attribute of the `logging` module with the value
    `level_val`. `method_name` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `method_name` is not specified, `level_name.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    Edited from: https://stackoverflow.com/a/35804945
    """
    if not method_name:
        method_name = level_name.lower()

    if hasattr(logging, level_name):
       raise AttributeError('{} already defined in logging module'.format(level_name))
    if hasattr(logging, method_name):
       raise AttributeError('{} already defined in logging module'.format(method_name))
    if hasattr(logging.getLoggerClass(), method_name):
       raise AttributeError('{} already defined in logger class'.format(method_name))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def for_log_level(self, message, *args, **kwargs):
        if self.isEnabledFor(level_val):
            self._log(level_val, message, args, **kwargs)
    def log_to_root(message, *args, **kwargs):
        logging.log(level_val, message, *args, **kwargs)

    logging.addLevelName(level_val, level_name)
    setattr(logging, level_name, level_val)
    setattr(logging.getLoggerClass(), method_name, for_log_level)
    setattr(logging, method_name, log_to_root)

def setup_logging(quiet=False, verbosity=0):
    """Configure logging based on verbosity and quiet flags"""
    add_logging_level(logging.INFO - 5, "VERBOSE")
    add_logging_level(logging.DEBUG - 5, "TRACE")
    if quiet:
        logging.basicConfig(level=logging.CRITICAL)
    else:
        log_level = logging.WARNING  # Default
        if verbosity == 0:
            log_level = logging.INFO
        elif verbosity == 1:
            log_level = logging.VERBOSE
        elif verbosity == 2:
            log_level = logging.DEBUG
        elif verbosity >= 3:
            log_level = logging.TRACE

        logging.basicConfig(
            level=log_level,
            format='%(message)s',  # Suppress level names
            datefmt='%H:%M:%S'     # Optional: time format if you want timestamps
        )

