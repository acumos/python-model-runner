# -*- coding: utf-8 -*-
# ===============LICENSE_START=======================================================
# Acumos Apache-2.0
# ===================================================================================
# Copyright (C) 2020 Orange All rights reserved.
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
Provides tests for backward compatibility
'''
import os

import pytest

from runner_helper import ModelRunner

MODELS_DIR = os.path.join(os.path.dirname(__file__), "data", "backward_compatible_models")
MODELS = os.listdir(MODELS_DIR)


@pytest.fixture(params=MODELS)
def model(request):
    return os.path.join(MODELS_DIR, request.param)


def test_model_load(model):
    """Tests that the model can be loaded"""
    with ModelRunner(model) as _:
        pass


def test_model_exec(model):
    """Tests that the model can be used"""
    with ModelRunner(model) as runner:
        api = runner.api

    add_input = {'x': 1, 'y': 2}

    resp_json = api.method('add', json=add_input)
    assert int(resp_json['value']) == 3

    resp_proto = api.method('add', proto=add_input)
    assert resp_proto.value == 3


if __name__ == '__main__':
    '''Test area'''
    pytest.main([__file__, ])
