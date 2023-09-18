import copyreg
import sys
from types import TracebackType, CodeType, FunctionType
from typing import Callable, List


def register_exception_serializer_to_pickle():
    copyreg.pickle(TracebackType, __pickle_traceback)


def __pickle_traceback(tb):
    return to_traceback, (from_traceback(tb),)


class Traceback:
    def __init__(self, tb):
        self.co_name = tb.tb_frame.f_code.co_name
        self.tb_lineno = int(tb.tb_lineno)
        self.co_filename = tb.tb_frame.f_code.co_filename
        self.f_globals = {k: v for k, v in tb.tb_frame.f_globals.items() if k in ("__file__", "__name__")}


def from_traceback(tb):
    stack = []
    while tb:
        stack.append(Traceback(tb))
        tb = tb.tb_next
    return stack


def to_traceback(tbs):
    stack: List[Callable] = [ValueError]
    for i, tb in enumerate(reversed(tbs)):
        code = compile("\n" * (tb.tb_lineno - 1) + "raise exception()", tb.co_filename, "exec")
        if hasattr(code, "replace"):
            code = code.replace(co_argcount=0, co_filename=tb.co_filename, co_name=tb.co_name,
                                co_freevars=(), co_cellvars=())
        elif sys.version_info < (3, 8):
            code = CodeType(
                co_argcount=0,
                co_kwonlyargcount=code.co_kwonlyargcount,
                co_nlocals=code.co_nlocals,
                co_stacksize=code.co_stacksize,
                co_coflags=code.co_flags,
                co_code=code.co_code,
                co_consts=code.co_consts,
                co_co_names=code.co_names,
                co_varnames=code.co_varnames,
                co_filename=tb.co_filename,
                co_coname=tb.co_name,
                co_firstlineno=code.co_firstlineno,
                co_lnotab=code.co_lnotab,
                co_freevars=(),
                co_cellvars=(),
            )
        else:
            assert False

        tb.f_globals["exception"] = stack[i]
        func = FunctionType(code, tb.f_globals, tb.co_name)
        stack.append(func)

    try:
        stack[-1]()
    except ValueError:
        tb = sys.exc_info()[2]
        assert tb
        return tb.tb_next
