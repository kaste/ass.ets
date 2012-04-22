import unittest2 as unittest
import pytest; expectedFailure = pytest.mark.xfail

from ass.ets.workers import filter, Incompatible

class Symbol(object):
	pass

items = Symbol()
contents = Symbol()

# @ensure(items % contents)
@filter(yields='items')
def yields_items(items):
	for item in items:
		yield item

@filter(accepts='items')
def accepts_items(items):
	for item in items:
		yield item

@filter(accepts='contents')
def accepts_contents(contents):
	yield 'blub'

@filter()
def anything(items):
	for item in items:
		yield item

class EnsureInformalTypesTest(unittest.TestCase):
	def testIncomatible(self):
		try:
			assert [1,2] | yields_items() | accepts_contents() == ['blub']
			self.fail()
		except Incompatible:
			pass

	def testCompatible(self):
		try:
			assert [1,2] | yields_items() | accepts_items() == [1,2]
		except:
			raise
			# self.fail()

	def testUnspecifiedMeansAnything(self):
		try:
			assert [1,2] | anything() | anything() == [1,2]
		except:
			raise
			# self.fail()

	def testAccessOriginalFunc(self):
		def origin(items):
			for i in items: yield i

		wrapped = filter(origin)

		assert wrapped.original_function == origin

	def testFurtherDecorate(self):
		@filter
		def origin(items):
			for i in items: yield i

		state = [1]
		def decorator(f):
			def decorated(i, *a, **kw):
				state.append(2)
				return f(i, *a, **kw)
			return decorated

		origin.decorate_with(decorator)

		assert [1,2] | origin() == [1,2]
		assert state == [1, 2]






