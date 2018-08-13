# -*- coding: utf-8 -*-
# ===============LICENSE_START=======================================================
# Acumos Apache-2.0
# ===================================================================================
# Copyright (C) 2017-2018 AT&T Intellectual Property & Tech Mahindra. All rights reserved.
# ===================================================================================
# This Acumos software file is distributed by AT&T and Tech Mahindra
# under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============LICENSE_END=========================================================
from os.path import dirname, abspath, join as path_join
from setuptools import setup, find_packages


SETUP_DIR = abspath(dirname(__file__))
DOCS_DIR = path_join(SETUP_DIR, 'docs')

with open(path_join(SETUP_DIR, 'acumos_model_runner', '_version.py')) as file:
    globals_dict = dict()
    exec(file.read(), globals_dict)
    __version__ = globals_dict['__version__']


def _long_descr():
    '''Yields the content of documentation files for the long description'''
    for file in ('user-guide.rst', path_join('tutorial', 'index.rst'), 'release-notes.rst', 'developer-guide.rst'):
        doc_path = path_join(DOCS_DIR, file)
        with open(doc_path) as f:
            yield f.read()


setup(
    author='Paul Triantafyllou, Eric Zavesky',
    author_email='trianta@research.att.com, ezavesky@research.att.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: Apache Software License',
    ],
    description='Acumos model runner for Python models',
    entry_points="""
    [console_scripts]
    acumos_model_runner=acumos_model_runner.runner:run_app_cli
    """,
    install_requires=['acumos>=0.5.3',
                      'lark-parser',
                      'connexion<2.0.0',
                      'gunicorn',
                      'pyyaml',
                      'jinja2',
                      'protobuf',
                      'flask-cors',
                      'swagger_ui_bundle'],
    keywords='acumos machine learning model runner server protobuf ml ai',
    license='Apache License 2.0',
    long_description='\n'.join(_long_descr()),
    name='acumos_model_runner',
    packages=find_packages(),
    package_data={'acumos_model_runner': [path_join('data', 'proto3.ebnf'),
                                          path_join('data', 'templates', '*.yaml')]},
    python_requires='>=3.4',
    url='https://gerrit.acumos.org/r/gitweb?p=python-model-runner.git',
    version=__version__,
)
