# -*- coding: utf-8 -*-
# ===============LICENSE_START=======================================================
# Acumos Apache-2.0
# ===================================================================================
# Copyright (C) 2017-2020 AT&T Intellectual Property & Tech Mahindra. All rights reserved.
# Modifications Copyright (C) 2020 Nordix Foundation.
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
Provides utilities for generating an Open API specification from protobuf IDL and model metadata
"""
import yaml
from collections import namedtuple
from jinja2 import Environment, FileSystemLoader

from acumos_model_runner.proto_parser import Message, RepeatedField, MapField, Enum, parse_proto
from acumos_model_runner.utils import data_path
from acumos_model_runner.api import _PROTO, _JSON, _OCTET_STREAM, _TEXT


class TemplateError(Exception):
    pass


_OasFormat = namedtuple('_OasFormat', 'type, format, description')
_OasFormat.__new__.__defaults__ = (None, None, None)

_64NOTE = 'Note: 64-bit integers are string-encoded when using application/json'

_PROTO_OAS_MAP = {
    'double': _OasFormat('number', 'double'),
    'float': _OasFormat('number', 'float'),
    'int32': _OasFormat('integer', 'int32'),
    'int64': _OasFormat('integer', 'int64', _64NOTE),
    'uint32': _OasFormat('integer', 'int32'),
    'uint64': _OasFormat('integer', 'int64', _64NOTE),
    'sint32': _OasFormat('integer', 'int32'),
    'sint64': _OasFormat('integer', 'int64', _64NOTE),
    'fixed32': _OasFormat('integer', 'int32'),
    'fixed64': _OasFormat('integer', 'int64', _64NOTE),
    'sfixed32': _OasFormat('integer', 'int32'),
    'sfixed64': _OasFormat('integer', 'int64', _64NOTE),
    'bool': _OasFormat('boolean'),
    'string': _OasFormat('string'),
    'bytes': _OasFormat('string', 'byte')}


def create_oas(metadata, protobuf):
    '''Returns an OAS YAML string'''
    top_level = parse_proto(protobuf)
    schema = metadata["schema"]
    version = schema[schema.index(":") + 1:]
    current_version = tuple(map(int, version.split('.')))
    version_dir = version
    major_minor = current_version[:2]
    protobuf_defs = _create_definitions(top_level)

    if major_minor >= (0, 6):
        raw_defs = _create_raw_types_definitions(metadata["methods"])
    else:
        raw_defs = {}

    if major_minor > (0, 6):
        raise Exception('Latest supported schema is 0.6.*')
    elif major_minor < (0, 6):
        # older schema are converted to 0.6.0
        version_dir = '0.6.0'

    all_defs = {**protobuf_defs, **raw_defs}

    defs_yaml = yaml.dump(all_defs, default_flow_style=False)
    methods = [_format_method(name, method, major_minor) for name, method in metadata['methods'].items()]
    template_path = data_path('templates', version_dir)
    env = Environment(loader=FileSystemLoader(template_path), trim_blocks=True)
    gen_yaml = env.get_template('base.yaml').render(model=metadata, methods=methods, definitions=defs_yaml)
    return gen_yaml


def _format_method(name, method, major_minor):
    '''Returns a method dict to be used in the method template'''
    method_fmt = dict(name=name, **method)
    for key in ('input', 'output'):
        method_fmt[key] = method[key]
        # 0.6.0 input, output are objects not just strings
        if major_minor == (0, 6):
            method_fmt[key] = method[key]
            method_fmt[key]['name'] = _prefix_name(method[key]['name'])
            if _PROTO in method_fmt[key]["media_type"]:
                # If the method accepts/produces protobuf, then it also accepts/produces json
                method_fmt[key]["media_type"] = [_JSON, _PROTO]
        else:
            # older method when input, output were strings
            # convert to 0.6.0 format
            method_fmt[key] = {"name": _prefix_name(method[key]), "media_type": [_JSON, _PROTO]}

    return method_fmt


def _create_definitions(top_level):
    '''Returns OAS definitions for all protobuf top-level definitions'''
    refs = {ref for item in top_level for ref in _find_refs(item)}
    defs = {name: definition for item in top_level for name, definition in _find_definitions(item, refs)}
    defs_prefixed = {_prefix_name(key): val for key, val in defs.items()}
    return defs_prefixed


def _create_raw_types_definitions(methods):
    '''Returns OAS definitions for all raw type definitions'''
    raw_types = {}
    for method in methods.values():
        for key in 'input', 'output':
            type_def = method[key]
            type_name = _prefix_name(type_def['name'])
            media_type = type_def['media_type'][0]

            if type_name in raw_types:
                # type already registered
                continue

            if media_type == _PROTO:
                # protobuf types are handled in _create_definitions
                continue

            if media_type == _JSON:
                _def = {"type": "object"}

            elif media_type == _TEXT:
                _def = {"type": "string"}

            elif media_type == _OCTET_STREAM:
                _def = {"type": "string", "format": "binary"}

            else:
                raise TemplateError(f"Unknown media type {media_type}")

            _def["description"] = type_def['description'] or ""

            metadata = type_def.get('metadata', None)
            if metadata:
                # user-defined fields must start with 'x-'
                _def["x-metadata"] = metadata

            raw_types[type_name] = _def

    return raw_types


def _find_refs(item, root=()):
    '''Yields tuples representing a hierarchy of custom named types'''
    yield root + (item.name, )
    if isinstance(item, Message):
        child_root = root + (item.name, )
        for enum in item.enums:
            yield child_root + (enum.name, )
        for msg in item.messages:
            yield from _find_refs(msg, child_root)


def _find_definitions(item, refs, prefix=()):
    '''Yields OAS definitions contained within a top-level protobuf definition'''
    if isinstance(item, Message):
        yield from _find_message_definitions(item, refs, prefix)
    elif isinstance(item, Enum):
        yield _define_enum(item, prefix)
    else:
        raise TemplateError("Cannot create definition item {}".format(item))


def _find_message_definitions(message, refs, prefix):
    '''Yields OAS definitions contained within to a protobuf message'''
    scope = prefix + (message.name, )

    for enum in message.enums:
        yield _define_enum(enum, scope)

    for msg in message.messages:
        yield from _find_message_definitions(msg, refs, scope)

    properties = {field.name: _define_field(field, refs, scope) for field in message.fields}

    def_obj = {'type': 'object'}
    if properties:
        # Swagger 2.0 spec REQUIRES a non-empty list of required fields
        # only add properties and required if there are fields.
        def_obj['required'] = sorted(properties.keys())
        def_obj['properties'] = properties
    def_name = ".".join(scope)
    yield def_name, def_obj


def _define_enum(enum, prefix):
    '''Returns an OAS object corresponding to a protobuf enum'''
    def_name = ".".join(prefix + (enum.name, ))
    return def_name, {'type': 'string', 'enum': enum.enums}


def _define_field(field, refs, prefix):
    '''Returns an OAS object corresponding to a protobuf field'''
    if isinstance(field, MapField):
        field_type = _resolve_type(field.val_type, refs, prefix)
        return {'type': 'object', 'additionalProperties': field_type}
    else:
        field_type = _resolve_type(field.type, refs, prefix)
        if isinstance(field, RepeatedField):
            return {'type': 'array', 'items': field_type}
        else:
            return field_type


def _resolve_type(type_name, refs, prefix):
    '''Returns an OAS object corresponding to a protobuf type. Returns a reference for named types'''
    if type_name in _PROTO_OAS_MAP:
        oas_type = _PROTO_OAS_MAP[type_name]
        return {k: v for k, v in oas_type._asdict().items() if v is not None}
    else:
        ref_tuple = _resolve_named_type(type_name, refs, prefix)
        ref_str = "#/definitions/{}".format(_prefix_name(".".join(ref_tuple)))
        return {'$ref': ref_str}


def _resolve_named_type(type_name, refs, prefix):
    '''Returns the full identifier for a given named type'''
    type_idents = tuple(type_name.split('.'))

    # look within the most local scope first, and gradually move towards global scope
    for i in reversed(range(len(prefix) + 1)):
        full_ident = prefix[:i] + type_idents
        if full_ident in refs:
            return full_ident
    else:
        raise TemplateError("Failed to find a reference for named type {}".format('/'.join(prefix + type_idents)))


def _prefix_name(name):
    '''Adds a "Model" prefix to type names to avoid naming collisions'''
    return "Model.{}".format(name)
