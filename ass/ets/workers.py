# from useless.pipes import worker
import inspect 
from useless.pipes.pipes import Worker as _Worker

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
        accepts = self.target.original_function.accepts
        return (symbol in accepts or accepts == anything) if symbol else accepts

    def yields(self, symbol=None):
        yields = self.target.original_function.yields
        return (symbol in yields or yields == anything) if symbol else yields

    @property
    def __doc__(self):
        return self.target.__doc__

    @property
    def __name__(self):
        return self.target.__name__
    
def _worker(func, accepts=anything, yields=anything):
    spec = inspect.getargspec(func)
    args_with_defaults = spec.defaults and len(spec.defaults) or 0
    kw_args = spec.args[args_with_defaults:]
    possible_one_step = len(spec.args) == 1

    bound_kw = {}
    def bind(*a, **kw):
        # trigger three step process if kw has only keyword arguments
        # in python we can def f(a, b=1) => f(a=1, b=2)
        # t.i. a positional arg can be treated as if it were a kw argument
        # but this shouldn't trigger three-step, only e.g. f(b=2)
        if kw and not a and set(kw_args).difference(kw):
            bound_kw.update(kw)
            return bind

        kw.update(bound_kw)
        def apply(iter):
            return apply.original_function(iter, *a, **kw)

        apply.original_function = bind.original_function
        apply.__name__ = func.__name__
        apply.__doc__ = func.__doc__
        return Worker(apply)

    bind.accepts = func.accepts = accepts 
    bind.yields  = func.yields  = yields 
    bind.original_function = func
    bind.__name__ = func.__name__
    bind.__doc__ = func.__doc__

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

