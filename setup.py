__version__ = "0.0.1"
from setuptools import setup, find_packages

setup(
	name='ass.ets',
	version=__version__,
	description='Asset management for Python.',
	long_description='',
	author="herr kaste",
	author_email="herr.kaste@gmail.com",
	packages=find_packages(exclude=['tests']),
	install_requires=[],
	tests_require=['pytest', 'unittest2'],
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