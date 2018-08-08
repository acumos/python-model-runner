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
'''
Provides a model runner based on a connexion application and gunicorn server
'''
import json
import argparse
from functools import partial
from os.path import join as path_join

from gunicorn.app.base import BaseApplication
from connexion import App
from connexion.resolver import Resolver
from flask import redirect
from acumos.wrapped import load_model

from acumos_model_runner.api import methods
from acumos_model_runner.oas_gen import create_oas


def run_app():
    '''CLI entry point for starting the model runner'''
    parser = argparse.ArgumentParser()
    parser.add_argument('model_dir', type=str, help='Directory containing a dumped Acumos Python model')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='The interface to bind to')
    parser.add_argument('--port', type=int, default=3330, help='The port to bind to')
    parser.add_argument('--workers', type=int, default=1, help='The number of gunicorn workers to spawn')
    parser.add_argument('--timeout', type=int, default=120, help='Time to wait (seconds) before a frozen worker is restarted')

    pargs = parser.parse_args()

    _write_oas(pargs.model_dir)
    StandaloneApplication(**vars(pargs)).run()


def _write_oas(model_dir):
    '''Writes an Open API specification file the model directory'''
    with open(path_join(model_dir, 'metadata.json')) as file:
        metadata = json.load(file)

    with open(path_join(model_dir, 'model.proto')) as file:
        proto = file.read()

    oas_yaml = create_oas(metadata, proto)
    with open(path_join(model_dir, 'oas.yaml'), 'w') as file:
        file.write(oas_yaml)


class StandaloneApplication(BaseApplication):
    '''Custom gunicorn app. Modified from http://docs.gunicorn.org/en/stable/custom.html'''

    def __init__(self, host, port, workers, timeout, model_dir):
        self.model_dir = model_dir
        self.options = {'bind': "{}:{}".format(host, port), 'workers': workers, 'timeout': timeout}
        super().__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in self.options.items()
                       if key in self.cfg.settings and value is not None])
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return _build_app(self.model_dir)


def _build_app(model_dir):
    '''Builds and returns a connexion app'''
    connexion_app = App('model_runner', specification_dir=model_dir)
    connexion_app.add_api('oas.yaml', resolver=_CustomResolver())

    flask_app = connexion_app.app
    flask_app.model = load_model(model_dir)
    flask_app.model_dir = model_dir

    @flask_app.route('/')
    def redirect_ui():
        return redirect('/ui')

    return flask_app


class _CustomResolver(Resolver):

    def resolve_function_from_operation_id(self, operation_id):
        '''Routes model methods to a generic handler so that methods can be enumerated in the OAS'''
        if operation_id.startswith('methods'):
            _, method_name = operation_id.split('.')
            return partial(methods, method_name=method_name)
        else:
            return super().resolve_function_from_operation_id(operation_id)