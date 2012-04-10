import unittest2 as unittest
import pytest; expectedFailure = pytest.mark.xfail

from ass.ets import filters
from ass import ets
from ass.ets import filters as f
import os



class InheritableOptionsTest(unittest.TestCase):
	def testRaisesUndefinedIfUndefined(self):
		assets = ets.Assets()

		try:
			assert assets.map_from == 'etc'
			self.fail('Should have raised undefined.')
		except ets.Undefined:
			pass

	def testReturnsValueIfPresent(self):
		assets = ets.Assets(map_from='etc')

		assert assets.map_from == 'etc'


	def testReturnsParentsValueIfNotPresentOnItself(self):
		assets = ets.Assets(map_from='etc')
		bundle = ets.Bundle(env=assets)

		assert bundle.map_from == 'etc'

	def testReturnsDefaultValueIfNotOverriden(self):
		assets = ets.Assets()

		assert assets.map_to == '/'

	def testSetsValuesOnInstantiation(self):
		bundle = ets.Bundle(map_from='etc')

		assert bundle.map_from == 'etc'

	def testDifferentBundlesHaveDifferentOptions(self):
		a = ets.Bundle(map_from='etc')
		b = ets.Bundle(map_from='pp')

		assert a.map_from == 'etc'
		assert b.map_from == 'pp'

	@expectedFailure
	def testStoreOptionUnderDifferentName(self):
		class Op(ets.Options):
			build = ets.Option(name='build_')

		o = Op(build='this')

		print o._options
		assert o.build_ == 'this'

class O(ets.Options):
	defaults=ets.Option(getter=ets.options.dict_getter)

class RecursiveDictGetterTest(unittest.TestCase):
	def testReturnsDictIfGiven(self):

		o = O(defaults={'a': 1})
		assert o.defaults == {'a': 1}

	def testReturnsParentsDictIfNotPresentOnItself(self):
		parent = O(defaults={'a': 1})
		o = O()
		o.parent = parent

		assert o.defaults == {'a': 1}

	def testReturnsMergedDictIfBothPresent(self):
		parent = O(defaults={'a': 1})
		o = O(defaults={'b' : 2})
		o.parent = parent

		assert o.defaults == {'a': 1, 'b': 2}

	def testMergeDictInDict(self):
		parent = O(defaults={'a': dict(x=1, y=1), 'b': dict(z=4)})
		o = O(defaults={'a' : dict(y=2), 'c': 'zero'})
		o.parent = parent

		assert o.defaults == {'a': dict(x=1, y=2), 'b': dict(z=4), 'c': 'zero'}

		


import StringIO
class StrIO(StringIO.StringIO):
	def __enter__(self):
		return self
	def __exit__(self, exc, value, tb):
		self.close()

class OptionsTest(unittest.TestCase):
	def testManifestOptionAcceptsFilename(self):
		assets = ets.Assets(map_from='/', manifest='file')
		assert isinstance(assets.manifest, ets.Manifest)


from pipeable import worker

