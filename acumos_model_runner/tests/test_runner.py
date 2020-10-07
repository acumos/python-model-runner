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
import json
import os
import contextlib
from tempfile import TemporaryDirectory
from collections import Counter

import pytest
import requests
from acumos.session import AcumosSession
from acumos.modeling import Model, List, Dict, new_type

from acumos_model_runner.api import _JSON, _PROTO, _TEXT, _OCTET_STREAM

from runner_helper import ModelRunner


@contextlib.contextmanager
def _dumped_model(model: Model, model_name: str = 'test-model') -> str:
    """Dumps a model an returns its path"""
    with TemporaryDirectory() as dump_dir:
        session = AcumosSession()
        session.dump(model, model_name, dump_dir)

        model_dir = os.path.join(dump_dir, model_name)
        yield model_dir


@contextlib.contextmanager
def _run_model(model, model_name='test-model', options=None):
    '''Dumps and runs a model, and returns an api object'''
    with _dumped_model(model=model, model_name=model_name) as model_dir:
        with ModelRunner(model_dir, options=options) as runner:
            yield runner


@pytest.fixture(scope="session")
def model():
    '''Returns a simple test model'''
    def add(x: int, y: int) -> int:
        '''Adds two numbers'''
        return x + y

    def count(strings: List[str]) -> Dict[str, int]:
        return Counter(strings)

    def empty() -> int:
        return 1

    Image = new_type(raw_type=bytes, name="Image", metadata={"test": "this is a test"})

    def rotate_image(img: Image) -> Image:
        return img

    Dictionary = new_type(raw_type=dict, name="Dictionary", metadata={"test": "this is a test"})

    def handle_dict(_dict: Dictionary) -> Dictionary:
        return _dict

    Text = new_type(str, 'Text')

    def count_words(text: Text) -> int:
        '''Counts the number of words in the text'''
        return len(text.split(u' '))

    def create_words(n: int) -> Text:
        return " ".join(["éééé"] * n)

    model = Model(add=add, count=count, empty=empty, rotate_image=rotate_image, handle_dict=handle_dict, count_words=count_words, create_words=create_words)
    return model


@pytest.fixture(scope="session")
def model_oas(model):
    from yaml import load
    from acumos_model_runner.runner import _write_oas
    with _dumped_model(model) as model_dir:
        _write_oas(model_dir)
        with open(os.path.join(model_dir, "oas.yaml"), "r") as oas_file:
            oas = load(oas_file)
    return oas


def test_create_oas_add(model_oas):
    add_definition = model_oas["paths"]["/model/methods/add"]["post"]
    assert add_definition["parameters"][0].items() >= {"in": "body", "schema": {"$ref": '#/definitions/Model.AddIn'}}.items()
    assert add_definition["responses"][200].items() >= {"schema": {"$ref": '#/definitions/Model.AddOut'}}.items()
    assert add_definition["consumes"] == add_definition["produces"] == [_JSON, _PROTO]


def test_create_oas_count(model_oas):
    count_definition = model_oas["paths"]["/model/methods/count"]["post"]
    assert count_definition["parameters"][0].items() >= {"in": "body", "schema": {"$ref": '#/definitions/Model.CountIn'}}.items()
    assert count_definition["responses"][200].items() >= {"schema": {"$ref": '#/definitions/Model.CountOut'}}.items()
    assert count_definition["consumes"] == count_definition["produces"] == [_JSON, _PROTO]


def test_create_oas_empty(model_oas):
    empty_definition = model_oas["paths"]["/model/methods/empty"]["post"]
    assert empty_definition["parameters"][0].items() >= {"in": "body", "schema": {"$ref": '#/definitions/Model.Empty'}}.items()
    assert empty_definition["responses"][200].items() >= {"schema": {"$ref": '#/definitions/Model.EmptyOut'}}.items()
    assert empty_definition["consumes"] == empty_definition["produces"] == [_JSON, _PROTO]


def test_create_oas_image(model_oas):
    rotate_image_definition = model_oas["paths"]["/model/methods/rotate_image"]["post"]
    assert rotate_image_definition["parameters"][0].items() >= {"in": "body", "schema": {"$ref": '#/definitions/Model.Image'}}.items()
    assert rotate_image_definition["responses"][200].items() >= {"schema": {"$ref": '#/definitions/Model.Image'}}.items()
    assert rotate_image_definition["consumes"] == rotate_image_definition["produces"] == [_OCTET_STREAM]


def test_create_oas_dict(model_oas):
    handle_dict_definition = model_oas["paths"]["/model/methods/handle_dict"]["post"]
    assert handle_dict_definition["parameters"][0].items() >= {"in": "body", "schema": {"$ref": '#/definitions/Model.Dictionary'}}.items()
    assert handle_dict_definition["responses"][200].items() >= {"schema": {"$ref": '#/definitions/Model.Dictionary'}}.items()
    assert handle_dict_definition["consumes"] == handle_dict_definition["produces"] == [_JSON]


def test_create_oas_text_to_int(model_oas):
    handle_dict_definition = model_oas["paths"]["/model/methods/count_words"]["post"]
    assert handle_dict_definition["parameters"][0].items() >= {"in": "body", "schema": {"$ref": '#/definitions/Model.Text'}}.items()
    assert handle_dict_definition["responses"][200].items() >= {"schema": {"$ref": '#/definitions/Model.CountWordsOut'}}.items()
    assert handle_dict_definition["consumes"] == [_TEXT]
    assert handle_dict_definition["produces"] == [_JSON, _PROTO]


