# -*- coding: utf-8 -*-
#quckstarted Options:
#
# sqlalchemy: True
# auth:       sqlalchemy
# mako:       False
#
#

#This is just a work-around for a Python2.7 issue causing
#interpreter crash at exit when trying to log an info message.
try:
    import logging
    import multiprocessing
except:
    pass

import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

testpkgs=['WebTest >= 1.2.3',
               'nose',
               'coverage',
               'wsgiref',
               'repoze.who-testutil >= 1.0.1',
               ]
install_requires=[
    'python-dateutil>=1.5,<2.0dev',
    "TurboGears2 >= 2.3.4",
    "Genshi",
    "Mako",
    "zope.sqlalchemy >= 0.4",
    "sqlalchemy",
    "repoze.who",
    "tw.forms",
#    "tgext.admin >= 0.6.1",
    "tw.jquery",
    "tw.jqgrid",
    "pygraphviz",
    "tgext.menu",
    "tgscheduler",
    "BeautifulSoup",
    'WebHelpers',
    'psycopg2',
    'vobject',
    'gevent',
    'ws4py',
    'wsaccel',
        ]

if sys.version_info[:2] == (2,4):
    testpkgs.extend(['hashlib', 'pysqlite'])
    install_requires.extend(['hashlib', 'pysqlite'])

print install_requires

setup(
    name='astportal2',
    version='20141031',
    description='Asterisk Portal',
    author='Jean-Denis Girard',
    author_email='jd.girard@sysnux.pf',
    #url='',

    packages=find_packages(exclude=['ez_setup']),
    install_requires=install_requires,
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=testpkgs,
    package_data={'astportal2': ['i18n/*/LC_MESSAGES/*.mo',
                                 'templates/*/*',
                                 'public/*/*']},
    message_extractors={'astportal2': [
            ('**.py', 'python', None),
            ('templates/**.html', 'genshi', None),
            ('public/**', 'ignore', None)]},

    entry_points={
        'paste.app_factory': [
            'main = astportal2.config.middleware:make_app'
        ],
        'paste.server_runner': [
            'ws4py = astportal2.lib.server:serve'
        ],
        'gearbox.plugins': [
            'turbogears-devtools = tg.devtools'
        ]
    },
    zip_safe=False
)

