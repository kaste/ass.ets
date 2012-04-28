from ass.ets.workers import filter


@filter(accepts='contents', yields='contents')
def cssminify(files, bundle):
	import cssmin

	for file in files:
		yield cssmin.cssmin(file)

minify = cssminify

__all__ = ('cssminify', 'minify')