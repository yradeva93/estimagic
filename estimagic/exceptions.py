try:
    from better_exceptions import format_exception
except ImportError:
    from traceback import format_exception
import sys


class TableExistsError(Exception):
    pass


class StopOptimization(Exception):
    def __init__(self, message, current_status):
        super().__init__(message)
        self.message = message
        self.current_status = current_status

    def __reduce__(self):
        """Taken from here: https://tinyurl.com/y6eeys2f"""
        return (StopOptimization, (self.message, self.current_status))


def get_traceback():
    tb = format_exception(*sys.exc_info())
    if isinstance(tb, list):
        tb = "".join(tb)
    return tb
