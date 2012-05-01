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
		
# An Environment is a configuration object. All bundles connected to this environment
# actually inherit all its options, but can override anything at their will.
env = Environment(
	map_from=os.path.join(here, 'static'),
	map_to='/static',

	# a 'manifest' is just a dict stored on disc
	manifest=os.path.join(here, 'assets-manifest.yaml')   # we don't want the manifest in the static dir
													      # so we provide a full path
													      # by default stores a .yaml file if yaml is available
													      # otherwise just pickles.
)			

# a filter chain we use below
merge_and_store = [read, merge, store]

# Assets are container objects for bundles
# We connect the environment once and all nested bundles inherit this setting,
# unless you speciyfy a different env or None
assets = Assets(
	env=env,
	production=use_manifest,
	bundles=[
		Bundle(
			Bundle(
				"jquery.1.7.1.js", 
			    "underscore1.1.7.js", "underscore.string.js", 
			    name='jslib',
			    output='jslib.js',
			    development=merge_and_store,
			    build_=read, # current implementation of read expects sub-bundles to yield their content
			    			 # this read here correspondents to the read on the parent bundle's built_ chain 
			),
			Bundle(
			    "templates/router.js", "templates/cache.js", #etc.
			    name='jsapp',
				map_from=here,
				map_to='/',   
				output='static/jsapp.js',
			    development=merge_and_store,
			    build_=read,
			),
			name='generaljs',
			development=as_is,
		    build_=[read, merge, uglifyjs, store_as('general-%(version)s.js'), store_manifest],
		),
	]
)
# now on assets.bundles.generaljs we have a bundle that yields two files during development, 
# but one uglified, versioned file 'general-78ghdfe.js' on the server
# you need to build at least once to get this file and the manifest 

# another way to define and assign an asset
# this way the name is automatically set to 'all_styles'
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
# all_styles yields three files during development: styles.less, less-1.2.1.min.js and main.css
# and one minified, versioned file styles-zhg67.css on the server


