# -*- coding: utf-8 -*-
#quckstarted Options:
#
# sqlalchemy: True
# auth:       sqlalchemy
# mako:       False
#
#

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
    "TurboGears2 >= 2.1.4",
    "Genshi",
    "zope.sqlalchemy >= 0.4",
    "repoze.tm2 >= 1.0a5",
    "sqlalchemy",
    "sqlalchemy-migrate",
    "repoze.what >= 1.0.8",
    "repoze.who-friendlyform >= 1.0.4",
    "repoze.what-pylons >= 1.0",
    "repoze.who==1.0.19",
    "tgext.admin >= 0.3.11",
    "repoze.what-quickstart",
    "repoze.what.plugins.sql>=1.0.1",
    "tw.forms",
    "tw.jquery",
    "tw.jqgrid",
    "pygraphviz",
    "tgext.menu",
    "tgscheduler",
    "BeautifulSoup",
        ]

if sys.version_info[:2] == (2,4):
    testpkgs.extend(['hashlib', 'pysqlite'])
    install_requires.extend(['hashlib', 'pysqlite'])

print install_requires

setup(
    name='astportal2',
    version='20141007',
    description='Asterisk Portal',
    author='Jean-Denis Girard',
    author_email='jd.girard@sysnux.pf',
    #url='',
    setup_requires=["PasteScript >= 1.7"],
    paster_plugins=['PasteScript', 'Pylons', 'TurboGears2', 'tg.devtools'],
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
            ('templates/**.mako', 'mako', None),
            ('templates/**.html', 'genshi', None),
            ('public/**', 'ignore', None)]},

    entry_points="""
    [paste.app_factory]
    main = astportal2.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller

    """,
    dependency_links=[
        "http://www.turbogears.org/2.1/downloads/current/"
        ],
    zip_safe=False
)