def test_create_oas_int_to_text(model_oas):
    handle_dict_definition = model_oas["paths"]["/model/methods/create_words"]["post"]
    assert handle_dict_definition["parameters"][0].items() >= {"in": "body", "schema": {"$ref": '#/definitions/Model.CreateWordsIn'}}.items()
    assert handle_dict_definition["responses"][200].items() >= {"schema": {"$ref": '#/definitions/Model.Text'}}.items()
    assert handle_dict_definition["consumes"] == [_JSON, _PROTO]
    assert handle_dict_definition["produces"] == [_TEXT]


@pytest.fixture()
def model_runner(model):
    runner = None
    try:
        with _run_model(model) as runner:

            yield runner
    except Exception:
        if runner is not None:
            output = runner._child.read()
            print(output.decode("utf-8"))
        raise


@pytest.fixture()
def runner_api(model_runner):
    yield model_runner.api


def test_runner(runner_api):
    '''Tests model runner basic usage'''

    # =============================================================================
    # verify artifact APIs
    # =============================================================================

    resp = runner_api.get('/model/artifacts/protobuf')
    assert 'text/plain' in resp.headers['Content-Type']

    resp = runner_api.get('/model/artifacts/metadata')
    assert resp.headers['Content-Type'] == _JSON


def test_runner_add(runner_api):

    # =============================================================================
    # add test
    # =============================================================================

    add_input = {'x': 1, 'y': 2}

    resp_json = runner_api.method('add', json=add_input)
    assert int(resp_json['value']) == 3

    resp_proto = runner_api.method('add', proto=add_input)
    assert resp_proto.value == 3


def test_runner_count(runner_api):

    # =============================================================================
    # count test
    # =============================================================================

    count_input = {'strings': ['a'] * 3 + ['b'] * 2 + ['c']}
    count_output = {'a': 3, 'b': 2, 'c': 1}

    resp_json = runner_api.method('count', json=count_input)
    assert {k: int(v) for k, v in resp_json['value'].items()} == count_output

    resp_proto = runner_api.method('count', proto=count_input)
    assert dict(resp_proto.value.items()) == count_output


def test_runner_empty(runner_api):

    # =============================================================================
    # no params test
    # =============================================================================

    empty_input = {}
    empty_output = 1

    resp_json = runner_api.method('empty', json=empty_input)
    assert int(resp_json['value']) == empty_output

    resp_proto = runner_api.method('empty', proto=empty_input)
    assert resp_proto.value == empty_output


def test_runner_image(runner_api):

    # =============================================================================
    # raw test image
    # =============================================================================

    with open(os.path.join(os.path.dirname(__file__), "data", "acumos_logo.png"), "rb") as f:
        raw_image_input = f.read()
    raw_image_output = raw_image_input

    resp_raw_image = runner_api._post_octet_stream('rotate_image', data=raw_image_input)
    assert resp_raw_image == raw_image_output


def test_runner_dict(runner_api):

    # =============================================================================
    # raw test dict
    # =============================================================================

    raw_dict_input = dict(a=1, b=2)
    raw_dict_output = raw_dict_input

    resp_raw_dict = runner_api._post_json('handle_dict', data=raw_dict_input)
    assert resp_raw_dict == raw_dict_output


def test_runner_count_words(runner_api, model_runner):

    # =============================================================================
    # raw test count words
    # =============================================================================

    text_input = " ".join(["abcd"] * 10)
    value = 10

    resp_raw_json = runner_api._post_text_stream('count_words', data=text_input, accept=_JSON)
    # protobuf.json_format.MessageToJson converts int to str
    assert json.loads(resp_raw_json.decode())["value"] == str(value)


def test_runner_create_words(runner_api, model_runner):

    # =============================================================================
    # raw test create words
    # =============================================================================

    input_data = dict(n=10)
    text_output = " ".join(["éééé"] * 10)

    raw_text_response = runner_api._post_json('create_words', data=input_data, convert=False, accept=_TEXT)
    assert raw_text_response.decode() == text_output


def test_runner_headers(runner_api):

    # =============================================================================
    # headers test
    # =============================================================================

    add_input = {'x': 1, 'y': 2}

    try:
        runner_api.method('add', json=add_input, headers={})
    except requests.HTTPError as err:
        assert err.response.status_code == 400

    try:
        runner_api.method('add', json=add_input, headers={'Content-Type': _JSON, 'Accept': 'invalid'})
    except requests.HTTPError as err:
        assert err.response.status_code == 415


def test_cors(model):
    '''Tests model runner CORS'''

    # test CORS is disabled by default
    with _run_model(model) as runner:
        url = runner.api.resolve_method('count')
        headers = requests.options(url).headers
        assert 'Access-Control-Allow-Origin' not in headers

    # test wildcard
    with _run_model(model, options={'cors': "'*'"}) as runner:
        url = runner.api.resolve_method('count')
        headers = requests.options(url).headers
        assert headers['Access-Control-Allow-Origin'] == '*'

    # test specific origin
    with _run_model(model, options={'cors': 'foobar.com'}) as runner:
        url = runner.api.resolve_method('count')
        headers = requests.options(url).headers
        assert headers['Access-Control-Allow-Origin'] == 'foobar.com'


if __name__ == '__main__':
    '''Test area'''
    pytest.main([__file__, ])
