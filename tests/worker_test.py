import unittest2 as unittest
import pytest; expectedFailure = pytest.mark.xfail

# from pipeable import worker
from pipeable.pipes import Worker as _Worker

class Incompatible(Exception): pass

class Worker(_Worker):
    def __ror__(self, left):
    	try:
    		# print 'L', left.target.wrapped_func
    		(lin, lout) = left.target.wrapped_func.ensure
    		(rin, rout) = self.target.wrapped_func.ensure
    		# print '++', lout, rin
    		if lout and rin and lout not in rin:
    			raise Incompatible('Incompatible left: %s to right: %s' % (lout, rin))
    	except AttributeError:
    		pass

    	return super(Worker, self).__ror__(left)
    
def _worker(func):
    def wrapper(*a, **kw):
        def f(iter):
            return func(iter, *a, **kw)
        f.wrapped_func = func
        f.__name__ = func.__name__
        return Worker(f)
    
    return wrapper


def worker(func=None,accept=None, spits=None):
	if func:
		return _worker(func)

	# if accept is None and spits is None:
	#     def wrapper(*a, **kw):
	#         def f(iter):
	#             return func(iter, *a, **kw)
	#         f.wrapped_func = func
	#         f.__name__ = func.__name__  + 'WRAPPED'
	#         return Worker(f)
	    
	#     return wrapper

	def wrap(f):
		f.ensure = (accept, spits)
		return _worker(f)

	return wrap   

def ensure(in_=None, out=None):

	def wrapp(f):
		f.ensure = (in_, out)
		return f

	return wrapp

declare = ensure


class Symbol(object):
	pass

items = Symbol()
contents = Symbol()

# @ensure(items % contents)
@worker(accept='items', spits='items')
# @ensure(in_='items', out='items')
def echo(items):
	for item in items:
		yield item

@worker(accept='contents')
# @ensure(in_='contents')
def failing(contents):
	yield 'blub'

class EnsureTest(unittest.TestCase):
	def testEnsure(self):

		print echo
		# print echo.ensure
		w = echo()
		try:
			assert [1,2] | w | w | failing() == ['blub']
			self.fail()
		except Incompatible,e :
			print e

		print repr(w)
		print w.target
		print w.target.ensure


		assert False
		pass