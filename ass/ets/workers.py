# from useless.pipes import worker
import inspect 
from useless.pipes.pipes import Worker as _Worker
from functools import partial, wraps, update_wrapper

class Incompatible(Exception): pass

anything = '*'

class Worker(_Worker):
    def __ror__(self, left):
        try:
            yields = left.yields()
            if not all( (self.accepts(symbol) for symbol in yields.split()) ):
                raise Incompatible('Incompatible left: %s to right: %s' % (yields, self.accepts()))
        except AttributeError:
            pass

        return super(Worker, self).__ror__(left)

    def accepts(self, symbol=None):
        return self.target.accepts(symbol)

    def yields(self, symbol=None):
        return self.target.yields(symbol)

    @property
    def __doc__(self):
        return self.target.__doc__

    @property
    def __name__(self):
        return self.target.__name__
    
def _get_kw_arguments(func):
    spec = inspect.getargspec(func)
    args_with_defaults = spec.defaults and len(spec.defaults) or 0
    return spec.args[-(args_with_defaults):]

def _worker(func):
    kw_args = _get_kw_arguments(func)

    @wraps(func)
    def bind(*a, **kw):
        # trigger three step process if kw has only keyword arguments
        # in python we can def f(a, b=1) => f(a=1, b=2)
        # t.i. a positional arg can be treated as if it were a kw argument
        # but this shouldn't trigger three-step, only e.g. f(b=2)
        if kw and not a and not set(kw).difference(kw_args):
            return wraps(bind) (partial(bind, *a, **kw))

        @wraps(bind)
        def apply(iter):
            return apply.original_function(iter, *a, **kw)

        return Worker(apply)

    bind.original_function = func

    def decorate_with(f):
        bind.original_function = f(bind.original_function)
    bind.decorate_with = decorate_with

    return bind


def worker(func=None, accepts=anything, yields=anything):
    def _accepts(symbol=None):
        return (symbol in accepts or anything in [accepts, symbol]) if symbol else accepts
    def _yields(symbol=None):
        return (symbol in yields or yields == anything) if symbol else yields

    if func:
        func.accepts = _accepts
        func.yields = _yields
        return _worker(func)


    @wraps(worker)
    def wrapped(f):
        return worker(f, accepts, yields)

    return wrapped   

filter = worker

def discover_filters(module):
    """Helper for the usual

            __all__ = discover_filters(globals())
        
    """
    return [symbol for symbol, code in module.iteritems() if getattr(code, 'original_function', False)]

class Pipe(list):
    def __init__(self, seq):
        if not hasattr(seq, '__iter__'):
            seq = [seq]

        list.__init__(self, seq)

    def accepts(self, symbol=None):
        accepts = self[0].accepts
        return symbol in accepts if symbol else accepts

    def yields(self, symbol=None):
        yields = self[-1].yields
        return symbol in yields if symbol else yields

    def prepend(self, worker):
        self.insert(0, worker)

    def apply(self, iter, *a, **kw):
        p = iter
        for worker in self:
            p |= worker(*a, **kw)

        return p

