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
Provides tests for OAS generation
'''
import json

import pytest

from acumos_model_runner.proto_parser import parse_proto
from acumos_model_runner.oas_gen import _create_definitions

from testing_utils import load_testing_data


def test_oas_defs():
    '''Tests correct generation of oas definitions'''
    proto = load_testing_data('sample.proto')
    top_level = parse_proto(proto)
    oas_defs = _create_definitions(top_level)
    assert oas_defs == load_testing_data('sample.json', loader=json.load)


if __name__ == '__main__':
    '''Test area'''
    pytest.main([__file__, ])
