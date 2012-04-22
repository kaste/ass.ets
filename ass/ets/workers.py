# from useless.pipes import worker
from useless.pipes.pipes import Worker as _Worker

class Incompatible(Exception): pass

class Worker(_Worker):
    def __ror__(self, left):
        try:
            accepts = self.target.original_function.accepts
            yields  = left.target.original_function.yields
            if not accepts.intersection(yields):
                raise Incompatible('Incompatible left: %s to right: %s' % (yields, accepts))
        except AttributeError:
            pass

        return super(Worker, self).__ror__(left)
    
def _worker(func, accepts='*', yields='*'):
    def bind(*a, **kw):
        def apply(iter):
            return apply.original_function(iter, *a, **kw)
            
        apply.original_function = bind.original_function
        apply.__name__ = func.__name__
        return Worker(apply)

    func.accepts = set(accepts.split())
    func.yields  = set(yields.split())
    bind.original_function = func

    def decorate_with(f):
        bind.original_function = f(bind.original_function)
    bind.decorate_with = decorate_with

    return bind


def worker(func=None, accepts='*', yields='*'):
    if func:
        return _worker(func)

    def wrap(f):
        return _worker(f, accepts, yields)

    return wrap   

filter = worker


