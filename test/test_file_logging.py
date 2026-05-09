from __future__ import absolute_import

import logging
import os
import sys
import tempfile

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

import better_exceptions


def fail():
    marker = 'keeps stream color only'
    raise RuntimeError(marker)


def main():
    better_exceptions.SUPPORTS_COLOR = True

    logger = logging.getLogger('better_exceptions_file_logging_test')
    logger.setLevel(logging.ERROR)
    logger.propagate = False

    old_stderr = sys.stderr
    stream = StringIO()
    sys.stderr = stream
    stream_handler = logging.StreamHandler()

    fd, path = tempfile.mkstemp()
    os.close(fd)
    file_handler = logging.FileHandler(path)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    try:
        better_exceptions.hook()
        try:
            fail()
        except RuntimeError:
            logger.exception('callback failed')

        stream_output = stream.getvalue()
        with open(path, 'r') as log:
            file_output = log.read()

        assert '\x1b[' in stream_output
        assert '\x1b[' not in file_output
        assert 'keeps stream color only' in file_output
    finally:
        sys.stderr = old_stderr
        logger.removeHandler(stream_handler)
        logger.removeHandler(file_handler)
        stream_handler.close()
        file_handler.close()
        os.remove(path)


if __name__ == '__main__':
    main()
