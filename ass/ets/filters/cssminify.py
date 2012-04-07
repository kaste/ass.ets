from pipeable import worker

import cssmin

@worker
def cssminify(files, bundle):

	for file in files:
		yield cssmin.cssmin(file)

minify = cssminify

__all__ = ('cssminify', 'minify')