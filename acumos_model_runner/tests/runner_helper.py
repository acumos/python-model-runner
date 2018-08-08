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
"""
Provides a model runner helper utility
"""
import json
import os
import pexpect
import socket
from collections import namedtuple

import requests
from requests import ConnectionError
from acumos.wrapped import load_model

from acumos_model_runner.api import _PROTO, _JSON

_EXPECT_RE = r'^.*(Booting worker with pid).*$'


class Api(object):

    def __init__(self, config, model_dir):
        '''Helper class that invokes the model runner's APIs'''
        self._config = config
        self._model = load_model(model_dir)

    def method(self, method_name, json=None, proto=None, headers=None):
        '''Invokes a model method with data'''
        if json is not None:
            return self._post_json(method_name, json, headers)
        elif proto is not None:
            return self._post_proto(method_name, proto, headers)
        else:
            raise Exception('Must provide data for either json or protobuf')

    def _post_json(self, method_name, data, headers):
        '''Invokes a model method with json data'''
        headers = {'Content-Type': _JSON, 'Accept': _JSON} if headers is None else headers
        resp_data = self._post(method_name, json.dumps(data), headers)
        return json.loads(resp_data.decode())

    def _post_proto(self, method_name, data, headers):
        '''Invokes a model method with protobuf data'''
        method = self._model.methods[method_name]
        pb_input = method.pb_input_type(**data)

        headers = {'Content-Type': _PROTO, 'Accept': _PROTO} if headers is None else headers
        resp_data = self._post(method_name, pb_input.SerializeToString(), headers)

        pb_output = method.pb_output_type()
        pb_output.ParseFromString(resp_data)
        return pb_output

    def _post(self, method_name, data, headers):
        '''POSTs to a model method with data'''
        path = "/model/methods/{}".format(method_name)
        resp = requests.post(self._full_url(path), data=data, headers=headers)
        resp.raise_for_status()
        return resp.content

    def protobuf(self):
        '''Returns a model's protobuf str'''
        return self._get('/model/artifacts/protobuf')

    def metadata(self):
        '''Returns a model's metadata json str'''
        return self._get('/model/artifacts/metadata')

    def _get(self, path):
        '''GETs a model's resource'''
        resp = requests.get(self._full_url(path))
        resp.raise_for_status()
        return resp.text

    def _full_url(self, path):
        '''Creates a full URL given a path'''
        return "{}{}".format(self._config.base_url, path)


class ModelRunner(object):

    def __init__(self, model_dir, timeout=5, port=None):
        '''Invokes the model runner CLI in a separate process'''
        self._timeout = timeout
        self._child = None

        port = _find_port() if port is None else port
        config = _Config.from_port(port)
        self.api = Api(config, model_dir)
        self._config = config

        cmd = ['acumos_model_runner', model_dir, '--port', port]
        self._cmd = ' '.join(map(str, cmd))

    def __enter__(self):
        '''Spawns the child process and waits for server to start until `timeout`'''
        assert not _server_running(self._config.ui_url), 'A mock server is already running'
        self._child = pexpect.spawn(self._cmd, env=os.environ)
        self._child.expect(_EXPECT_RE, timeout=self._timeout)
        return self

    def __exit__(self, type, value, tb):
        '''Interrupts the server and cleans up'''
        if self._child is not None:
            self._child.sendintr()


def _find_port():
    '''Returns an open port number'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class _Config(namedtuple('_Config', ['base_url', 'ui_url', 'port'])):
    '''Configuration for ModelRunner'''

    @classmethod
    def from_port(cls, port):
        base_url = "http://localhost:{}".format(port)
        ui_url = "{}/ui".format(base_url)
        return cls(base_url, ui_url, port)


def _server_running(ui_url):
    '''Returns False if test server is not available'''
    try:
        requests.get(ui_url)
    except ConnectionError:
        return False
    else:
        return True
