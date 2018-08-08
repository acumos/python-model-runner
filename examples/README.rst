.. ===============LICENSE_START=======================================================
.. Acumos CC-BY-4.0
.. ===================================================================================
.. Copyright (C) 2017-2018 AT&T Intellectual Property & Tech Mahindra. All rights reserved.
.. ===================================================================================
.. This Acumos documentation file is distributed by AT&T and Tech Mahindra
.. under the Creative Commons Attribution 4.0 International License (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..      http://creativecommons.org/licenses/by/4.0
..
.. This file is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.
.. ===============LICENSE_END=========================================================

===================================
Acumos Python Model Runner Examples
===================================

This directory provides example scripts that demonstrate how to use the model runner.

example_model.py
================

Invoking this script creates an Acumos model and saves it to a directory ``example-model``. This model can then be used with the model runner.

.. code:: bash

    $ python example_model.py
    $ acumos_model_runner example-model/

chain_models.py
===============

This script shows how one can combine multiple Acumos models in a chain of operations.
