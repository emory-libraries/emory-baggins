#!/usr/bin/env python

import os
from setuptools import setup, find_packages
import baggins

LONG_DESCRIPTION = None
try:
    # read the description if it's there
    with open('README.md') as desc_f:
        LONG_DESCRIPTION = desc_f.read()
except:
    pass

CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: Apache Software License',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: System :: Archiving',
    'Topic :: Utilities'
]

requirements = [
    'eulxml',
    'requests',
    'pymarc',
    'bagit',
    'eulfedora',
    'pyyaml',
    'cached-property',
    'awesome-slugify',
]
dependency_links=[
        "git+ssh://git@github.com/mwilliamson/mayo.git@0.2.1#egg=mayo-0.2.1"
    ]

test_requirements = ['pytest', 'pytest-cov', 'mock']

setup(
    name='baggins',
    version=baggins.__version__,
    author='Emory University Libraries',
    author_email='libsysdev-l@listserv.cc.emory.edu',
    url='https://github.com/emory-libraries/emory-baggins',
    license='Apache License, Version 2.0',
    packages=find_packages(),
    install_requires=requirements,
    dependency_links=["git+ssh://git@github.com/LibraryOfCongress/bagit-python.git@master#egg=bagit"],
    setup_requires=['pytest-runner'],
    tests_require=test_requirements,
    extras_require={
        'test': test_requirements,
    },
    description='scripts and utilities for creating bagit archives of digital content',
    long_description=LONG_DESCRIPTION,
    classifiers=CLASSIFIERS,
    scripts=['scripts/lsdi-bagger'],
    package_data={'baggins': [
        "lsdi/content/*.*"
    ]}
)
