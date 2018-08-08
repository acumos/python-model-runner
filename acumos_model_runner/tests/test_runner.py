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
Provides tests for the model runner
'''
import os
import contextlib
from tempfile import TemporaryDirectory
from collections import Counter

import pytest
from requests import HTTPError
from acumos.session import AcumosSession
from acumos.modeling import Model, List, Dict

from acumos_model_runner.api import _JSON

from runner_helper import ModelRunner


@contextlib.contextmanager
def _run_model(model, model_name='test-model'):
    '''Dumps and runs a model, and returns an api object'''
    with TemporaryDirectory() as dump_dir:
        session = AcumosSession()
        session.dump(model, model_name, dump_dir)

        model_dir = os.path.join(dump_dir, model_name)
        with ModelRunner(model_dir) as runner:
            yield runner.api


def test_runner():
    '''Tests model runner basic usage'''

    def add(x: int, y: int) -> int:
        '''Adds two numbers'''
        return x + y

    def count(strings: List[str]) -> Dict[str, int]:
        return Counter(strings)

    model = Model(add=add, count=count)

    with _run_model(model) as api:

        # =============================================================================
        # verify artifact APIs don't raise
        # =============================================================================

        api.protobuf()
        api.metadata()

        # =============================================================================
        # add test
        # =============================================================================

        add_input = {'x': 1, 'y': 2}

        resp_json = api.method('add', json=add_input)
        assert int(resp_json['value']) == 3

        resp_proto = api.method('add', proto=add_input)
        assert resp_proto.value == 3

        # =============================================================================
        # count test
        # =============================================================================

        count_input = {'strings': ['a'] * 3 + ['b'] * 2 + ['c']}
        count_output = {'a': 3, 'b': 2, 'c': 1}

        resp_json = api.method('count', json=count_input)
        assert {k: int(v) for k, v in resp_json['value'].items()} == count_output

        resp_proto = api.method('count', proto=count_input)
        assert dict(resp_proto.value.items()) == count_output

        # =============================================================================
        # headers test
        # =============================================================================

        try:
            api.method('add', json=add_input, headers={})
        except HTTPError as err:
            assert err.response.status_code == 400

        try:
            api.method('add', json=add_input, headers={'Content-Type': _JSON, 'Accept': 'invalid'})
        except HTTPError as err:
            assert err.response.status_code == 415


if __name__ == '__main__':
    '''Test area'''
    pytest.main([__file__, ])
