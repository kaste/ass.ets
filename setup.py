__version__ = "0.0.3"
import os
from setuptools import setup, find_packages

def _read_contents(fn):
	here = os.path.dirname( os.path.realpath(__file__) )
	filename = os.path.join(here, fn)
	with open(filename) as file:
		return file.read()

setup(
	name='ass.ets',
	version=__version__,
	description='Asset management for webapps.',
	long_description=_read_contents('README'),
	author="herr kaste",
	author_email="herr.kaste@gmail.com",
	url='http://github.com/kaste/ass.ets',
	download_url='http://github.com/kaste/ass.ets/tarball/master',
	packages=find_packages(exclude=['tests']),
	install_requires=['useless.pipes'],
	tests_require=['pytest', 'unittest2', 'cssmin'],
	classifiers= [
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries',
        ],
)