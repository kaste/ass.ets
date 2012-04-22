import os

from ass.ets import *
from ass.ets.filters import *

here = os.path.dirname( os.path.realpath(__file__) )

def add(filename):
	@worker
	def add_(_, bundle):
		for item in _:
			yield item

		yield filename

	return add_
		
env = Environment(
	map_from=os.path.join(here, 'static'),
	map_to='/static',
	manifest=os.path.join(here, 'assets-manifest')   # we don't want the manifest in the static dir
)

# Assets are container objects for bundles
assets = Assets(
	env=env,
	production=use_manifest,
	bundles=[
		Bundle(
			Bundle(
				"jquery.1.7.1.js", 
			    "underscore1.1.7.js", "underscore.string.js", 
			    name='jslib',
			    development=[read, merge, store_as('jslib.js')],
			    build_=read, #current implementation of read expects sub-bundles to yield their content
			),
			Bundle(
			    "templates/router.js", "templates/cache.js", #etc.
			    name='jsapp',
				map_from=here,
				map_to='',   # would like to have a "/" here
			    development=[read, merge, store_as('static/jsapp.js')],
			    build_=read,
			),
			name='generaljs',
			development=as_is,
		    build_=[read, merge, uglifyjs, store_as('general-%(version)s.js'), store_manifest],
		),
	]
)

# another way to define and assign an asset
assets.bundles.all_styles = Bundle(
	assets=[
		Bundle(
			'styles.less',
			development=[as_is, add('less-1.2.1.min.js')],
			build_=[read, merge, lessify]
		), 'main.css'],
	development=as_is,
	build_=[read, merge, minify, store_as('styles-%(version)s.css'), store_manifest]
)


