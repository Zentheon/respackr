# respackr/logger.py

"""Houses all the setup and handling of logs, built upon Structlog."""

import logging
import typing

import structlog

STYLES = {
    "fore": {
        "red": "\033[31m",
        "blue": "\033[34m",
        "cyan": "\033[36m",
        "magenta": "\033[35m",
        "yellow": "\033[33m",
        "green": "\033[32m",
    },
    "back": {"black": "\x1b[40m"},
    "reset": "\033[0m",
    "bright": "\033[1m",
    "dim": "\033[2m",
}

try:
    import colorama

    colorama.init()
    STYLES = {
        "fore": {
            "blue": colorama.Fore.BLUE,
            "cyan": colorama.Fore.CYAN,
            "magenta": colorama.Fore.MAGENTA,
            "green": colorama.Fore.GREEN,
            "yellow": colorama.Fore.YELLOW,
            "red": colorama.Fore.RED,
        },
        "back": {"black": colorama.Back.BLACK},
        "reset": colorama.Style.RESET_ALL,
        "bright": colorama.Style.BRIGHT,
        "dim": colorama.Style.DIM,
    }
except ImportError:
    pass

LEVEL_STYLES = {
    "debug": STYLES["fore"]["blue"],
    "info": STYLES["fore"]["green"],
    "warning": STYLES["fore"]["yellow"],
    "error": STYLES["fore"]["red"],
    "critical": STYLES["back"]["black"] + STYLES["fore"]["red"] + STYLES["bright"],
    "unknown": STYLES["dim"],
}


class PrettyLevel:
    """Alternate level name processor for console rendering that's a bit prettier."""

    def __call__(self, key: str, value: object) -> str:
        value = str(value)
        level_width = 8  # Max width of a level name
        pad_amount = level_width - len(value)
        padded_level = f"- {LEVEL_STYLES.get(value, 'unknown')}{value}{STYLES['reset']}"
        padded_level = padded_level + " " * pad_amount if pad_amount >= 0 else ""

        return padded_level


class DictKeyReorderer:
    """A version of KeyValuerenderer that returns a dict instead of a string."""

    def __init__(
        self,
        sort_keys: bool = False,
        key_order: typing.Sequence[str] | None = None,
        drop_missing: bool = False,
        repr_native_str: bool = True,
    ):
        self._ordered_items = structlog.processors._items_sorter(sort_keys, key_order, drop_missing)

        if repr_native_str is True:
            self._repr = repr
        else:

            def _repr(inst: typing.Any) -> str:
                if isinstance(inst, str):
                    return inst

                return repr(inst)

            self._repr = _repr

    def __call__(
        self, logger: object, event_name: str, event_dict: structlog.types.EventDict
    ) -> dict:
        sorted_items = self._ordered_items(event_dict)
        sorted_dict = {key: value for key, value in sorted_items}
        return sorted_dict


