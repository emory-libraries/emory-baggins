baggins
=======

Python scripts and utilities for creating `bagit`_ archives of digital content

.. _bagit: https://en.wikipedia.org/wiki/BagIt

.. image:: https://travis-ci.org/emory-libraries/emory-baggins.svg?branch=develop
    :target: https://travis-ci.org/emory-libraries/emory-baggins
    :alt: Travis-CI build

.. image:: https://coveralls.io/repos/github/emory-libraries/emory-baggins/badge.svg?branch=develop
    :target: https://coveralls.io/github/emory-libraries/emory-baggins?branch=develop
    :alt: Code coverage

.. image:: https://landscape.io/github/emory-libraries/emory-baggins/develop/landscape.svg?style=flat
   :target: https://landscape.io/github/emory-libraries/emory-baggins/develop
   :alt: Code Health

Installation
------------

This python package and associated scripts can be installed from GitHub
using pip::

    pip install git+https://github.com/emory-libraries/emory-baggins.git#egg=baggins

To install a specific version by tag or branch, e.g. the current development
version, specify the tag or branch using `@tag`::

    pip install git+https://github.com/emory-libraries/emory-baggins.git@develop#egg=baggins


Developer Notes
---------------
This project uses `git-flow`_ branching conventions.

.. _git-flow: https://github.com/nvie/gitflow

To install dependencies for your local checkout of the code, run ``pip install``
in the project directory (the use of `virtualenv`_ is recommended)::

    pip install -e .

.. _virtualenv: http://www.virtualenv.org/en/latest/

Unit tests are written and run with `py.test`_. Install test dependencies::

    pip install -e ".[test]"

.. _py.test: http://docs.pytest.org/

Run unit tests: ``py.test`` or ``python setup.py test``

To run unit tests with output for continuous integration, use::

    py.test --cov=baggins --cov-report xml --junitxml=tests.xml

For development, you may also want to install ``pytest-sugar`` for prettier
test output.