class BundleTest(unittest.TestCase):
	def testGimmeUrlsAsIs(self):

		bundle = ets.Bundle(files=['a.js', 'b.js'], map_from='/assets', map_to='/static', 
						mode='development',
						development=ets.f.as_is)

		assert bundle.urls() == ['/static/a.js', '/static/b.js']

	def testGivesUrlsFromManifest(self):
		bundle = ets.Bundle(name='jslib', 
						files=['a.js', 'b.js'], 
						map_from='/assets', map_to='/static', 
						mode='development',
						manifest=dict(jslib=['generated.js']),
						development=ets.f.use_manifest)

		assert bundle.urls() == ['/static/generated.js']


	def testMergeFiles(self):
		import __builtin__, pickle
		from mockito import when, unstub

		a = os.path.join('/', 'a.js')
		b = os.path.join('/', 'b.js')
		when(__builtin__).open(a).thenReturn(StrIO('a'))
		when(__builtin__).open(b).thenReturn(StrIO('b'))

		bundle = ets.Bundle(files=['a.js', 'b.js'], map_from='/', map_to='/static', 
						development=[ets.f.read, ets.f.merge])
		
		assert bundle.apply('development') == ['ab']		

		unstub()

	def testContent(self):
		@worker
		def reverse(files, bundle):
			for file in files:
				yield file[::-1]

		import __builtin__, pickle
		from mockito import when, unstub

		a = os.path.join('/', 'a.js')
		b = os.path.join('/', 'b.js')
		when(__builtin__).open(a).thenReturn(StrIO('a'))
		when(__builtin__).open(b).thenReturn(StrIO('b'))

		bundle = ets.Bundle(files=['a.js', 'b.js'], map_from='/', map_to='/static', 
						development=[ets.f.read, ets.f.merge, reverse])
		
		assert bundle.apply('development') == ['ba']		

		unstub()	


	def testRealUglifyJsViaContent(self):
		import __builtin__, pickle
		from mockito import when, unstub


		bundle = ets.Bundle(files=['a.js'], map_from=os.path.dirname(__file__), map_to='/static', 
						development=[ets.f.read, ets.f.merge, ets.f.uglifyjs])
		
		assert bundle.apply('development') == ['var a=1;']		

		unstub()

	def testBuild(self):
		import __builtin__, pickle
		from mockito import when, unstub

		a1 = os.path.join(os.path.dirname(__file__), 'a1-43379278.js')
		
		bundle = ets.Bundle(files=['a.js'], map_from=os.path.dirname(__file__), map_to='/static', 
						mode='development',
						build_=[ets.f.read, ets.f.merge, 
									 ets.f.uglifyjs, 
									 ets.f.store_as('a1-%(version)s.js')]
							)
		
		assert bundle.build() == [a1]
		with open(a1) as f:
			assert f.read() == 'var a=1;'

		unstub()

	def testStoreManifest(self):
		manifest = dict()
		class MockedManifest(ets.Manifest):
			def __init__(self): pass
			def set(self, key, value):
				manifest[key] = value

		mocked_manifest = MockedManifest()
		bundle = ets.Bundle(name='jsall', files=['a.js'], 
						map_from=os.path.dirname(__file__), map_to='/static', 
						mode='development',
						manifest=mocked_manifest,
						development=[ets.f.store_manifest]
							)
		
		bundle.build('development')
		assert manifest['jsall'] == ['a.js']

	def testUrlsWithNestedBundles(self):

		nested_bundle = ets.Bundle(files=['a.js'],
						mode='development',
						development=[ets.f.echo]
						)
		bundle = ets.Bundle(files=[nested_bundle, 'b.js'], 
						map_to='/static',
						mode='development', 
						development=ets.f.as_is)

		assert bundle.urls() == ['/static/a.js', '/static/b.js']

	def testBuildWithNestedBundles(self):
		import __builtin__, pickle
		from mockito import when, unstub

		b = os.path.join('/', 'b.js')
		when(__builtin__).open(b).thenReturn(StrIO('b'))
		
		@worker
		def content(files, bundle):
			for a in files:
				assert a == 'a.js'
				yield 'a'

		@worker
		def store(contents, bundle):
			for content in contents:
				assert content == 'ab'
				yield 'ab.js'

		env = ets.Environment(mode='development', map_from='/')

		nested_bundle = ets.Bundle(files=['a.js'], env=env,
						development=[content])

		#keep in mind that build() expects a relative path at the end of the pipe
		bundle = ets.Bundle(files=[nested_bundle, 'b.js'], env=env,
						development=[ets.f.read, ets.f.merge, store])

		assert bundle.build('development') == [os.path.join('/', 'ab.js')]

		unstub()

	def testMixedBundle(self):
		from collections import defaultdict

		@worker
		def JS(i, bundle):
			for _ in i:
				yield 'JS'
		@worker
		def CSS(i, bundle):
			for _ in i:
				yield 'CSS'




		env = ets.Environment(mode='development', map_from='/',
							  filters={
							  	'js': {'development': [JS]}, 
							  	'css': {'development': [CSS]}
							  })
		bundle = ets.Bundle(files=['a.js', 'b.css'], env=env,
							development=[ets.f.automatic])

		assert bundle.apply() == ['JS', 'CSS']

class AssetsTest(unittest.TestCase):
	def testAssetsTakeBundlesKeyword(self):
		bundle = ets.Bundle()
		assets = ets.Assets(bundles={'app': bundle})

		assert assets.bundles.app == bundle

	def testAssetsAssignNameToBundleIfNoneIsGiven(self):
		bundle = ets.Bundle()
		assets = ets.Assets(bundles={'app': bundle})

		assert bundle.name == 'app'	

	def testAssignSelfToBundlesEnvIfNoneIsGiven(self):
		bundle = ets.Bundle()
		assets = ets.Assets(bundles={'app': bundle})

		assert bundle.env == assets

	def testIterateOverBundles(self):
		a = ets.Bundle()
		b = ets.Bundle()
		assets = ets.Assets(bundles={'app': a, 'lib': b})

		assert [a, b] == [bundle for bundle in assets.bundles]		

class FiltersTest(unittest.TestCase):
	def testLessify(self):

		less = '@base: #f938ab;p{color:@base;}'

		# lessify doesn't use any bundle-stuff
		# the output is actually beautified by lessc
		assert [less] | f.lessify(None) | list == ['p {\n  color: #f938ab;\n}\n']

	def testCssmin(self):

		css = 'p\n{color:#aaa;}'

		assert [css] | f.cssminify(None) | list == ['p{color:#aaa}']