class LogWrapper:
    """Structlog wrapper that does level + label filtering and mutliple formats.

    A logger is initialized with either pretty output for TTY sessions or json formatted lines
    for production/CI scenarios.

    Settings can be changed on the fly by calling 'set_level', 'set_filter' or 'set_logfile'.
    Internally, those options just call 'settings', which recreate the logger with new settings.
    """

    def __init__(
        self, name: str, level: int | str = "info", filter: list = [], format_json: bool = False
    ):
        """Initialize the logger with the defaults, or values where provided.

        Args:
            name (str): What to name the logger.
            level (int): Loglevel to filter messages by. Default: "info" (20)
            filter (list): List of strings for filtering by the extra 'label' event. Default: []
            format_json (bool): Switch to json-formatted logging. Default: False
        """
        self.filter_all_keywords = ["all", "everything", "open_the_floodgates"]

        self.console_renderer = structlog.dev.ConsoleRenderer(
            columns=[
                # Timestamps are the same as the default.
                structlog.dev.Column(
                    "timestamp",
                    structlog.dev.KeyValueColumnFormatter(
                        key_style=None,
                        value_style=STYLES["dim"],
                        reset_style=STYLES["reset"],
                        value_repr=str,
                    ),
                ),
                structlog.dev.Column("level", PrettyLevel()),
                # Message content
                structlog.dev.Column(
                    "event",
                    structlog.dev.KeyValueColumnFormatter(
                        key_style=None,
                        value_style=STYLES["bright"],
                        reset_style=STYLES["reset"],
                        value_repr=str,
                    ),
                ),
                # The extra arg the is used for filtering.
                structlog.dev.Column(
                    "label",
                    structlog.dev.KeyValueColumnFormatter(
                        key_style=None,
                        value_style=STYLES["fore"]["green"],
                        reset_style=STYLES["reset"],
                        value_repr=str,
                        prefix="[",
                        postfix="]",
                    ),
                ),
                # All other extra params.
                structlog.dev.Column(
                    "",
                    structlog.dev.KeyValueColumnFormatter(
                        key_style=STYLES["fore"]["cyan"],
                        value_style=STYLES["fore"]["green"],
                        reset_style=STYLES["reset"],
                        value_repr=str,
                    ),
                ),
            ]
        )

        self.shared_processors = [
            self.label_filterer,
            structlog.processors.add_log_level,
        ]

        self.json_processors = [
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.format_exc_info,
            DictKeyReorderer(
                sort_keys=True,
                key_order=["timestamp", "level", "event", "label", "exception"],
                drop_missing=False,
            ),
            structlog.processors.JSONRenderer(),
        ]

        self.console_processors = [
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            self.console_renderer,
        ]

        self.settings(name, level, filter, format_json)

    def settings(self, name: str, level: int | str, filter: list, format_json: bool):
        """Recreate the logger with new settings.

        Args:
            name (str): What to name the loggers. Will be suffixed with '_toconsole' or '_tofile'
            level (int): Loglevel to filter messages by.
            filter (list): List of strings for filtering by the extra 'label' event.
            logfile (str): Filepath to log to. Default:
        """
        # Infer level from string name
        if isinstance(level, str):
            level = getattr(logging, level.upper())

        if format_json:
            self.logger = structlog.get_logger(
                name,
                processors=self.shared_processors + self.json_processors,
                wrapper_class=structlog.make_filtering_bound_logger(level),
                cache_logger_on_first_use=True,
            )
        else:
            self.logger = structlog.get_logger(
                name,
                processors=self.shared_processors + self.console_processors,
                wrapper_class=structlog.make_filtering_bound_logger(level),
                cache_logger_on_first_use=True,
            )

        global filter_list
        filter_list = filter

        self.name = name
        self.level = level
        self.filter = filter
        self.format_json = format_json

    def set_level(self, level: int | str):
        """Sets the loglevel to filter messages by."""
        self.settings(self.name, level, self.filter, self.format_json)

    def set_filter(self, filter: list):
        """Sets the 'label' filters.

        'all', 'everything' and 'open_the_floodgates' lets everything though, or whatever is
        specified in self.filter_all_keywords
        """
        self.settings(self.name, self.level, filter, self.format_json)

    def label_filterer(self, logger, method_name, event_dict):
        """Filters out messages by "label" key and values from a filter list."""
        if "all" in self.filter:
            return event_dict

        if "label" in event_dict:
            if event_dict["label"] not in self.filter:
                raise structlog.DropEvent  # Skip logging this message
        return event_dict

    def set_json_output(self, format_json: bool):
        """Sets whether to use pretty formatting (False) or structured json (True)"""
        self.settings(self.name, self.level, self.filter, format_json)

    def debug(self, *args, **kwargs):
        """Logs to the configured logger with level 'debug'"""
        self.logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs):
        """Logs to the configured logger with level 'info'"""
        self.logger.info(*args, **kwargs)

    def warn(self, *args, **kwargs):
        """Logs to the configured logger with level 'warning'"""
        self.logger.warn(*args, **kwargs)

    def error(self, *args, **kwargs):
        """Logs to the configured logger with level 'error'"""
        self.logger.error(*args, **kwargs)

    def critical(self, *args, **kwargs):
        """Logs to the configured logger with level 'critical'"""
        self.logger.critical(*args, **kwargs)
