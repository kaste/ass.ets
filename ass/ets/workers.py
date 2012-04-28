# from useless.pipes import worker
import inspect 
from useless.pipes.pipes import Worker as _Worker
from functools import partial, wraps, update_wrapper

class Incompatible(Exception): pass

anything = '*'

class Worker(_Worker):
    def __ror__(self, left):
        try:
            accepts = self.accepts()
            yields  = left.yields()
            if accepts != anything and yields != anything and yields not in accepts:
                raise Incompatible('Incompatible left: %s to right: %s' % (yields, accepts))
        except AttributeError:
            pass

        return super(Worker, self).__ror__(left)

    def accepts(self, symbol=None):
        accepts = self.target.accepts #self.target.original_function.accepts
        return (symbol in accepts or accepts == anything) if symbol else accepts

    def yields(self, symbol=None):
        yields = self.target.yields #self.target.original_function.yields
        return (symbol in yields or yields == anything) if symbol else yields

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

def _worker(func, accepts=anything, yields=anything):
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

    bind.accepts = accepts
    bind.yields  = yields
    bind.original_function = func

    def decorate_with(f):
        bind.original_function = f(bind.original_function)
    bind.decorate_with = decorate_with

    return bind


def worker(func=None, accepts=anything, yields=anything):
    if func:
        return _worker(func)

    def wrap(f):
        return _worker(f, accepts, yields)

    return wrap   

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

