# respackr/logger.py


import logging

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


console_renderer = structlog.dev.ConsoleRenderer(
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

filter = []


def filter_logs(logger, method_name, event_dict):
    """Filters out messages by "label" key and values from a filter list."""
    if "all" in filter:
        return event_dict

    if "label" in event_dict:
        if event_dict["label"] not in filter:
            raise structlog.DropEvent  # Skip logging this message
    return event_dict


def logging_init(name: str, level: int | str, filter_list: list):
    """Setup Structlog with custom processors and filters using event args."""
    global filter
    filter = filter_list

    # Infer log level from name
    if isinstance(level, str):
        level = getattr(logging, level.upper())

    log = structlog.get_logger(name)
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
        processors=[
            filter_logs,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            console_renderer,
        ],
    )
    return log
