# -*- coding: utf-8 -*-
"""
TIPTOP-ipy: A python wrapper for the ESO TIPTOP AO PSF generator microservice

How to compile and put these on pip::

    $ python setup.py sdist bdist_wheel
    $ twine upload dist/*

"""
from setuptools import setup, find_packages

with open('README.md') as f:
    __readme__ = f.read()

with open('LICENSE') as f:
    __license__ = f.read()

with open('tiptop_ipy/version.py') as f:
    __version__ = f.readline().split("'")[1]


print(__version__)


def setup_package():
    setup(
        name='tiptop_ipy',
        version=__version__,
        description='A python wrapper for the ESO TIPTOP AO PSF generator microserice',
        long_description=__readme__,
        long_description_content_type="text/markdown",
        author='The TIPTOP team, wrapped by Kieran Leschinski and Martin Baláž',
        author_email='kieran.leschinski@univie.ac.at',
        url='https://github.com/astronomyk/tiptop_ipy',
        license="GNU General Public License v3 (GPLv3)",
        include_package_data=True,
        packages=find_packages(exclude=('tests', 'docs')),
        package_dir={'tiptop_ipy': 'tiptop_ipy'},
        install_requires=['numpy', 'astropy', 'matplotlib', 'yaml', 'requests', 'requests_toolbelt'],
        classifiers=["Programming Language :: Python :: 3",
                     "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
                     "Operating System :: OS Independent",
                     "Intended Audience :: Science/Research",
                     "Topic :: Scientific/Engineering :: Astronomy",
        ]
    )


if __name__ == '__main__':
    setup_package()
