from useless.pipes import worker


@worker
def cssminify(files, bundle):
	import cssmin

	for file in files:
		yield cssmin.cssmin(file)

minify = cssminify

__all__ = ('cssminify', 'minify')