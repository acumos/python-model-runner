#!/usr/bin/env python3
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
Provides an example of how to chain Acumos models
'''
from collections import Counter

import requests
import pexpect
from acumos.session import AcumosSession
from acumos.modeling import Model, List, Dict


_JSON = 'application/json'


class Runner(object):
    _HEADERS = {'Accept': _JSON, 'Content-Type': _JSON}

    def __init__(self, model_dir, port, host='localhost'):
        '''Helper class for managing model runners'''
        self.model_dir = model_dir
        self.base_url = "http://{}:{}".format(host, port)
        self.chains = dict()

        cmd = "acumos_model_runner --host {} --port {} {}".format(host, port, model_dir)
        self.proc = pexpect.spawn(cmd)
        self.proc.expect(r'^.*(Booting worker with pid).*$', timeout=5)

    def create_chain(self, chain_name, upstream_method, downstream_runner, downstream_method):
        '''Creates a chain that invokes a downstream runner with the response of the upstream runner'''
        self.chains[chain_name] = (upstream_method, downstream_runner, downstream_method)

    def call(self, method, data):
        '''Calls a model method with JSON data. If `method` is a chain, returns the downstream response'''
        if method in self.chains:
            upstream_method, downstream_runner, downstream_method = self.chains[method]
            resp_up = requests.post(self._full_url(upstream_method), json=data, headers=self._HEADERS).json()
            resp = downstream_runner.call(downstream_method, resp_up)
        else:
            resp = requests.post(self._full_url(method), json=data, headers=self._HEADERS).json()
        return resp

    def _full_url(self, method):
        '''Returns a full url given a method name'''
        return "{}/model/methods/{}".format(self.base_url, method)


if __name__ == '__main__':
    '''Test area'''

    def tokenize(value: str) -> List[str]:
        '''Segments text into tokens'''
        return value.split()

    def count(value: List[str]) -> Dict[str, int]:
        '''Returns a count of tokens'''
        return Counter(value)

    # define models
    tokenizer = Model(tokenize=tokenize)
    counter = Model(count=count)

    # save models
    session = AcumosSession()
    session.dump(tokenizer, 'tokenizer', '.')
    session.dump(counter, 'counter', '.')

    # instantiate runners
    runner1 = Runner('tokenizer', 3330)
    runner2 = Runner('counter', 3331)

    # call individual methods
    runner1.call('tokenize', {'value': 'hello world'})                  # {'value': ['hello', 'world']}
    runner2.call('count', {'value': ['hello', 'world']})                # {'value': {'hello': 1, 'world': 1}}

    # create and call chain
    runner1.create_chain('count_tokens', 'tokenize', runner2, 'count')
    runner1.call('count_tokens', {'value': 'hello world'})              # {'value': {'world': 1, 'hello': 1}}

    runner1.proc.terminate()
    runner2.proc.terminate()
