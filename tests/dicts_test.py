import unittest2 as unittest
import pytest; expectedFailure = pytest.mark.xfail

from ass.ets import Bundle
from ass.ets.dicts import dotted, ordered

class dotor(ordered, dotted): pass

class NaiveDictsTest(unittest.TestCase):
	def tests(self):
		l = dotor({'a': 1})
		assert l.a == 1


		l = dotor({})
		l.b = 2
		assert l['b'] == 2


		l = dotor({'a': 1})
		assert l['a'] == 1


		l = dotor()
		l['b'] = 2

		assert l.b == 2


		l = dotor()
		l.a = 1
		l.a = 2

		assert l.a == 2


		l = dotor()
		l.b = 2
		l.a = 1

		assert [2, 1] == list(l.itervalues())


		l = dotor()
		l.b = 2
		l.a = 1
		l.c = 3

		del l.a
		
		assert [2, 3] == list(l.itervalues())


		l = dotor()
		l.b = 2
		l.a = 1
		l.c = 3

		l.a = 5

		assert [2, 5, 3] == list(l.itervalues())

