from __future__ import absolute_import

import sys

from logging import FileHandler, Formatter, Logger, StreamHandler


def _make_logging_format_exception(colored):
    def logging_format_exception(exc_info):
        from . import format_exception

        exc, value, tb = exc_info
        return u''.join(format_exception(exc, value, tb, colored=colored))

    return logging_format_exception


def _patch_formatter(formatter, format_exception):
    formatter.formatException = format_exception

    if not hasattr(formatter, '_betexc_format'):
        formatter._betexc_format = formatter.format

        def format_record(record):
            if record.exc_info:
                exc_text = record.exc_text
                record.exc_text = None
                try:
                    return formatter._betexc_format(record)
                finally:
                    record.exc_text = exc_text

            return formatter._betexc_format(record)

        formatter.format = format_record


def patch():
    import logging
    from . import SUPPORTS_COLOR

    stream_format_exception = _make_logging_format_exception(SUPPORTS_COLOR)
    file_format_exception = _make_logging_format_exception(False)

    if hasattr(logging, '_defaultFormatter'):
        _patch_formatter(logging._defaultFormatter, stream_format_exception)

    handlers = [handler() for handler in logging._handlerList]
    handlers = [handler for handler in handlers if isinstance(handler, StreamHandler)]
    handlers = [handler for handler in handlers if isinstance(handler, FileHandler) or handler.stream == sys.stderr]
    for handler in handlers:
        if handler.formatter is None:
            handler.formatter = Formatter()
        if isinstance(handler, FileHandler):
            _patch_formatter(handler.formatter, file_format_exception)
        else:
            _patch_formatter(handler.formatter, stream_format_exception)


class BetExcLogger(Logger):
    def __init__(self, *args, **kwargs):
        super(BetExcLogger, self).__init__(*args, **kwargs)
        patch()
