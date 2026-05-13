from __future__ import absolute_import

from copy import copy
import sys

from logging import FileHandler, Logger, StreamHandler


FORMATTER_PATCHED = '_betexc_patched'
FORMATTER_COLORED = '_betexc_colored'


def _make_logging_format_exception(colored):
    def logging_format_exception(exc_info):
        from . import format_exception

        exc, value, tb = exc_info
        restore_args = exc is AssertionError and value is not None
        args = value.args if restore_args else None

        try:
            return u''.join(format_exception(exc, value, tb, colored=colored))
        finally:
            if restore_args:
                value.args = args

    return logging_format_exception


def _clone_formatter(formatter):
    formatter = copy(formatter)

    if getattr(formatter, FORMATTER_PATCHED, False):
        for name in ('format', 'formatException', FORMATTER_PATCHED, FORMATTER_COLORED):
            if name in formatter.__dict__:
                delattr(formatter, name)

    return formatter


def _patch_formatter(formatter, colored):
    if (getattr(formatter, FORMATTER_PATCHED, False) and
            getattr(formatter, FORMATTER_COLORED, None) == colored):
        return formatter

    formatter = _clone_formatter(formatter)
    format_record = formatter.format

    def format(record):
        exc_text = record.exc_text
        record.exc_text = None
        try:
            return format_record(record)
        finally:
            record.exc_text = exc_text

    formatter.formatException = _make_logging_format_exception(colored)
    formatter.format = format
    setattr(formatter, FORMATTER_PATCHED, True)
    setattr(formatter, FORMATTER_COLORED, colored)
    return formatter


def _handler_supports_color(handler):
    return isinstance(handler, StreamHandler) and handler.stream == sys.stderr


def _should_patch_handler(handler):
    return isinstance(handler, FileHandler) or _handler_supports_color(handler)


def patch():
    import logging
    from . import SUPPORTS_COLOR

    if hasattr(logging, '_defaultFormatter'):
        logging._defaultFormatter = _patch_formatter(logging._defaultFormatter, SUPPORTS_COLOR)

    for handler_ref in logging._handlerList:
        handler = handler_ref()
        if not _should_patch_handler(handler):
            continue

        colored = SUPPORTS_COLOR and _handler_supports_color(handler)
        formatter = handler.formatter or logging._defaultFormatter
        handler.setFormatter(_patch_formatter(formatter, colored))


class BetExcLogger(Logger):
    def __init__(self, *args, **kwargs):
        super(BetExcLogger, self).__init__(*args, **kwargs)
        patch()
