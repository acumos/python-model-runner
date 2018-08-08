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
Provides tests for protobuf parsing
'''
import pytest

from acumos_model_runner.proto_parser import Message, RepeatedField, MapField, Enum, Field, parse_proto

from testing_utils import load_testing_data


def test_proto_parser():
    '''Tests correct parsing of protobuf'''
    proto = load_testing_data('sample.proto')
    top_level = parse_proto(proto)

    msg_a = Message(name='MessageA', fields=[Field(type='string', name='x', number=1), Field(type='int32', name='y', number=2)], messages=[], enums=[])
    msg_b = Message(name='MessageB', fields=[RepeatedField(type='string', name='texts', number=1), MapField(key_type='string', val_type='int32', name='counter', number=2)], messages=[], enums=[])
    msg_inner = Message(name='Inner', fields=[Field(type='int32', name='x', number=1)], messages=[], enums=[])
    msg_outer = Message(name='Outer', fields=[Field(type='Inner', name='inner', number=1)], messages=[msg_inner], enums=[])
    enum_a = Enum(name='EnumA', enums=['x', 'y', 'z'])

    assert top_level == [msg_a, msg_b, msg_outer, enum_a]


if __name__ == '__main__':
    '''Test area'''
    pytest.main([__file__, ])
