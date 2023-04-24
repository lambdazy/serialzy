import copyreg
import sys
from types import CodeType, TracebackType


def register_exception_serializer_to_pickle():
    copyreg.pickle(TracebackType, __pickle_traceback)


def __unpickle_traceback(tb_frame, tb_lineno, tb_next):
    ret = object.__new__(Traceback)
    ret.tb_frame = tb_frame
    ret.tb_lineno = tb_lineno
    ret.tb_next = tb_next
    return ret.to_traceback()


def __pickle_traceback(tb):
    return __unpickle_traceback, (Frame(tb.tb_frame), tb.tb_lineno, tb.tb_next and Traceback(tb.tb_next))


# noinspection PyPep8Naming
class __traceback_maker(Exception):
    pass


class Frame(object):
    def __init__(self, frame):
        self.f_locals = {}
        self.f_globals = {k: v for k, v in frame.f_globals.items() if k in ("__file__", "__name__")}
        self.f_code = frame.f_code
        self.f_lineno = frame.f_lineno


class Traceback(object):
    tb_next = None

    def __init__(self, tb):
        self.tb_frame = Frame(tb.tb_frame)
        self.tb_lineno = int(tb.tb_lineno)

        tb = tb.tb_next
        prev_traceback = self
        cls = type(self)
        while tb is not None:
            traceback = object.__new__(cls)
            traceback.tb_frame = Frame(tb.tb_frame)
            traceback.tb_lineno = int(tb.tb_lineno)
            prev_traceback.tb_next = traceback
            prev_traceback = traceback
            tb = tb.tb_next

    def to_traceback(self):
        current = self
        top_tb = None
        tb = None
        while current:
            f_code = current.tb_frame.f_code
            code = compile('\n' * (current.tb_lineno - 1) + 'raise __traceback_maker', current.tb_frame.f_code.co_filename, 'exec')
            if hasattr(code, "replace"):
                # Python 3.8 and newer
                code = code.replace(co_argcount=0, co_filename=f_code.co_filename, co_name=f_code.co_name, co_freevars=(), co_cellvars=())
            else:
                code = CodeType(
                    0,
                    code.co_kwonlyargcount,
                    code.co_nlocals,
                    code.co_stacksize,
                    code.co_flags,
                    code.co_code,
                    code.co_consts,
                    code.co_names,
                    code.co_varnames,
                    f_code.co_filename,
                    f_code.co_name,
                    code.co_firstlineno,
                    code.co_lnotab,
                    (),
                    (),
                )

            # noinspection PyBroadException
            try:
                exec(code, dict(current.tb_frame.f_globals), {})
            except Exception:
                next_tb = sys.exc_info()[2].tb_next
                if top_tb is None:
                    top_tb = next_tb
                if tb is not None:
                    tb.tb_next = next_tb
                tb = next_tb
                del next_tb

            current = current.tb_next
        try:
            return top_tb
        finally:
            del top_tb
            del tb
