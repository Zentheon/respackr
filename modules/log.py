# log.py

# Revision of this module:
__version__ = "1.0.0"

import logging
from modules.arguments import args

class LogInit:
    def __init__(self):
        # --verbose and --quiet arguments are used here
        self.add_logging_level(logging.INFO - 5, "VERBOSE")
        self.add_logging_level(logging.DEBUG - 5, "TRACE")
        self.args = args
        logging.trace(f"Setup logging with args (quiet={self.args.quiet}, verbosity={self.args.verbose})")
        self.log_level = 10
        if self.args.quiet:
            self.log_level = logging.CRITICAL
        else:
            self.log_level = logging.INFO  # Default
            if self.args.verbose == 1:
                self.log_level = logging.VERBOSE
            elif self.args.verbose == 2:
                self.log_level = logging.DEBUG
            elif self.args.verbose >= 3:
                self.log_level = logging.TRACE

        logging.basicConfig(
            force=True, # Required now for some reason
            level=self.log_level,
            format=self.set_format(),  # Suppress level names
            datefmt='%H:%M:%S'
        )

    def set_format(self):
        if args.debug:
            self.fmt = '%(asctime)s:%(name)s:%(levelname)s: %(message)s'
            return(fmt)
        else:
            self.fmt = '%(messages)s'

    def add_logging_level(self, level_val, level_name, method_name=None):
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


# Set up logging when the module is loaded
LogInit()
